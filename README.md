# Portfolio Risk Calculator: Historical VaR and Expected Shortfall

Python tool that measures 1-day market risk for a multi-asset portfolio of **any stocks, ETFs, or indexes** using historical simulation.

## What it does
- Takes user-chosen tickers and weights (command line or interactive prompts)
- Downloads daily adjusted prices (Yahoo Finance via `yfinance`)
- Computes log returns (per asset) and simple returns (portfolio aggregation)
- Calculates 1-day **VaR** and **Expected Shortfall (CVaR)** at any confidence levels
- Plots the return distribution and a rolling VaR

## Install
```bash
pip install -r requirements.txt
```

## Run it

**Interactive** (easiest): run with no arguments and answer the prompts.
```bash
python var_calculator.py
```

**Command line:**
```bash
# Equal-weighted portfolio
python var_calculator.py --tickers SPY TLT GLD

# Custom weights (percentages or fractions both work) and start date
python var_calculator.py --tickers AAPL MSFT TLT --weights 40 40 20 --start 2015-01-01

# Indexes: wrap ^ symbols in quotes
python var_calculator.py --tickers "^GSPC" "^GSPTSE" --weights 60 40

# Custom confidence levels, rolling window, and portfolio size
python var_calculator.py --tickers SPY QQQ --confidence 0.90 0.975 0.99 --window 500 --value 250000
```

| Option | Meaning | Default |
|---|---|---|
| `--tickers` | Yahoo Finance symbols, space- or comma-separated | prompts you |
| `--weights` | One per ticker; rescaled to sum to 1 | equal weight |
| `--start` / `--end` | Date range (`YYYY-MM-DD`) | 2019-01-01 / today |
| `--confidence` | One or more levels (`0.99` or `99`) | 0.95 0.99 |
| `--window` | Rolling VaR window in trading days | 250 |
| `--value` | Portfolio value for amount VaR | 100,000 |

### Finding symbols
Search any name on [finance.yahoo.com](https://finance.yahoo.com) and copy the symbol exactly.

| Symbol | What it is |
|---|---|
| `^GSPC` | S&P 500 index |
| `^GSPTSE` | S&P/TSX Composite index |
| `^IXIC` | Nasdaq Composite index |
| `^DJI` | Dow Jones Industrial Average |
| `^FTSE` | FTSE 100 (UK) |
| `SPY`, `QQQ`, `TLT`, `GLD` | ETFs (US equities, Nasdaq-100, long Treasuries, gold) |
| `XIU.TO` | TSX 60 ETF (Toronto-listed, priced in CAD) |

Tip: in Windows Command Prompt, `^` is a special character, so always put index symbols in quotes (or use interactive mode).

## Method
- **Historical VaR:** the (1 − confidence) quantile of the portfolio's daily returns, reported as a positive loss.
- **Expected Shortfall:** the average loss on days worse than the VaR cutoff.
- **Rolling VaR:** uses only the prior N days for each forecast (no look-ahead).

## Example portfolio
| Ticker | Weight |
|---|---|
| | |

## Results


## Assumptions and limitations
- Past returns are representative of future risk.
- Constant weights, rebalanced daily; no transaction costs; no short positions.
- Historical VaR has no information about volatility regimes and reacts slowly to shocks.
- VaR says nothing about how bad losses are *beyond* the cutoff (ES partly addresses this).
- **Currency:** prices are used in their local currency. Mixing currencies (e.g., `^GSPC` in USD with `^GSPTSE` in CAD) ignores FX risk.
- **Calendars:** days when any asset has no price (market holidays, a later listing date) are dropped, which can shorten the sample.
- **Indexes are not tradable.** Index data is fine for measuring risk, but real portfolios hold funds or stocks.
- High confidence levels need long histories: 99% VaR on 5 years of data rests on only ~12 tail days. The tool warns you when the tail is too thin.

## Next steps
Parametric and Monte Carlo VaR, backtesting (Kupiec test), and GARCH volatility are covered in later projects.
