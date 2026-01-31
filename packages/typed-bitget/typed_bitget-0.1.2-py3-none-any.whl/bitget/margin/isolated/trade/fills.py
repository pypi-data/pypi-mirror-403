from typing_extensions import Literal
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, Timestamp, timestamp as ts, rate_limit

class FeeDetail(TypedDict):
  deduction: Literal['yes', 'no']
  """Discount or not"""
  feeCoin: str
  """Transaction fee currency"""
  totalDeductionFee: Decimal
  """Total transaction fee discount"""
  totalFee: Decimal
  """Total transaction fee"""

class Fill(TypedDict):
  orderId: str
  """Order no."""
  tradeId: str
  """Order details ID"""
  orderType: Literal['limit', 'market']
  """Order type: limit, market"""
  size: Decimal
  """Filled quantity"""
  priceAvg: Decimal
  """Filled price"""
  amount: Decimal
  """Filled quantity"""
  side: Literal['sell', 'buy']
  """Direction: sell: Sell, buy: Buy"""
  tradeScope: Literal['taker', 'maker']
  """Trader tag: taker, maker"""
  cTime: Timestamp
  """Creation time, millisecond timestamp"""
  uTime: Timestamp
  """Update time, millisecond timestamp"""
  feeDetail: FeeDetail
  """Transaction fee breakdown"""

class Response(TypedDict):
  fills: list[Fill]
  """List"""
  maxId: str | None
  """Max ID of current search result"""
  minId: str | None
  """Min ID of current search result, use: `idLessThan=minId` in the next query"""

validate_response = validator(Response)

@dataclass
class Fills(AuthEndpoint):
  @rate_limit(timedelta(seconds=0.1))
  async def fills(
    self,
    symbol: str,
    *,
    start: datetime,
    end: datetime | None = None,
    order_id: str | None = None,
    id_less_than: str | None = None,
    limit: int | None = None,
    validate: bool | None = None
  ):
    """Get Isolated Order Fills
    
    - `symbol`: Trading pairs, BTCUSDT
    - `start`: Start time, Unix millisecond timestamps
    - `end`: End time, Unix millisecond timestamps. Maximum interval between start and end times is 90 days
    - `order_id`: Order ID
    - `id_less_than`: Match order ID. A parameter for paging. No setting is needed when querying for the first time. Set to to smallest orderId returned from the last query when searching for data in the second page and other paged. Data smaller than the orderId entered will be returned. This is designed to shorten the query response time.
    - `limit`: Number of queries. Default: 100, maximum: 500
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/margin/isolated/trade/Get-Isolated-Transaction-Details)
    """
    params = {}
    params['symbol'] = symbol
    params['startTime'] = ts.dump(start)
    
    if order_id is not None:
      params['orderId'] = order_id
    if end is not None:
      params['endTime'] = ts.dump(end)
    if id_less_than is not None:
      params['idLessThan'] = id_less_than
    if limit is not None:
      params['limit'] = limit
      
    r = await self.authed_request('GET', '/api/v2/margin/isolated/fills', params=params)
    return self.output(r.text, validate_response, validate=validate)

  async def fills_paged(
    self,
    symbol: str,
    *,
    start: datetime,
    end: datetime | None = None,
    limit: int | None = None,
    validate: bool | None = None
  ):
    """Get Isolated Order Fills, automatically paginated.
    
    - `symbol`: Trading pairs, BTCUSDT
    - `start`: Start time, Unix millisecond timestamps
    - `end`: End time, Unix millisecond timestamps. Maximum interval between start and end times is 90 days
    - `limit`: Number of queries. Default: 100, maximum: 500
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/margin/isolated/trade/Get-Isolated-Transaction-Details)
    """
    last_id: str | None = None
    while True:
      r = await self.fills(symbol=symbol, start=start, end=end, limit=limit, validate=validate, id_less_than=last_id)
      chunk = r['fills']
      if chunk and (last_id := r.get('minId')) is not None:
        yield chunk
      else:
        break
