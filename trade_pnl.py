from account import Account
from typing import List
from time import sleep
import os


def pnl(accounts: List[Account] = None) -> None:
    """
    Prints p&l of a trade across all accounts

    Parameters
    ----------
    accounts: List[Account], default: None
        List of accounts to trade
    """
    while True:
        total_realised: float = 0.0
        total_unrealised: float = 0.0
        total_pnl: float = 0.0
        pnl_string_list: List[str] = []
        pnl_string: str = "Account ID\t\t\t     Realised\t\t\t     Unrealised\t\t\t     Current P&L\n"
        pnl_string_list.append(pnl_string)
        for account in accounts:
            realised, unrealised, current_pnl = account.get_pnl()
            total_realised += realised
            total_unrealised += unrealised
            total_pnl += current_pnl
            account_id: str = account.account_id
            account_id = "*****" + account_id[-3:]
            pnl_string = (account_id + "\t\t\t\t" + str(realised) + "\t\t\t\t" + str(unrealised)
                          + "\t\t\t\t" + str(current_pnl) + "\n")
            pnl_string_list.append(pnl_string)
        sleep(1)
        os.system("clear")
        print("Total realised: Rs " + str(total_realised))
        print("Total unrealised: Rs " + str(total_unrealised))
        print("Total p&l: Rs " + str(total_pnl))
        print("\n")
        for pnl_string in pnl_string_list:
            print(pnl_string)
