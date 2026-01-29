# Pumpfun API Wrapper

Python wrapper for [pumpfun-scraper-api](https://rapidapi.com/domainfinderapi/api/pumpfun-scraper-api)

[![PyPI Downloads](https://static.pepy.tech/badge/pypumpfun)](https://pepy.tech/projects/pypumpfun)

## Installation

```bash
pip install pypumpfun
```

## API Key Required

⚠️ **Important:** This module requires an API key to perform requests. Get your API key from [RapidAPI - Pumpfun Scraper API](https://rapidapi.com/domainfinderapi/api/pumpfun-scraper-api)

## Quick Start

```python
from pypumpfun import Pumpfun

# Initialize with your API key
api = Pumpfun("YOUR_API_KEY")

# Search for tokens
results = api.search_tokens(term="your_search_term")
print(results)

# Get recommended tokens
tokens = api.tokens_for_you(limit=50, offset=0, include_nsfw=False)
print(tokens)
```


## Available Methods

- `ping()`: Check API health
- `search_tokens(term)`: Search tokens by term
- `tokens_for_you(limit=50, offset=0, include_nsfw=False)`: Get recommended tokens
- `similar_projects_by_mint(address, limit=50)`: Find similar projects
- `get_featured_coins()`: Get featured coins
- `get_about_graduates()`: Get graduates information
- `get_runner_tokens()`: Get runner tokens
- `get_tokens_by_meta(meta, include_nsfw=False)`: Search by metadata
- `get_token_metadata_trades(address)`: Get token metadata and trades (legacy)
- `get_pumpfun_replies(address, limit=1000, offset=0)`: Get replies
- `get_candlesticks(address, created_ts=None, limit=60, interval="1m")`: Get candlestick data
- `get_king_hell(include_nsfw=False)`: Get King Hell information
- `global_params()`: Get global parameters
- `get_latest_token()`: Get latest token information
- `get_user_created_coins(address, offset=0, limit=10, include_nsfw=False)`: Get coins created by a user
- `get_user_followings(address)`: Get addresses followed by a user
- `get_user_followers(address)`: Get followers of a user
- `get_user_holdings(address, limit=50, offset=0)`: Get holdings of a user
- `get_token_basic_metadata(address)`: Get basic metadata and trades for a token
- `get_current_token_livestreams(sort_order="DESC", offset=0, limit=48, include_nsfw=False)`: Get current token livestreams
- `get_latest_trade()`: Get the latest trade
- `get_graduated_tokens(sort_by="marketCap")`: Get graduated tokens
- `get_token_trades(address, limit=100, cursor=0, min_sol_amount=0.0, program="pump", created_ts=None)`: Get trades for a token
- `get_sol_price()`: Get current SOL price
- `get_current_metas()`: Get current metas

## Example: New Endpoints

```python
# Get user created coins
user_coins = api.get_user_created_coins(address="SOME_ADDRESS", limit=5)
print(user_coins)

# Get user followings
followings = api.get_user_followings(address="SOME_ADDRESS")
print(followings)

# Get token basic metadata
meta = api.get_token_basic_metadata(address="SOME_TOKEN_ADDRESS")
print(meta)

# Get token trades
trades = api.get_token_trades(address="SOME_TOKEN_ADDRESS", limit=10)
print(trades)
```

## Error Handling

The module includes built-in error handling and will return appropriate error messages if:
- API key is invalid
- API request fails
- Response parsing fails

## Rate Limits

Please be aware of the rate limits associated with your API key tier on RapidAPI.

## Support

For API access and pricing, visit [RapidAPI - Pumpfun Scraper API](https://rapidapi.com/domainfinderapi/api/pumpfun-scraper-api)

For package issues, contact: [contact@tomris.dev](mailto:contact@tomris.dev)
