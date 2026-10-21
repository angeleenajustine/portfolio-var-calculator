"""
Project 1: Portfolio Risk Calculator (Historical VaR and Expected Shortfall)

Usage
  python var_calculator.py                          # interactive prompts
  python var_calculator.py --tickers SPY TLT GLD    # equal weights
  python var_calculator.py --tickers "^GSPC" "^GSPTSE" --weights 60 40 --start 2015-01-01

Any symbol that works on finance.yahoo.com works here (stocks, ETFs, indexes).
"""
import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

DEFAULT_START = "2019-01-01"
DEFAULT_CONFIDENCE = [0.95, 0.99]
DEFAULT_WINDOW = 250          # ~1 trading year
DEFAULT_VALUE = 100_000       # portfolio size, for amount VaR
FIG_DIR = Path("figures")
COLORS = ["#E69F00", "#C00000", "#2E75B6", "#548235"]


# ------------------------------------------------------------ INPUT HANDLING
def split_items(items):
    """Accept 'SPY TLT', 'SPY,TLT' or 'SPY, TLT' and return a clean list."""
    out = []
    for item in items:
        out += [x.strip() for x in str(item).replace(",", " ").split() if x.strip()]
    return out


def clean_inputs(tickers_raw, weights_raw, confidence_raw):
    """Validate user input. Returns (tickers, weights, confidence levels)."""
    tickers = list(dict.fromkeys(t.upper() for t in split_items(tickers_raw)))  # dedupe, keep order
    if not tickers:
        raise SystemExit("Please enter at least one ticker.")

    if weights_raw:
        try:
            weights = np.array([float(w) for w in split_items(weights_raw)])
        except ValueError:
            raise SystemExit("Weights must be numbers, e.g. 60 40 or 0.6 0.4.")
        if len(weights) != len(tickers):
            raise SystemExit(f"You gave {len(tickers)} tickers but {len(weights)} weights.")
        if (weights < 0).any() or weights.sum() <= 0:
            raise SystemExit("Weights must be non-negative and not all zero.")
        if not np.isclose(weights.sum(), 1.0):
            print(f"Weights summed to {weights.sum():g}; rescaled to sum to 1.")
            weights = weights / weights.sum()
    else:
        weights = np.full(len(tickers), 1 / len(tickers))

    levels = [c / 100 if c > 1 else c for c in confidence_raw]   # allow 95 or 0.95
    if not all(0.5 <= c < 1 for c in levels):
        raise SystemExit("Confidence levels must be between 50% and 100% (e.g. 0.95 0.99 or 95 99).")
    return tickers, weights, sorted(levels)


def prompt_inputs(args):
    """Interactive mode: ask the user instead of requiring command-line flags."""
    print("Portfolio Risk Calculator (type symbols as on finance.yahoo.com)\n"
          "Examples: SPY, TLT, AAPL, ^GSPC (S&P 500), ^GSPTSE (TSX), ^IXIC (Nasdaq)\n")
    args.tickers = [input("Tickers / indexes, separated by commas: ")]
    w = input("Weights, e.g. 60, 40 (press Enter for equal weights): ").strip()
    args.weights = [w] if w else None
    s = input(f"Start date YYYY-MM-DD (Enter = {DEFAULT_START}): ").strip()
    args.start = s or args.start
    v = input(f"Portfolio value (Enter = {DEFAULT_VALUE:,}): ").strip()
    args.value = float(v.replace(",", "")) if v else args.value
    return args


def parse_args():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--tickers", nargs="+", help="Yahoo Finance symbols (stocks, ETFs, indexes)")
    p.add_argument("--weights", nargs="+", help="One per ticker; default equal weight")
    p.add_argument("--start", default=DEFAULT_START, help="YYYY-MM-DD")
    p.add_argument("--end", default=None, help="YYYY-MM-DD (default: today)")
    p.add_argument("--confidence", nargs="+", type=float, default=DEFAULT_CONFIDENCE)
    p.add_argument("--window", type=int, default=DEFAULT_WINDOW, help="rolling VaR window (days)")
    p.add_argument("--value", type=float, default=DEFAULT_VALUE, help="portfolio value")
    return p.parse_args()


# -------------------------------------------------------------- LAYER 1: DATA
def get_prices(tickers, start, end=None):
    """Download adjusted daily close prices; drop days where any asset is missing."""
    import yfinance as yf

    data = yf.download(tickers, start=start, end=end, auto_adjust=True, progress=False)
    if data.empty:
        raise SystemExit("No data returned. Check your tickers, dates, and internet connection.")
    close = data["Close"]
    if isinstance(close, pd.Series):                       # single-ticker edge case
        close = close.to_frame(tickers[0])
    bad = [t for t in tickers if t not in close.columns or close[t].dropna().empty]
    if bad:
        raise SystemExit(f"No data found for: {', '.join(bad)}. "
                         "Check the symbols on finance.yahoo.com.")
    close = close[tickers]
    n_before = len(close)
    close = close.dropna()
    if len(close) < n_before:
        print(f"Dropped {n_before - len(close)} days where at least one asset had no price "
              "(different market holidays or a later start date).")
    return close


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
                     "VaR (amt)": var * value, "ES (amt)": es * value})
    return pd.DataFrame(rows).set_index("Confidence").round(2)


# --------------------------------------------------------------- LAYER 3: PLOTS
def plot_distribution(port_ret, levels, path):
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.hist(port_ret * 100, bins=80, color="#1F3864", alpha=0.8)
    for i, c in enumerate(levels):
        col = COLORS[i % len(COLORS)]
        ax.axvline(-historical_var(port_ret, c) * 100, color=col, ls="--", label=f"{c:.0%} VaR")
        ax.axvline(-historical_es(port_ret, c) * 100, color=col, ls=":", label=f"{c:.0%} ES")
    ax.set(title="Daily Portfolio Returns with VaR and ES",
           xlabel="Daily return (%)", ylabel="Frequency")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def plot_rolling(port_ret, levels, window, path):
    fig, ax = plt.subplots(figsize=(9, 5))
    for i, c in enumerate(levels):
        (rolling_var(port_ret, c, window) * 100).plot(ax=ax, color=COLORS[i % len(COLORS)],
                                                      label=f"{c:.0%} VaR")
    ax.set(title=f"Rolling {window}-Day Historical VaR",
           xlabel="Date", ylabel="1-day VaR (% of portfolio)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------------ MAIN
def main():
    args = parse_args()
    if not args.tickers:
        args = prompt_inputs(args)
    tickers, weights, levels = clean_inputs(args.tickers, args.weights, args.confidence)

    prices = get_prices(tickers, args.start, args.end)
    log_ret, simple_ret = get_returns(prices)
    port_ret = portfolio_returns(simple_ret, weights)
    n = len(port_ret)

    print("\nPortfolio:")
    print(pd.Series(weights, index=tickers).map("{:.1%}".format).to_string())
    print(f"\nSample: {prices.index[0].date()} to {prices.index[-1].date()} ({n} trading days)")
    for c in levels:
        if n * (1 - c) < 10:
            print(f"Warning: {c:.0%} VaR rests on only ~{n * (1 - c):.0f} tail days; "
                  "use a longer history for a more reliable estimate.")
    print("\nAnnualized volatility by asset (log returns):")
    print((log_ret.std() * np.sqrt(252)).round(3).to_string())
    print("\n1-day portfolio risk:")
    print(risk_table(port_ret, levels, args.value))

    FIG_DIR.mkdir(exist_ok=True)
    plot_distribution(port_ret, levels, FIG_DIR / "return_distribution.png")
    if n > args.window:
        plot_rolling(port_ret, levels, args.window, FIG_DIR / "rolling_var.png")
    else:
        print(f"\nSkipped rolling plot: need more than {args.window} days of data.")
    print(f"\nFigures saved to {FIG_DIR}/")


if __name__ == "__main__":
    main()
