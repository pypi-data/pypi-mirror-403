<div align="center">
<img width="100px" height="100px" alt="API-Forwarder" src="https://raw.githubusercontent.com/CrossDarkrix/API-Forwarder/main/image/icon.png">

  <h1>API Forwarder</h1>
  <h3>Simplify API calls by sharing a base URL</h3>
</div>
<h2>Features</h2>
<ul>
  <li>No need to repeat the same base API URL for every request.</li>
  <li>Specify a base URL once, then call API endpoints using relative paths.</li>
  <li>Pluggable HTTP backends (httpx or CloudScraper).</li>
</ul>

This library is designed to be imported and reused across projects,
providing a consistent and clean way to interact with HTTP-based APIs.

## Usage

```python
from api_forwarder import Forwarder

async def get_api():
    async with Forwarder("https://api.example.com") as fw:
        response = await fw.get("/v1/status")
        response.raise_for_status()
        print(response.json())
```

## Use Other Options

```python
from api_forwarder import Forwarder
async def get_api():
    async with Forwarder(
        "https://api.example.com",
        backend="cloudscraper",
        timeout=5.0,
        retries=3,
        retry_delay=1.0,
    ) as fw:
        response = await fw.get("/v1/status")
        response.raise_for_status()
        print(response.json())
```
