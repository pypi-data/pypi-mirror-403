"""
Microsoft Graph API implementation for SharePoint operations.
Primary API for all SharePoint operations in Azure Government Cloud.
"""
import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, quote
import requests

logger = logging.getLogger(__name__)


class GraphAPIClient:
    """
    Microsoft Graph API client for SharePoint operations.
    Primary client for all SharePoint operations, especially in Azure Government Cloud
    where SharePoint REST API may not support app-only authentication.
    """

    def __init__(self, site_url: str, token_callback):
        """
        Initialize Graph API client.

        Args:
            site_url: SharePoint site URL (e.g., https://tenant.sharepoint.us/sites/SiteName)
            token_callback: Function that returns access token
        """
        self.site_url = site_url.rstrip("/")
        self.token_callback = token_callback
        self._site_id = None
        self._drive_id = None  # Cache drive ID to avoid repeated API calls

        # Determine Graph API endpoint based on cloud
        if ".sharepoint.us" in site_url:
            self.graph_endpoint = "https://graph.microsoft.us/v1.0"
            logger.info("Using Microsoft Graph US Government endpoint")
        else:
            self.graph_endpoint = "https://graph.microsoft.com/v1.0"
            logger.info("Using Microsoft Graph Commercial endpoint")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with access token."""
        logger.debug("Getting authorization headers...")
        token_obj = self.token_callback()
        # Handle both TokenResponse objects and plain strings
        if hasattr(token_obj, 'accessToken'):
            token = token_obj.accessToken
        else:
            token = str(token_obj)

        logger.debug(f"Token acquired for headers (length: {len(token)}, starts with: {token[:20]}...)")

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _handle_response(self, response: requests.Response) -> None:
        """
        Handle Graph API response and raise detailed errors if needed.

        Graph API returns errors in format:
        {
          "error": {
            "code": "itemNotFound",
            "message": "The resource could not be found."
          }
        }
        """
        if response.ok:
            return

        try:
            error_data = response.json()
            if "error" in error_data:
                error = error_data["error"]
                code = error.get("code", "Unknown")
                message = error.get("message", "Unknown error")
                raise requests.HTTPError(
                    f"Graph API error [{code}]: {message}",
                    response=response
                )
        except (ValueError, KeyError):
            # If we can't parse the error, fall back to standard handling
            pass

        self._handle_response(response)

    def _get_site_id(self) -> str:
        """
        Get the site ID from the site URL.
        Caches the result for reuse.
        """
        if self._site_id:
            logger.debug(f"Using cached site ID: {self._site_id}")
            return self._site_id

        parsed = urlparse(self.site_url)
        hostname = parsed.netloc
        path = parsed.path.strip("/")

        # For root site: https://tenant.sharepoint.us
        if not path or path == "sites":
            url = f"{self.graph_endpoint}/sites/{hostname}"
        # For subsite: https://tenant.sharepoint.us/sites/SiteName
        else:
            url = f"{self.graph_endpoint}/sites/{hostname}:/{path}"

        logger.info(f"Fetching site ID from: {url}")
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            self._site_id = response.json()["id"]
            logger.info(f"Retrieved site ID: {self._site_id}")
            return self._site_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting site ID: {type(e).__name__}: {e}", exc_info=True)
            raise

    def _get_drive_id(self) -> str:
        """
        Get the default document library drive ID.
        Caches the result for reuse.
        """
        if self._drive_id:
            logger.debug(f"Using cached drive ID: {self._drive_id}")
            return self._drive_id

        site_id = self._get_site_id()
        url = f"{self.graph_endpoint}/sites/{site_id}/drive"

        logger.info(f"Fetching drive ID from: {url}")
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            self._drive_id = response.json()["id"]
            logger.info(f"Retrieved drive ID: {self._drive_id}")
            return self._drive_id
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting drive ID: {type(e).__name__}: {e}", exc_info=True)
            raise

    def list_folders(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """
        List folders in the specified path.

        Args:
            folder_path: Relative path from document library root

        Returns:
            List of folder objects with name, id, webUrl
        """
        logger.info(f"Listing folders in '{folder_path}'")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if folder_path:
            # URL encode the path
            encoded_path = quote(folder_path)
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root/children"

        logger.info(f"Fetching folders from: {url}")
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            items = response.json().get("value", [])
            # Filter to only folders
            folders = [
                {
                    "name": item["name"],
                    "id": item["id"],
                    "webUrl": item.get("webUrl", ""),
                }
                for item in items
                if "folder" in item
            ]

            logger.info(f"Found {len(folders)} folders in '{folder_path}'")
            return folders
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error listing folders: {type(e).__name__}: {e}", exc_info=True)
            raise

    def list_documents(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """
        List documents in the specified folder.

        Args:
            folder_path: Relative path from document library root

        Returns:
            List of file objects with name, id, size, webUrl
        """
        logger.info(f"Listing documents in '{folder_path}'")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if folder_path:
            encoded_path = quote(folder_path)
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root/children"

        logger.info(f"Fetching documents from: {url}")
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            items = response.json().get("value", [])
            # Filter to only files
            files = [
                {
                    "name": item["name"],
                    "id": item["id"],
                    "size": item.get("size", 0),
                    "webUrl": item.get("webUrl", ""),
                }
                for item in items
                if "file" in item
            ]

            logger.info(f"Found {len(files)} files in '{folder_path}'")
            return files
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error listing documents: {type(e).__name__}: {e}", exc_info=True)
            raise

    def get_file_content(self, file_path: str) -> bytes:
        """
        Get the content of a file.

        Args:
            file_path: Relative path to the file

        Returns:
            File content as bytes
        """
        logger.info(f"Getting content for file '{file_path}'")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        encoded_path = quote(file_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"

        logger.info(f"Fetching file content from: {url}")
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=60)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            logger.info(f"Retrieved content for '{file_path}' ({len(response.content)} bytes)")
            return response.content
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error getting file content: {type(e).__name__}: {e}", exc_info=True)
            raise

    def upload_file(self, folder_path: str, file_name: str, content: bytes) -> Dict[str, Any]:
        """
        Upload a file to SharePoint.

        Args:
            folder_path: Destination folder path
            file_name: Name of the file
            content: File content as bytes

        Returns:
            File metadata
        """
        logger.info(f"Uploading file '{file_name}' to '{folder_path}' ({len(content)} bytes)")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if folder_path:
            full_path = f"{folder_path}/{file_name}"
        else:
            full_path = file_name

        encoded_path = quote(full_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"

        logger.info(f"Uploading to: {url}")
        headers = self._get_headers()
        headers["Content-Type"] = "application/octet-stream"

        try:
            response = requests.put(url, headers=headers, data=content, timeout=120)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            logger.info(f"Successfully uploaded '{file_name}' to '{folder_path}'")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error uploading file: {type(e).__name__}: {e}", exc_info=True)
            raise

    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.

        Args:
            file_path: Relative path to the file
        """
        logger.info(f"Deleting file '{file_path}'")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        encoded_path = quote(file_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"

        logger.info(f"Deleting from: {url}")
        try:
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            logger.info(f"Successfully deleted '{file_path}'")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error deleting file: {type(e).__name__}: {e}", exc_info=True)
            raise

    def create_folder(self, parent_path: str, folder_name: str) -> Dict[str, Any]:
        """
        Create a new folder.

        Args:
            parent_path: Path to parent folder
            folder_name: Name of the new folder

        Returns:
            Folder metadata
        """
        logger.info(f"Creating folder '{folder_name}' in '{parent_path}'")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if parent_path:
            encoded_path = quote(parent_path)
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root/children"

        logger.info(f"Creating folder at: {url}")
        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }

        try:
            response = requests.post(url, headers=self._get_headers(), json=payload, timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            logger.info(f"Successfully created folder '{folder_name}' in '{parent_path}'")
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error creating folder: {type(e).__name__}: {e}", exc_info=True)
            raise

    def delete_folder(self, folder_path: str) -> None:
        """
        Delete a folder.

        Args:
            folder_path: Relative path to the folder
        """
        logger.info(f"Deleting folder '{folder_path}'")
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        encoded_path = quote(folder_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"

        logger.info(f"Deleting folder from: {url}")
        try:
            response = requests.delete(url, headers=self._get_headers(), timeout=30)
            logger.debug(f"Response status: {response.status_code}")
            self._handle_response(response)

            logger.info(f"Successfully deleted folder '{folder_path}'")
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error deleting folder: {type(e).__name__}: {e}", exc_info=True)
            raise
