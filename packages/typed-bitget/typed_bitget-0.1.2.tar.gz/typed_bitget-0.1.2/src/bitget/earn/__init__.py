from bitget.core import AuthRouter
from .account import Account
from .savings import Savings


class Earn(AuthRouter):
  account: Account
  savings: Savings