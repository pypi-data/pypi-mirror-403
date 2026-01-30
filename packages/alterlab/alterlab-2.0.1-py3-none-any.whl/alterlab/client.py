"""AlterLab SDK - Production-ready Python client for the AlterLab Scraping API.

This SDK provides full feature parity with the AlterLab API including:
- Unified endpoint with all scraping modes (auto, html, js, pdf, ocr)
- Automatic polling for async jobs with exponential backoff
- Advanced options (render_js, screenshot, markdown, PDF generation, OCR)
- Cost controls (max_credits, max_tier, prefer_cost/speed, fail_fast)
- Structured extraction (schemas, prompts, profiles)
- Cost estimation before scraping
- Usage tracking and credit management
- Batch scraping with webhooks
- Comprehensive error handling with retries

Version: 2.0.0 (Breaking changes from 1.x - see migration guide)
"""

from typing import Optional, Dict, Any, List, Literal, Union
import httpx
import asyncio
import time
import warnings
import logging
from urllib.parse import urljoin

logger = logging.getLogger("alterlab")


class AdvancedOptions:
    """Advanced scraping options with credit costs.

    Credit Costs:
    - render_js: +3 credits (forces mode="js")
    - screenshot: +1 credit (requires render_js)
    - generate_pdf: +2 credits (requires render_js)
    - ocr: +5 credits (refunded if no images found)
    - use_proxy: +1 credit
    - markdown: Free
    - wait_condition: Free
    """

    def __init__(
        self,
        render_js: bool = False,
        screenshot: bool = False,
        markdown: bool = False,
        generate_pdf: bool = False,
        ocr: bool = False,
        use_proxy: bool = False,
        wait_condition: str = "networkidle"
    ):
        """Initialize advanced options.

        Args:
            render_js: Render JavaScript using headless browser (+3 credits)
            screenshot: Capture full-page screenshot (+1 credit, requires render_js)
            markdown: Extract content as Markdown (free)
            generate_pdf: Generate PDF of rendered page (+2 credits, requires render_js)
            ocr: Extract text from images using OCR (+5 credits)
            use_proxy: Route request through premium proxy (+1 credit)
            wait_condition: Wait condition for JS rendering (domcontentloaded|networkidle|load)

        Raises:
            ValueError: If screenshot or generate_pdf is True but render_js is False
        """
        if screenshot and not render_js:
            raise ValueError("screenshot requires render_js=True")
        if generate_pdf and not render_js:
            raise ValueError("generate_pdf requires render_js=True")

        valid_conditions = ["domcontentloaded", "networkidle", "load"]
        if wait_condition not in valid_conditions:
            raise ValueError(f"wait_condition must be one of {valid_conditions}")

        self.render_js = render_js
        self.screenshot = screenshot
        self.markdown = markdown
        self.generate_pdf = generate_pdf
        self.ocr = ocr
        self.use_proxy = use_proxy
        self.wait_condition = wait_condition

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        return {
            "render_js": self.render_js,
            "screenshot": self.screenshot,
            "markdown": self.markdown,
            "generate_pdf": self.generate_pdf,
            "ocr": self.ocr,
            "use_proxy": self.use_proxy,
            "wait_condition": self.wait_condition
        }

    def calculate_credits(self) -> int:
        """Calculate additional credits for advanced options."""
        credits = 0
        if self.render_js:
            credits += 3
        if self.screenshot:
            credits += 1
        if self.generate_pdf:
            credits += 2
        if self.ocr:
            credits += 5
        if self.use_proxy:
            credits += 1
        return credits


class CostControls:
    """Cost control parameters for scraping requests.

    Provides fine-grained control over credit spending and tier escalation.
    """

    def __init__(
        self,
        max_credits: Optional[float] = None,
        max_tier: Optional[str] = None,
        prefer_cost: bool = False,
        prefer_speed: bool = False,
        fail_fast: bool = False
    ):
        """Initialize cost controls.

        Args:
            max_credits: Maximum credits to spend on this request
            max_tier: Maximum tier to escalate to (0.5, 1, 1.5, 2, 3, 4)
            prefer_cost: Optimize for cost (try cheaper tiers first)
            prefer_speed: Optimize for speed (skip to reliable tier)
            fail_fast: Return error instead of escalating to expensive tiers

        Raises:
            ValueError: If max_tier is not a valid tier value
        """
        valid_tiers = ["0.5", "1", "1.5", "2", "3", "4"]
        if max_tier and max_tier not in valid_tiers:
            raise ValueError(f"max_tier must be one of {valid_tiers}")

        if max_credits and max_credits <= 0:
            raise ValueError("max_credits must be greater than 0")

        self.max_credits = max_credits
        self.max_tier = max_tier
        self.prefer_cost = prefer_cost
        self.prefer_speed = prefer_speed
        self.fail_fast = fail_fast

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request."""
        result = {
            "prefer_cost": self.prefer_cost,
            "prefer_speed": self.prefer_speed,
            "fail_fast": self.fail_fast
        }
        if self.max_credits is not None:
            result["max_credits"] = self.max_credits
        if self.max_tier is not None:
            result["max_tier"] = self.max_tier
        return result


class AlterLabError(Exception):
    """Base exception for AlterLab SDK errors."""
    pass


class AlterLabAPIError(AlterLabError):
    """API error with status code and detail."""

    def __init__(self, status_code: int, detail: str, response: Optional[httpx.Response] = None):
        """Initialize API error.

        Args:
            status_code: HTTP status code
            detail: Error detail message
            response: Optional httpx Response object for inspection
        """
        self.status_code = status_code
        self.detail = detail
        self.response = response
        super().__init__(f"API Error {status_code}: {detail}")


class AlterLabTimeoutError(AlterLabError):
    """Timeout error for async job polling."""
    pass


class AlterLabValidationError(AlterLabError):
    """Validation error for request parameters."""
    pass


class AlterLab:
    """AlterLab API client with full feature support.

    This client provides:
    - Unified scraping endpoint with all modes (auto, html, js, pdf, ocr)
    - Automatic polling for async jobs with configurable backoff
    - Advanced features (render_js, screenshot, markdown, PDF, OCR)
    - Cost controls and estimation
    - Structured extraction with schemas, prompts, and profiles
    - Batch scraping with webhooks
    - Comprehensive error handling with automatic retries
    - Usage tracking and credit management

    Example:
        async with AlterLab(api_key="sk_test_...") as client:
            # Simple scraping
            result = await client.scrape("https://example.com")

            # Advanced scraping with JS rendering and screenshot
            result = await client.scrape(
                "https://example.com",
                mode="js",
                advanced=AdvancedOptions(render_js=True, screenshot=True)
            )

            # Estimate cost before scraping
            estimate = await client.estimate_cost("https://example.com")
            print(f"Estimated credits: {estimate['estimated_credits']}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.alterlab.io",
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """Initialize AlterLab client.

        Args:
            api_key: Your API key (get from https://dashboard.alterlab.io)
            base_url: API base URL (default: https://api.alterlab.io)
            timeout: Default request timeout in seconds
            max_retries: Maximum number of retries for transient failures
            retry_delay: Initial delay between retries in seconds (uses exponential backoff)

        Raises:
            ValueError: If api_key is empty or invalid
        """
        if not api_key or not api_key.strip():
            raise ValueError("api_key is required and cannot be empty")

        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-API-Key": api_key,
                "User-Agent": "AlterLab-Python-SDK/2.0.0",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(timeout)
        )

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        **kwargs
    ) -> httpx.Response:
        """Make HTTP request with retry logic for transient failures.

        Args:
            method: HTTP method (GET, POST, etc.)
            path: API path
            **kwargs: Additional arguments for httpx request

        Returns:
            httpx.Response object

        Raises:
            AlterLabAPIError: On API errors
            AlterLabError: On network errors after all retries
        """
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = await self.client.request(method, path, **kwargs)

                # Handle error responses
                if response.status_code >= 400:
                    try:
                        error_data = response.json()
                        detail = error_data.get('detail', response.text)
                    except Exception:
                        detail = response.text

                    # Don't retry client errors (4xx except 429)
                    if 400 <= response.status_code < 500 and response.status_code != 429:
                        logger.debug(
                            "Non-retriable client error %d on %s %s: %s",
                            response.status_code, method, path, detail
                        )
                        raise AlterLabAPIError(response.status_code, detail, response)

                    # Retry server errors (5xx) and rate limits (429)
                    last_error = AlterLabAPIError(response.status_code, detail, response)
                    remaining_attempts = self.max_retries - attempt - 1

                    # Check for Retry-After header
                    retry_after = response.headers.get('Retry-After')
                    if retry_after:
                        sleep_time = float(retry_after)
                    else:
                        # Exponential backoff
                        sleep_time = self.retry_delay * (2 ** attempt)

                    logger.warning(
                        "Retriable error %d on %s %s (attempt %d/%d). "
                        "Retrying in %.1fs. %d attempts remaining. Detail: %s",
                        response.status_code, method, path,
                        attempt + 1, self.max_retries,
                        sleep_time, remaining_attempts, detail
                    )
                    await asyncio.sleep(sleep_time)
                    continue

                return response

            except (httpx.TimeoutException, httpx.NetworkError) as e:
                last_error = AlterLabError(f"Network error: {str(e)}")
                remaining_attempts = self.max_retries - attempt - 1

                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    sleep_time = self.retry_delay * (2 ** attempt)
                    logger.warning(
                        "Network error on %s %s (attempt %d/%d): %s. "
                        "Retrying in %.1fs. %d attempts remaining.",
                        method, path, attempt + 1, self.max_retries,
                        str(e), sleep_time, remaining_attempts
                    )
                    await asyncio.sleep(sleep_time)
                else:
                    logger.error(
                        "Network error on %s %s (attempt %d/%d): %s. "
                        "No retries remaining.",
                        method, path, attempt + 1, self.max_retries, str(e)
                    )
                continue

        # All retries exhausted
        logger.error(
            "All %d retry attempts exhausted for %s %s. Last error: %s",
            self.max_retries, method, path, last_error
        )
        raise last_error or AlterLabError("Request failed after retries")

    async def scrape(
        self,
        url: str,
        mode: Literal["auto", "html", "js", "pdf", "ocr"] = "auto",
        sync: bool = True,
        advanced: Optional[AdvancedOptions] = None,
        cost_controls: Optional[CostControls] = None,
        force_refresh: bool = False,
        include_raw_html: bool = False,
        timeout: Optional[int] = None,
        formats: Optional[List[Literal["text", "json", "html", "markdown"]]] = None,
        extraction_schema: Optional[Dict[str, Any]] = None,
        extraction_prompt: Optional[str] = None,
        extraction_profile: Optional[Literal["auto", "product", "article", "job_posting", "faq", "recipe", "event"]] = None,
        evidence: bool = False,
        promote_schema_org: bool = True,
        wait_for: Optional[str] = None,
        screenshot: bool = False,
        wait_until: str = "networkidle",
        pdf_format: str = "markdown",
        ocr_language: str = "eng",
        poll_interval: float = 1.0,
        poll_timeout: float = 300.0,
        poll_backoff_multiplier: float = 1.5,
        poll_max_interval: float = 10.0
    ) -> Dict[str, Any]:
        """Scrape a URL using the unified AlterLab API endpoint.

        This is the main method for scraping content. It supports all scraping modes
        and automatically handles async job polling when needed.

        Args:
            url: URL to scrape
            mode: Scraping mode (auto, html, js, pdf, ocr)
            sync: Return synchronous response when possible (default: True).
                  Set to False to always use async worker queue.
            advanced: Advanced scraping options (AdvancedOptions object)
            cost_controls: Cost control parameters (CostControls object)
            force_refresh: Bypass cache and fetch fresh content
            include_raw_html: Include raw HTML in response
            timeout: Request timeout in seconds (overrides default)
            formats: Output formats for content transformation (e.g., ["html", "markdown"])
            extraction_schema: JSON Schema for structured extraction
            extraction_prompt: Natural language instructions for extraction
            extraction_profile: Pre-defined extraction profile (auto, product, article, etc.)
            evidence: Include provenance/evidence for extracted fields
            promote_schema_org: Use Schema.org as primary structure
            wait_for: CSS selector to wait for (JS mode)
            screenshot: Capture screenshot (JS mode, requires advanced.render_js=True)
            wait_until: Wait condition (domcontentloaded|networkidle|load)
            pdf_format: PDF output format (text|markdown)
            ocr_language: OCR language code (e.g., "eng", "fra", "deu")
            poll_interval: Initial polling interval for async jobs (seconds)
            poll_timeout: Maximum time to wait for async jobs (seconds)
            poll_backoff_multiplier: Multiplier for exponential backoff (default: 1.5)
            poll_max_interval: Maximum polling interval (seconds)

        Returns:
            Scrape response dictionary with content, metadata, and billing details

        Raises:
            AlterLabAPIError: On API errors
            AlterLabTimeoutError: If async job polling times out
            AlterLabValidationError: If parameters are invalid

        Example:
            # Simple HTML scraping
            result = await client.scrape("https://example.com")

            # JavaScript rendering with screenshot
            result = await client.scrape(
                "https://example.com",
                mode="js",
                advanced=AdvancedOptions(render_js=True, screenshot=True)
            )

            # Structured extraction
            result = await client.scrape(
                "https://example.com/product",
                extraction_profile="product"
            )

            # Cost-controlled scraping
            result = await client.scrape(
                "https://example.com",
                cost_controls=CostControls(max_credits=5, fail_fast=True)
            )
        """
        # Build request payload
        payload: Dict[str, Any] = {
            "url": url,
            "mode": mode,
            "sync": sync,
            "force_refresh": force_refresh,
            "include_raw_html": include_raw_html,
            "timeout": timeout or self.timeout,
            "evidence": evidence,
            "promote_schema_org": promote_schema_org
        }

        # Add advanced options
        if advanced:
            payload["advanced"] = advanced.to_dict()

        # Add cost controls
        if cost_controls:
            payload["cost_controls"] = cost_controls.to_dict()

        # Add optional parameters
        if formats:
            payload["formats"] = formats
        if extraction_schema:
            payload["extraction_schema"] = extraction_schema
        if extraction_prompt:
            payload["extraction_prompt"] = extraction_prompt
        if extraction_profile:
            payload["extraction_profile"] = extraction_profile

        # JS-specific options
        if wait_for:
            payload["wait_for"] = wait_for
        if screenshot:
            payload["screenshot"] = screenshot
        if wait_until:
            payload["wait_until"] = wait_until

        # PDF-specific options
        if mode == "pdf":
            payload["pdf_format"] = pdf_format

        # OCR-specific options
        if mode == "ocr":
            payload["ocr_language"] = ocr_language

        # Make request
        response = await self._request_with_retry(
            "POST",
            "/api/v1/scrape",
            json=payload
        )

        result = response.json()

        # Check if response is async (202 Accepted with job_id)
        if response.status_code == 202 and "job_id" in result:
            if not sync:
                # Return job info immediately
                return result

            # Poll for job completion with exponential backoff
            job_id = result["job_id"]
            return await self.wait_for_job(
                job_id,
                poll_interval=poll_interval,
                poll_timeout=poll_timeout,
                backoff_multiplier=poll_backoff_multiplier,
                max_interval=poll_max_interval
            )

        # Synchronous response
        return result

    async def wait_for_job(
        self,
        job_id: str,
        poll_interval: float = 1.0,
        poll_timeout: float = 300.0,
        backoff_multiplier: float = 1.5,
        max_interval: float = 10.0
    ) -> Dict[str, Any]:
        """Wait for async job completion with exponential backoff.

        This method polls the job status endpoint until the job completes or fails.
        It uses exponential backoff to reduce API load for long-running jobs.

        Args:
            job_id: Job ID to poll
            poll_interval: Initial polling interval in seconds
            poll_timeout: Maximum time to wait in seconds
            backoff_multiplier: Multiplier for exponential backoff
            max_interval: Maximum polling interval (caps exponential growth)

        Returns:
            Job result when completed

        Raises:
            AlterLabTimeoutError: If job doesn't complete within timeout
            AlterLabAPIError: On API errors or job failure

        Example:
            # Start async job
            response = await client.scrape("https://example.com", sync=False)
            job_id = response["job_id"]

            # Wait for completion
            result = await client.wait_for_job(job_id)
        """
        start_time = time.time()
        current_interval = poll_interval

        while True:
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > poll_timeout:
                raise AlterLabTimeoutError(
                    f"Job {job_id} did not complete within {poll_timeout} seconds"
                )

            # Get job status
            response = await self._request_with_retry(
                "GET",
                f"/api/v1/jobs/{job_id}"
            )

            job = response.json()
            status = job.get("status")

            if status == "completed":
                return job.get("result", job)
            elif status == "failed":
                error = job.get("error", "Job failed")
                raise AlterLabAPIError(500, f"Job failed: {error}")
            elif status in ["pending", "running"]:
                # Continue polling
                pass
            else:
                # Unknown status
                raise AlterLabError(f"Unknown job status: {status}")

            # Wait before next poll with exponential backoff
            await asyncio.sleep(current_interval)
            current_interval = min(current_interval * backoff_multiplier, max_interval)

    async def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Get the current status of an async job without waiting.

        This method retrieves the current job status without polling.
        Use this for checking status manually or wait_for_job() for automatic polling.

        Args:
            job_id: Job ID to check

        Returns:
            Job status dictionary with keys: status, result (if completed), error (if failed)

        Raises:
            AlterLabAPIError: On API errors

        Example:
            status = await client.get_job_status("job_123")
            print(f"Status: {status['status']}")
            if status['status'] == 'completed':
                result = status['result']
        """
        response = await self._request_with_retry(
            "GET",
            f"/api/v1/jobs/{job_id}"
        )
        return response.json()

    async def estimate_cost(
        self,
        url: str,
        mode: Literal["auto", "html", "js", "pdf", "ocr"] = "auto",
        advanced: Optional[AdvancedOptions] = None,
        cost_controls: Optional[CostControls] = None,
        formats: Optional[List[Literal["text", "json", "html", "markdown"]]] = None,
    ) -> Dict[str, Any]:
        """Estimate cost for a scrape request without executing it.

        This method provides a cost estimate based on the URL and options.
        Use this before scraping to avoid unexpected credit charges.

        Args:
            url: URL to estimate
            mode: Scraping mode
            advanced: Advanced options to include in estimate
            cost_controls: Optional cost controls for estimation (max_credits, max_tier, etc.)
            formats: Optional output formats for transformation (text, json, html, markdown)

        Returns:
            Cost estimate dictionary with keys:
            - url: URL being estimated
            - estimated_tier: Expected tier (e.g., "1", "2")
            - estimated_credits: Expected credit cost
            - confidence: Confidence level (low, medium, high)
            - max_possible_credits: Maximum credits if all escalations occur
            - reasoning: Explanation of estimate

        Raises:
            AlterLabAPIError: On API errors

        Example:
            estimate = await client.estimate_cost(
                "https://example.com",
                mode="js",
                advanced=AdvancedOptions(render_js=True, screenshot=True)
            )
            print(f"Estimated: {estimate['estimated_credits']} credits")
            print(f"Max possible: {estimate['max_possible_credits']} credits")
        """
        payload: Dict[str, Any] = {
            "url": url,
            "mode": mode
        }

        if advanced:
            payload["advanced"] = advanced.to_dict()

        if cost_controls:
            payload["cost_controls"] = cost_controls.to_dict()

        if formats:
            payload["formats"] = formats

        response = await self._request_with_retry(
            "POST",
            "/api/v1/scrape/estimate",
            json=payload
        )

        return response.json()

    async def get_usage(self) -> Dict[str, Any]:
        """Get current usage statistics and credit balance.

        Returns:
            Usage stats dictionary with keys:
            - credits_available: Current credit balance
            - credits_used: Credits used this billing period
            - credits_limit: Total credits in subscription
            - requests_count: Number of requests made
            - subscription_tier: Current subscription tier
            - billing_period_start: Start of billing period
            - billing_period_end: End of billing period

        Raises:
            AlterLabAPIError: On API errors

        Example:
            usage = await client.get_usage()
            print(f"Credits remaining: {usage['credits_available']}")
            print(f"Subscription: {usage['subscription_tier']}")
        """
        response = await self._request_with_retry(
            "GET",
            "/api/v1/usage"
        )

        return response.json()

    async def batch_scrape(
        self,
        requests: List[Dict[str, Any]],
        webhook_url: Optional[str] = None
    ) -> Dict[str, Any]:
        """Submit multiple scrape requests as a batch.

        Batch requests are processed asynchronously. You can provide a webhook URL
        to receive notifications when the batch completes.

        Args:
            requests: List of scrape request dictionaries. Each dict should contain
                     the same parameters as scrape() method (url, mode, advanced, etc.)
            webhook_url: Optional webhook URL for completion notification

        Returns:
            Batch job information with keys:
            - batch_id: Unique batch identifier
            - job_ids: List of individual job IDs
            - total_requests: Number of requests in batch
            - status: Batch status (pending, running, completed, failed)

        Raises:
            AlterLabAPIError: On API errors

        Example:
            requests = [
                {"url": "https://example.com/page1", "mode": "html"},
                {"url": "https://example.com/page2", "mode": "js"},
                {"url": "https://example.com/page3", "mode": "html"}
            ]
            batch = await client.batch_scrape(
                requests,
                webhook_url="https://myapp.com/webhook"
            )
            print(f"Batch ID: {batch['batch_id']}")

            # Check individual job statuses
            for job_id in batch['job_ids']:
                status = await client.get_job_status(job_id)
                print(f"Job {job_id}: {status['status']}")
        """
        payload: Dict[str, Any] = {
            "requests": requests
        }

        if webhook_url:
            payload["webhook_url"] = webhook_url

        response = await self._request_with_retry(
            "POST",
            "/api/v1/batch",
            json=payload
        )

        return response.json()

    # Convenience methods with preset configurations

    async def scrape_html(
        self,
        url: str,
        use_proxy: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """Scrape HTML content without JavaScript rendering.

        This is a convenience method for simple HTTP requests. It's the fastest
        and most cost-effective option (1 credit base).

        Args:
            url: URL to scrape
            use_proxy: Use premium proxy (+1 credit)
            **kwargs: Additional arguments passed to scrape()

        Returns:
            Scrape response

        Example:
            result = await client.scrape_html("https://example.com")
            print(result['content'])
        """
        advanced = AdvancedOptions(use_proxy=use_proxy)
        return await self.scrape(url, mode="html", advanced=advanced, **kwargs)

    async def scrape_js(
        self,
        url: str,
        screenshot: bool = False,
        markdown: bool = False,
        wait_for: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Scrape content with JavaScript rendering.

        This convenience method renders JavaScript using a headless browser.
        Base cost is 4 credits, plus additional costs for screenshot/markdown.

        Args:
            url: URL to scrape
            screenshot: Capture full-page screenshot (+1 credit)
            markdown: Convert to markdown (free)
            wait_for: CSS selector to wait for before capturing content
            **kwargs: Additional arguments passed to scrape()

        Returns:
            Scrape response

        Example:
            # Render JS and capture screenshot
            result = await client.scrape_js(
                "https://example.com",
                screenshot=True,
                wait_for=".content-loaded"
            )
            screenshot_url = result['screenshot_url']
        """
        advanced = AdvancedOptions(
            render_js=True,
            screenshot=screenshot,
            markdown=markdown
        )
        return await self.scrape(
            url,
            mode="js",
            advanced=advanced,
            wait_for=wait_for,
            **kwargs
        )

    async def scrape_pdf(
        self,
        url: str,
        format: str = "markdown",
        **kwargs
    ) -> Dict[str, Any]:
        """Extract content from PDF files.

        This convenience method extracts text from PDF documents.
        Base cost is 3 credits.

        Args:
            url: PDF URL
            format: Output format (text or markdown)
            **kwargs: Additional arguments passed to scrape()

        Returns:
            Scrape response with extracted PDF content

        Example:
            result = await client.scrape_pdf(
                "https://example.com/document.pdf",
                format="markdown"
            )
            print(result['content'])
        """
        return await self.scrape(
            url,
            mode="pdf",
            pdf_format=format,
            **kwargs
        )

    async def scrape_ocr(
        self,
        url: str,
        language: str = "eng",
        **kwargs
    ) -> Dict[str, Any]:
        """Extract text from images using OCR.

        This convenience method performs optical character recognition on images.
        Base cost is 6 credits.

        Args:
            url: Image URL
            language: OCR language code (eng, fra, deu, spa, etc.)
            **kwargs: Additional arguments passed to scrape()

        Returns:
            Scrape response with OCR-extracted text

        Example:
            result = await client.scrape_ocr(
                "https://example.com/image.png",
                language="eng"
            )
            print(result['content'])
            print(result['ocr_results'])  # Detailed OCR results with bounding boxes
        """
        return await self.scrape(
            url,
            mode="ocr",
            ocr_language=language,
            **kwargs
        )

    # Deprecated methods for backwards compatibility

    async def scrape_light(self, url: str, **kwargs) -> Dict[str, Any]:
        """DEPRECATED: Use scrape() or scrape_html() instead.

        This method is deprecated and will be removed in version 3.0.
        Use scrape(url, mode="html") or scrape_html(url) instead.

        Args:
            url: URL to scrape
            **kwargs: Additional arguments

        Returns:
            Scrape response
        """
        warnings.warn(
            "scrape_light() is deprecated and will be removed in version 3.0. "
            "Use scrape(url, mode='html') or scrape_html(url) instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return await self.scrape_html(url, **kwargs)

    async def close(self):
        """Close the HTTP client.

        Call this method when you're done using the client to free up resources.
        Alternatively, use the client as an async context manager.

        Example:
            client = AlterLab(api_key="sk_test_...")
            try:
                result = await client.scrape("https://example.com")
            finally:
                await client.close()
        """
        await self.client.aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()


# Synchronous wrapper for convenience
class AlterLabSync:
    """Synchronous wrapper for AlterLab client.

    This wrapper provides synchronous methods for developers who prefer
    synchronous code or are working in non-async environments.

    Note: This still uses asyncio internally, so performance is identical
    to the async client. Consider using the async client directly for better
    integration with async codebases.

    Example:
        with AlterLabSync(api_key="sk_test_...") as client:
            result = client.scrape("https://example.com")
            print(result['content'])
    """

    def __init__(self, api_key: str, **kwargs):
        """Initialize synchronous client.

        Args:
            api_key: Your API key
            **kwargs: Additional arguments passed to AlterLab()
        """
        self._client = AlterLab(api_key, **kwargs)
        self._loop = asyncio.new_event_loop()

    def _run(self, coro):
        """Run async coroutine synchronously."""
        return self._loop.run_until_complete(coro)

    def scrape(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of scrape()."""
        return self._run(self._client.scrape(*args, **kwargs))

    def estimate_cost(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of estimate_cost()."""
        return self._run(self._client.estimate_cost(*args, **kwargs))

    def get_usage(self) -> Dict[str, Any]:
        """Synchronous version of get_usage()."""
        return self._run(self._client.get_usage())

    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Synchronous version of get_job_status()."""
        return self._run(self._client.get_job_status(job_id))

    def wait_for_job(self, job_id: str, **kwargs) -> Dict[str, Any]:
        """Synchronous version of wait_for_job()."""
        return self._run(self._client.wait_for_job(job_id, **kwargs))

    def batch_scrape(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of batch_scrape()."""
        return self._run(self._client.batch_scrape(*args, **kwargs))

    def scrape_html(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of scrape_html()."""
        return self._run(self._client.scrape_html(*args, **kwargs))

    def scrape_js(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of scrape_js()."""
        return self._run(self._client.scrape_js(*args, **kwargs))

    def scrape_pdf(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of scrape_pdf()."""
        return self._run(self._client.scrape_pdf(*args, **kwargs))

    def scrape_ocr(self, *args, **kwargs) -> Dict[str, Any]:
        """Synchronous version of scrape_ocr()."""
        return self._run(self._client.scrape_ocr(*args, **kwargs))

    def close(self):
        """Close the client and event loop."""
        self._run(self._client.close())
        self._loop.close()

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
