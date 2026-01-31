# Rapida Python SDK

[![Build and Publish Python SDK](https://github.com/rapidaai/rapida-python/actions/workflows/python-build.yml/badge.svg?branch=main)](https://github.com/rapidaai/rapida-python/actions/workflows/build.yml)

The Rapida Python SDK provides a powerful interface for interacting with Rapida AI services. This SDK simplifies the process of making API calls, handling authentication, and managing responses from Rapida endpoints.

## Installation

To install the Rapida Python SDK, use the following command:

```bash
pip install rapida-python
```

## Quick Start

Here's how to get started with the Rapida Python SDK:

```python
from rapida import (
    ConnectionConfig,
)
from pprint import pprint


connection_config = ConnectionConfig.default_connection_config(
    ConnectionConfig.with_sdk(
        "{your-api-key-here}"  # Replace with your actual API key
    )
)

```

## Authentication

You can configure the Rapida SDK to authenticate using your **API Key** or **Personal Token**:

### Authenticating with API Key

```python
import os
from rapida.connections import ConnectionConfig
connection_config = ConnectionConfig.with_sdk(
    os.environ["RAPIDA_API_KEY"]  # API Key from environment variables
)
```

### Authenticating with Personal Token

```python
import os
from rapida.connections import ConnectionConfig

connection_config = ConnectionConfig.with_personal_token(
  os.environ["RAPIDA_AUTHORIZATION_TOKEN"],  # Authorization Token
  os.environ["RAPIDA_AUTH_ID"],              # Authentication ID
  os.environ["RAPIDA_PROJECT_ID"],           # Project ID
)
```

## Configuration Options

The `DefaultConnectionConfig` accepts multiple options for configuring the SDK. Key options include:

- `with_sdk(api_key: str)`: Sets the API key for authentication.
- `with_personal_token(auth_token: str, auth_id: str, project_id: str)`: Configures the connection for personal tokens.
- `with_endpoint_url(url: str)`: Overrides the default API endpoint URL.
- `with_timeout(timeout: float)`: Sets the timeout for API requests (in seconds).

## Compatibility

This SDK requires **Python 3.8 or later**. Ensure your system meets this requirement:

```bash
python --version
```

To upgrade or specify a version, use the following command:

```bash
pip install --upgrade rapida-python
```

---

## Conclusion

The Rapida Python SDK provides everything necessary to integrate seamlessly with Rapida AI services, offering flexible configuration and authentication options. With the examples provided, you should be able to get started quickly and make advanced API calls as needed.

