# Portfolio Risk Calculator: Historical VaR and Expected Shortfall

Python tool that measures 1-day market risk for a multi-asset portfolio of any stocks, ETFs, or indexes using historical simulation.

## What it does
- Asks for your tickers and weights
- Downloads daily adjusted prices (Yahoo Finance via `yfinance`)
- Computes daily returns for each asset and for the weighted portfolio
- Calculates 1-day **VaR** and **Expected Shortfall (ES)** at 95% and 99%
- Plots the return distribution and a rolling VaR

## Install
```bash
pip install -r requirements.txt
```

## Run it
```bash
python var_calculator_simple.py
```
You will be asked for:
1. **Tickers**, separated by commas (e.g. `SPY, TLT, ^GSPC`)
2. **Weights**, separated by commas (e.g. `50, 30, 20`), or press Enter for equal weights. Weights are rescaled to sum to 1, so percentages and fractions both work.

### Settings
Edit these constants at the top of `var_calculator_simple.py`:

| Setting | Meaning | Default |
|---|---|---|
| `START_DATE` | First date of price history | 2019-01-01 |
| `CONFIDENCE_LEVELS` | VaR and ES confidence levels | 95%, 99% |
| `WINDOW` | Days used for rolling VaR | 250 |
| `PORTFOLIO_VALUE` | Converts percentages into amounts | 100,000 |

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

## Method
- **Historical VaR:** the (1 − confidence) quantile of the portfolio's daily returns, reported as a positive loss.
- **Expected Shortfall:** the average loss on days worse than the VaR cutoff.
- **Rolling VaR:** uses only the prior `WINDOW` days for each forecast (no look-ahead).

## Example Portfolio

## Results

## Assumptions and limitations
- Past returns are representative of future risk.
- Constant weights, rebalanced daily; no transaction costs; no short positions.
- Historical VaR has no information about volatility regimes and reacts slowly to shocks.
- VaR says nothing about how bad losses are *beyond* the cutoff (ES partly addresses this).
- **Currency:** prices are used in their local currency. Mixing currencies (e.g., `^GSPC` in USD with `^GSPTSE` in CAD) ignores FX risk.
- **Calendars:** days when any asset has no price (market holidays, a later listing date) are dropped, which can shorten the sample.
- **Indexes are not tradable.** Index data is fine for measuring risk, but real portfolios hold funds or stocks.
- **Small tail samples:** 99% VaR on 5 years of data rests on only ~12 tail days, so the estimate is noisy.
