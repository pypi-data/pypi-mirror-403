from asyncio import open_connection, sleep, StreamReader, StreamWriter, wait_for
from dataclasses import dataclass, field
from enum import Enum
from hashlib import sha256
from json import JSONDecodeError, loads as json_loads
from logging import Logger
from os import close
from pathlib import Path
from shutil import move
from ssl import create_default_context, SSLContext, CERT_NONE, SSLError
from tempfile import mkstemp
from typing import Callable, Any
from urllib.parse import urlparse
from sys import stdout


class DownloadError(Exception):
    """base exception for download errors"""
    pass


class RetryableError(DownloadError):
    """error where it makes sense to retry the attempt"""
    pass


class FatalError(DownloadError):
    """fatal error, repetition is meaningless"""
    pass


class HTTPStatus(Enum):
    """categories of http status codes"""
    SUCCESS = 'success'
    REDIRECT = 'redirect'
    CLIENT_ERROR = 'client_error'
    SERVER_ERROR = 'server_error'

    @classmethod
    def from_code(cls, code: int) -> 'HTTPStatus':
        if 200 <= code < 300:
            return cls.SUCCESS
        elif 300 <= code < 400:
            return cls.REDIRECT
        elif 400 <= code < 500:
            return cls.CLIENT_ERROR
        else:
            return cls.SERVER_ERROR


@dataclass
class HTTPResponse:
    """parsed http response"""
    status_code: int
    status_text: str
    headers: dict[str, str]
    body_reader: StreamReader
    writer: StreamWriter | None = None

    def close(self):
        """close connection"""
        if self.writer:
            self.writer.close()

    async def wait_closed(self):
        """wait for the connection to close"""
        if self.writer:
            try:
                await self.writer.wait_closed()
            except Exception:
                pass


@dataclass
class DownloadConfig:
    """download configuration"""

    # timeouts
    connect_timeout: float = 30.0
    read_timeout: float = 60.0
    total_timeout: float = 1800.0  # 30 min.

    # repeated attempts
    max_retries: int = 5
    retry_delay_base: float = 1.0
    retry_delay_max: float = 60.0
    retry_backoff_factor: float = 2.0

    # buffers sizes
    chunk_size: int = 64 * 1024  # 64 KB

    # memory limits for fetch
    max_memory_size: int = 10 * 1024 * 1024  # 10 MB default limit

    # redirects
    max_redirects: int = 10

    # validations
    verify_ssl: bool = True
    expected_size: int | None = None
    expected_hash: str | None = None  # sha-256

    # progeress
    progress_callback: Callable[[int, int | None], None] | None = None
    logger: Logger = None

    # http-headers
    user_agent: str = 'Python-AsyncDownloader/1.0'
    extra_headers: dict[str, str] = field(default_factory=dict)


@dataclass
class DownloadResult:
    """download result"""
    success: bool
    file_path: Path | None
    file_size: int
    sha256_hash: str
    attempts: int
    error: str | None = None


@dataclass
class FetchResult:
    """result of fetching data into memory"""
    success: bool
    status_code: int
    headers: dict[str, str]
    content: bytes
    url: str  # final url after redirects
    attempts: int
    error: str | None = None

    # cached parsed data
    _text: str | None = field(default=None, repr=False)
    _json: Any | None = field(default=None, repr=False)
    _json_parsed: bool = field(default=False, repr=False)

    @property
    def text(self) -> str:
        """decode content as text"""
        if self._text is None:
            encoding = self._detect_encoding()
            self._text = self.content.decode(encoding, errors='replace')
        return self._text

    def _detect_encoding(self) -> str:
        """detect encoding from content-type header"""
        content_type = self.headers.get('content-type', '')

        # extract charset from content-type: text/html; charset=utf-8
        if 'charset=' in content_type.lower():
            parts = content_type.lower().split('charset=')
            if len(parts) > 1:
                charset = parts[1].split(';')[0].strip().strip('"\'')
                return charset

        return 'utf-8'

    def json(self) -> Any:
        """parse content as JSON"""
        if not self._json_parsed:
            try:
                self._json = json_loads(self.content)
            except JSONDecodeError as e:
                raise ValueError(f'failed to parse JSON: {e}')
            self._json_parsed = True
        return self._json

    @property
    def content_type(self) -> str:
        """get content-type without parameters"""
        ct = self.headers.get('content-type', '')
        return ct.split(';')[0].strip()

    @property
    def is_json(self) -> bool:
        """check if content-type indicates JSON"""
        ct = self.content_type.lower()
        return ct == 'application/json' or ct.endswith('+json')

    def __len__(self) -> int:
        return len(self.content)


class AsyncHTTPClient:
    """low-level asynchronous http client"""

    def __init__(self, config: DownloadConfig):
        self.config = config
        self._ssl_context: SSLContext | None = None

    def _get_ssl_context(self) -> SSLContext:
        """get or create ssl-context"""
        if self._ssl_context is None:
            if self.config.verify_ssl:
                self._ssl_context = create_default_context()
            else:
                self._ssl_context = create_default_context()
                self._ssl_context.check_hostname = False
                self._ssl_context.verify_mode = CERT_NONE
        return self._ssl_context

    @staticmethod
    def _parse_url(url: str) -> tuple[str, str, int, str, bool]:
        """url components parsing"""
        parsed = urlparse(url)

        scheme = parsed.scheme.lower()
        if scheme not in ('http', 'https'):
            raise FatalError(f'unsupported url-scheme: {scheme}')

        use_ssl = scheme == 'https'
        host = parsed.hostname
        if not host:
            raise FatalError(f'invalid URL: missing host')

        port = parsed.port or (443 if use_ssl else 80)
        path = parsed.path or '/'
        if parsed.query:
            path = f'{path}?{parsed.query}'

        return host, parsed.netloc, port, path, use_ssl

    def _build_request(self, host: str, path: str, extra_headers: dict | None = None) -> bytes:
        """http request building"""
        headers = {
            'Host': host,
            'User-Agent': self.config.user_agent,
            'Accept': '*/*',
            'Accept-Encoding': 'identity',
            'Connection': 'close',
        }

        if extra_headers:
            headers.update(extra_headers)

        headers.update(self.config.extra_headers)

        lines = [f'GET {path} HTTP/1.1']
        lines.extend(f'{k}: {v}' for k, v in headers.items())
        lines.append('')
        lines.append('')

        return '\r\n'.join(lines).encode('utf-8')

    async def _parse_response_headers(self, reader: StreamReader) -> tuple[int, str, dict[str, str]]:
        """parse http-headers from response"""
        status_line = await wait_for(
            reader.readline(),
            timeout=self.config.read_timeout
        )

        if not status_line:
            raise RetryableError('empty response from server')

        status_line = status_line.decode('utf-8', errors='replace').strip()

        try:
            # http/1.1 200 ok
            parts = status_line.split(' ', 2)
            status_code = int(parts[1])
            status_text = parts[2] if len(parts) > 2 else ''
        except (IndexError, ValueError) as e:
            raise RetryableError(f'invalid status line: {status_line}')

        headers: dict[str, str] = {}
        while True:
            line = await wait_for(
                reader.readline(),
                timeout=self.config.read_timeout
            )
            line = line.decode('utf-8', errors='replace').strip()

            if not line:
                break

            if ':' in line:
                key, value = line.split(':', 1)
                headers[key.strip().lower()] = value.strip()

        return status_code, status_text, headers

    async def request(self, url: str) -> HTTPResponse:
        """выполнить http-get запрос"""
        host, netloc, port, path, use_ssl = self._parse_url(url)

        ssl_context = self._get_ssl_context() if use_ssl else None

        try:
            reader, writer = await wait_for(
                open_connection(
                    host, port, ssl=ssl_context
                ),
                timeout=self.config.connect_timeout
            )
        except TimeoutError:
            raise RetryableError(f'connection timeout to {host}:{port}')
        except SSLError as e:
            raise RetryableError(f'ssl error: {e}')
        except OSError as e:
            raise RetryableError(f'network error: {e}')

        try:
            request = self._build_request(netloc, path)
            writer.write(request)
            await wait_for(
                writer.drain(),
                timeout=self.config.read_timeout
            )

            status_code, status_text, headers = await self._parse_response_headers(reader)

            return HTTPResponse(
                status_code=status_code,
                status_text=status_text,
                headers=headers,
                body_reader=reader,
                writer=writer
            )

        except Exception:
            writer.close()
            try:
                await writer.wait_closed()
            except Exception:
                pass
            raise


class FileDownloader:
    def __init__(self, config: DownloadConfig | None = None):
        self.config = config or DownloadConfig()
        self.client = AsyncHTTPClient(self.config)

    def _calculate_retry_delay(self, attempt: int) -> float:
        """calculation of delay before retry"""
        delay = self.config.retry_delay_base * (
                self.config.retry_backoff_factor ** attempt
        )
        return min(delay, self.config.retry_delay_max)

    @staticmethod
    async def _close_response(response: HTTPResponse):
        """safely close response"""
        response.close()
        await response.wait_closed()

    async def _follow_redirects(self, url: str) -> tuple[HTTPResponse, str]:
        """following to redirects"""
        current_url = url

        for redirect_count in range(self.config.max_redirects + 1):
            response = await self.client.request(current_url)
            status = HTTPStatus.from_code(response.status_code)

            if status == HTTPStatus.SUCCESS:
                return response, current_url

            elif status == HTTPStatus.REDIRECT:
                # close current connection
                await self._close_response(response)

                location = response.headers.get('location')
                if not location:
                    raise FatalError(
                        f'redirect {response.status_code} w/o "location" header'
                    )

                # relative urls
                if location.startswith('/'):
                    parsed = urlparse(current_url)
                    location = f'{parsed.scheme}://{parsed.netloc}{location}'
                elif not location.startswith(('http://', 'https://')):
                    parsed = urlparse(current_url)
                    base_path = '/'.join(parsed.path.split('/')[:-1])
                    location = f'{parsed.scheme}://{parsed.netloc}{base_path}/{location}'

                if self.config.logger: self.config.logger.info(f'redirect {response.status_code}: {location}')
                current_url = location

            elif status == HTTPStatus.CLIENT_ERROR:
                await self._close_response(response)
                raise FatalError(
                    f'client error {response.status_code}: {response.status_text}'
                )

            else:  # SERVER_ERROR
                await self._close_response(response)
                raise RetryableError(
                    f'server error {response.status_code}: {response.status_text}'
                )

        raise FatalError(f'maximum number of redirects exceeded: {self.config.max_redirects}')

    async def _download_to_file(self, response: HTTPResponse, temp_path: Path) -> tuple[int, str]:
        """loading the response body into a file"""
        content_length = response.headers.get('content-length')
        expected_size = int(content_length) if content_length else None

        if self.config.expected_size and expected_size:
            if expected_size != self.config.expected_size:
                raise FatalError(
                    f'size mismatch: expected {self.config.expected_size}, but got {expected_size}'
                )

        hasher = sha256()
        downloaded = 0

        with open(temp_path, 'wb') as f:
            while True:
                try:
                    chunk = await wait_for(
                        response.body_reader.read(self.config.chunk_size),
                        timeout=self.config.read_timeout
                    )
                except TimeoutError:
                    raise RetryableError('read timeout after {downloaded} bytes')

                if not chunk:
                    break

                f.write(chunk)
                hasher.update(chunk)
                downloaded += len(chunk)

                # callback progress
                if self.config.progress_callback:
                    try:
                        self.config.progress_callback(downloaded, expected_size)
                    except Exception as e:
                        if self.config.logger: self.config.logger.warning(f'progress callback error: {e}')

        # filesize check
        if expected_size and downloaded != expected_size:
            raise RetryableError(
                f'incomplete download: received {downloaded} of {expected_size} bytes'
            )

        file_hash = hasher.hexdigest()

        # file hash check
        if self.config.expected_hash:
            if file_hash.lower() != self.config.expected_hash.lower():
                raise FatalError(f'hash mismatch: expected {self.config.expected_hash}, got {file_hash}')

        return downloaded, file_hash

    async def _read_to_memory(
            self,
            response: HTTPResponse,
            max_size: int | None = None
    ) -> bytes:
        """read response body into memory with size limit"""
        limit = max_size or self.config.max_memory_size
        is_chunked = response.headers.get('transfer-encoding', '').lower() == 'chunked'

        content_length = response.headers.get('content-length')
        if content_length and not is_chunked:
            expected_size = int(content_length)
            if expected_size > limit:
                raise FatalError(
                    f'content too large: {expected_size} bytes exceeds limit of {limit} bytes'
                )

        chunks: list[bytes] = []
        total_read = 0

        if is_chunked:
            while True:
                try:
                    size_line = await wait_for(
                        response.body_reader.readline(),
                        timeout=self.config.read_timeout
                    )
                    
                    size_str = size_line.decode('ascii').strip().split(';')[0]
                    chunk_size = int(size_str, 16)

                    if chunk_size == 0:
                        await response.body_reader.readline()
                        break

                    chunk_data = await wait_for(
                        response.body_reader.readexactly(chunk_size),
                        timeout=self.config.read_timeout
                    )
                    
                    await response.body_reader.readline()

                    total_read += len(chunk_data)
                    if total_read > limit:
                        raise FatalError(f'content too large: exceeded limit of {limit} bytes')

                    chunks.append(chunk_data)

                except TimeoutError:
                    raise RetryableError(f'read timeout after {total_read} bytes')
        else:
            while True:
                try:
                    chunk = await wait_for(
                        response.body_reader.read(self.config.chunk_size),
                        timeout=self.config.read_timeout
                    )
                except TimeoutError:
                    raise RetryableError(f'read timeout after {total_read} bytes')

                if not chunk:
                    break

                total_read += len(chunk)
                if total_read > limit:
                    raise FatalError(f'content too large: exceeded limit of {limit} bytes')

                chunks.append(chunk)

                if self.config.progress_callback:
                    expected = int(content_length) if content_length else None
                    try:
                        self.config.progress_callback(total_read, expected)
                    except Exception as e:
                        if self.config.logger:
                            self.config.logger.warning(f'progress callback error: {e}')

        return b''.join(chunks)

    async def _fetch_attempt(
        self,
        url: str,
        max_size: int | None = None
    ) -> tuple[bytes, dict[str, str], int, str]:
        """single fetch attempt, returns (content, headers, status_code, final_url)"""
        response, final_url = await self._follow_redirects(url)

        try:
            content = await self._read_to_memory(response, max_size)
            return content, response.headers, response.status_code, final_url
        finally:
            await self._close_response(response)

    async def fetch(
        self,
        url: str,
        *,
        max_size: int | None = None
    ) -> FetchResult:
        """
        fetch URL content into memory

        Args:
            url: URL to fetch
            max_size: maximum content size in bytes (default from config: 10MB)

        Returns:
            FetchResult with response data
        """
        last_error: str | None = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if self.config.logger:
                    self.config.logger.info(
                        f'fetch attempt {attempt + 1}/{self.config.max_retries + 1}: {url}'
                    )

                content, headers, status_code, final_url = await wait_for(
                    self._fetch_attempt(url, max_size),
                    timeout=self.config.total_timeout
                )

                if self.config.logger:
                    self.config.logger.info(
                        f'successfully fetched: {len(content)} bytes'
                    )

                return FetchResult(
                    success=True,
                    status_code=status_code,
                    headers=headers,
                    content=content,
                    url=final_url,
                    attempts=attempt + 1
                )

            except FatalError as e:
                if self.config.logger:
                    self.config.logger.error(f'fatal error: {e}')
                return FetchResult(
                    success=False,
                    status_code=0,
                    headers={},
                    content=b'',
                    url=url,
                    attempts=attempt + 1,
                    error=str(e)
                )

            except (RetryableError, TimeoutError, OSError) as e:
                last_error = str(e)
                if self.config.logger:
                    self.config.logger.warning(f'attempt {attempt + 1} failed: {e}')

                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    if self.config.logger:
                        self.config.logger.info(f'retry after {delay:.1f} sec...')
                    await sleep(delay)

            except Exception as e:
                last_error = f'unexpected error: {type(e).__name__}: {e}'
                if self.config.logger:
                    self.config.logger.exception(f'unexpected error: {e}')
                if attempt < self.config.max_retries:
                    delay = self._calculate_retry_delay(attempt)
                    await sleep(delay)

        # all attempts exhausted
        return FetchResult(
            success=False,
            status_code=0,
            headers={},
            content=b'',
            url=url,
            attempts=self.config.max_retries + 1,
            error=f'all attempts exhausted, last error: {last_error}'
        )

    async def _download_attempt(self, url: str, temp_path: Path) -> tuple[int, str]:
        """single download attempt"""
        response, final_url = await self._follow_redirects(url)

        try:
            return await self._download_to_file(response, temp_path)
        finally:
            await self._close_response(response)

    async def download(self, url: str, destination: Path | str) -> DownloadResult:
        """
        asynchronous file download with retry mechanism

        Args:
            url: url of file to download
            destination: path to save the file

        Returns:
            DownloadResult with download information
        """
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path_str = mkstemp(dir=destination.parent, prefix=f'.{destination.name}.', suffix='.download')
        close(temp_fd)
        temp_path = Path(temp_path_str)
        last_error: str | None = None

        try:
            for attempt in range(self.config.max_retries + 1):
                try:
                    if self.config.logger: self.config.logger.info(f'attempt {attempt + 1}/{self.config.max_retries + 1}: {url}')

                    file_size, file_hash = await wait_for(
                        self._download_attempt(url, temp_path),
                        timeout=self.config.total_timeout
                    )

                    # successful download -> moving
                    move(str(temp_path), str(destination))

                    if self.config.logger: self.config.logger.info(f'successful downloaded: {file_size} bytes, SHA-256: {file_hash[:16]}...')

                    return DownloadResult(
                        success=True,
                        file_path=destination,
                        file_size=file_size,
                        sha256_hash=file_hash,
                        attempts=attempt + 1
                    )

                except FatalError as e:
                    if self.config.logger: self.config.logger.error(f'fatal error: {e}')
                    return DownloadResult(
                        success=False,
                        file_path=None,
                        file_size=0,
                        sha256_hash='',
                        attempts=attempt + 1,
                        error=str(e)
                    )

                except (RetryableError, TimeoutError, OSError) as e:
                    last_error = str(e)
                    if self.config.logger: self.config.logger.warning(f'attempt {attempt + 1} failed: {e}')

                    if attempt < self.config.max_retries:
                        delay = self._calculate_retry_delay(attempt)
                        if self.config.logger: self.config.logger.info(f'retry after {delay:.1f} sec...')
                        await sleep(delay)
                        if temp_path.exists():
                            temp_path.unlink()

                except Exception as e:
                    last_error = f'unexpected error: {type(e).__name__}: {e}'
                    if self.config.logger: self.config.logger.exception(f'unexpected error: {e}')
                    if attempt < self.config.max_retries:
                        delay = self._calculate_retry_delay(attempt)
                        await sleep(delay)

            # all attempts are exhausted
            return DownloadResult(
                success=False,
                file_path=None,
                file_size=0,
                sha256_hash='',
                attempts=self.config.max_retries + 1,
                error=f'all attempts are exhausted, last error: {last_error}'
            )

        finally:
            if self.config.progress_callback: stdout.write('\n')
            # clearing temporary file
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass


def create_progress_bar(width: int = 50) -> Callable[[int, int | None], None]:
    """callback to display console progress-bar"""
    def callback(downloaded: int, total: int | None) -> None:
        if total:
            percent = downloaded / total
            filled = int(width * percent)
            bar = "█" * filled + "░" * (width - filled)
            mb_down = downloaded / (1024 * 1024)
            mb_total = total / (1024 * 1024)
            stdout.write(
                f"\r[{bar}] {percent * 100:.1f}% ({mb_down:.1f}/{mb_total:.1f} MB)"
            )
        else:
            mb_down = downloaded / (1024 * 1024)
            stdout.write(f'\rdownloaded: {mb_down:.1f} MB')
        stdout.flush()

    return callback


async def download_file(
        url: str,
        destination: Path | str,
        *,
        max_retries: int = 5,
        timeout: float = 1800.0,
        verify_ssl: bool = True,
        expected_hash: str | None = None,
        progress_callback: Callable[[int, int | None], None] | None = None,
        logger: Logger = None,
) -> DownloadResult:
    """
    simple interface for file downloading.

    Args:
        url: file URL
        destination: save path
        max_retries: maximum retries
        timeout: total timeout in seconds
        verify_ssl: verify SSL certificates
        expected_hash: expected SHA-256 hash (optional)
        progress_callback: function callback(downloaded, total)
        logger: configured logger logging.Logger

    Returns:
        DownloadResult
    """
    config = DownloadConfig(
        max_retries=max_retries,
        total_timeout=timeout,
        verify_ssl=verify_ssl,
        expected_hash=expected_hash,
        progress_callback=progress_callback,
        logger=logger,
    )

    downloader = FileDownloader(config)
    return await downloader.download(url, destination)


async def fetch_url(
    url: str,
    *,
    max_retries: int = 3,
    timeout: float = 60.0,
    max_size: int = 10 * 1024 * 1024,  # 10 MB
    verify_ssl: bool = True,
    headers: dict[str, str] | None = None,
    logger: Logger = None,
) -> FetchResult:
    """
    simple interface for fetching URL content into memory.

    Args:
        url: URL to fetch
        max_retries: maximum retry attempts
        timeout: total timeout in seconds
        max_size: maximum content size in bytes
        verify_ssl: verify SSL certificates
        headers: additional HTTP headers
        logger: configured logger

    Returns:
        FetchResult with response data

    Example:
        # get HTML page
        result = await fetch_url('https://example.com')
        if result.success:
            print(result.text)

        # get JSON API response
        result = await fetch_url('https://api.example.com/data')
        if result.success:
            data = result.json()
            print(data['key'])
    """
    config = DownloadConfig(
        max_retries=max_retries,
        total_timeout=timeout,
        max_memory_size=max_size,
        verify_ssl=verify_ssl,
        extra_headers=headers or {},
        logger=logger,
    )

    downloader = FileDownloader(config)
    return await downloader.fetch(url, max_size=max_size)


async def fetch_json(
    url: str,
    *,
    max_retries: int = 3,
    timeout: float = 60.0,
    max_size: int = 10 * 1024 * 1024,
    verify_ssl: bool = True,
    headers: dict[str, str] | None = None,
    logger: Logger = None,
) -> tuple[Any | None, FetchResult]:
    """
    fetch URL and parse as JSON.

    Args:
        url: URL to fetch
        max_retries: maximum retry attempts
        timeout: total timeout in seconds
        max_size: maximum content size in bytes
        verify_ssl: verify SSL certificates
        headers: additional HTTP headers
        logger: configured logger

    Returns:
        tuple of (parsed JSON data or None, FetchResult)

    Example:
        data, result = await fetch_json('https://api.example.com/users')
        if result.success and data:
            for user in data['users']:
                print(user['name'])
    """
    # add Accept header for JSON
    all_headers = {'Accept': 'application/json'}
    if headers:
        all_headers.update(headers)

    result = await fetch_url(
        url,
        max_retries=max_retries,
        timeout=timeout,
        max_size=max_size,
        verify_ssl=verify_ssl,
        headers=all_headers,
        logger=logger,
    )

    if result.success:
        try:
            return result.json(), result
        except ValueError:
            return None, result

    return None, result