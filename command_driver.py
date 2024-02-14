from index import Index
from spread import Spread
from typing import Optional, Dict, List
from execute import Execute
from account import Account
from time import sleep
import os
import codecs


def driver(command: str = None, accounts: List[Account] = None, my_account: Account = None):
    if command is None or accounts is None or my_account is None:
        print("Missing data")
        print("\n")
        return
    command = command.strip()
    command_type: str = command.split(' ')[0]
    if command_type == "ENTRY":
        parts: List[str] = command.split(' ')
        if len(parts) != 4:
            print("Incomplete command")
            return
        index: str = parts[1].strip()
        strike: str = parts[2].strip()
        index_details: Dict = Index.get_details(index=index)
        if index_details == {}:
            print("Index is wrong or not provided")
            print("\n")
            return
        expiry: str = parts[3].strip()
        exit_command: str = "EXIT" + " " + index + " " + strike + " " + expiry
        spread: Spread = Spread()
        spread.create_spread(command=index + " " + strike, expiry=expiry)
        spread.get_margin_per_lot(smartapi=my_account.smartapi)
        if spread.buying_order is None or spread.selling_order is None:
            print("Wrong trade command\n")
            return
        print("\n")
        print("Entry spread details")
        print("Buying symbol: " + str(spread.buying_order.symbol))
        print("Selling symbol: " + str(spread.selling_order.symbol))
        print("Margin per lot: Rs " + str(spread.margin_per_lot))
        print("\n")
        freeze_quantity: int = index_details["freeze_quantity"]
        for account in accounts:
            print("Account ID: " + str(account.account_id))
            account.create_list_of_orders(spread=spread, freeze_quantity=freeze_quantity)
            print("\n")
        Execute.place_order(accounts=accounts)
        exit_file = codecs.open("exit_file.txt", "w")
        exit_file.write(exit_command)
        exit_file.close()
    elif command_type == "EXIT":
        parts: List[str] = command.split(' ')
        if len(parts) != 4:
            print("Incomplete command\n")
            return
        index: str = parts[1].strip()
        strike: str = parts[2].strip()
        index_details: Dict = Index.get_details(index=index)
        if index_details == {}:
            print("Index is wrong or not provided\n")
            return
        expiry: str = parts[3].strip()
        spread: Spread = Spread()
        spread.create_spread(command=index + " " + strike, expiry=expiry)
        spread.reverse()
        if spread.buying_order is None or spread.selling_order is None:
            print("Wrong trade command")
            return
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
            print("Account ID: " + str(account.account_id))
            account.create_list_of_orders(spread=spread,
                                          freeze_quantity=freeze_quantity,
                                          total_number_of_spreads=result["total_number_of_spreads"])
            print("\n")
        Execute.place_order(accounts=accounts)
        exit_file = codecs.open("exit_file.txt", "w")
        exit_file.write("")
        exit_file.close()
    elif command_type == "AUTOEXIT":
        parts: List[str] = command.split(' ')
        if len(parts) != 3:
            print("Incomplete command")
            return
        sl_string: str = parts[1].strip()
        tgt_string: str = parts[2].strip()
        sl: Optional[float] = float(sl_string.split('=')[1]) if sl_string.split('=')[0] == "SL" else None
        tgt: Optional[float] = float(tgt_string.split('=')[1]) if tgt_string.split('=')[0] == "TGT" else None
        if sl is None or tgt is None:
            print("Wrong command")
            print("\n")
            return
        if tgt < 0:
            print("Wrong SL or target")
            print("\n")
            return
        exit_command: str = ""
        exit_file = codecs.open("exit_file.txt", "r")
        for lin in exit_file:
            exit_command = lin.strip()
        exit_file.close()
        if len(exit_command) == 0:
            print("No exit command specified")
            print("\n")
            return
        while True:
            realised, unrealised, pnl = my_account.get_pnl()
            if unrealised > tgt:
                sleep(1)
                print("Target reached")
                print("\n")
                driver(command=exit_command, accounts=accounts, my_account=my_account)
                break
            if unrealised < sl:
                print("SL hit")
                print("\n")
                driver(command=exit_command, accounts=accounts, my_account=my_account)
                break
            sleep(1)
        exit_file = codecs.open("exit_file.txt", "w")
        exit_file.write("")
        exit_file.close()
        return
    elif command_type == "DETAILS":
        my_account_position: List[Dict] = my_account.get_current_positions()
        if not my_account_position:
            print("No current position in primary account.\n")
            return
        verification_data: Dict[str, Dict] = {}
        for position in my_account_position:
            verification_data[position["strike"]] = position
        sleep(1)
        while True:
            incomplete_trades: int = 0
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
                    position_string: str = position_string + (account.account_id + "\t\t" + position["symbol_name"]
                                                         + "\t\t" + position["strike"] + "\t\t" + quantity_type + "\t\t"
                                                         + position["quantity"]) + "\n"
                position_string_list.append(position_string)
            sleep(1)
            os.system("clear")
            print("Incomplete trades: " + str(incomplete_trades))
            print("\n")
            for position_string in position_string_list:
                print(position_string)
    elif command_type == "PNL":
        while True:
            total_realised: float = 0.0
            total_unrealised: float = 0.0
            total_pnl: float = 0.0
            pnl_string_list: List[str] = []
            for account in accounts:
                realised, unrealised, pnl = account.get_pnl()
                total_realised += realised
                total_unrealised += unrealised
                total_pnl += pnl
                pnl_string: str = (account.account_id + "\t\t\t" + str(realised) + "\t\t\t" + str(unrealised)
                              + "\t\t\t" + str(pnl) + "\n")
                pnl_string_list.append(pnl_string)
            sleep(1)
            os.system("clear")
            print("Total realised: Rs " + str(total_realised))
            print("Total unrealised: Rs " + str(total_unrealised))
            print("Total p&l: Rs " + str(total_pnl))
            print("\n")
            for pnl_string in pnl_string_list:
                print(pnl_string)
    else:
        print("Wrong command\n")
