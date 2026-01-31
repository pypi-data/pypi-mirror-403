from ohlcutils.data import load_symbol
from ohlcutils.enums import Periodicity

symbol = "NSENIFTY_OPT_20240926_PUT_25950"
md = load_symbol(symbol, start_time="2024-09-26", end_time="2024-09-26")
md = load_symbol(
    "INFY_STK___",
    days=100,
    src=Periodicity.DAILY,
    dest_bar_size="1W",
    label="left",
    adjust_for_holidays=True,
    adjustment="fbd",
)
print(md)
