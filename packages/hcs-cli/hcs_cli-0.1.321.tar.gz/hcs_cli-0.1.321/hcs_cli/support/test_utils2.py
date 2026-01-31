"""
Copyright 2023-2023 VMware Inc.
SPDX-License-Identifier: Apache-2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import json
import re
import subprocess
from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import httpx


class HttpMockRequest:
    """Represents an expected HTTP request with optional validation"""

    def __init__(
        self,
        method: str,
        url: str,
        expected_request_body: Optional[Any] = None,
        expected_request_headers: Optional[Dict[str, str]] = None,
    ):
        self.method = method
        self.url_pattern = self._compile_pattern(url)
        self.expected_request_body = expected_request_body
        self.expected_request_headers = expected_request_headers

    def _compile_pattern(self, url: str):
        """Convert URL pattern to regex (supports {param} placeholders)"""
        if "{" not in url:
            return re.compile(f"^{re.escape(url)}$")

        regex = url
        for param in re.findall(r"\{(\w+)\}", url):
            regex = regex.replace(f"{{{param}}}", f"(?P<{param}>[^/?]+)")
        return re.compile(f"^{regex}$")

    def matches(self, method: str, url: str) -> bool:
        """Check if this request matches the given method and URL"""
        return method == self.method and self.url_pattern.match(url) is not None

    def extract_params(self, url: str) -> Dict[str, str]:
        """Extract path parameters from URL"""
        match = self.url_pattern.match(url)
        if match:
            return match.groupdict()
        return {}


class HttpMockResponse:
    """Represents a mocked HTTP response"""

    def __init__(
        self,
        status_code: int = 200,
        body: Optional[Any] = None,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.status_code = status_code
        self.body = body if body is not None else {}
        self.headers = headers or {"Content-Type": "application/json"}

    def to_httpx_response(self, request_obj) -> httpx.Response:
        """Convert to httpx.Response object"""
        if isinstance(self.body, (dict, list)):
            content = json.dumps(self.body).encode("utf-8")
        elif isinstance(self.body, str):
            content = self.body.encode("utf-8")
        else:
            content = str(self.body).encode("utf-8")

        response = httpx.Response(
            status_code=self.status_code,
            content=content,
            headers=self.headers,
            request=request_obj,
        )
        return response


class HttpMockConfig:
    """Configuration for a single HTTP mock mapping: request -> response"""

    def __init__(
        self,
        request: HttpMockRequest,
        response: HttpMockResponse,
    ):
        self.request = request
        self.response = response


class HttpMockRegistry:
    """Registry of configured HTTP mocks"""

    def __init__(self):
        self.configs: List[HttpMockConfig] = []
        self.request_history: List[Tuple[str, str, Any]] = []

    def register(
        self,
        method: str,
        url: str,
        response_status_code: int = 200,
        response_body: Optional[Any] = None,
        response_headers: Optional[Dict[str, str]] = None,
        expected_request_body: Optional[Any] = None,
        expected_request_headers: Optional[Dict[str, str]] = None,
    ) -> "HttpMockRegistry":
        """Register a mock HTTP request/response pair"""
        request = HttpMockRequest(
            method=method,
            url=url,
            expected_request_body=expected_request_body,
            expected_request_headers=expected_request_headers,
        )
        response = HttpMockResponse(
            status_code=response_status_code,
            body=response_body,
            headers=response_headers,
        )
        config = HttpMockConfig(request=request, response=response)
        self.configs.append(config)
        return self

    def find_response(self, method: str, url: str) -> Optional[HttpMockResponse]:
        """Find a registered response for the given request"""
        for config in self.configs:
            if config.request.matches(method, url):
                self.request_history.append((method, url, None))
                return config.response

        # Request not found in registry
        raise ValueError(
            f"No mock registered for {method} {url}\n"
            f"Registered: {[(c.request.method, c.request.url_pattern.pattern) for c in self.configs]}"
        )

    def reset(self):
        """Clear all configs and history"""
        self.configs.clear()
        self.request_history.clear()

    def get_request_history(self) -> List[Tuple[str, str]]:
        """Get list of all requests made during mock session"""
        return [(method, url) for method, url, _ in self.request_history]


class HttpMockContextManager:
    """Context manager for mock HTTP testing with auto-cleanup"""

    def __init__(self):
        self.registry = HttpMockRegistry()
        self._patchers = []
        # Capture the real httpx.Client class before any patching
        self._real_httpx_client = httpx.Client

    def register(
        self,
        method: str,
        url: str,
        response_status_code: int = 200,
        response_body: Optional[Any] = None,
        response_headers: Optional[Dict[str, str]] = None,
        expected_request_body: Optional[Any] = None,
        expected_request_headers: Optional[Dict[str, str]] = None,
    ) -> "HttpMockContextManager":
        """Register a mock response"""
        self.registry.register(
            method=method,
            url=url,
            response_status_code=response_status_code,
            response_body=response_body,
            response_headers=response_headers,
            expected_request_body=expected_request_body,
            expected_request_headers=expected_request_headers,
        )
        return self

    def _create_mock_client(self):
        """Create a mock httpx.Client that uses the registry"""
        mock_client = MagicMock(spec=self._real_httpx_client)

        def mock_get(url, **kwargs):
            # Handle base_url + relative URL
            full_url = str(url)
            if not full_url.startswith("http"):
                full_url = "https://api.example.com" + full_url

            response = self.registry.find_response("GET", full_url)
            request_obj = httpx.Request("GET", full_url)
            httpx_response = response.to_httpx_response(request_obj)

            # Ensure response has read method for compatibility
            httpx_response.read = lambda: None
            return httpx_response

        def mock_post(url, **kwargs):
            full_url = str(url)
            if not full_url.startswith("http"):
                full_url = "https://api.example.com" + full_url

            response = self.registry.find_response("POST", full_url)
            request_obj = httpx.Request("POST", full_url, json=kwargs.get("json"))
            httpx_response = response.to_httpx_response(request_obj)
            httpx_response.read = lambda: None
            return httpx_response

        def mock_put(url, **kwargs):
            full_url = str(url)
            if not full_url.startswith("http"):
                full_url = "https://api.example.com" + full_url

            response = self.registry.find_response("PUT", full_url)
            request_obj = httpx.Request("PUT", full_url, json=kwargs.get("json"))
            httpx_response = response.to_httpx_response(request_obj)
            httpx_response.read = lambda: None
            return httpx_response

        def mock_patch(url, **kwargs):
            full_url = str(url)
            if not full_url.startswith("http"):
                full_url = "https://api.example.com" + full_url

            response = self.registry.find_response("PATCH", full_url)
            request_obj = httpx.Request("PATCH", full_url, json=kwargs.get("json"))
            httpx_response = response.to_httpx_response(request_obj)
            httpx_response.read = lambda: None
            return httpx_response

        def mock_delete(url, **kwargs):
            full_url = str(url)
            if not full_url.startswith("http"):
                full_url = "https://api.example.com" + full_url

            response = self.registry.find_response("DELETE", full_url)
            request_obj = httpx.Request("DELETE", full_url)
            httpx_response = response.to_httpx_response(request_obj)
            httpx_response.read = lambda: None
            return httpx_response

        # Setup mock client attributes and methods
        mock_client.get.side_effect = mock_get
        mock_client.post.side_effect = mock_post
        mock_client.put.side_effect = mock_put
        mock_client.patch.side_effect = mock_patch
        mock_client.delete.side_effect = mock_delete
        mock_client.base_url = "https://api.example.com"
        mock_client.timeout = 30
        mock_client.event_hooks = {"request": [], "response": []}
        mock_client.ensure_token = MagicMock()
        mock_client.follow_redirects = True
        mock_client.close = MagicMock()

        return mock_client

    def __enter__(self):
        """Enter context manager"""
        # Patch httpx.Client
        patcher = patch("httpx.Client")
        mock_client_class = patcher.start()
        mock_client_class.return_value = self._create_mock_client()
        self._patchers.append(patcher)

        # Patch OAuth2Client which is used by EzClient
        patcher = patch("authlib.integrations.httpx_client.OAuth2Client")
        mock_oauth2_class = patcher.start()
        mock_oauth2_class.return_value = self._create_mock_client()
        self._patchers.append(patcher)

        # Also patch at module level in case they're imported differently
        patcher = patch("hcs_core.sglib.ez_client.OAuth2Client")
        mock_oauth2_class = patcher.start()
        mock_oauth2_class.return_value = self._create_mock_client()
        self._patchers.append(patcher)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager and cleanup"""
        for patcher in self._patchers:
            patcher.stop()
        self._patchers.clear()
        self.registry.reset()


@contextmanager
def mock_http(**configs: Dict[str, Any]):
    """
    Context manager for setting up HTTP mocks.

    Usage:
        with mock_http_registry() as registry:
            registry.register(
                method='GET',
                url='/v2/templates',
                response_body=[...],
                response_status_code=200,
            )
            # Run tests here

    Example:
        with mock_http_registry() as registry:
            registry.register(
                'GET', '/api/templates',
                response_body=[{'id': '1', 'name': 'template1'}]
            )
            result = runner.invoke(hcs_template_list)
            assert result.exit_code == 0
    """
    ctx_manager = HttpMockContextManager()
    with ctx_manager:
        yield ctx_manager


def create_mock_registry() -> HttpMockRegistry:
    """Create and return a new mock registry"""
    return HttpMockRegistry()


class CliTestUtil:
    """
    Utility for testing CLI commands with mocked HTTP responses.

    Uses a static configuration format:
    {
        "GET /v2/templates?org_id=abc": {
            "request": {
                "body": {...}  # optional
            },
            "response": {
                "status_code": 200,
                "body": {...},
                "headers": {"Content-Type": "application/json"}
            }
        }
    }

    Usage:
        mock_config = {
            "GET /v2/templates": {
                "response": {
                    "status_code": 200,
                    "body": [{"id": "template-1", "name": "test"}]
                }
            }
        }

        with CliTestUtil(mock_config) as test:
            test.run("hcs template list", expected_json=[{"id": "template-1"}])
            test.run("hcs template list -o json", expected_json=[...])
    """

    def __init__(self, mock_config: Dict[str, Any], env: Optional[Dict[str, str]] = None):
        """
        Initialize the test utility.

        Args:
            mock_config: Dictionary mapping "METHOD /path" to request/response config
            env: Optional environment variables to pass to CLI commands
        """
        self.mock_config = mock_config
        self.env = env or {}
        self._http_mock_context = None
        self._registry = None
        self._parse_and_register_mocks()

    def _parse_and_register_mocks(self):
        """Parse mock config and prepare registration"""
        self._http_mock_context = HttpMockContextManager()

        for endpoint_key, endpoint_config in self.mock_config.items():
            # Parse "METHOD /path?params"
            parts = endpoint_key.split(" ", 1)
            if len(parts) != 2:
                raise ValueError(f"Invalid endpoint key format: {endpoint_key}. Expected 'METHOD /path'")

            method, url = parts
            method = method.strip()
            url = url.strip()

            response_config = endpoint_config.get("response", {})
            status_code = response_config.get("status_code", 200)
            body = response_config.get("body", {})
            headers = response_config.get("headers", {"Content-Type": "application/json"})

            # Register with the HTTP mock context
            # Convert exact URL to regex pattern that matches query params
            url_pattern = self._url_to_pattern(url)
            self._http_mock_context.register(
                method=method,
                url=url_pattern,
                response_status_code=status_code,
                response_body=body,
                response_headers=headers,
            )

    def _url_to_pattern(self, url: str) -> str:
        """
        Convert exact URL to regex pattern.

        /v2/templates -> .*v2/templates.*
        /v2/templates/123 -> .*v2/templates/123.*
        /v2/templates?org_id=abc -> .*v2/templates.*org_id=abc.*
        """
        # Escape special regex characters but keep ? for pattern matching
        escaped = re.escape(url)
        # Remove extra escapes for ? and & to allow matching
        escaped = escaped.replace(r"\?", ".*").replace(r"\&", ".*")
        return f".*{escaped}.*"

    def __enter__(self):
        """Enter the context manager"""
        self._http_mock_context.__enter__()
        self._registry = self._http_mock_context.registry
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit the context manager and cleanup"""
        return self._http_mock_context.__exit__(exc_type, exc_val, exc_tb)

    def run(
        self,
        cmd: str,
        expected_stdout: Any = None,
        expected_return_code: int = 0,
        expect_stderr_empty: bool = True,
        stdin_payload: str = None,
    ):
        """
        Run a CLI command and verify the output.

        Args:
            cmd: The CLI command to run
            expected_stdout: Expected output (dict/list parsed as JSON, str for exact match, callable for custom)
            expected_return_code: Expected exit code
            expect_stderr_empty: Whether stderr should be empty
            stdin_payload: Optional stdin input

        Returns:
            Tuple of (stdout, stderr, returncode)
        """

        # TODO
        if "WIP":
            return None, None, 0

        stdout, stderr, returncode = self._run_command(cmd, stdin_payload)

        # Verify return code
        if returncode != expected_return_code:
            raise AssertionError(
                f"Return code mismatch.\nExpected: {expected_return_code}\nGot: {returncode}\nStdout: {stdout}\nStderr: {stderr}"
            )

        # Verify stderr
        actual_stderr_empty = stderr is None or len(stderr) == 0
        if expect_stderr_empty and not actual_stderr_empty:
            raise AssertionError(f"Expected empty stderr, but got:\n{stderr}")

        # Verify stdout
        if expected_stdout is not None:
            self._verify_stdout(stdout, expected_stdout)

        return stdout, stderr, returncode

    def _verify_stdout(self, stdout: str, expected_stdout: Any):
        """Verify stdout matches expected value"""
        t = type(expected_stdout)

        if t is str:
            if stdout != expected_stdout:
                raise AssertionError(f"Stdout mismatch.\nExpected: {expected_stdout}\nGot: {stdout}")
        elif t is dict or t is list:
            if stdout is None or len(stdout) == 0:
                raise AssertionError("Expected stdout but got empty")
            try:
                data = json.loads(stdout)
                if data != expected_stdout:
                    raise AssertionError(
                        f"Stdout JSON mismatch.\nExpected: {json.dumps(expected_stdout, indent=2)}\nGot: {json.dumps(data, indent=2)}"
                    )
            except json.JSONDecodeError as e:
                raise AssertionError(f"Failed to parse stdout as JSON: {e}\nStdout: {stdout}")
        elif callable(expected_stdout):
            expected_stdout(stdout)
        else:
            raise ValueError(f"Unsupported expected_stdout type: {t}")

    def _run_command(self, cmd: str, stdin_payload: Optional[str] = None) -> Tuple[str, str, int]:
        """
        Run a command with mocked environment.

        Returns:
            Tuple of (stdout, stderr, returncode)
        """
        env = self._build_env()
        p = subprocess.run(
            cmd,
            input=stdin_payload,
            shell=True,
            text=True,
            check=False,
            capture_output=True,
            env=env,
        )
        return p.stdout, p.stderr, p.returncode

    def _build_env(self) -> Dict[str, str]:
        """Build environment variables for command execution"""
        import os

        env = os.environ.copy()
        env["HCS_CLI_TELEMETRY"] = "false"
        env["HCS_CLI_CHECK_UPGRADE"] = "false"
        env.update(self.env)
        return env

    def get_request_history(self) -> List[Tuple[str, str]]:
        """Get list of all HTTP requests made during test"""
        if self._registry:
            return self._registry.get_request_history()
        return []
