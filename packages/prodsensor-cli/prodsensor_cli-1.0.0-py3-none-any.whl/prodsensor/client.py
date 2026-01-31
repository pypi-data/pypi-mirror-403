"""
ProdSensor API Client
Handles communication with the ProdSensor API
"""

import os
import time
import logging
from typing import Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import httpx

logger = logging.getLogger(__name__)


class AnalysisStatus(str, Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class Verdict(str, Enum):
    PRODUCTION_READY = "PRODUCTION_READY"
    NOT_PRODUCTION_READY = "NOT_PRODUCTION_READY"
    CONDITIONALLY_READY = "CONDITIONALLY_READY"


@dataclass
class AnalysisResult:
    """Result of a production readiness analysis"""
    run_id: str
    status: AnalysisStatus
    verdict: Optional[Verdict] = None
    score: Optional[int] = None
    blocker_count: int = 0
    major_count: int = 0
    minor_count: int = 0
    report_url: Optional[str] = None
    error: Optional[str] = None


class ApiError(Exception):
    """API request error"""
    def __init__(self, message: str, status_code: int = 0):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class AuthError(ApiError):
    """Authentication error"""
    pass


class RateLimitError(ApiError):
    """Rate limit exceeded error"""
    def __init__(self, retry_after: int = 3600):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after} seconds.", 429)


class ProdSensorClient:
    """Client for the ProdSensor API"""

    DEFAULT_API_URL = "https://ps-production-5531.up.railway.app"
    CONFIG_DIR = Path.home() / ".prodsensor"
    CONFIG_FILE = CONFIG_DIR / "config"

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the ProdSensor client.

        Args:
            api_key: API key for authentication. If not provided, reads from
                     PRODSENSOR_API_KEY env var or config file.
            api_url: Base URL for the API. Defaults to production.
            timeout: Request timeout in seconds.
        """
        self.api_key = api_key or self._get_api_key()
        self.api_url = (api_url or os.getenv("PRODSENSOR_API_URL", self.DEFAULT_API_URL)).rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.Client] = None

    def _get_api_key(self) -> Optional[str]:
        """Get API key from environment or config file"""
        # Check environment variable first
        key = os.getenv("PRODSENSOR_API_KEY")
        if key:
            return key

        # Check config file
        if self.CONFIG_FILE.exists():
            try:
                content = self.CONFIG_FILE.read_text().strip()
                for line in content.split("\n"):
                    if line.startswith("api_key="):
                        return line.split("=", 1)[1].strip()
            except Exception as e:
                logger.warning(f"Failed to read config file: {e}")

        return None

    @classmethod
    def save_api_key(cls, api_key: str) -> None:
        """Save API key to config file"""
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        cls.CONFIG_FILE.write_text(f"api_key={api_key}\n")
        # Set restrictive permissions
        cls.CONFIG_FILE.chmod(0o600)

    @classmethod
    def clear_api_key(cls) -> None:
        """Remove saved API key"""
        if cls.CONFIG_FILE.exists():
            cls.CONFIG_FILE.unlink()

    @property
    def client(self) -> httpx.Client:
        """Get or create the HTTP client"""
        if self._client is None:
            headers = {"User-Agent": "prodsensor-cli/1.0.0"}
            if self.api_key:
                headers["X-API-Key"] = self.api_key
            self._client = httpx.Client(
                base_url=self.api_url,
                headers=headers,
                timeout=self.timeout
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client"""
        if self._client:
            self._client.close()
            self._client = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _handle_response(self, response: httpx.Response) -> Dict[str, Any]:
        """Handle API response and raise appropriate errors"""
        if response.status_code == 401:
            raise AuthError("Invalid or missing API key", 401)
        elif response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 3600))
            raise RateLimitError(retry_after)
        elif response.status_code >= 400:
            try:
                error_data = response.json()
                message = error_data.get("detail", error_data.get("error", "Unknown error"))
            except Exception:
                message = response.text or f"HTTP {response.status_code}"
            raise ApiError(message, response.status_code)

        return response.json()

    def analyze_repo(self, repo_url: str) -> str:
        """
        Start analysis of a GitHub repository.

        Args:
            repo_url: GitHub repository URL

        Returns:
            Run ID for tracking the analysis
        """
        response = self.client.post(
            "/v1/analyze/repo",
            json={"repo_url": repo_url}
        )
        data = self._handle_response(response)
        return data["run_id"]

    def get_run_status(self, run_id: str) -> AnalysisResult:
        """
        Get the status of an analysis run.

        Args:
            run_id: The analysis run ID

        Returns:
            AnalysisResult with current status
        """
        response = self.client.get(f"/v1/runs/{run_id}")
        data = self._handle_response(response)

        verdict = None
        if data.get("verdict"):
            try:
                verdict = Verdict(data["verdict"])
            except ValueError:
                verdict = None

        return AnalysisResult(
            run_id=run_id,
            status=AnalysisStatus(data["status"]),
            verdict=verdict,
            score=data.get("score"),
            blocker_count=data.get("blocker_count", 0),
            major_count=data.get("major_count", 0),
            minor_count=data.get("minor_count", 0),
            report_url=f"{self.api_url}/v1/runs/{run_id}/report.json",
            error=data.get("error")
        )

    def get_report(self, run_id: str) -> Dict[str, Any]:
        """
        Get the full analysis report.

        Args:
            run_id: The analysis run ID

        Returns:
            Full report data
        """
        response = self.client.get(f"/v1/runs/{run_id}/report.json")
        return self._handle_response(response)

    def wait_for_completion(
        self,
        run_id: str,
        timeout: int = 600,
        poll_interval: int = 5,
        progress_callback=None
    ) -> AnalysisResult:
        """
        Wait for an analysis to complete.

        Args:
            run_id: The analysis run ID
            timeout: Maximum time to wait in seconds
            poll_interval: Time between status checks
            progress_callback: Optional callback(status, elapsed_time)

        Returns:
            Final AnalysisResult

        Raises:
            TimeoutError: If analysis doesn't complete within timeout
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                raise TimeoutError(f"Analysis did not complete within {timeout} seconds")

            result = self.get_run_status(run_id)

            if progress_callback:
                progress_callback(result.status, elapsed)

            if result.status in (AnalysisStatus.COMPLETE, AnalysisStatus.FAILED):
                return result

            time.sleep(poll_interval)

    def analyze_and_wait(
        self,
        repo_url: str,
        timeout: int = 600,
        poll_interval: int = 5,
        progress_callback=None
    ) -> AnalysisResult:
        """
        Start analysis and wait for completion.

        Args:
            repo_url: GitHub repository URL
            timeout: Maximum time to wait
            poll_interval: Time between status checks
            progress_callback: Optional callback(status, elapsed_time)

        Returns:
            Final AnalysisResult
        """
        run_id = self.analyze_repo(repo_url)
        return self.wait_for_completion(
            run_id,
            timeout=timeout,
            poll_interval=poll_interval,
            progress_callback=progress_callback
        )
