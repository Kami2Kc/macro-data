"""A read-only MCP server that lets an AI assistant query the macro database."""

import datetime as dt
import os

from dotenv import load_dotenv
from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from sqlalchemy import create_engine, text

load_dotenv()

engine = create_engine(os.environ["READONLY_DATABASE_URL"])
mcp = MCPServer("Macro data")


def check_request(ticker: str, start: dt.date, end: dt.date, max_days: int) -> None:
    """Reject bad requests with a message the model can act on."""
    if end < start:
        raise ToolError("end must be on or after start.")
    if (end - start).days > max_days:
        raise ToolError(
            f"That range is too long for this tool (max {max_days} days). "
            "Use get_monthly_average for long periods."
        )

    with engine.connect() as conn:
        known = conn.execute(
            text("SELECT 1 FROM series WHERE series_id = :ticker"),
            {"ticker": ticker},
        ).first()
        if known is None:
            raise ToolError(
                f"Unknown ticker {ticker!r}. Call list_series to see the options."
            )


@mcp.tool()
def list_series() -> list[dict]:
    """List every macroeconomic series in the database."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT series_id AS ticker, name, frequency, unit
                FROM series
                ORDER BY series_id
                """
            )
        )
        return [dict(row._mapping) for row in rows]


@mcp.tool()
def get_series(ticker: str, start: dt.date, end: dt.date) -> list[dict]:
    """Return every observation of one series between two dates, inclusive."""
    check_request(ticker, start, end, max_days=366)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT obs_date, value
                FROM observation
                WHERE series_id = :ticker
                  AND obs_date BETWEEN :start AND :end
                ORDER BY obs_date
                """
            ),
            {"ticker": ticker, "start": start, "end": end},
        )
        return [
            {
                "date": row.obs_date.isoformat(),
                "value": None if row.value is None else float(row.value),
            }
            for row in rows
        ]


@mcp.tool()
def get_monthly_average(ticker: str, start: dt.date, end: dt.date) -> list[dict]:
    """Return one series' average value for each month between two dates."""
    check_request(ticker, start, end, max_days=30 * 366)

    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT
                    DATE_TRUNC('month', obs_date)::date AS month,
                    AVG(value) AS avg_value
                FROM observation
                WHERE series_id = :ticker
                  AND obs_date BETWEEN :start AND :end
                GROUP BY 1
                ORDER BY 1
                """
            ),
            {"ticker": ticker, "start": start, "end": end},
        )
        return [
            {
                "month": row.month.isoformat()[:7],
                "average": None if row.avg_value is None else round(float(row.avg_value), 3),
            }
            for row in rows
        ]


if __name__ == "__main__":
    mcp.run()
