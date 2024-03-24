# copytrade
Copy trade code</br>
This code places only credit spreads in all the accounts mentioned.</br>
Please note, that this code does not guarantee profits in Options trading. Strategy is something that you need to
figure on your own.

## Table of contents
- Installation and setup
- Commands
- Code

## Installation and setup
This code is tested in a python3.11 and pip3.11
```bash
pip3.11 install -r requirements.txt
```
To start the code
```bash
python3.11 main.py
```

## Files

### Credentials
For credentials, you need credentials.txt </br>
The format for the credentials.txt is same as sample_credentials.txt</br>
my_account_id is necessary to validate positions in all other accounts. This is the primary account which will be 
treated as the source of truth. In case you want to write credentials but not use them to place trade, write # before 
that particular line. All sets of credentials should be separated by a newline character.</br>
capital_to_use should be strictly less than the actual balance in your account. This is because the code will try to
utilise the amount mentioned and doing so it might create a spread that requires more than the amount mentioned. </br>

### Tokens
You need to save the content of this [file](https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json) 
in tokens.json</br>
The code will fetch symbol details from this file. Make sure you update this file before you place an entry trade. Don't
update the file if you are going to place an exit trade, as this might probably remove the token details needed to exit
a trade.</br>

### Index
Details related to indices are in index_details.txt</br>
You might need to change the parameters accordingly if needed. This file contains the details of each index where 
trading will be done. Usually the freeze_quantity and quantity_per_lot get changed. Keep yourself updated. spreadwidth
is the gap between buying and selling strikes in the credit spread you will deploy in a particular index.</br>

## Commands
Use proper spellings for indices</br>
NIFTY</br>
BANKNIFTY</br>
MIDCPNIFTY</br>
FINNIFTY</br>

For strike, specify the strike and then append whether it is CE or PE. This is the strike which you sell</br>
If you are bullish on the market, then go for Bull-Put spread where you need to sell Put options. In case you are 
bearish in the market, then go for Bear-Call spread where you need to sell Call options. Spreadwidth will be fetched
from index_details.txt</br>

Expiry will be exactly as mentioned in tokens.json .</br>

### To place an entry trade

```text
ENTER index strike expiry
ENTER BANKNIFTY 48000PE 20MAR24
```
The above command will place a Bull-Put spread at 48000 PE for the expiry on 20th March 2024. First the buying leg will
be placed and then the selling leg. Each pair of buying-selling legs, will be placed with a maximum quantity of freeze
quantity.</br>
In case buying leg fails to execute, the selling leg is not placed. If the selling leg fails to execute, the 
corresponding buying leg of that pair will be reverted.</br>

### To place an exit trade

```text
EXIT index strike expiry
EXIT BANKNIFTY 48000PE 20MAR24
```
The above command will exit a Bull-Put spread at 48000 PE for the expiry on 20th March 2024. This command will only run
on accounts who already have an open position and exactly Bull-Put at 48000 PE for 20th March 2024.</br>
Reversal of orders in case of failed orders, happen similarly like the entry.</br>

### To check P&L

```text
PNL
```
This command will keep on displaying the current realised, unrealised and total p&l across all the accounts. In case
code faces any broker side exception or network issue, appropriate message will be displayed. This command runs on an
infinite loop, so to run any other command, exit the current session.</br>

### To verify trades

```text
DETAILS
```
The primary account will be used to verify trades. So make sure you run this command once you have checked that the
primary account has got the right trades. This can be manually verified from the broker's platform. To see if remaining
accounts have the same trades, use this command, and check whether the strikes are same as expected and absolute value
of the quantities are equal for both the strikes. This command runs on an infinite loop, so to run any other command, 
exit the current session.</br>

### To autoexit

```text
AUTOEXIT SL=<stoploss> TGT=<target>
AUTOEXIT SL=-10000 TGT=10000
```

This command is to put stoploss and target. The code will keep on checking the current unrealised p&l of the primary
account and takes decision accordingly. The moment, the primary account meets the stoploss or target value, this will
trigger the exit command in all the accounts.</br>
While running autoexit in a session, if you run PNL or DETAILS in some other session, you will see exception message in
all the sessions. The reason is each session will try to fetch the current positions, which will hit the rate limit of
the API.

## Code
This section will explain the code in brief, which will help you in tweaking the parameters if required.