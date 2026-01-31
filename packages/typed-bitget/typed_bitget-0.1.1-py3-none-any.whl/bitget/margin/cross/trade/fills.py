from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp, timestamp as ts, rate_limit

class FeeDetail(TypedDict):
  deduction: Literal['yes', 'no']
  """Discount or not"""
  feeCoin: str
  """Coin for transaction fee"""
  totalDeductionFee: Decimal
  """Total discounted transaction fee"""
  totalFee: Decimal
  """Total transaction fee"""

class Fill(TypedDict):
  orderId: str
  """Order no."""
  tradeId: str
  """Transaction detail ID"""
  orderType: Literal['limit', 'market']
  """Order type: limit: limit price, market: market price"""
  side: Literal['sell', 'buy', 'liquidation_buy', 'liquidation_sell', 'system_repay_buy', 'system_repay_sell']
  """Direction: sell: Sell, buy: Buy, liquidation_buy: Settlement – buy, liquidation_sell: Settlement – sell, system_repay_buy: Repay by system – buy, system_repay_sell: Repay by system – sell"""
  priceAvg: Decimal
  """Order price"""
  size: Decimal
  """Filled quantity"""
  amount: Decimal
  """Filled quantity"""
  tradeScope: Literal['taker', 'maker']
  """Trader tag: taker: Taker, maker: Maker"""
  cTime: Timestamp
  """Creation time, millisecond timestamp"""
  uTime: Timestamp
  """Update time, millisecond timestamp"""
  feeDetail: FeeDetail
  """Transaction fee details"""

class Response(TypedDict):
  fills: list[Fill]
  maxId: str | None
  minId: str | None

validate_response = validator(Response)

@dataclass
class Fills(AuthEndpoint):
  @rate_limit(timedelta(seconds=0.1))
  async def fills(
    self, symbol: str,
    *,
    start: datetime, end: datetime | None = None,
    order_id: str | None = None,
    id_less_than: str | None = None,
    limit: int | None = None,
    validate: bool | None = None
  ):
    """Get Cross Order Fills
    
    - `symbol`: Trading pairs, like BTCUSDT
    - `start`: Start time, Unix millisecond timestamp
    - `end`: End time, Unix millisecond timestamp. Maximum interval between start time and end time is 90 days
    - `order_id`: Order ID
    - `id_less_than`: Match order ID, relative parameters of turning pages. The first query is not passed. When querying data in the second page and the data beyond, the last fillId returned in the last query is used, and the result will return data with a value less than this one; the query response time will be shortened.
    - `limit`: Number of queries. Default: 100, maximum: 500
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/margin/cross/trade/Get-Cross-Order-Fills)
    """
    params = {}
    params['symbol'] = symbol
    params['startTime'] = ts.dump(start)
    
    if order_id is not None:
      params['orderId'] = order_id
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    if end is not None:
      params['endTime'] = ts.dump(end)
    if limit is not None:
      params['limit'] = limit
      
    r = await self.authed_request('GET', '/api/v2/margin/crossed/fills', params=params)
    return self.output(r.text, validate_response, validate=validate)


  async def fills_paged(
    self, symbol: str,
    *,
    start: datetime, end: datetime | None = None,
    limit: int | None = None,
    validate: bool | None = None
  ):
    """Get Cross Order Fills, automatically paginated.
    
    - `symbol`: Trading pairs, like BTCUSDT
    - `start`: Start time, Unix millisecond timestamp
    - `end`: End time, Unix millisecond timestamp. Maximum interval between start time and end time is 90 days
    - `order_id`: Order ID
    - `id_less_than`: Match order ID, relative parameters of turning pages. The first query is not passed. When querying data in the second page and the data beyond, the last fillId returned in the last query is used, and the result will return data with a value less than this one; the query response time will be shortened.
    - `limit`: Number of queries. Default: 100, maximum: 500
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/margin/cross/trade/Get-Cross-Order-Fills)
    """
    last_id: str | None = None
    while True:
      r = await self.fills(symbol=symbol, start=start, end=end, limit=limit, validate=validate, id_less_than=last_id)
      chunk = r['fills']
      if chunk and (last_id := r.get('minId')) is not None:
        yield chunk
      else:
        break