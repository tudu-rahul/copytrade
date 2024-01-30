from typing import List, Optional, Dict
from SmartApi import SmartConnect
from order import Order
from account import Account
import threading


class Execute:
    """
    Manages all tasks related to execution of order.

    ...

    Methods
    -------
    place_order(accounts=None) -> None:
        Places order for all accounts one by one
    place_order_for_one_account(account: Account = None) -> None:
        Places orders for one particular account
    place_spread(b_order: Order = None, s_order: Order = None, account: Account = None) -> bool:
        Places spread order and returns status of placed spread if any
    place_leg(order: Order = None, account: Account = None) -> (str, str):
        Places any leg of any strategy
    revert_order(unique_orderid: str = None, account: Account = None) -> bool:
        Reverts any previous completed order
    """

    def __init__(self):
        pass

    @staticmethod
    def place_order(accounts: List[Account] = None) -> None:
        """
        Places order for all accounts one by one.

        Each account is assigned a single thread for placing order. Further these threads spawn child threads to
        place order for each account.

        Parameters
        ---------
        accounts : List[Account], default: None
            List of accounts where orders have to be placed

        Returns
        -------
        None
        """
        all_threads: List[threading.Thread] = []
        for account in accounts:
            thread: threading.Thread = threading.Thread(target=Execute.place_order_for_one_account,
                                                        kwargs={"account": account},
                                                        name="")
            all_threads.append(thread)
        for thread in all_threads:
            thread.daemon = False
            thread.start()
        for thread in all_threads:
            thread.join()

    @staticmethod
    def place_order_for_one_account(account: Account = None) -> None:
        """
        Places orders for one particular account.

        Each buy-sell pair is assigned a single thread for placing order. Since api limit is 20 per second and each
        pair can have at max 3 orders in a very short span of time, a max of 6 pairs is allowed to be executed in one
        batch of threads.

        Parameters
        ----------
        account : Account, default: None
            Account where order has to be placed

        Returns
        -------
        None
        """
        order_list: Optional[list[[Order, Order]]] = account.orders
        all_threads: List[threading.Thread] = []
        if order_list is None:
            return None
        for order in order_list:
            b_order: Order = order[0]
            s_order: Order = order[1]
            thread: threading.Thread = threading.Thread(target=Execute.place_spread,
                                      kwargs={"b_order": b_order, "s_order": s_order, "account": account},
                                      name="")
            all_threads.append(thread)
        start: int = 0
        end: int = 6
        while True:
            current_batch: List[threading.Thread] = all_threads[start: end]
            for single_thread in current_batch:
                single_thread.daemon = False
                single_thread.start()
            for single_thread in current_batch:
                single_thread.join()
            if start == len(all_threads):
                break
            start = end
            end = min(start + 6, len(all_threads))

        return None

    @staticmethod
    def place_spread(b_order: Order = None, s_order: Order = None, account: Account = None) -> bool:
        """
        Places spread order and returns status of placed spread if any.

        First buying leg is placed. If buying leg is completed, then selling leg is placed, else execution of the
        spread is cancelled. If after a successful execution of buying leg, selling leg gets rejected, then buying leg
        gets reverted.

        Parameters
        ----------
        b_order : Order, default: None
            Buying order
        s_order : Order, default: None
            Selling order
        account : Account, default: None
            Account where spread has to be placed

        Returns
        -------
        bool
        """
        status, unique_orderid = Execute.place_leg(order=b_order, account=account)
        if status == "rejected":
            return False
        if status == "complete":
            status, _ = Execute.place_leg(order=s_order, account=account)
            if status == "rejected":
                Execute.revert_order(unique_orderid=unique_orderid, account=account)
                return False
            if status == "complete":
                return True

    @staticmethod
    def place_leg(order: Order = None, account: Account = None) -> (str, str):
        """
        Places any leg of any strategy.

        After placing order, the order is identified by a unique order-id. This unique order-id is then used to
        fetch status of the order and accordingly retrying continues. At the end the status and the unique order-id is
        returned.

        Parameters
        ----------
        order : Order, default: None
            Order to place
        account : Account, default: None
            Account where order is placed

        Returns
        -------
        str, str:
            Status, unique order-id
        """
        smartapi: SmartConnect = account.smartapi
        order_response: Optional[Dict] = smartapi.placeOrderFullResponse(order.__dict__)["data"]
        unique_orderid: Optional[str] = None
        if order_response:
            unique_orderid = order_response["uniqueorderid"]
        else:
            return "rejected", unique_orderid
        order_status: Optional[Dict] = smartapi.individual_order_details(unique_orderid)["data"]
        if order_status:
            order_status = order_status["orderstatus"]
        else:
            return "rejected", unique_orderid
        while order_status != "complete":
            order_status = smartapi.individual_order_details(unique_orderid)["data"]
            if order_status:
                order_status = order_status["orderstatus"]
            if order_status == "rejected":
                return "rejected", unique_orderid

        return "complete", unique_orderid

    @staticmethod
    def revert_order(unique_orderid: str = None, account: Account = None) -> bool:
        """
        Reverts any previous completed order.

        Revert in a spread will only occur for a buying order which gets completed but in the next iteration the
        corresponding selling order gets rejected. After reverting the status of revert is returned.

        Parameters
        ----------
        unique_orderid: str, default: None
            Unique order-id of the order to revert
        account: Account, default: None
            Account for which order is to be reverted

        Returns
        -------
        bool
        """
        smartapi: SmartConnect = account.smartapi
        order_data: Dict = smartapi.individual_order_details(unique_orderid)["data"]
        if order_data:
            reverting_order: Order = Order(quantity=int(order_data["quantity"]),
                                           symbol=order_data["tradingsymbol"],
                                           token=order_data["symboltoken"],
                                           tradetype="SELL")
            status, unique_orderid = Execute.place_leg(order=reverting_order, account=account)
            if status == "complete":
                return True
            if status == "rejected":
                return False
        else:
            return False
