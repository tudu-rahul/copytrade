from account import Account
from typing import List, Dict
# from SmartApi import SmartConnect
import threading
from order import Order
from time import sleep
from index import Index


def trade_exit_all(accounts: List[Account] = None) -> None:
    """
    Exits all existing open positions

    Parameters
    ----------
    accounts: List[Account], default=None
        List of all trading accounts
    """
    all_threads: List[threading.Thread] = []
    for account in accounts:
        thread: threading.Thread = threading.Thread(target=exit_current_of_a_single_account,
                                                    kwargs={"account": account},
                                                    name="")
        all_threads.append(thread)
    for thread in all_threads:
        thread.daemon = False
        thread.start()
    for thread in all_threads:
        thread.join()


def exit_current_of_a_single_account(account: Account = None) -> None:
    positions_details: List[Dict] = account.get_current_positions()
    # smartapi: SmartConnect = account.smartapi
    for position in positions_details:
        # if position is closed and position["quantity"] > 0
        if True:
            quantity: int = int(position["quantity"])
            index: str = ""
            index_details: Dict = Index.get_details(index=index)
            freeze_quantity: int = index_details["freeze_quantity"]
            symbol: str = ""
            token: str = ""
            tradetype: str = ""
            while quantity > 0:
                _: Order = Order(quantity=min(freeze_quantity, quantity),
                                 symbol=symbol,
                                 token=token,
                                 tradetype=tradetype)
                # smartapi.placeOrderFullResponse(order)
                quantity = quantity - freeze_quantity
                sleep(1)
