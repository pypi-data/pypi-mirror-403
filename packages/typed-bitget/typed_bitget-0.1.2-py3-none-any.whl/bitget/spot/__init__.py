from bitget.core import AuthRouter
from .account import Account
from .market import Market
from .trade import Trade

class Spot(AuthRouter):
  account: Account
  market: Market
  trade: Trade