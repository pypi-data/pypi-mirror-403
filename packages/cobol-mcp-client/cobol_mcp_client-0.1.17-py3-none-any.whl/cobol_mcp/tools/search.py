import os
import httpx

DEFAULT_API_URL = "https://cobol-mcp-backend.onrender.com"
MAX_RESULT_LENGTH = 8000

try:
    SEARCH_TIMEOUT = float(os.environ.get("COBOL_MCP_SEARCH_TIMEOUT", "30.0"))
except (ValueError, TypeError):
    SEARCH_TIMEOUT = 30.0


async def search(query: str, top_k: int = 8) -> str:
    api_key = os.environ.get("COBOL_MCP_API_KEY")
    api_url = os.environ.get("COBOL_MCP_API_URL", DEFAULT_API_URL).rstrip("/")

    if not api_key:
        return "Search is not configured. Set COBOL_MCP_API_KEY environment variable."

    if not isinstance(top_k, int) or top_k < 1:
        top_k = 1
    top_k = min(top_k, 20)

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{api_url}/search",
                json={"query": query, "top_k": top_k},
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=SEARCH_TIMEOUT,
            )
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                return "Authentication failed. Check your COBOL_MCP_API_KEY."
            return f"Search API error: {e.response.status_code}"
        except httpx.RequestError as e:
            return f"Search API connection error: {e}"

        try:
            payload = resp.json()
        except ValueError as e:
            return f"Search API returned invalid JSON: {e}"

        if not isinstance(payload, dict):
            return "Search API returned unexpected response shape."

        results = payload.get("results") or []
        if not isinstance(results, list):
            return "Search API returned unexpected 'results' shape."

    if not results:
        return f"No results found for: {query}"

    return _format_results(query, results)


def _format_results(query: str, results: list[dict]) -> str:
    lines = [f"## Search results for: {query}\n"]
    total_len = 0

    for i, r in enumerate(results, 1):
        title = r.get("title", "Untitled")
        source = r.get("source", "unknown")
        text = r.get("chunk_text", r.get("text", ""))
        score = r.get("score", 0)

        if len(text) > MAX_RESULT_LENGTH:
            text = text[:MAX_RESULT_LENGTH] + "\n[...truncated]"

        chunk = f"### {i}. {title} (source: {source}, score: {score:.2f})\n{text.strip()}\n"

        if total_len + len(chunk) > 16000 and i > 1:
            lines.append(f"\n[...{len(results) - i + 1} more results truncated]")
            break

        lines.append(chunk)
        total_len += len(chunk)

    return "\n".join(lines)
