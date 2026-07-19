from types import SimpleNamespace

import pandas as pd
import pytest

from tradingagents.dataflows.errors import NoMarketDataError
from tradingagents.dataflows.symbol_utils import is_etf_identity
from tradingagents.dataflows import y_finance


@pytest.mark.unit
@pytest.mark.parametrize(
    "identity,expected",
    [
        ({"quote_type": "ETF", "company_name": "SPDR S&P 500"}, True),
        ({"quote_type": "EQUITY", "company_name": "CSI 300 ETF"}, True),
        ({"quote_type": "MUTUALFUND", "company_name": "Vanguard Index Fund"}, False),
        ({"quote_type": "EQUITY", "company_name": "Apple Inc."}, False),
        ({}, False),
    ],
)
def test_is_etf_identity(identity, expected):
    assert is_etf_identity(identity) is expected


def _fake_funds_data():
    return SimpleNamespace(
        fund_overview={"categoryName": "Large Blend", "family": "Test Family", "legalType": "ETF"},
        fund_operations=pd.DataFrame(
            {"TEST": [0.0009, 0.02, 100_000_000]},
            index=["Annual Report Expense Ratio", "Annual Holdings Turnover", "Total Net Assets"],
        ),
        asset_classes={"cashPosition": 0.01, "stockPosition": 0.99},
        top_holdings=pd.DataFrame(
            {"Name": ["Alpha", "Beta"], "Holding Percent": [0.12, 0.08]},
            index=["AAA", "BBB"],
        ),
        equity_holdings=pd.DataFrame({"TEST": [25.0]}, index=["Price/Earnings"]),
        bond_holdings=pd.DataFrame(),
        bond_ratings={},
        sector_weightings={"technology": 0.4, "financial_services": 0.2},
    )


@pytest.mark.unit
def test_get_fund_holdings_formats_etf_portfolio(monkeypatch):
    fake_ticker = SimpleNamespace(
        info={"quoteType": "ETF", "longName": "Test ETF"},
        funds_data=_fake_funds_data(),
    )
    monkeypatch.setattr(y_finance.yf, "Ticker", lambda _symbol: fake_ticker)
    monkeypatch.setattr(y_finance, "yf_retry", lambda fn: fn())

    report = y_finance.get_fund_holdings("TEST", "2025-01-02")

    assert "ETF Holdings and Portfolio Composition for TEST" in report
    assert "AAA" in report and "12.00%" in report
    assert "Technology" in report and "40.00%" in report
    assert "not historical point-in-time holdings" in report
    assert "Requested analysis date: 2025-01-02" in report


@pytest.mark.unit
def test_get_fund_holdings_rejects_non_etf(monkeypatch):
    fake_ticker = SimpleNamespace(
        info={"quoteType": "EQUITY", "longName": "Example Corp"},
        funds_data=_fake_funds_data(),
    )
    monkeypatch.setattr(y_finance.yf, "Ticker", lambda _symbol: fake_ticker)
    monkeypatch.setattr(y_finance, "yf_retry", lambda fn: fn())

    with pytest.raises(NoMarketDataError, match="not identified as an ETF"):
        y_finance.get_fund_holdings("EXAMPLE", "2026-01-01")
