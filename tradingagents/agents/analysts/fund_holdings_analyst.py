from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from tradingagents.agents.utils.agent_utils import (
    get_fund_holdings,
    get_instrument_context_from_state,
    get_language_instruction,
)


def create_fund_holdings_analyst(llm):
    """Create the ETF-only analyst that evaluates portfolio composition."""

    def fund_holdings_analyst_node(state):
        current_date = state["trade_date"]
        instrument_context = get_instrument_context_from_state(state)
        tools = [get_fund_holdings]

        system_message = (
            "You are an ETF fund-holdings analyst. You must call `get_fund_holdings` "
            "for the exact ETF ticker before drawing conclusions. Analyze the latest "
            "available portfolio disclosure: top-holding concentration, sector and asset "
            "allocation, issuer/category, expense ratio and turnover, equity style or bond "
            "credit characteristics, and diversification risks. Quantify concentration when "
            "the returned data permits it. Clearly identify missing fields and never invent "
            "holdings. Yahoo holdings are latest-disclosed data, not a historical point-in-time "
            "snapshot; if the requested analysis date is earlier than the retrieval date, label "
            "the data as current supplemental context and do not imply it was known then. "
            "Conclude with actionable ETF-specific risks and strengths, followed by a concise "
            "Markdown table of the key exposures."
            + get_language_instruction()
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant collaborating with other investment analysts. "
                    "Use the provided tools to make evidence-based progress. You have access to: "
                    "{tool_names}. Today's date is {current_date}; treat it as the requested analysis "
                    "date. {instrument_context}\n{system_message}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        ).partial(
            system_message=system_message,
            tool_names=", ".join(tool.name for tool in tools),
            current_date=current_date,
            instrument_context=instrument_context,
        )

        result = (prompt | llm.bind_tools(tools)).invoke(state["messages"])
        report = result.content if not result.tool_calls else ""
        return {"messages": [result], "fund_holdings_report": report}

    return fund_holdings_analyst_node
