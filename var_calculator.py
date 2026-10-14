"""
Project 1: Portfolio Risk Calculator (Historical VaR and Expected Shortfall)

Run:  python var_calculator.py
Edit the CONFIG block to change assets, weights, dates, or confidence levels.
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# ------------------------------------------------------------------ CONFIG
TICKERS = ["SPY", "TLT", "GLD", "XLF", "EFA", "AAPL"]   # USD-listed to avoid FX risk
WEIGHTS = [0.30, 0.25, 0.10, 0.10, 0.15, 0.10]          # must sum to 1
START = "2019-01-01"
END = None                                              # None = today
CONFIDENCE_LEVELS = [0.95, 0.99]
ROLLING_WINDOW = 250                                    # ~1 trading year
PORTFOLIO_VALUE = 100_000                               # for dollar VaR
FIG_DIR = Path("figures")


# -------------------------------------------------------------- LAYER 1: DATA
def get_prices(tickers, start, end=None):
    """Download adjusted daily close prices; drop days with missing data."""
    import yfinance as yf

    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    prices = data["Close"][tickers]  # keep the ticker order
    missing = prices.isna().sum()
    if missing.any():
        print("Missing values per ticker (rows will be dropped):\n", missing[missing > 0])
    return prices.dropna()


def get_returns(prices):
    """Per-asset log returns and simple returns.

    Log returns are used for single-asset statistics.
    Simple returns are used to aggregate into a portfolio, because log returns
    do not add up across assets (only across time).
    """
    log_ret = np.log(prices / prices.shift(1)).dropna()
    simple_ret = prices.pct_change().dropna()
    return log_ret, simple_ret


def portfolio_returns(simple_ret, weights):
    """Daily portfolio return assuming weights are rebalanced each day."""
    w = np.asarray(weights, dtype=float)
    assert np.isclose(w.sum(), 1.0), "Weights must sum to 1"
    return simple_ret @ w


# -------------------------------------------------------------- LAYER 2: RISK
def historical_var(returns, confidence):
    """VaR as a positive loss fraction: the (1 - confidence) quantile of returns."""
    return -np.quantile(returns, 1 - confidence)


def historical_es(returns, confidence):
    """Expected Shortfall (CVaR): average loss on days worse than the VaR cutoff."""
    cutoff = np.quantile(returns, 1 - confidence)
    return -returns[returns <= cutoff].mean()


def rolling_var(returns, confidence, window):
    """VaR forecast for day t using only the prior `window` days (no look-ahead)."""
    return -returns.rolling(window).quantile(1 - confidence).shift(1)


def risk_table(port_ret, levels, value):
    rows = []
    for c in levels:
        var, es = historical_var(port_ret, c), historical_es(port_ret, c)
        rows.append({"Confidence": f"{c:.0%}",
                     "VaR (%)": var * 100, "ES (%)": es * 100,
                     "VaR ($)": var * value, "ES ($)": es * value})
    return pd.DataFrame(rows).set_index("Confidence").round(2)


# --------------------------------------------------------------- LAYER 3: PLOTS
def plot_distribution(port_ret, levels, path):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(port_ret * 100, bins=80, color="#1F3864", alpha=0.8)
    colors = ["#E69F00", "#C00000"]
    for c, col in zip(levels, colors):
        ax.axvline(-historical_var(port_ret, c) * 100, color=col, ls="--",
                   label=f"{c:.0%} VaR")
        ax.axvline(-historical_es(port_ret, c) * 100, color=col, ls=":",
                   label=f"{c:.0%} ES")
    ax.set(title="Daily Portfolio Returns with VaR and ES",
           xlabel="Daily return (%)", ylabel="Frequency")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_rolling(port_ret, levels, window, path):
    fig, ax = plt.subplots(figsize=(9, 5))
    for c in levels:
        (rolling_var(port_ret, c, window) * 100).plot(ax=ax, label=f"{c:.0%} VaR")
    ax.set(title=f"Rolling {window}-Day Historical VaR",
           xlabel="Date", ylabel="1-day VaR (% of portfolio)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------------ MAIN
def main():
    FIG_DIR.mkdir(exist_ok=True)
    prices = get_prices(TICKERS, START, END)
    log_ret, simple_ret = get_returns(prices)
    port_ret = portfolio_returns(simple_ret, WEIGHTS)

    print(f"\nSample: {prices.index[0].date()} to {prices.index[-1].date()} "
          f"({len(port_ret)} trading days)")
    print("\nAnnualized volatility by asset (log returns):")
    print((log_ret.std() * np.sqrt(252)).round(3))
    print("\n1-day portfolio risk:")
    print(risk_table(port_ret, CONFIDENCE_LEVELS, PORTFOLIO_VALUE))

    plot_distribution(port_ret, CONFIDENCE_LEVELS, FIG_DIR / "return_distribution.png")
    plot_rolling(port_ret, CONFIDENCE_LEVELS, ROLLING_WINDOW, FIG_DIR / "rolling_var.png")
    print(f"\nFigures saved to {FIG_DIR}/")


if __name__ == "__main__":
    main()
