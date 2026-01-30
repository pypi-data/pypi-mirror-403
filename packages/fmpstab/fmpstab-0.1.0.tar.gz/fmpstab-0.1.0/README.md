# Important Note
This is a clone of fmp-stable that is lightly modified for a personal project. It's reorganized for use with uv as a package / project manager. This should (eventually) work... but you'll probably want to access the real source.

# FMP Client Library
A Python client library for the [Financial Modeling Prep (FMP) API](https://financialmodelingprep.com/). This library provides both synchronous REST API and asynchronous WebSocket support, all in a modular, easy-to-use package.

The client is built to work with the [**Stable** version](https://site.financialmodelingprep.com/developer/docs/stable) of the Financial Modeling Prep (FMP) API. All endpoints are configured to use the stable base URL:
```arduino
https://financialmodelingprep.com/stable/
```
The endpoints available in this stable version are defined in the fmpstab_endpoints.json file

## Features

- **Unified API Client:**  
  Dynamically access FMP endpoints using Pythonic method names.

- **Rate-Limited HTTP Session:**  
  Built-in rate limiting using the `ratelimit` library and robust error handling with logging.

- **Dynamic Endpoint Methods:**  
  Automatically attaches methods based on your configuration file (`fmpstab_endpoints.json`).

- **Asynchronous WebSocket Clients:**  
  Separate clients for stocks, crypto, and forex data available in the `fmpstab_websockets` subpackage.

- **Flexible Configuration and Logging:**  
  Easily configure your endpoints with a JSON file and log messages to a file in the same directory as your main script.

## Installation
Using ```pip```

```bash
pip install fmpstab
```

Clone the repository and install the dependencies:

```bash
FIXME:: git clone https://github.com/Vimal-Seshadri-Raguraman/FMP.git
FIXME:: cd FMP
FIXME:: pip install -r requirements.txt
FIXME:: python setup.py install
```
Alternatively, install directly from Github:
```bash
FIXME:: pip install git+https://github.com/Vimal-Seshadri-Raguraman/FMP.git
```

## Usage
### API Client
Initialize the client with your API Key and call any endpoint dynmically:
```python
from fmpstab import FMPStab

# Initialize client with your API Key
client = fmpstab(api_key = "YOUR_API_KEY")

# Call an endpoint (e.g., "Profile")
response = client.profile(symbol = "AAPL")
print("Status Code:", response.status_code)
print("Profile Data:", response.json())
```
#### Dynmic Methods and Help
The client automatically attaches methods based on the JSON configuration. To see available endpoints and their parameters:
```python
# General help for all endpoints
print(client.help())

# Detailed help for a specific endpoint (e.g., "profile")
print(client.help("profile"))

# Generate a manual page of endpoints
man_doc = client.man_page() # Create a text file
print(man_doc)
```
### WebSocket Clients
The library includes asynchronous WebSocket clients for real-time data.
#### Stock WebSocket Example
```python
import asyncio
from fmpstab import StockWebsockets

async def run_stock_ws():
    stock_ws = StockWebsockets(tickers=["AAPL", "MSFT"], api_key="YOUR_API_KEY")
    async for message in stock_ws.run():
        print("Stock WebSocket Message:", message)

asyncio.run(run_stock_ws())
```
#### Crypto and Forex WebSocket Example
```python
import asyncio
from fmpstab import CryptoWebsockets, ForexWebsockets

async def run_crypto_ws():
    crypto_ws = CryptoWebsockets(tickers=["BTCUSD", "ETHUSD"], api_key="YOUR_API_KEY")
    async for message in crypto_ws.run():
        print("Crypto WebSocket Message:", message)

async def run_forex_ws():
    forex_ws = ForexWebsockets(pairs=["EURUSD", "GBPUSD"], api_key="YOUR_API_KEY")
    async for message in forex_ws.run():
        print("Forex WebSocket Message:", message)

# Run one example at a time:
asyncio.run(run_crypto_ws())
# asyncio.run(run_forex_ws())
```
## Configuration
By default, the client loads endpoint configuration from ```fmpstab_endpoints.json``` located in the same directory as ```fmpstab_client.py```. To use a custom configuration file:
```python
client = FMPStab(api_key="YOUR_API_KEY", config_file="path/to/your_config.json")
```
If you update the configuration file during runtime, force a reload with:
```python
client.config_manager.reload()
```
## Logging
Logging is enabled by default and creates a log file (```fmpstab.log```) in the directory where your main script is located. To disable logging:
```python
client = FMP(api_key="YOUR_API_KEY", log_enabled=False)
```
## Contributing
Contributions, bug reports, and feature requests are welcome. Please open an issue or submit a pull request.

## License
This project is licensed under the MIT License. See the FIXME [```LICENSE.md```](https://github.com/Vimal-Seshadri-Raguraman/FMP/blob/main/LICENSE) file for details.
