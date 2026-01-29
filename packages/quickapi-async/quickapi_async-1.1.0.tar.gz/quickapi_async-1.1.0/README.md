# QuickAPI Async

**QuickAPI Async** is an asynchronous HTTP client for Python that supports GET and POST requests with retry, timeout, and optional SSL verification bypass.  

---

## Features

- Asynchronous GET and POST requests using `aiohttp`
- Configurable timeout for requests
- Automatic retries on failure
- Optional SSL verification bypass (`ignore_ssl=True`) for development or self-signed certificates
- Optional progress bar for request execution (`show_progress=True`)

---

### Installation

```bash
pip install quickapi_async
```

#### Optional Parameters

- .timeout(seconds) – set request timeout (default: 5)
- .retry(n) – number of retries if request fails (default: 0)
- .auth(token) – add Bearer token authentication
- .headers(dict) – add custom HTTP headers
- .data(dict) – provide JSON data for POST requests
- .json(ignore_ssl=True/False, show_progress=True/False) – send the request and return a response object with:
    - .status → HTTP status code (int)
    - .data → parsed JSON response as dict, or None if the response is not JSON
- ignore_ssl=True disables SSL verification; only use for testing or self-signed certificates
- show_progress=True shows a horizontal progress bar that covers all retry attempts

##### Example Usage
``` bash
**GET Request**

import asyncio
from quickapi_async import QuickAPIAsync

async def main():
    client = QuickAPIAsync()

    response = await (
        client.get("https://jsonplaceholder.typicode.com/todos/1")
              .timeout(10)
              .retry(2)
              .json(ignore_ssl=False, show_progress=True)
    )

    print("Status:", response.status)
    print("Data:", response.data)

asyncio.run(main())

----------
This GET request will try up to 3 times (1 initial + 2 retries) if it fails.
The progress bar will remain on screen after the request completes.
----------
```

``` bash
**POST Request with JSON and Authorization**

import asyncio
from quickapi_async import QuickAPIAsync

async def main():
    client = QuickAPIAsync()

    response = await (
        client.post("https://jsonplaceholder.typicode.com/posts")
              .timeout(10)
              .retry(2)
              .auth("your_bearer_token_here")
              .headers({"Custom-Header": "Value"})
              .data({
                  "title": "foo",
                  "body": "bar",
                  "userId": 1
              })
              .json(ignore_ssl=False, show_progress=True)
    )

    print("Status:", response.status)
    print("Data:", response.data)

asyncio.run(main())

----------
This POST request sends JSON data with custom headers and Bearer token authorization.
The progress bar shows the request progress across all retry attempts.
.data() provides the JSON payload for the POST request.
----------
```