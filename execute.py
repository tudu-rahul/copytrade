from typing import List, Optional, Dict
from SmartApi import SmartConnect
from order import Order
from account import Account
import threading
from time import sleep
import logging
import sys

log = logging.getLogger()


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
        name: str = str(account.account_name)
        name = name[:3] + "*****"
        print("All orders placed for " + name + "\n")

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
            sleep(1)
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
        buying_order_exception_present: bool = False
        while True:
            try:
                order_response: Optional[Dict] = smartapi.placeOrderFullResponse(order.__dict__)["data"]
                if buying_order_exception_present:
                    print("Buying order exception solved.\n")
                    buying_order_exception_present = False
                break
            except Exception as exp:
                log.exception("Buying order exception: " + str(exp))
                if buying_order_exception_present:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                buying_order_exception_present = True
                print("Buying order exception occurring.")
            sleep(1)
        unique_orderid: Optional[str] = None
        if order_response:
            unique_orderid = order_response["uniqueorderid"]
        else:
            return "rejected", unique_orderid
        order_status: Optional[str] = None
        order_detail_exception_present: bool = False
        while order_status != "complete":
            try:
                order_data: Optional[Dict] = smartapi.individual_order_details(unique_orderid)["data"]
                if order_detail_exception_present:
                    print("Order detail exception solved.\n")
                    order_detail_exception_present = False
                if order_data:
                    order_status = order_data["orderstatus"]
                if order_status == "rejected":
                    return "rejected", unique_orderid
            except Exception as exp:
                log.exception("Order detail exception: " + str(exp))
                if order_detail_exception_present:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                order_detail_exception_present = True
                print("Order details exception occurring.")
                order_status = None
                sleep(1)

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
        order_detail_exception_in_revert_present = False
        while True:
            try:
                order_data: Optional[Dict] = smartapi.individual_order_details(unique_orderid)["data"]
                if order_detail_exception_in_revert_present:
                    print("Order detail exception in revert solved.\n")
                    order_detail_exception_in_revert_present = False
                break
            except Exception as exp:
                log.exception("Order detail exception in revert: " + str(exp))
                if order_detail_exception_in_revert_present:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                order_detail_exception_in_revert_present = True
                print("Exception while getting individual order details. " + str(exp) + "\n")
                sleep(1)
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
