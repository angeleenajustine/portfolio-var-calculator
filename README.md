# Portfolio Risk Calculator: Historical VaR and Expected Shortfall (WIP)

Python tool that measures 1-day market risk for a multi-asset portfolio using historical simulation.

## What it does
- Downloads daily adjusted prices (Yahoo Finance via `yfinance`)
- Computes log returns (per asset) and simple returns (portfolio aggregation)
- Calculates 1-day **VaR** and **Expected Shortfall (CVaR)** at 95% and 99%
- Plots the return distribution and a rolling 250-day VaR

## Run it
```bash
pip install -r requirements.txt
python var_calculator.py
```

## Method
- **Historical VaR:** the (1 − confidence) quantile of the portfolio's daily returns, reported as a positive loss.
- **Expected Shortfall:** the average loss on days worse than the VaR cutoff.
- **Rolling VaR:** uses only the prior 250 days for each forecast (no look-ahead).

## Portfolio
| Ticker | Weight |
|---|---|
|  | |

## Results


## Assumptions and limitations
- Past returns are representative of future risk.
- Constant weights, rebalanced daily; no transaction costs.
- Historical VaR has no information about volatility regimes and reacts slowly to shocks.
- VaR says nothing about how bad losses are *beyond* the cutoff (ES partly addresses this).
- All tickers are USD-listed; adding non-USD assets would introduce FX risk.

## Next steps
