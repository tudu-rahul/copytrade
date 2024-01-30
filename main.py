from index import Index
from login import Login
from spread import Spread
from trading_symbols import TradingSymbols
from typing import Optional, Dict, List
from execute import Execute
from account import Account
from time import sleep
import os


if __name__ == '__main__':
    """
    Sample commands:
        entry:
            ENTRY MIDCPNIFTY 10525CE 29JAN24
        exit:
            EXIT MIDCPNIFTY 10525CE 29JAN24
        details:
            DETAILS
        p&l:
            PNL
    """
    accounts, defaulters, my_account_id = Login.read_credentials_and_login()
    if my_account_id is None:
        exit(1)
    TradingSymbols.initialize()
    total_balance: float = 0.0
    my_account: Optional[Account] = None
    for account in accounts:
        if account.account_id == my_account_id:
            my_account = account
        total_balance += account.balance
        print(str(account.account_name) + " successfully logged in")
        print("Balance: Rs " + str(account.balance) + "\n")
    print("\n")
    print("Total balance: Rs " + str(total_balance))
    print("Defaulters: " + str(defaulters))
    print("Total valid clients: " + str(len(accounts)))
    print("------------------------------------------------------------\n")
    while True:
        print("Command: ")
        command: str = input()
        command = command.strip()
        command_type: str = command.split(' ')[0]
        if command_type == "ENTRY":
            parts: List[str] = command.split(' ')
            index: str = parts[1].strip()
            strike: str = parts[2].strip()
            index_details: Dict = Index.get_details(index=index)
            if index_details == {}:
                print("Index is wrong or not provided")
                print("\n")
                continue
            expiry: str = parts[3].strip()
            spread: Spread = Spread()
            spread.create_spread(command=index + " " + strike, expiry=expiry)
            if spread.buying_order is None or spread.selling_order is None:
                print("Wrong trade command\n")
                continue
            print("\n")
            print("Entry spread details")
            print("Buying symbol: " + str(spread.buying_order.symbol))
            print("Selling symbol: " + str(spread.selling_order.symbol))
            margin_per_lot: float = spread.get_margin_per_lot(smartapi=my_account.smartapi)
            print("Margin per lot: Rs " + str(margin_per_lot))
            print("\n")
            freeze_quantity: int = index_details["freeze_quantity"]
            for account in accounts:
                account.create_list_of_orders(spread=spread, freeze_quantity=freeze_quantity)
            # Execute.place_order(accounts=accounts)
        elif command_type == "EXIT":
            parts: List[str] = command.split(' ')
            index: str = parts[1].strip()
            strike: str = parts[2].strip()
            index_details: Dict = Index.get_details(index=index)
            if index_details == {}:
                print("Index is wrong or not provided\n")
                continue
            expiry: str = parts[3].strip()
            spread: Spread = Spread()
            spread.create_spread(command=index + " " + strike, expiry=expiry)
            spread.reverse()
            if spread.buying_order is None or spread.selling_order is None:
                print("Wrong trade command")
                continue
            print("\n")
            print("Exit spread details")
            print("Selling symbol: " + str(spread.selling_order.symbol))
            print("Buying symbol: " + str(spread.buying_order.symbol))
            print("\n")
            freeze_quantity: int = index_details["freeze_quantity"]
            for account in accounts:
                result: Dict = account.get_total_number_of_spreads_and_symbols()
                if result is None:
                    continue
                if (result["buying_symbol"] != spread.selling_order.symbol
                        or result["selling_symbol"] != spread.buying_order.symbol):
                    print("Exit order mismatch with entry order for " + str(account.account_id))
                    continue
                account.create_list_of_orders(spread=spread,
                                              freeze_quantity=freeze_quantity,
                                              total_number_of_spreads=result["total_number_of_spreads"])
            # Execute.place_order(accounts=accounts)
        elif command_type == "DETAILS":
            my_account_position: List[Dict] = my_account.get_current_positions()
            sleep(1)
            verification_data: Dict[str, Dict] = {}
            for position in my_account_position:
                verification_data[position["strike"]] = position
            while True:
                incomplete_trades: int = 0
                position_string: str = ""
                position_string_list: List[str] = []
                for account in accounts:
                    position_string = ""
                    position_detail: List[Dict] = account.get_current_positions(verification_data=verification_data)
                    if len(position_detail) == 0:
                        incomplete_trades += 1
                        continue
                    for position in position_detail:
                        quantity_type: str = "BUY"
                        if int(position["quantity"]) < 0:
                            quantity_type = "SELL"
                        position_string = position_string + (account.account_id + "\t\t" + position["symbol_name"]
                                        + "\t\t" + position["strike"] + "\t\t" + quantity_type + "\t\t"
                                        + position["quantity"]) + "\n"
                    position_string_list.append(position_string)
                os.system("clear")
                print("Incomplete trades: " + str(incomplete_trades))
                print("\n")
                for position_string in position_string_list:
                    print(position_string)
                sleep(1)
        elif command_type == "PNL":
            sleep(1)
            while True:
                total_realised: float = 0.0
                total_unrealised: float = 0.0
                total_pnl: float = 0.0
                pnl_string: str = ""
                pnl_string_list: List[str] = []
                for account in accounts:
                    realised, unrealised, pnl = account.get_pnl()
                    total_realised += realised
                    total_unrealised += unrealised
                    total_pnl += pnl
                    pnl_string = (account.account_id + "\t\t\t" + str(realised) + "\t\t\t" + str(unrealised)
                                  + "\t\t\t" + str(pnl) + "\n")
                    pnl_string_list.append(pnl_string)
                os.system("clear")
                print("Total realised: Rs " + str(total_realised))
                print("Total unrealised: Rs " + str(total_unrealised))
                print("Total p&l: Rs " + str(total_pnl))
                print("\n")
                for pnl_string in pnl_string_list:
                    print(pnl_string)
                sleep(1)
        else:
            print("Wrong command\n")
