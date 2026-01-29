from typing import Any

import httpx

from dooray_mcp.utils.config import config
from dooray_mcp.utils.errors import (
    ErrorType,
    DoorayError,
    create_api_error,
    create_auth_invalid_error,
    create_auth_missing_error,
    create_not_found_error,
)
from dooray_mcp.utils.logger import get_logger


logger = get_logger(__name__)


class DoorayClient:
    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    def _get_headers(self) -> dict[str, str]:
        api_key = config.api_key
        if not api_key:
            raise create_auth_missing_error()

        return {
            "Authorization": f"dooray-api {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=config.base_url,
                headers=self._get_headers(),
                timeout=30.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    def _parse_error_response(self, response: httpx.Response) -> str:
        try:
            data = response.json()
            if "header" in data:
                header = data["header"]
                if "message" in header:
                    return header["message"]
            return response.text
        except Exception:
            return response.text

    async def request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        client = await self._get_client()

        cleaned_params = None
        if params:
            cleaned_params = {k: v for k, v in params.items() if v is not None}

        logger.info(f"{method} {path}")

        response = await client.request(
            method=method,
            url=path,
            params=cleaned_params,
            json=json_data,
        )

        if response.status_code == 401:
            raise create_auth_invalid_error("Invalid API key or unauthorized access")

        if response.status_code == 404:
            raise create_not_found_error("Resource", path)

        if response.status_code >= 400:
            error_message = self._parse_error_response(response)
            raise create_api_error(error_message, response.status_code)

        return response.json()

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self.request("GET", path, params=params)

    async def post(
        self, path: str, json_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self.request("POST", path, json_data=json_data)

    async def put(
        self, path: str, json_data: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return await self.request("PUT", path, json_data=json_data)

    async def delete(self, path: str) -> dict[str, Any]:
        return await self.request("DELETE", path)


dooray_client = DoorayClient()
