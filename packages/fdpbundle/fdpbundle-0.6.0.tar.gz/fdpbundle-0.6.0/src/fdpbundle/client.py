"""API client for interacting with the FDP Workflow Engine."""

import json
import os
from typing import Any, Dict, Optional

import requests


class BundleClient:
    """Client for interacting with the Bundle Workflow Engine API."""

    def __init__(
        self,
        base_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the Workflow Engine (e.g., https://airflow.example.com/fdp_tools)
            username: Service account name (SERVICE_ACCOUNT_NAME)
            password: Service account token (SERVICE_ACCOUNT_TOKEN)
        """
        self.base_url = base_url.rstrip("/")
        self.api_base = f"{self.base_url}/v1"
        self.session = requests.Session()

        # Set default headers
        self.session.headers["Accept"] = "application/json"

        # Set authentication via Basic Auth
        if username and password:
            self.session.auth = (username, password)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make an HTTP request and handle common errors."""
        url = f"{self.api_base}{endpoint}"

        headers = kwargs.pop("headers", {})
        if "json" in kwargs:
            headers["Content-Type"] = "application/json"

        try:
            response = self.session.request(method, url, headers=headers, **kwargs)

            # Try to parse JSON response
            try:
                data = response.json()
            except json.JSONDecodeError:
                return {
                    "success": False, 
                    "error": f"Invalid JSON response: {response.text}",
                    "status_code": response.status_code
                }

            # Add status code to response
            data["status_code"] = response.status_code
            
            # Check for HTTP errors - but still return data if present
            if response.status_code >= 400:
                # If we have data, still include it (useful for validation errors)
                if "data" in data:
                    data["success"] = False
                    data["error"] = data.get("error", data.get("message", f"HTTP {response.status_code}"))
                else:
                    error_msg = data.get("error", data.get("message", f"HTTP {response.status_code}"))
                    return {
                        "success": False, 
                        "error": error_msg, 
                        "status_code": response.status_code,
                        "data": data.get("data")
                    }
            else:
                data["success"] = True

            return data

        except requests.exceptions.ConnectionError as e:
            return {"success": False, "error": f"Connection failed: {e}"}
        except requests.exceptions.Timeout as e:
            return {"success": False, "error": f"Request timeout: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Request failed: {e}"}

    def validate(self, spec: Dict[str, Any]) -> Dict[str, Any]:
        """Validate a bundle spec."""
        return self._request("POST", "/bundles/validate", json=spec)

    def import_bundle(
        self, spec: Dict[str, Any], set_as_current: bool = True
    ) -> Dict[str, Any]:
        """Import a bundle spec."""
        return self._request(
            "POST",
            "/bundles/import",
            params={"set_as_current": str(set_as_current).lower()},
            json=spec,
        )

    def diff(self, bundle_id: int, env: str = "dev") -> Dict[str, Any]:
        """Get diff for a bundle."""
        return self._request("GET", f"/bundles/{bundle_id}/diff", params={"env": env})

    def apply(
        self,
        bundle_id: int,
        env: str = "dev",
        dry_run: bool = False,
        version_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Apply a bundle to an environment."""
        kwargs: Dict[str, Any] = {
            "params": {"env": env, "dry_run": str(dry_run).lower()}
        }
        if version_id:
            kwargs["json"] = {"version_id": version_id}
        else:
            kwargs["json"] = {}

        return self._request("POST", f"/bundles/{bundle_id}/apply", **kwargs)

    def list_bundles(self, page: int = 1, page_size: int = 100) -> Dict[str, Any]:
        """List all bundles."""
        return self._request(
            "GET", "/bundles", params={"page": page, "page_size": page_size}
        )

    def get_bundle_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Find a bundle by name."""
        result = self.list_bundles()
        if result.get("success") or result.get("data"):
            items = result.get("data", {}).get("items", [])
            for bundle in items:
                if bundle.get("name") == name:
                    return bundle
        return None


def load_bundle_file(bundle_file: str) -> Dict[str, Any]:
    """Load and parse a bundle JSON file."""
    if not os.path.exists(bundle_file):
        raise FileNotFoundError(f"Bundle file not found: {bundle_file}")

    with open(bundle_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_bundle_name_from_file(bundle_file: str) -> str:
    """Extract bundle name from a bundle file."""
    spec = load_bundle_file(bundle_file)
    return spec.get("bundle", {}).get("name", "")
