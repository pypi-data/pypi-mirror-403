from bitget.core import AuthRouter
from .account import Account
from .market import Market
from .position import Position
from .trade import Trade

class Futures(AuthRouter):
  account: Account
  market: Market
  position: Position
  trade: Trade