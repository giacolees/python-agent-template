"""MCP server exposing agent-memory tools to any MCP-capable runtime.

Provides two thin tools over the shared memory core: `remember_insights`
(persist findings to the local store) and `recall` (semantic search). No LLM
runs inside the server — choosing what to remember is the caller's job.
"""

from mcp.server.fastmcp import FastMCP

from memory.cli import recall as cli_recall
from memory.insights import store_insights


def remember_insights(findings: list[str]) -> str:
    """Persist insight strings to the local agent-memory store.

    Parameters
    ----------
    findings : list[str]
        Insight strings to remember; blanks are skipped, capped at five.

    Returns
    -------
    str
        Human-readable summary of how many insights were stored.
    """
    stored = store_insights(findings)
    return f"stored {len(stored)} insight(s)"


def recall(query: str, top_k: int = 5) -> list[str]:
    """Search agent memory and return matching memory texts.

    Parameters
    ----------
    query : str
        Free-text search query.
    top_k : int, optional
        Maximum number of results, by default ``5``.

    Returns
    -------
    list[str]
        Matching memory texts, most relevant first.
    """
    return [result["memory"] for result in cli_recall(query, top_k=top_k)]


def _build_server() -> FastMCP:
    """Construct the FastMCP server with both tools registered.

    Returns
    -------
    FastMCP
        The configured server instance.
    """
    server = FastMCP("agent-memory")
    server.tool()(remember_insights)
    server.tool()(recall)
    return server


mcp = _build_server()


def main() -> None:
    """Run the agent-memory MCP server over stdio.

    Returns
    -------
    None
    """
    mcp.run()


if __name__ == "__main__":
    main()
