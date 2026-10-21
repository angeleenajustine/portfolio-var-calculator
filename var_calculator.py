"""
Project 1 (simple version): Portfolio Risk Calculator
Calculates 1-day Value at Risk (VaR) and Expected Shortfall (ES) for a portfolio.

Run:  python var_calculator_simple.py
You will be asked for your tickers and weights. Other settings are below.
Any symbol from finance.yahoo.com works (stocks, ETFs, indexes like ^GSPC).
"""
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf

# ---------------------------------------------------------------- SETTINGS
START_DATE = "2019-01-01"
CONFIDENCE_LEVELS = [0.95, 0.99]
WINDOW = 250               # days used for the rolling VaR (about 1 trading year)
PORTFOLIO_VALUE = 100000   # used to convert percentages into amounts


# ------------------------------------------------------ STEP 0: ASK THE USER
def ask_user():
    tickers_text = input("Tickers separated by commas (e.g. SPY, TLT, ^GSPC): ")
    tickers = [t.strip().upper() for t in tickers_text.split(",") if t.strip()]
    if len(tickers) == 0:
        raise SystemExit("No tickers entered.")  # stops the program with a message

    weights_text = input("Weights separated by commas (e.g. 60, 40) or Enter for equal: ")
    if weights_text.strip() == "":
        weights = [1] * len(tickers)             # equal weights
    else:
        weights = [float(w) for w in weights_text.split(",")]
        if len(weights) != len(tickers):
            raise SystemExit("You need exactly one weight per ticker.")

    total = sum(weights)
    weights = np.array(weights) / total          # rescale so weights add up to 1
    return tickers, weights


# ------------------------------------------------------------ LAYER 1: DATA
def get_prices(tickers):
    """Download daily prices. Returns a table: one row per day, one column per ticker."""
    data = yf.download(tickers, start=START_DATE, auto_adjust=True, progress=False)
    prices = data["Close"]
    if isinstance(prices, pd.Series):            # happens with a single ticker
        prices = prices.to_frame(tickers[0])

    bad = [t for t in tickers if t not in prices.columns or prices[t].isna().all()]
    if bad:
        raise SystemExit(f"No data found for: {bad}. Check the symbols on finance.yahoo.com.")

    prices = prices[tickers]
    return prices.dropna()                       # drop days where any price is missing


def get_returns(prices):
    """Daily percentage change of each asset (simple returns)."""
    return prices.pct_change().dropna()


def get_portfolio_returns(returns, weights):
    """Combine the assets into one daily return, using the weights."""
    return returns @ weights                     # weighted sum for each day


# ------------------------------------------------------------ LAYER 2: RISK
def historical_var(portfolio_returns, confidence):
    """VaR: the loss that is only exceeded on (1 - confidence) of days."""
    cutoff = np.quantile(portfolio_returns, 1 - confidence)   # e.g. the 1st percentile
    return -cutoff                                            # flip sign: report loss as positive


def historical_es(portfolio_returns, confidence):
    """ES: the average loss on the days that are worse than the VaR cutoff."""
    cutoff = np.quantile(portfolio_returns, 1 - confidence)
    worst_days = portfolio_returns[portfolio_returns <= cutoff]
    return -worst_days.mean()


def rolling_var(portfolio_returns, confidence, window):
    """VaR recalculated every day from the previous `window` days only."""
    cutoff = portfolio_returns.rolling(window).quantile(1 - confidence)
    return -cutoff.shift(1)       # shift(1): use yesterday's estimate, no peeking at today


# ------------------------------------------------------------ LAYER 3: PLOTS
def plot_distribution(portfolio_returns):
    plt.figure(figsize=(9, 5))
    plt.hist(portfolio_returns * 100, bins=80, color="#1F3864")
    colors = ["#E69F00", "#C00000"]
    for i, c in enumerate(CONFIDENCE_LEVELS):
        plt.axvline(-historical_var(portfolio_returns, c) * 100,
                    color=colors[i % 2], linestyle="--", label=f"{c:.0%} VaR")
        plt.axvline(-historical_es(portfolio_returns, c) * 100,
                    color=colors[i % 2], linestyle=":", label=f"{c:.0%} ES")
    plt.title("Daily Portfolio Returns with VaR and ES")
    plt.xlabel("Daily return (%)")
    plt.ylabel("Number of days")
    plt.legend()
    plt.tight_layout()
    plt.savefig("return_distribution.png", dpi=200)
    plt.close()


def plot_rolling(portfolio_returns):
    plt.figure(figsize=(9, 5))
    for c in CONFIDENCE_LEVELS:
        plt.plot(rolling_var(portfolio_returns, c, WINDOW) * 100, label=f"{c:.0%} VaR")
    plt.title(f"Rolling {WINDOW}-Day Historical VaR")
    plt.xlabel("Date")
    plt.ylabel("1-day VaR (% of portfolio)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("rolling_var.png", dpi=200)
    plt.close()


# --------------------------------------------------------------------- MAIN
def main():
    tickers, weights = ask_user()

    prices = get_prices(tickers)
    returns = get_returns(prices)
    portfolio = get_portfolio_returns(returns, weights)

    print("\nPortfolio weights:")
    for ticker, w in zip(tickers, weights):
        print(f"  {ticker}: {w:.1%}")
    print(f"\nData: {prices.index[0].date()} to {prices.index[-1].date()} "
          f"({len(portfolio)} trading days)")

    print("\n1-day risk (as % of portfolio, and in amount):")
    for c in CONFIDENCE_LEVELS:
        var = historical_var(portfolio, c)
        es = historical_es(portfolio, c)
        print(f"  {c:.0%} VaR: {var:.2%} ({var * PORTFOLIO_VALUE:,.0f})   "
              f"ES: {es:.2%} ({es * PORTFOLIO_VALUE:,.0f})")

    plot_distribution(portfolio)
    if len(portfolio) > WINDOW:
        plot_rolling(portfolio)
    print("\nCharts saved: return_distribution.png, rolling_var.png")


if __name__ == "__main__":
    main()
