# quickapi_async/core.py
import aiohttp
import asyncio
from typing import Optional


from rich.progress import Progress, BarColumn, TextColumn
from rich.console import Console


class _APIResponse:
    """
    Represents the response from an API request.

    Attributes:
        status (int): HTTP status code returned by the server.
        data (Optional[dict]): Parsed JSON data if available, otherwise None.
    """

    def __init__(self, status: int, data: Optional[dict]):
        self.status = status
        self.data = data


class QuickAPIAsync:
    """
    An asynchronous HTTP client supporting GET and POST requests,
    with timeout, retries, and optional SSL verification bypass.

    Example usage:
        res = await QuickAPIAsync() \
            .get("https://example.com/api") \
            .timeout(5) \
            .retry(2) \
            .json(ignore_ssl=True)

        print(res.status)
        print(res.data)
    """

    def __init__(self):
        """
        Initializes the client with default settings.
        """
        self._url: Optional[str] = None
        self._method: str = "GET"
        self._headers: dict = {}
        self._data: Optional[dict] = None
        self._timeout: float = 5  # Default timeout in seconds
        self._retries: int = 0    # Default retry count

    def get(self, url: str) -> "QuickAPIAsync":
        """
        Set up a GET request.

        Args:
            url (str): The URL to send the GET request to.

        Returns:
            self: Allows method chaining.
        """
        self._url = url
        self._method = "GET"
        return self

    def post(self, url: str) -> "QuickAPIAsync":
        """
        Set up a POST request.

        Args:
            url (str): The URL to send the POST request to.

        Returns:
            self: Allows method chaining.
        """
        self._url = url
        self._method = "POST"
        return self

    def headers(self, headers: dict) -> "QuickAPIAsync":
        """
        Add or update HTTP headers for the request.

        Args:
            headers (dict): Dictionary of headers to add/update.

        Returns:
            self: Allows method chaining.
        """
        self._headers.update(headers)
        return self

    def auth(self, token: str) -> "QuickAPIAsync":
        """
        Set an Authorization header using Bearer token.

        Args:
            token (str): Bearer token for authorization.

        Returns:
            self: Allows method chaining.
        """
        self._headers["Authorization"] = f"Bearer {token}"
        return self

    def data(self, data: dict) -> "QuickAPIAsync":
        """
        Set JSON data for a POST request.

        Args:
            data (dict): Data to be sent as JSON.

        Returns:
            self: Allows method chaining.
        """
        self._data = data
        return self

    def timeout(self, seconds: int) -> "QuickAPIAsync":
        """
        Set the request timeout in seconds.

        Args:
            seconds (int): Number of seconds to wait before timing out.

        Returns:
            self: Allows method chaining.

        Raises:
            ValueError: If seconds is not positive.
        """
        if seconds <= 0:
            raise ValueError("Timeout must be greater than 0")
        self._timeout = seconds
        return self

    def retry(self, n: int) -> "QuickAPIAsync":
        """
        Set the number of retries if the request fails.

        Args:
            n (int): Number of retry attempts (0 means no retry).

        Returns:
            self: Allows method chaining.

        Raises:
            ValueError: If n is negative.
        """
        if n < 0:
            raise ValueError("Retry count must be >= 0")
        self._retries = n
        return self


    async def json(self, ignore_ssl: bool = False, show_progress: bool = False) -> _APIResponse:
        """
        Execute the HTTP request and return the response as a structured object.

        Args:
            ignore_ssl (bool, optional): If True, bypass SSL certificate verification.
            show_progress (bool, optional): If True, show a single horizontal progress bar
                                            covering all retries.

        Returns:
            _APIResponse: An object containing the HTTP status code and JSON data (or None).
        """
        timeout = aiohttp.ClientTimeout(total=self._timeout)
        connector = aiohttp.TCPConnector(ssl=False) if ignore_ssl else None
        console = Console()

        total_attempts = self._retries + 1  # общее число попыток

        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                last_exc = None

                if show_progress:
                    with Progress(
                        TextColumn("[cyan]Отправка запроса..."),
                        BarColumn(),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                        console=console,
                        transient=False
                    ) as progress:
                        task = progress.add_task("request", total=total_attempts)

                        for attempt in range(total_attempts):
                            try:
                                if self._method == "GET":
                                    resp = await session.get(self._url, headers=self._headers)
                                else:
                                    resp = await session.post(self._url, headers=self._headers, json=self._data)

                                async with resp:
                                    try:
                                        data: Optional[dict] = await resp.json()
                                    except aiohttp.ContentTypeError:
                                        data = None
                                    progress.update(task, advance=total_attempts)  # заполняем весь бар
                                    return _APIResponse(status=resp.status, data=data)

                            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                                last_exc = e
                                progress.update(task, advance=1)  # прогресс растёт за каждую попытку
                                if attempt < self._retries:
                                    await asyncio.sleep(attempt + 1)
                                else:
                                    raise RuntimeError(
                                        f"Request failed after {total_attempts} attempts: {type(last_exc).__name__}: {last_exc}"
                                    ) from last_exc
                else:
                    for attempt in range(total_attempts):
                        try:
                            if self._method == "GET":
                                resp = await session.get(self._url, headers=self._headers)
                            else:
                                resp = await session.post(self._url, headers=self._headers, json=self._data)

                            async with resp:
                                try:
                                    data: Optional[dict] = await resp.json()
                                except aiohttp.ContentTypeError:
                                    data = None
                                return _APIResponse(status=resp.status, data=data)

                        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                            last_exc = e
                            if attempt < self._retries:
                                await asyncio.sleep(attempt + 1)
                            else:
                                raise RuntimeError(
                                    f"Request failed after {total_attempts} attempts: {type(last_exc).__name__}: {last_exc}"
                                ) from last_exc
        finally:
            if connector:
                await connector.close()