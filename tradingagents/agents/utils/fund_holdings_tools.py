from typing import Annotated

from langchain_core.tools import tool

from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_fund_holdings(
    ticker: Annotated[str, "ETF ticker symbol"],
    curr_date: Annotated[str, "analysis date in yyyy-mm-dd"],
) -> str:
    """Retrieve an ETF's latest disclosed holdings and portfolio composition.

    Holdings are current vendor data, not a point-in-time historical snapshot.
    The returned report explicitly warns when the analysis date is historical.
    """
    return route_to_vendor("get_fund_holdings", ticker, curr_date)
