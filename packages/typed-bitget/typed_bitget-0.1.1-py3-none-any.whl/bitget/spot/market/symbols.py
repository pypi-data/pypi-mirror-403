from typing_extensions import Literal
from dataclasses import dataclass
from decimal import Decimal

from bitget.core import Endpoint, validator, TypedDict, Timestamp

class Symbol(TypedDict):
  symbol: str
  """Trading pair"""
  baseCoin: str
  """Base currency, e.g. 'BTC' in the pair 'BTCUSDT'"""
  quoteCoin: str
  """Quoting currency, e.g. 'USDT' in the trading pair 'BTCUSDT'"""
  minTradeAmount: str
  """Minimum order amount (obsolete, please refer to minTradeUSDT)"""
  maxTradeAmount: str
  """Maximum order amount (obsolete, generally unlimited)"""
  takerFeeRate: str
  """Default taker transaction fee, can be overridden by individual transaction fee"""
  makerFeeRate: str
  """Default maker transaction fee, can be overridden by individual transaction fee"""
  pricePrecision: str
  """Pricing precision"""
  quantityPrecision: str
  """Amount precision"""
  quotePrecision: str
  """Quote coin precision"""
  minTradeUSDT: str
  """Minimum trading volume (USDT)"""
  status: str
  """Symbol status: 'offline', 'gray', 'online', 'halt'"""
  buyLimitPriceRatio: str
  """Percentage spread between bid and ask, in decimal form. Eg. 0.05 means 5%"""
  sellLimitPriceRatio: str
  """Percentage spread between sell and current price, in decimal form. Eg. 0.05 means 5%"""
  orderQuantity: str
  """The maximum number of orders allowed for the current symbol"""
  areaSymbol: str
  """Area symbol: 'yes', 'no'"""
  offTime: str
  """Symbol off time, e.g: 1744797600000"""
  openTime: str
  """This field has been deprecated"""

validate_response = validator(list[Symbol])

@dataclass
class Symbols(Endpoint):
  async def symbols(
    self, *,
    symbol: str | None = None,
    validate: bool | None = None
  ):
    """Get spot trading pair information.

    - `symbol`: Trading pair name, e.g. BTCUSDT. Leave blank to get all pairs.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/spot/market/Get-Symbols)
    """
    params = {}
    if symbol is not None:
      params['symbol'] = symbol
    r = await self.request('GET', '/api/v2/spot/public/symbols', params=params)
    return self.output(r.text, validate_response, validate=validate)

  
  async def symbol(self, symbol: str, *, validate: bool | None = None):
    """Get spot trading pair information for a specific symbol.

    - `symbol`: Trading pair name, e.g. BTCUSDT.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/spot/market/Get-Symbols)
    """
    return (await self.symbols(symbol=symbol, validate=validate))[0]