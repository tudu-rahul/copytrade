from trading_symbols import TradingSymbols
from index import Index
from order import Order
from typing import Dict, Optional
from SmartApi import SmartConnect


class Spread:
    """
    Class to represent a spread

    ...

    Attributes
    ----------
    buying_order: Optional[Order]
        Buying leg of the spread
    selling_order: Optional[Order]
        Selling leg of the spread
    margin_per_lot: Optional[float]
        Margin required to place one lot of spread

    Methods
    -------
    create_spread(self, command: str = None, expiry: str = None) -> None:
        Creates a new spread
    prepare_order(self, buying_symbol: str = None, buying_token: str = None, selling_symbol: str = None,
                  selling_token: str = None, quantity_per_lot: int = None) -> None:
        Prepares the orders to be placed as a part of the spread
    get_buying_symbol_and_token(index: str = None, expiry: str = None, selling_strike: str = None,
                                option_type: str = None, spreadwidth: int = None) -> (Optional[str], Optional[str]):
        Gets the buying symbol and buying token for the buying leg of the spread
    get_margin_per_lot(self, smartapi: SmartConnect = None) -> Optional[float]:
        Gets the margin required to place one lot of the spread
    reverse(self) -> None:
        Swaps the buying leg and the selling leg of the spread
    """

    def __init__(self):
        self.buying_order: Optional[Order] = None
        self.selling_order: Optional[Order] = None
        self.margin_per_lot: Optional[float] = None

    def create_spread(self, command: str = None, expiry: str = None) -> None:
        """
        Creates a new spread

        Details of index is fetched first and based on that buying and selling strike details are found. Once
        individual leg's details are generated, these details are sent to prepare a single spread.

        Parameters
        ----------
        command: str, default: None
            Command to create a spread
        expiry: str, default: None
            Expiry date of the spread
        """
        if command is None or expiry is None:
            print("Either command or expiry is None\n")
            return None
        index: str = command.split(' ')[0].strip()
        index_details: Dict = Index.get_details(index=index)
        if index_details == {}:
            print("Index details is empty\n")
            return None
        selling_strike: str = command.split(' ')[1].strip()
        option_type: str = selling_strike[-2:].upper()
        selling_strike: str = selling_strike[:-2]
        selling_symbol: str = index + expiry + selling_strike + option_type
        selling_token: str = TradingSymbols.get_token(symbol=selling_symbol)
        buying_symbol, buying_token = Spread.get_buying_symbol_and_token(index=index,
                                                                         expiry=expiry,
                                                                         selling_strike=selling_strike,
                                                                         option_type=option_type,
                                                                         spreadwidth=index_details["spreadwidth"])
        if buying_symbol is None or buying_token is None:
            print("Either buying symbol or buying token is None\n")
            return None
        self.prepare_order(buying_symbol=buying_symbol, buying_token=buying_token,
                           selling_symbol=selling_symbol, selling_token=selling_token,
                           quantity_per_lot=index_details["quantity_per_lot"])

        return None

    def prepare_order(self, buying_symbol: str = None, buying_token: str = None, selling_symbol: str = None,
                      selling_token: str = None, quantity_per_lot: int = None) -> None:
        """
        Prepares the orders to be placed as a part of the spread

        Individual leg details are filled from the data provided

        Parameters
        ----------
        buying_symbol: str, default: None
            Buying symbol of the order
        buying_token: str, default: None
            Buying token of the order
        selling_symbol: str, default: None
            Selling symbol of the order
        selling_token: str, default: None
            Selling token of the order
        quantity_per_lot: int, default: None
            Quantity per lot of the index being traded
        """
        if (buying_symbol is None or buying_token is None
                or selling_symbol is None or selling_token is None
                or quantity_per_lot is None):
            print("Either buying symbol or buying token or selling symbol or selling token or "
                  "quantity per lot is None\n")
            return None
        buying_order: Order = Order(quantity=quantity_per_lot,
                                    symbol=buying_symbol,
                                    token=buying_token,
                                    tradetype="BUY")
        self.buying_order = buying_order
        selling_order: Order = Order(quantity=quantity_per_lot,
                                     symbol=selling_symbol,
                                     token=selling_token,
                                     tradetype="SELL")
        self.selling_order = selling_order

        return None

    @staticmethod
    def get_buying_symbol_and_token(index: str = None, expiry: str = None, selling_strike: str = None,
                                    option_type: str = None, spreadwidth: int = None) -> (Optional[str], Optional[str]):
        """
        Gets the buying symbol and buying token for the buying leg of the spread

        Based on the spreadwidth and selling leg details provided, buying leg details are generated. Buying symbol
        and corresponding buying token is returned.

        Parameters
        ----------
        index: str, default: None
            Index on which trading is done
        expiry: str, default: None
            Expiry date of the current options
        selling_strike: str, default: None
            Selling strike of the spread
        option_type: str, default: None
            Option type of the selling strike
        spreadwidth: int, default: None
            Spreadwidth between the buying and selling legs
        """
        if index is None or expiry is None or selling_strike is None or option_type is None or spreadwidth is None:
            return None, None
        buying_symbol: Optional[str] = None
        if option_type == "CE":
            buying_strike: str = str(int(selling_strike) + spreadwidth)
            buying_symbol = index + expiry + buying_strike + option_type
        if option_type == "PE":
            buying_strike: str = str(int(selling_strike) - spreadwidth)
            buying_symbol = index + expiry + buying_strike + option_type
        buying_token: Optional[str] = TradingSymbols.get_token(symbol=buying_symbol)

        return buying_symbol, buying_token

    def get_margin_per_lot(self, smartapi: SmartConnect = None) -> Optional[float]:
        """
        Gets the margin required to place one lot of the spread

        Parameters
        ----------
        smartapi: SmartConnect, default: None
            SmartConnect object to connect to Angel One

        Returns
        -------
        Optional[float]:
            Margin required to place one lot of spread
        """
        if smartapi is None:
            return None
        params: Dict = {"positions": []}
        params["positions"].append(self.buying_order.__dict__)
        params["positions"].append(self.selling_order.__dict__)
        data: Dict = smartapi.getMarginApi(params=params)["data"]
        if data is None:
            return None
        margin_per_lot: float = float(data["totalMarginRequired"])
        self.margin_per_lot = margin_per_lot

        return margin_per_lot

    def reverse(self) -> None:
        """
        Swaps the buying leg and the selling leg of the spread

        This is done while exiting any spread. Swapping the legs will allow to place the opposite orders that were
        placed during entry.
        """
        temp_order: Order = self.selling_order
        self.selling_order = self.buying_order
        self.selling_order.transactiontype = "SELL"
        self.selling_order.tradeType = "SELL"
        self.buying_order = temp_order
        self.buying_order.transactiontype = "BUY"
        self.buying_order.tradeType = "BUY"

        return None
