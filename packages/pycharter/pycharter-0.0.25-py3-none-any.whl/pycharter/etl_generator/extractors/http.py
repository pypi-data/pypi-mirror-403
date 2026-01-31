"""
HTTP/API extractor for ETL orchestrator.

Handles HTTP-based data extraction with support for:
- GET and POST requests
- Retry logic with exponential backoff
- Rate limiting
- Pagination (page, offset, cursor, next_url, link_header)
- Response parsing (JSON, text)
- Path parameter substitution
"""

import asyncio
import logging
import re
import time
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from pycharter.etl_generator.extractors.base import BaseExtractor
from pycharter.utils.value_injector import resolve_values

logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_RATE_LIMIT_DELAY = 0.2
DEFAULT_MAX_ATTEMPTS = 3
DEFAULT_BACKOFF_FACTOR = 2.0
DEFAULT_RETRY_STATUS_CODES = [429, 500, 502, 503, 504]
DEFAULT_TIMEOUT_CONNECT = 10.0
DEFAULT_TIMEOUT_READ = 30.0
DEFAULT_TIMEOUT_WRITE = 10.0
DEFAULT_TIMEOUT_POOL = 10.0

# Common response data keys
RESPONSE_DATA_KEYS = ['data', 'results', 'items', 'records', 'values']


class HTTPExtractor(BaseExtractor):
    """
    Extractor for HTTP/API data sources.
    
    Supports two modes:
    1. Programmatic API:
        >>> extractor = HTTPExtractor(url="https://api.example.com/users")
        >>> async for batch in extractor.extract():
        ...     process(batch)
    
    2. Config-driven (legacy):
        >>> extractor = HTTPExtractor()
        >>> async for batch in extractor.extract_streaming(config, params, headers):
        ...     process(batch)
    """
    
    def __init__(
        self,
        url: Optional[str] = None,
        base_url: Optional[str] = None,
        endpoint: Optional[str] = None,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        body: Optional[Any] = None,
        response_path: Optional[str] = None,
        batch_size: int = 1000,
        pagination: Optional[Dict[str, Any]] = None,
    ):
        self.url = url
        self.base_url = base_url or ""
        self.endpoint = endpoint or ""
        self.method = method
        self.headers = headers or {}
        self.params = params or {}
        self.body = body
        self.response_path = response_path
        self.batch_size = batch_size
        self.pagination = pagination or {}
    
    @classmethod
    def from_config(cls, config: Dict[str, Any]) -> "HTTPExtractor":
        """Create extractor from configuration dict."""
        return cls(
            url=config.get("url"),
            base_url=config.get("base_url", ""),
            endpoint=config.get("api_endpoint", config.get("endpoint", "")),
            method=config.get("method", "GET"),
            headers=config.get("headers", {}),
            params=config.get("params", {}),
            body=config.get("body"),
            response_path=config.get("response_path"),
            batch_size=config.get("batch_size", 1000),
            pagination=config.get("pagination"),
        )
    
    async def extract(self, **params) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from HTTP source.
        
        Yields:
            Batches of records
        """
        # Build extract config from instance attributes
        extract_config = {
            "base_url": self.base_url,
            "api_endpoint": self.url or self.endpoint,
            "method": self.method,
            "response_path": self.response_path,
            "pagination": self.pagination,
        }
        
        merged_params = {**self.params, **params}
        
        async for batch in self.extract_streaming(
            extract_config,
            merged_params,
            self.headers,
            batch_size=self.batch_size,
        ):
            yield batch
    
    def validate_config(self, extract_config: Dict[str, Any]) -> None:
        """Validate HTTP extractor configuration."""
        if 'source_type' in extract_config and extract_config['source_type'] != 'http':
            raise ValueError(f"HTTPExtractor requires source_type='http', got '{extract_config.get('source_type')}'")
        
        # Check for required HTTP config fields
        if not extract_config.get('api_endpoint') and not extract_config.get('base_url'):
            # Allow if api_endpoint is a full URL
            api_endpoint = extract_config.get('api_endpoint', '')
            if not api_endpoint.startswith(('http://', 'https://')):
                raise ValueError(
                    "HTTP extractor requires either 'api_endpoint' (with 'base_url') "
                    "or 'api_endpoint' as full URL"
                )
    
    async def extract_streaming(
        self,
        extract_config: Dict[str, Any],
        params: Dict[str, Any],
        headers: Dict[str, Any],
        contract_dir: Optional[Any] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """
        Extract data from HTTP/API source with pagination support.
        
        Yields batches as they are extracted, preventing memory exhaustion for large datasets.
        """
        pagination_config = extract_config.get('pagination', {})
        
        # If pagination is not enabled, extract all and yield in batches
        if not pagination_config.get('enabled', False):
            logger.info("Pagination disabled, extracting all data in single request")
            all_data = await self._extract_with_retry(
                extract_config, params, headers, contract_dir, config_context=config_context
            )
            if max_records:
                logger.info(f"Limiting to {max_records} records (extracted {len(all_data)})")
                all_data = all_data[:max_records]
            
            logger.info(f"Yielding {len(all_data)} records in batches of {batch_size}")
            for i in range(0, len(all_data), batch_size):
                batch = all_data[i:i + batch_size]
                logger.debug(f"Yielding batch {i // batch_size + 1} with {len(batch)} records")
                yield batch
            return
        
        # Pagination enabled - stream pages and yield in batches
        async for batch in self._extract_with_pagination(
            extract_config, params, headers, contract_dir, batch_size, max_records, config_context
        ):
            yield batch
    
    async def _extract_with_retry(
        self,
        extract_config: Dict[str, Any],
        params: Dict[str, Any],
        headers: Dict[str, Any],
        contract_dir: Optional[Any] = None,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract data from API with retry logic."""
        extracted_data, _, _ = await self._extract_single_page(
            extract_config, params, headers, contract_dir, return_full_response=False, config_context=config_context
        )
        return extracted_data
    
    async def _extract_single_page(
        self,
        extract_config: Dict[str, Any],
        params: Dict[str, Any],
        headers: Dict[str, Any],
        contract_dir: Optional[Any] = None,
        return_full_response: bool = False,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Dict[str, Any]], Optional[Any], Optional[httpx.Response]]:
        """Extract data from a single API request with retry logic."""
        # Get configuration
        base_url = extract_config.get('base_url', '')
        api_endpoint = extract_config.get('api_endpoint', '')
        method = extract_config.get('method', 'GET').upper()
        timeout_config = extract_config.get('timeout', {})
        retry_config = extract_config.get('retry', {})
        response_path = extract_config.get('response_path')
        response_format = extract_config.get('response_format', 'json')
        rate_limit_delay = extract_config.get('rate_limit_delay', DEFAULT_RATE_LIMIT_DELAY)
        body = extract_config.get('body')
        
        # Resolve variables and convert types
        source_file = str(contract_dir / "extract.yaml") if contract_dir else None
        resolved_params = resolve_values(params, context=config_context, source_file=source_file)
        resolved_headers = resolve_values(headers, context=config_context, source_file=source_file)
        resolved_timeout_config = resolve_values(timeout_config, context=config_context, source_file=source_file)
        resolved_rate_limit_delay = self._resolve_rate_limit_delay(rate_limit_delay, contract_dir, config_context)
        
        if body:
            resolved_body = resolve_values(body, context=config_context, source_file=source_file)
        else:
            resolved_body = None
        
        # Extract path parameters from api_endpoint
        path_params = {}
        if '{' in api_endpoint:
            path_param_names = re.findall(r'\{(\w+)\}', api_endpoint)
            for param_name in path_param_names:
                if param_name in resolved_params:
                    path_params[param_name] = resolved_params.pop(param_name)
        
        # Build URL with path parameter substitution
        url = self._build_request_url(base_url, api_endpoint, path_params)
        
        # Configure timeout
        timeout = self._configure_timeout(resolved_timeout_config)
        
        # Configure retry
        max_attempts = int(retry_config.get('max_attempts', DEFAULT_MAX_ATTEMPTS))
        backoff_factor = float(retry_config.get('backoff_factor', DEFAULT_BACKOFF_FACTOR))
        retry_on_status = retry_config.get('retry_on_status', DEFAULT_RETRY_STATUS_CODES)
        
        # Make request with retry logic
        last_exception = None
        request_start_time = None
        
        logger.info(
            f"Starting HTTP extraction: {method} {url} "
            f"(timeout: connect={timeout.connect}s, read={timeout.read}s, "
            f"max_attempts={max_attempts})"
        )
        logger.debug(f"Request params: {resolved_params}")
        logger.debug(f"Request headers: {dict(resolved_headers)}")
        
        for attempt in range(max_attempts):
            try:
                request_start_time = time.time()
                logger.debug(f"HTTP request attempt {attempt + 1}/{max_attempts} to {url}")
                
                async with httpx.AsyncClient(timeout=timeout) as client:
                    if attempt > 0:
                        wait_time = backoff_factor ** (attempt - 1)
                        logger.info(f"Retrying after {wait_time:.2f}s (attempt {attempt + 1}/{max_attempts})")
                        await asyncio.sleep(wait_time)
                    
                    request_attempt_start = time.time()
                    try:
                        response = await self._make_http_request(
                            client, method, url, resolved_params, resolved_headers, resolved_body
                        )
                        request_duration = time.time() - request_attempt_start
                        logger.info(
                            f"HTTP request completed: {response.status_code} "
                            f"({request_duration:.2f}s, attempt {attempt + 1}/{max_attempts})"
                        )
                    except httpx.TimeoutException as timeout_error:
                        request_duration = time.time() - request_attempt_start
                        timeout_info = ""
                        if hasattr(timeout_error, 'timeout') and isinstance(timeout_error.timeout, httpx.Timeout):
                            timeout_info = (
                                f" (connect={timeout_error.timeout.connect}s, "
                                f"read={timeout_error.timeout.read}s)"
                            )
                        logger.error(
                            f"HTTP request timeout after {request_duration:.2f}s{timeout_info}: "
                            f"{type(timeout_error).__name__}: {timeout_error} "
                            f"(attempt {attempt + 1}/{max_attempts})"
                        )
                        raise
                    except httpx.RequestError as request_error:
                        request_duration = time.time() - request_attempt_start
                        logger.error(
                            f"HTTP request error after {request_duration:.2f}s: "
                            f"{type(request_error).__name__}: {request_error} "
                            f"(attempt {attempt + 1}/{max_attempts})"
                        )
                        raise
                    
                    # Check if we should retry based on status code
                    if response.status_code in retry_on_status and attempt < max_attempts - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"HTTP {response.status_code} received, will retry after {wait_time:.2f}s "
                            f"(attempt {attempt + 1}/{max_attempts})"
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # Raise for non-2xx status codes
                    response.raise_for_status()
                    
                    # Parse response
                    parse_start = time.time()
                    if response_format == 'json':
                        data = response.json()
                    else:
                        data = response.text
                    parse_duration = time.time() - parse_start
                    logger.debug(f"Response parsed in {parse_duration:.3f}s")
                    
                    # Extract data array
                    extract_start = time.time()
                    if response_path:
                        extracted_data = self._extract_by_path(data, response_path)
                    else:
                        extracted_data = self._extract_data_array(data)
                    extract_duration = time.time() - extract_start
                    
                    total_duration = time.time() - request_start_time
                    logger.info(
                        f"Extraction successful: {len(extracted_data)} records extracted "
                        f"(total: {total_duration:.2f}s, parse: {parse_duration:.3f}s, "
                        f"extract: {extract_duration:.3f}s)"
                    )
                    
                    # Apply rate limiting delay
                    if resolved_rate_limit_delay > 0:
                        logger.debug(f"Applying rate limit delay: {resolved_rate_limit_delay}s")
                        await asyncio.sleep(resolved_rate_limit_delay)
                    
                    if return_full_response:
                        return extracted_data, data, response
                    return extracted_data, None, None
                    
            except httpx.HTTPStatusError as e:
                last_exception = e
                request_duration = time.time() - request_start_time if request_start_time else 0
                
                logger.error(
                    f"HTTP status error {e.response.status_code}",
                    extra={
                        'status_code': e.response.status_code,
                        'url': url,
                        'attempt': attempt + 1,
                        'duration': request_duration,
                    },
                    exc_info=True
                )
                
                if e.response.status_code in retry_on_status and attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise RuntimeError(
                    f"HTTP error {e.response.status_code}: {e.response.text}"
                ) from e
            except httpx.TimeoutException as e:
                last_exception = e
                request_duration = time.time() - request_start_time if request_start_time else 0
                
                logger.error(
                    "HTTP timeout",
                    extra={
                        'url': url,
                        'duration': request_duration,
                        'attempt': attempt + 1,
                    },
                    exc_info=True
                )
                
                if attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise RuntimeError(f"Request timeout after {request_duration:.2f}s: {e}") from e
            except httpx.RequestError as e:
                last_exception = e
                request_duration = time.time() - request_start_time if request_start_time else 0
                
                logger.error(
                    "HTTP request error",
                    extra={
                        'url': url,
                        'duration': request_duration,
                        'attempt': attempt + 1,
                    },
                    exc_info=True
                )
                
                if attempt < max_attempts - 1:
                    wait_time = backoff_factor ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise RuntimeError(f"Request failed: {e}") from e
            except Exception as e:
                request_duration = time.time() - request_start_time if request_start_time else 0
                
                logger.error(
                    "Unexpected extraction error",
                    extra={
                        'url': url,
                        'duration': request_duration,
                        'attempt': attempt + 1,
                    },
                    exc_info=True
                )
                raise RuntimeError(f"Extraction failed: {e}") from e
        
        # If we exhausted all retries
        if last_exception:
            raise RuntimeError(
                f"Extraction failed after {max_attempts} attempts: {last_exception}"
            ) from last_exception
        raise RuntimeError("Extraction failed: unknown error")
    
    async def _extract_with_pagination(
        self,
        extract_config: Dict[str, Any],
        params: Dict[str, Any],
        headers: Dict[str, Any],
        contract_dir: Optional[Any] = None,
        batch_size: int = 1000,
        max_records: Optional[int] = None,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[List[Dict[str, Any]]]:
        """Extract data with pagination support."""
        pagination_config = extract_config.get('pagination', {})
        strategy = pagination_config.get('strategy', 'page')
        stop_conditions = pagination_config.get('stop_conditions', [])
        page_delay = float(pagination_config.get('page_delay', 0.1))
        max_pages = 1000
        max_records_from_config = None
        
        # Get max_pages and max_records from stop conditions
        for condition in stop_conditions:
            if condition.get('type') == 'max_pages':
                max_pages = condition.get('value', 1000)
            elif condition.get('type') == 'max_records':
                max_records_from_config = condition.get('value')
        
        if max_records is None:
            max_records = max_records_from_config
        
        current_batch = []
        total_extracted = 0
        page_count = 0
        current_url = None
        current_cursor = None
        
        # Initialize pagination state
        if strategy == 'page':
            page_config = pagination_config.get('page', {})
            current_page = page_config.get('start', 0)
            page_increment = page_config.get('increment', 1)
            page_param_name = page_config.get('param_name', 'page')
        elif strategy == 'offset':
            offset_config = pagination_config.get('offset', {})
            current_offset = offset_config.get('start', 0)
            offset_param_name = offset_config.get('param_name', 'offset')
            increment_by = offset_config.get('increment_by', 'limit')
        elif strategy == 'cursor':
            cursor_config = pagination_config.get('cursor', {})
            cursor_param_name = cursor_config.get('param_name', 'cursor')
            cursor_response_path = cursor_config.get('response_path', 'next_cursor')
        elif strategy == 'next_url':
            next_url_config = pagination_config.get('next_url', {})
            next_url_response_path = next_url_config.get('response_path', 'next_url')
        elif strategy == 'link_header':
            pass
        else:
            raise ValueError(f"Unsupported pagination strategy: {strategy}")
        
        extract_config_copy = extract_config.copy()
        original_endpoint = extract_config_copy.get('api_endpoint')
        original_base_url = extract_config_copy.get('base_url', '')
        
        logger.info(
            f"Starting paginated extraction (strategy: {strategy}, "
            f"max_pages: {max_pages}, batch_size: {batch_size}, "
            f"page_delay: {page_delay}s)"
        )
        
        while page_count < max_pages:
            # Check max_records limit
            if max_records and total_extracted >= max_records:
                logger.info(
                    f"Reached max_records limit ({max_records}), stopping pagination "
                    f"(extracted {total_extracted} records from {page_count} pages)"
                )
                if current_batch:
                    yield current_batch
                return
            
            # Update params/URL based on strategy
            if strategy == 'page':
                params[page_param_name] = current_page
                logger.debug(f"Fetching page {current_page} (page_count: {page_count + 1}/{max_pages})")
            elif strategy == 'offset':
                params[offset_param_name] = current_offset
            elif strategy == 'cursor' and current_cursor:
                params[cursor_param_name] = current_cursor
            elif strategy == 'next_url' and current_url:
                extract_config_copy['api_endpoint'] = current_url
                extract_config_copy['base_url'] = ''
            
            # Make request
            need_full_response = strategy in ['cursor', 'next_url', 'link_header']
            try:
                logger.debug(f"Extracting page {page_count + 1} (total extracted so far: {total_extracted})")
                page_data, full_response_data, response_obj = await self._extract_single_page(
                    extract_config_copy, params, headers, contract_dir, return_full_response=need_full_response, config_context=config_context
                )
                logger.info(f"Page {page_count + 1} extracted: {len(page_data)} records")
            except Exception as e:
                logger.error(
                    f"Error extracting page {page_count + 1}",
                    extra={
                        'page': page_count + 1,
                        'extracted': total_extracted,
                    },
                    exc_info=True
                )
                if current_batch:
                    yield current_batch
                raise
            
            # Restore original endpoint if modified
            if strategy == 'next_url' and current_url:
                extract_config_copy['api_endpoint'] = original_endpoint
                extract_config_copy['base_url'] = original_base_url
            
            # Check for empty page first
            if not page_data:
                logger.info(f"Empty page {page_count + 1} received, stopping pagination")
                if current_batch:
                    yield current_batch
                break
            
            # Check stop conditions
            page_count += 1
            limit_value = params.get('limit', 100)
            record_count = len(page_data)
            logger.info(
                f"Evaluating stop conditions for page {page_count}: "
                f"{record_count} records returned, limit={limit_value}"
            )
            should_stop = self._check_stop_conditions(page_data, stop_conditions, params, full_response_data)
            if should_stop:
                logger.info(
                    f"✅ Stop condition met at page {page_count} "
                    f"(page returned {record_count} records, limit: {limit_value})"
                )
                for record in page_data:
                    current_batch.append(record)
                    total_extracted += 1
                    if len(current_batch) >= batch_size:
                        yield current_batch
                        current_batch = []
                if current_batch:
                    yield current_batch
                break
            
            # Add page data to current batch
            for record in page_data:
                current_batch.append(record)
                total_extracted += 1
                
                if len(current_batch) >= batch_size:
                    yield current_batch
                    current_batch = []
                
                if max_records and total_extracted >= max_records:
                    if current_batch:
                        yield current_batch
                    return
            
            # Extract pagination token/URL for next iteration
            if strategy == 'cursor' and full_response_data:
                try:
                    current = full_response_data
                    for part in cursor_response_path.split('.'):
                        if isinstance(current, dict):
                            current = current.get(part)
                        elif isinstance(current, list) and part.isdigit():
                            current = current[int(part)]
                        else:
                            current = None
                            break
                    
                    if current and isinstance(current, str):
                        current_cursor = current
                    elif current:
                        current_cursor = str(current)
                    else:
                        if current_batch:
                            yield current_batch
                        break
                except (KeyError, IndexError, TypeError, ValueError):
                    if current_batch:
                        yield current_batch
                    break
            
            elif strategy == 'next_url' and full_response_data:
                try:
                    current = full_response_data
                    for part in next_url_response_path.split('.'):
                        if isinstance(current, dict):
                            current = current.get(part)
                        elif isinstance(current, list) and part.isdigit():
                            current = current[int(part)]
                        else:
                            current = None
                            break
                    
                    if current and isinstance(current, str):
                        current_url = current
                    else:
                        current_url = None
                    
                    if not current_url:
                        if current_batch:
                            yield current_batch
                        break
                except (KeyError, IndexError, TypeError, ValueError):
                    if current_batch:
                        yield current_batch
                    break
            
            elif strategy == 'link_header' and response_obj:
                current_url = self._extract_link_header_url(response_obj)
                if not current_url:
                    if current_batch:
                        yield current_batch
                    break
                extract_config_copy['api_endpoint'] = current_url
                extract_config_copy['base_url'] = ''
            
            # Update pagination state
            if strategy == 'page':
                current_page += page_increment
            elif strategy == 'offset':
                limit = params.get('limit', 100)
                if increment_by == 'limit':
                    current_offset += limit
                else:
                    current_offset += int(increment_by)
            
            # Delay between pages
            if page_delay > 0:
                await asyncio.sleep(page_delay)
        
        # Yield remaining records
        if current_batch:
            yield current_batch
    
    # Helper methods
    def _resolve_rate_limit_delay(
        self,
        rate_limit_delay: Any,
        contract_dir: Optional[Any] = None,
        config_context: Optional[Dict[str, Any]] = None,
    ) -> float:
        """Resolve and convert rate_limit_delay to float."""
        if isinstance(rate_limit_delay, str):
            source_file = str(contract_dir / "extract.yaml") if contract_dir else None
            resolved = resolve_values(rate_limit_delay, context=config_context, source_file=source_file)
            return float(resolved)
        return float(rate_limit_delay)
    
    def _build_request_url(
        self,
        base_url: str,
        api_endpoint: str,
        path_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build full request URL from base URL and endpoint."""
        if api_endpoint.startswith(('http://', 'https://')):
            url = api_endpoint
        elif base_url:
            base_url = base_url.rstrip('/')
            endpoint = api_endpoint.lstrip('/')
            url = f"{base_url}/{endpoint}"
        else:
            raise ValueError(
                "Either 'api_endpoint' must be a full URL (starting with http:// or https://) "
                "or 'base_url' must be provided in extract.yaml"
            )
        
        # Substitute path parameters
        if path_params and '{' in url:
            try:
                url = url.format(**path_params)
            except KeyError as e:
                raise ValueError(
                    f"Missing required path parameter in URL: {e}. "
                    f"URL: {url}, Available params: {list(path_params.keys())}"
                ) from e
        
        return url
    
    def _configure_timeout(self, timeout_config: Dict[str, Any]) -> httpx.Timeout:
        """Configure HTTP timeout from config dictionary."""
        timeout = httpx.Timeout(
            connect=float(timeout_config.get('connect', DEFAULT_TIMEOUT_CONNECT)),
            read=float(timeout_config.get('read', DEFAULT_TIMEOUT_READ)),
            write=float(timeout_config.get('write', DEFAULT_TIMEOUT_WRITE)),
            pool=float(timeout_config.get('pool', DEFAULT_TIMEOUT_POOL)),
        )
        logger.debug(
            f"Configured HTTP timeout: connect={timeout.connect}s, "
            f"read={timeout.read}s, write={timeout.write}s, pool={timeout.pool}s"
        )
        return timeout
    
    async def _make_http_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, Any],
        body: Optional[Any] = None,
    ) -> httpx.Response:
        """Make HTTP request with specified method."""
        method = method.upper()
        
        logger.debug(f"Making {method} request to {url}")
        
        try:
            if method == 'GET':
                return await client.get(url, params=params, headers=headers)
            elif method == 'POST':
                if body:
                    return await client.post(
                        url,
                        json=body if isinstance(body, dict) else body,
                        params=params,
                        headers=headers,
                    )
                else:
                    return await client.post(url, params=params, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
        except httpx.TimeoutException as e:
            timeout_info = ""
            if hasattr(e, 'timeout') and isinstance(e.timeout, httpx.Timeout):
                timeout_info = (
                    f" (connect timeout: {e.timeout.connect}s, "
                    f"read timeout: {e.timeout.read}s)"
                )
            logger.error(f"HTTP request timeout for {method} {url}{timeout_info}")
            raise
        except httpx.RequestError as e:
            logger.error(f"HTTP request error for {method} {url}: {type(e).__name__}: {e}")
            raise
    
    def _extract_by_path(self, data: Any, path: str) -> List[Dict[str, Any]]:
        """Extract data using a simple path notation (e.g., 'data.items')."""
        current = data
        for part in path.split('.'):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                current = current[int(part)]
            else:
                return []
            
            if current is None:
                return []
        
        if isinstance(current, list):
            return current
        elif isinstance(current, dict):
            return [current]
        else:
            return []
    
    def _extract_data_array(self, data: Any) -> List[Dict[str, Any]]:
        """Extract data array from response, handling common response structures."""
        if isinstance(data, list):
            return data
        elif isinstance(data, dict):
            # Try common keys for data arrays
            for key in RESPONSE_DATA_KEYS:
                if key in data and isinstance(data[key], list):
                    return data[key]
            # If no array found, return as single-item list
            return [data]
        else:
            return []
    
    def _check_stop_conditions(
        self,
        page_data: List[Dict[str, Any]],
        stop_conditions: List[Dict[str, Any]],
        params: Dict[str, Any],
        response_data: Any = None,
    ) -> bool:
        """Check if pagination should stop based on configured stop conditions."""
        if not stop_conditions:
            # Default: stop if fewer records than limit
            limit = params.get('limit', 100)
            return len(page_data) < limit
        
        for condition in stop_conditions:
            if self._check_stop_condition(condition, page_data, params, response_data):
                return True
        
        return False
    
    def _check_stop_condition(
        self,
        condition: Dict[str, Any],
        page_data: List[Dict[str, Any]],
        params: Dict[str, Any],
        response_data: Any = None,
    ) -> bool:
        """Check a single stop condition."""
        condition_type = condition.get('type')
        
        if condition_type == 'empty_response':
            if not page_data:
                logger.debug("Stop condition 'empty_response' triggered: page is empty")
                return True
        
        elif condition_type == 'fewer_records':
            limit = params.get('limit', 100)
            record_count = len(page_data)
            if record_count < limit:
                logger.debug(
                    f"Stop condition 'fewer_records' triggered: "
                    f"page returned {record_count} records < limit {limit}"
                )
                return True
        
        elif condition_type == 'max_pages':
            max_pages = condition.get('value', 1000)
            current_page = params.get('page', 0)
            if current_page >= max_pages:
                logger.debug(f"Stop condition 'max_pages' triggered: page {current_page} >= {max_pages}")
                return True
        
        elif condition_type == 'custom':
            return self._check_custom_stop_condition(condition, response_data)
        
        return False
    
    def _check_custom_stop_condition(
        self,
        condition: Dict[str, Any],
        response_data: Any,
    ) -> bool:
        """Check custom stop condition based on response path."""
        response_path = condition.get('response_path')
        expected_value = condition.get('value')
        
        if not response_path or not response_data:
            return False
        
        try:
            current = response_data
            for part in response_path.split('.'):
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    current = current[int(part)]
                else:
                    return False
            return current == expected_value
        except (KeyError, IndexError, TypeError):
            return False
    
    def _extract_link_header_url(self, response: httpx.Response) -> Optional[str]:
        """Extract next URL from Link header (RFC 5988)."""
        link_header = response.headers.get('Link', '')
        if not link_header:
            return None
        
        # Parse Link header: <url>; rel="next"
        pattern = r'<([^>]+)>;\s*rel=["\']?next["\']?'
        match = re.search(pattern, link_header, re.IGNORECASE)
        if match:
            return match.group(1)
        
        return None
