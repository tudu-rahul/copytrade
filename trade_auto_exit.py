from account import Account
from typing import Optional, List
import codecs
from time import sleep
import trade_exit


def trade_auto_exit(command: str = None, accounts: List[Account] = None, my_account: Account = None) -> None:
    """
    Auto exits a trade based on SL and target

    Parameters
    ----------
    command: str, default: None
        The command
    accounts: List[Account], default: None
        List of accounts to trade
    my_account: Account, default: None
        My primary trading account
    """
    parts: List[str] = command.split(' ')
    if len(parts) != 3:
        print("Incomplete command")
        return None
    sl_string: str = parts[1].strip()
    tgt_string: str = parts[2].strip()
    sl: Optional[float] = float(sl_string.split('=')[1]) if sl_string.split('=')[0] == "SL" else None
    tgt: Optional[float] = float(tgt_string.split('=')[1]) if tgt_string.split('=')[0] == "TGT" else None
    if sl is None or tgt is None:
        print("Wrong command")
        print("\n")
        return None
    if tgt < 0:
        print("Wrong SL or target")
        print("\n")
        return None
    exit_command: str = ""
    exit_file = codecs.open("exit_file.txt", "r")
    for lin in exit_file:
        exit_command = lin.strip()
    exit_file.close()
    if len(exit_command) == 0:
        print("No exit command specified")
        print("\n")
        return None
    while True:
        realised, unrealised, pnl = my_account.get_pnl()
        if unrealised > tgt:
            sleep(1)
            print("Target reached")
            print("\n")
            trade_exit.trade_exit(command=exit_command, accounts=accounts)
            break
        if unrealised < sl:
            print("SL hit")
            print("\n")
            trade_exit.trade_exit(command=exit_command, accounts=accounts)
            break
        sleep(1)
    exit_file = codecs.open("exit_file.txt", "w")
    exit_file.write("")
    exit_file.close()
    return None
