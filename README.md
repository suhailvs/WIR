## WIR

### about 

* WIR was founded in 1934. 
* WIR created a credit system which issues credit in WIR francs to its members, with credit lines secured by members pledging assets. This ensures the currency is asset-backed. 
* The WIR franc is pegged 1:1 to the Swiss franc

WIR functions as a closed-loop ledger. Every "creation" of currency is balanced by an equal and opposite debt.
* Zero-Sum Balance: At any given moment, the sum of all positive balances in the WIR network exactly equals the sum of all negative balances (debts).
* The Ledger Entry: If Business A (with a zero balance) buys $1,000$ CHW worth of supplies from Business B, the system records:
    * Business A: $-1,000$ CHW (Debt/Liability)
    * Business B: $+1,000$ CHW (Asset/Credit)
* New Liquidity: $1,000$ "new" units of currency have now entered the circulation of the network to facilitate that trade.

### load test

```bash
$ locust
```

### configuration

For local development:

```bash
cp .env.example .env
bash run.sh
python manage.py runserver
```