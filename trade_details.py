from account import Account
from typing import List, Dict, Optional
from time import sleep
import os


def details(accounts: List[Account] = None, my_account: Account = None) -> None:
    """
    Prints details of a trade across all account

    Parameters
    ----------
    accounts: List[Account], default: None
        List of accounts to trade
    my_account: Account, default: None
        My primary trading account
    """
    my_account_position: List[Dict] = my_account.get_current_positions()
    if not my_account_position:
        print("No current position in primary account.\n")
        my_account_position = []
    verification_data: Optional[Dict[str, Dict]] = {}
    for position in my_account_position:
        verification_data[position["strike"]] = position
    if verification_data == {}:
        verification_data = None
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
                account_id: str = account.account_id
                account_id = "*****" + account_id[-3:]
                position_string: str = position_string + (account_id + "\t\t" + position["symbol_name"]
                                                          + "\t\t" + position["strike"] + "\t\t"
                                                          + quantity_type + "\t\t"
                                                          + position["quantity"]) + "\n"
            position_string_list.append(position_string)
        sleep(1)
        os.system("clear")
        print("Incomplete trades: " + str(incomplete_trades))
        print("\n")
        for position_string in position_string_list:
            print(position_string)
