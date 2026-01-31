from typing_extensions import Literal
from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from bitget.core import AuthEndpoint, validator, TypedDict, rate_limit


class ApyInfo(TypedDict):
  rateLevel: str
  """Rate level"""
  minStepVal: Decimal
  """Ladder minimum amount value"""
  maxStepVal: Decimal
  """Ladder maximum amount value"""
  currentApy: Decimal
  """Current tiered annual interest rate"""


class Product(TypedDict):
  productId: str
  """Product id"""
  coin: str
  """Savings subscription coin"""
  periodType: Literal['flexible', 'fixed']
  """Period type: `flexible` flexible period, `fixed` fixed period"""
  period: str
  """Period (not returned for flexible)"""
  apyType: Literal['single', 'ladder']
  """Interest rate type: `single` single interest rate, `ladder` ladder income"""
  advanceRedeem: str
  """Whether early redemption is allowed: `Yes` allowed, `No` not allowed"""
  settleMethod: str
  """Settlement method: `daily` daily interest and settlement, `maturity` repayment at maturity"""
  apyList: list[ApyInfo]
  """Ladder interest rate information"""
  status: Literal['not_started', 'in_progress', 'paused', 'completed', 'sold_out', 'off_line']
  """Product status"""
  productLevel: Literal['beginner', 'normal', 'vip']
  """Product level"""


validate_response = validator(list[Product])


@dataclass
class Products(AuthEndpoint):
  @rate_limit(timedelta(seconds=0.1))
  async def products(
    self,
    *,
    coin: str | None = None,
    filter: Literal['available', 'held', 'available_and_held', 'all'] | None = None,
    validate: bool | None = None
  ):
    """Savings Product List
    
    - `coin`: Coin, e.g. BTC.
    - `filter`: Filter conditions: `available` available for subscription, `held` held, `available_and_held` available and held, `all` query all including removed.
    - `validate`: Whether to validate the response against the expected schema (default: True).

    > [Bitget API docs](https://www.bitget.com/api-doc/earn/savings/Savings-Products)
    """
    params = {}
    if coin is not None:
      params['coin'] = coin
    if filter is not None:
      params['filter'] = filter
    r = await self.authed_request('GET', '/api/v2/earn/savings/product', params=params)
    return self.output(r.text, validate_response, validate=validate)
