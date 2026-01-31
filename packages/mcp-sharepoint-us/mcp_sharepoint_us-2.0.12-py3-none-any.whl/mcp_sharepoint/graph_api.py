"""
Microsoft Graph API implementation for SharePoint operations
Used as a fallback when SharePoint REST API doesn't support app-only tokens
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
    Fallback for when SharePoint REST API doesn't support app-only authentication.
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

        # Determine Graph API endpoint based on cloud
        if ".sharepoint.us" in site_url:
            self.graph_endpoint = "https://graph.microsoft.us/v1.0"
            logger.info("Using Microsoft Graph US Government endpoint")
        else:
            self.graph_endpoint = "https://graph.microsoft.com/v1.0"
            logger.info("Using Microsoft Graph Commercial endpoint")

    def _get_headers(self) -> Dict[str, str]:
        """Get authorization headers with access token."""
        token_obj = self.token_callback()
        # Handle both TokenResponse objects and plain strings
        if hasattr(token_obj, 'accessToken'):
            token = token_obj.accessToken
        else:
            token = str(token_obj)

        return {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        }

    def _get_site_id(self) -> str:
        """
        Get the site ID from the site URL.
        Caches the result for reuse.
        """
        if self._site_id:
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

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        self._site_id = response.json()["id"]
        logger.info(f"Retrieved site ID: {self._site_id}")
        return self._site_id

    def _get_drive_id(self) -> str:
        """Get the default document library drive ID."""
        site_id = self._get_site_id()
        url = f"{self.graph_endpoint}/sites/{site_id}/drive"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        drive_id = response.json()["id"]
        logger.info(f"Retrieved drive ID: {drive_id}")
        return drive_id

    def list_folders(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """
        List folders in the specified path.

        Args:
            folder_path: Relative path from document library root

        Returns:
            List of folder objects with name, id, webUrl
        """
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if folder_path:
            # URL encode the path
            encoded_path = quote(folder_path)
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root/children"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

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

    def list_documents(self, folder_path: str = "") -> List[Dict[str, Any]]:
        """
        List documents in the specified folder.

        Args:
            folder_path: Relative path from document library root

        Returns:
            List of file objects with name, id, size, webUrl
        """
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if folder_path:
            encoded_path = quote(folder_path)
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root/children"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

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

    def get_file_content(self, file_path: str) -> bytes:
        """
        Get the content of a file.

        Args:
            file_path: Relative path to the file

        Returns:
            File content as bytes
        """
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        encoded_path = quote(file_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"

        response = requests.get(url, headers=self._get_headers())
        response.raise_for_status()

        logger.info(f"Retrieved content for '{file_path}' ({len(response.content)} bytes)")
        return response.content

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
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if folder_path:
            full_path = f"{folder_path}/{file_name}"
        else:
            full_path = file_name

        encoded_path = quote(full_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/content"

        headers = self._get_headers()
        headers["Content-Type"] = "application/octet-stream"

        response = requests.put(url, headers=headers, data=content)
        response.raise_for_status()

        logger.info(f"Uploaded '{file_name}' to '{folder_path}'")
        return response.json()

    def delete_file(self, file_path: str) -> None:
        """
        Delete a file.

        Args:
            file_path: Relative path to the file
        """
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        encoded_path = quote(file_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"

        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()

        logger.info(f"Deleted '{file_path}'")

    def create_folder(self, parent_path: str, folder_name: str) -> Dict[str, Any]:
        """
        Create a new folder.

        Args:
            parent_path: Path to parent folder
            folder_name: Name of the new folder

        Returns:
            Folder metadata
        """
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        if parent_path:
            encoded_path = quote(parent_path)
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}:/children"
        else:
            url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root/children"

        payload = {
            "name": folder_name,
            "folder": {},
            "@microsoft.graph.conflictBehavior": "fail"
        }

        response = requests.post(url, headers=self._get_headers(), json=payload)
        response.raise_for_status()

        logger.info(f"Created folder '{folder_name}' in '{parent_path}'")
        return response.json()

    def delete_folder(self, folder_path: str) -> None:
        """
        Delete a folder.

        Args:
            folder_path: Relative path to the folder
        """
        site_id = self._get_site_id()
        drive_id = self._get_drive_id()

        encoded_path = quote(folder_path)
        url = f"{self.graph_endpoint}/sites/{site_id}/drives/{drive_id}/root:/{encoded_path}"

        response = requests.delete(url, headers=self._get_headers())
        response.raise_for_status()

        logger.info(f"Deleted folder '{folder_path}'")
