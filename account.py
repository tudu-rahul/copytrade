from spread import Spread
from order import Order
from copy import deepcopy
from SmartApi import SmartConnect
from typing import Optional, Dict, List
import logging
from time import sleep
import sys

log = logging.getLogger()


class Account:
    """
    Class to represent any trading account

    ...

    Attributes
    ----------
    orders: Optional[List[Order, Order]], default: None
        List of orders to be executed
    account_id: str
        Account ID of the current account
    account_name: str
        Name of the owner of the account
    balance: float
        Current available balance of the account which can be used in trading
    realised_profit: float
        Current realised profit
    unrealised_profit: float
        Current unrealised profit
    smartapi: SmartConnect
        Smartapi object
    refresh_token: str
        Refresh token generated by smartapi

    Methods
    -------
    create_list_of_orders(self, spread: Spread = None, freeze_quantity: int = None,
                          total_number_of_spreads: Optional[int] = None) -> None:
        Creates list of orders to be executed in an account
    get_current_positions(self, verification_data: Dict[str, Dict] = None) -> List[Dict]:
        Gets current open position of an account and if necessary will verify against an expected set of positions
    get_pnl(self) -> (float, float, float):
        Gets current P&L data if an account
    get_total_number_of_spreads_and_symbols(self) -> Optional[Dict]:
        Gets total number of spreads and synbols that are currently in an open position
    """

    def __init__(self, account_id: str = None, account_name: str = None, balance: float = None,
                 realised_profit: float = None, unrealised_profit: float = None, smartapi: SmartConnect = None,
                 refresh_token: str = None):
        self.orders: Optional[List[Order, Order]] = None
        self.account_id: str = account_id
        self.account_name: str = account_name
        self.balance: float = balance
        self.realised_profit: float = realised_profit
        self.unrealised_profit: float = unrealised_profit
        self.smartapi: SmartConnect = smartapi
        self.refresh_token: str = refresh_token

    def create_list_of_orders(self, spread: Spread = None, freeze_quantity: int = None,
                              total_number_of_spreads: Optional[int] = None) -> None:
        """
        Creates list of orders to be executed in an account

        If total number of spreads is not defined, then based on margin required total number of spreads will be
        calculated. Based on the freeze quantity and total number of spreads possible order blocks will be created.

        Parameters
        ----------
        spread : Spread, default: None
            Spread which will be executed
        freeze_quantity : int, default: None
            Freeze quantity for the current index
        total_number_of_spreads : Optional[int], default: None
            Total number of spreads to be exited. In entry this valued will be calculated based on margin required
        """
        if spread is None or freeze_quantity is None:
            return None
        order_list: list[[Order, Order]] = []
        if total_number_of_spreads is None:
            total_number_of_spreads: int = int((self.balance*1.0)/spread.margin_per_lot)
        spreads_per_order: int = freeze_quantity // spread.buying_order.qty
        print("Total number of spreads: " + str(total_number_of_spreads))
        if spread.margin_per_lot is not None:
            print("Total capital used: Rs " + str(total_number_of_spreads * 1.0 * spread.margin_per_lot))
        if total_number_of_spreads > 0:
            while total_number_of_spreads:
                b_order: Order = deepcopy(spread.buying_order)
                s_order: Order = deepcopy(spread.selling_order)
                if total_number_of_spreads >= spreads_per_order:
                    b_order.qty = freeze_quantity
                    b_order.quantity = str(b_order.qty)
                    s_order.qty = freeze_quantity
                    s_order.quantity = str(s_order.qty)
                    total_number_of_spreads = total_number_of_spreads - spreads_per_order
                else:
                    b_order.qty = int(spread.buying_order.qty * total_number_of_spreads)
                    b_order.quantity = str(b_order.qty)
                    s_order.qty = int(spread.selling_order.qty * total_number_of_spreads)
                    s_order.quantity = str(s_order.qty)
                    total_number_of_spreads = 0
                order_list.append([b_order, s_order])
        self.orders = order_list

    def get_current_positions(self, verification_data: Dict[str, Dict] = None) -> List[Dict]:
        """
        Gets current open position of an account and if necessary will verify against an expected set of positions

        This will fetch current positions of all trading accounts and verify against a verification data. This is done
        to ensure all trading accounts have the same orders open, and if any account has mismatch that will be notified
        early. If all goes good, then current positions will be returned.

        Parameters
        ----------
        verification_data : Dict[str, Dict], default: None
            The source of truth against which all account's orders will be verified

        Returns
        -------
        List[Dict]:
            [{ "symbol_name": str,  "strike": str, "quantity": str }
        """
        smartapi: SmartConnect = self.smartapi
        position_exception_present: bool = False
        while True:
            try:
                position = smartapi.position()["data"]
                if position_exception_present:
                    print("Position exception in details solved.\n")
                    position_exception_present = False
                break
            except Exception as exp:
                log.exception("Position exception in details: " + str(exp))
                if position_exception_present:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                position_exception_present = True
                print("Position exception in details occurring.")
                sleep(1)
        if position is None:
            return []
        strike_check: int = 0
        if verification_data is not None:
            strike_check: int = len(verification_data)
        details: List[Dict] = []
        total_quantity: int = 0
        for single_position in position:
            symbol_name: str = single_position["symbolname"]
            strike: str = str(int(float(single_position["strikeprice"]))) + " " + single_position["optiontype"]
            quantity: int = int(single_position["netqty"])
            if verification_data is not None:
                verification_strike_data = verification_data[strike]
                if (verification_strike_data["symbol_name"] == symbol_name and
                        int(verification_strike_data["quantity"]) / abs(int(verification_strike_data["quantity"]))
                        == quantity / abs(quantity)):
                    total_quantity = total_quantity + quantity
                    strike_check = strike_check - 1
            details.append({"symbol_name": str(symbol_name),
                            "strike": str(strike),
                            "quantity": str(quantity)})
        if strike_check != 0 or total_quantity != 0:
            details = []
        details = sorted(details, key=lambda d: d["quantity"], reverse=True)

        return details

    def get_pnl(self) -> (float, float, float):
        """
        Gets current P&L data if an account

        Current P&L consists of three parts: realised, unrealised and overall. These three parts will help track the
        current scenario as well as profit/loss booked after exiting positions

        Returns
        -------
        float, float, float:
            Realised, unrealised, overall p&l
        """
        smartapi: SmartConnect = self.smartapi
        position_exception_present: bool = False
        while True:
            try:
                position = smartapi.position()["data"]
                if position_exception_present:
                    print("Position exception in pnl solved.\n")
                    position_exception_present = False
                break
            except Exception as exp:
                log.exception("Position exception in pnl: " + str(exp))
                if position_exception_present:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                position_exception_present = True
                print("Position exception in pnl occurring.")
                sleep(1)
        if position is None:
            return 0.0, 0.0, 0.0
        realised: float = 0.0
        unrealised: float = 0.0
        for single_position in position:
            realised = realised + float(single_position["realised"])
            unrealised = unrealised + float(single_position["unrealised"])

        return realised, unrealised, realised + unrealised

    def get_total_number_of_spreads_and_symbols(self) -> Optional[Dict]:
        """
        Gets total number of spreads and synbols that are currently in an open position

        After fetching position details for an account, based on the sign of quantity, buying and selling strikes are
        found. At the same time it is also verified if quantities in all strikes are same or not, just to be safe
        while exiting the position.

        Returns
        -------
        Optional[Dict]:
            { "buying_symbol": str, "selling_symbol": str, "total_number_of_spreads": int }
        """
        smartapi: SmartConnect = self.smartapi
        position_exception_present: bool = False
        while True:
            try:
                position = smartapi.position()["data"]
                if position_exception_present:
                    print("Position exception in total number of spreads solved.\n")
                    position_exception_present = False
                break
            except Exception as exp:
                log.exception("Position exception in total number of spreads: " + str(exp))
                if position_exception_present:
                    sys.stdout.write("\033[F")
                    sys.stdout.write("\033[K")
                position_exception_present = True
                print("Position exception in total number of spreads occurring.")
                sleep(1)
        if position is None:
            return None
        quantity: int = 0
        buying_symbol: Optional[str] = None
        selling_symbol: Optional[str] = None
        lotsize: Optional[int] = None
        for single_position in position:
            if int(single_position["netqty"]) == 0:
                continue
            if quantity == 0:
                quantity = int(single_position["netqty"])
                temp_quantity = quantity
            else:
                temp_quantity = int(single_position["netqty"])
                if abs(temp_quantity) != abs(quantity):
                    print("Mismatching quantity")
                    return None
            lotsize = int(single_position["lotsize"])
            trading_symbol: str = single_position["tradingsymbol"]
            if temp_quantity < 0:
                selling_symbol = trading_symbol
            else:
                buying_symbol = trading_symbol
        result: Dict = {"buying_symbol": buying_symbol,
                        "selling_symbol": selling_symbol,
                        "total_number_of_spreads": abs(quantity) // abs(lotsize)}
        return result
