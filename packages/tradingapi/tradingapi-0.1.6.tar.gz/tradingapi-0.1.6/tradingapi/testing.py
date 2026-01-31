import datetime as dt
import importlib.util
import logging
import os
import pkgutil
import sys

from pandas.core.internals.blocks import new_block
from tradingapi import error_handling

# Make sure breeze_connect sees its own config.py as the top‑level `config` module,
# instead of accidentally importing `tradingapi.config`.
loader = pkgutil.get_loader("breeze_connect")
if loader is not None and hasattr(loader, "get_filename"):
    breeze_pkg_path = os.path.dirname(loader.get_filename())
    breeze_cfg_path = os.path.join(breeze_pkg_path, "config.py")
    if os.path.exists(breeze_cfg_path):
        spec = importlib.util.spec_from_file_location("config", breeze_cfg_path)
        breeze_config_module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(breeze_config_module)  # type: ignore[attr-defined]
            sys.modules.setdefault("config", breeze_config_module)
        except Exception:
            # If this fails, we just let the original error surface.
            pass

# def disable_validate_inputs():
#     def passthrough(*checks, **kw):
#         def decorator(func):
#             return func
#         return decorator
#     error_handling.validate_inputs = passthrough
#
# disable_validate_inputs()

from tradingapi.shoonya import Shoonya, save_symbol_data as save_symbol_data_sh
from tradingapi.fivepaisa import FivePaisa, save_symbol_data as save_symbol_data_fp
from tradingapi.icicidirect import IciciDirect, save_symbol_data as save_symbol_data_ic
from tradingapi.utils import (
    Price,
    get_pnl_table,
    calculate_mtm,
    calc_pnl,
    get_exit_candidates,
    place_combo_order,
    get_delta_strike,
    register_strategy_capital
)
from tradingapi import configure_logging
from tradingapi.error_handling import set_execution_time_logging, set_retry_enabled
from chameli.dateutils import get_expiry

# Configure logging first, before any other operations
# Clear existing handlers and configure with file logging
# Don't configure root logger to avoid duplicate logs
configure_logging(
    level=logging.INFO,
    log_file="/home/psharma/testing.log",
    clear_existing_handlers=True,
    enable_console=True,
    configure_root_logger=False,
)

# Disable execution time logging for easier debugging
set_execution_time_logging(False)
set_retry_enabled(False)
from tradingapi import trading_logger
# save_symbol_data_ic()

fp = FivePaisa()
fp.connect(8)

sh = Shoonya()
sh.connect(7)
brok = sh
strategy = "SCALPING05"
exchange="NSE"
pnl_table = get_pnl_table(brok,strategy, refresh_status=False)
today = dt.date.today().strftime("%Y-%m-%d")
print(pnl_table.loc[pnl_table.entry_time.str[0:10] == today,])
pnl_table = get_pnl_table(fp, "SCALPING02", refresh_status=False)
pnl_table = calculate_mtm(fp,pnl_table)
pnl_table = calc_pnl(pnl_table,fp)
today = dt.date.today().strftime("%Y-%m-%d")
pnl_table =  pnl_table.loc[pnl_table.entry_time.str[0:10] == today]
# print(pnl_table.loc[pnl_table.entry_time.str[0:10] == today,["symbol","pnl","exit_time","int_order_id"]])
# f'Day Profit: {(pnl_table.loc[pnl_table.entry_time.str[0:10] == today,["symbol","gross_pnl"]].gross_pnl.sum())}'
sh = Shoonya()
sh.connect(4)
register_strategy_capital("TEST02", fp, 1000000)
brok = fp
exch_order_id = "1766721485284341216"
new_price = 89.30000000000001
order_quantity = 80
out = fp.api.modify_order(ExchOrderID=exch_order_id, Price=new_price, Qty=order_quantity)

out = sh.api.single_order_history("25121900430323")
symbol = "NIFTY_OPT_20251230_CALL_25950?-75:NIFTY_OPT_20251230_PUT_25950?75"
place_combo_order(brok, "TEST01", symbol,1,entry=True,exchanges="NSE",price_types=["LMT"], paper=True)

pnl = calculate_mtm(sh,get_pnl_table(sh,"NIFTY01"))
pnl = pnl.loc[pnl.symbol=="NIFTY_FUT_20251230__"]
pnl = calc_pnl(pnl,sh)

expiry = get_expiry(dt.date.today(),weekly=0,day_of_week=2).strftime("%Y%m%d")
symbol = get_delta_strike(sh,"NIFTY_IND___",0.5,expiry,"PUT")
# place_combo_order(brok, "TEST01", "INFY_STK___", 1, entry=True, exchanges="NSE", price_types=1450, paper=False)
place_combo_order(brok, "TEST01", "INFY_STK___", -1, entry=False, exchanges="NSE", price_types=1551, paper=False)
pnl = get_pnl_table(brok, "TEST01", refresh_status=False)
print(pnl)
pnl = get_pnl_table(brok, "TEST01", refresh_status=True)
print(pnl)
symbol = get_delta_strike(sh,"INFY",0.5,expiry,"PUT")
place_combo_order(
    sh,
    "IRONCONDOR01",
    symbols=symbol,
    quantities=-6,
    entry=False,
    exchanges="BSE",
    price_types="LMT",
    paper=False,
)

pnl_table = get_pnl_table(sh, "STRADDLE01", refresh_status=False)
open_trades = pnl_table.loc[pnl_table.entry_quantity + pnl_table.exit_quantity != 0]
symbol = open_trades.iloc[0]["symbol"]
quantity = open_trades.iloc[0]["entry_quantity"] + open_trades.iloc[0]["exit_quantity"]
quantity = -quantity
exchange = "BSE" if "SENSEX" in symbol else "NSE"

out = get_exit_candidates(sh, "STRADDLE01", symbol, "SELL")
place_combo_order(
    sh,
    "STRADDLE01",
    symbols=symbol,
    quantities=2,
    entry=True,
    exchanges=exchange,
    price_types="MKT",
    paper=True,
)
print(out)
