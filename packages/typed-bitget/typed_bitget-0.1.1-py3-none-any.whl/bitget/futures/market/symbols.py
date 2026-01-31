from typing_extensions import Literal
from dataclasses import dataclass

from bitget.core import Endpoint, validator, TypedDict

class Symbol(TypedDict):
  symbol: str
  """Product name, e.g. 'BTCUSDT'"""
  baseCoin: str
  """Base currency, e.g. 'BTC' in 'BTCUSDT'"""
  quoteCoin: str
  """Quote currency, e.g. 'USDT' in 'BTCUSDT'"""
  buyLimitPriceRatio: str
  """Ratio of bid price to limit price"""
  sellLimitPriceRatio: str
  """Ratio of ask price to limit price"""
  feeRateUpRatio: str
  """Transaction fee increase ratio"""
  makerFeeRate: str
  """Maker rate"""
  takerFeeRate: str
  """Taker rate"""
  openCostUpRatio: str
  """Opening cost increase ratio"""
  supportMarginCoins: list[str]
  """Supported margin coins"""
  minTradeNum: str
  """Minimum opening amount (base currency)"""
  priceEndStep: str
  """Price step length"""
  volumePlace: str
  """Decimal places of the quantity"""
  pricePlace: str
  """Decimal places of the price"""
  sizeMultiplier: str
  """Quantity multiplier, must be multiple of this and > minTradeNum"""
  symbolType: str
  """Futures types: perpetual; delivery"""
  minTradeUSDT: str
  """Minimum USDT transaction amount"""
  maxSymbolOrderNum: str
  """Maximum number of orders held - symbol dimension"""
  maxProductOrderNum: str
  """Maximum number of held orders - product type dimension"""
  maxPositionNum: str
  """Maximum number of positions held"""
  symbolStatus: str
  """Trading pair status: 'listed', 'normal', 'maintain', 'limit_open', 'restrictedAPI', 'off'"""
  offTime: str
  """Removal time, '-1' means normal"""
  limitOpenTime: str
  """Time to open positions, '-1' means normal; otherwise, under (upcoming) maintenance"""
  deliveryTime: str
  """Delivery time"""
  deliveryStartTime: str
  """Delivery start time"""
  deliveryPeriod: str
  """Delivery period, e.g. 'this_quarter', 'next_quarter'"""
  launchTime: str
  """Listing time"""
  fundInterval: str
  """Funding fee settlement cycle [hours]"""
  minLever: str
  """Minimum leverage"""
  maxLever: str
  """Maximum leverage"""
  posLimit: str
  """Position limits"""
  maintainTime: str
  """Maintenance time (usually absent unless under/upcoming maintenance)"""
  maxMarketOrderQty: str
  """Maximum order qty for single market order"""
  maxOrderQty: str
  """Maximum order qty for single limit order"""
  isRwa: Literal['YES', 'NO']
  """Is this an RWA Symbol 'YES' or 'NO'"""
  openTime: str
  """This field has been deprecated"""

validate_response = validator(list[Symbol])

@dataclass
class Symbols(Endpoint):
  async def symbols(
    self, product_type: Literal['USDT-FUTURES', 'COIN-FUTURES', 'USDC-FUTURES'],
    *,
    symbol: str | None = None,
    validate: bool | None = None
  ):
    """Get futures contract configuration information.

    - `productType`: Product type: "USDT-FUTURES", "COIN-FUTURES", or "USDC-FUTURES". (Required)
    - `symbol`: Trading pair name (e.g. BTCUSDT), optional.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    https://www.bitget.com/api-doc/contract/market/Get-All-Symbols-Contracts
    """
    params = {'productType': product_type}
    if symbol is not None:
      params['symbol'] = symbol
    r = await self.request('GET', '/api/v2/mix/market/contracts', params=params)
    return self.output(r.text, validate_response, validate=validate)

  async def all_symbols(self, *, validate: bool | None = None) -> list[Symbol]:
    """Get futures contract configuration information for all product types.

    - `validate`: Whether to validate the response against the expected schema (default: True).

    https://www.bitget.com/api-doc/contract/market/Get-All-Symbols-Contracts
    """
    symbols: list[Symbol] = []
    for product_type in ('USDT-FUTURES', 'COIN-FUTURES', 'USDC-FUTURES'):
      symbols.extend(await self.symbols(product_type, validate=validate))
    return symbols

  async def symbol(
    self, 
    product_type: Literal['USDT-FUTURES', 'COIN-FUTURES', 'USDC-FUTURES'],
    symbol: str,
    *,
    validate: bool | None = None
  ):
    """Get contract info for one symbol.

    - `productType`: Product type: "USDT-FUTURES", "COIN-FUTURES", or "USDC-FUTURES". (Required)
    - `symbol`: Trading pair name (e.g. BTCUSDT)
    - `validate`: Whether to validate the response against the expected schema (default: True).

    https://www.bitget.com/api-doc/contract/market/Get-All-Symbols-Contracts
    """
    data = await self.symbols(product_type, symbol=symbol, validate=validate)
    if len(data) == 0:
      raise ValueError(f"Symbol not found: {symbol}")
    return data[0]