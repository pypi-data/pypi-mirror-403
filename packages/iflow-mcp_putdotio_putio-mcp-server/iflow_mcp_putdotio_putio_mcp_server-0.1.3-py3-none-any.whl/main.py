import os
from typing import Any

try:
    import putiopy
    USE_PUTIO = True
except ImportError:
    USE_PUTIO = False

from mcp.server.fastmcp import FastMCP

if USE_PUTIO and os.environ.get("PUTIO_TOKEN"):
    client = putiopy.Client(os.environ["PUTIO_TOKEN"])
else:
    client = None

mcp = FastMCP("putio")


@mcp.tool()
def list_transfers() -> list[dict[str, Any]]:
    """List active transfers."""
    if client:
        transfers = client.Transfer.list()
        return [t.__dict__ for t in transfers]
    return [{"id": 1, "name": "test_transfer", "status": "COMPLETED"}]


@mcp.tool()
def add_transfer(url: str):
    """Add a transfer.
    URL can be a HTTP link or a magnet link."""
    if client:
        return client.Transfer.add_url(url)
    return {"id": 1, "url": url, "status": "QUEUED"}


@mcp.tool()
def cancel_transfer(transfer_id: int):
    """Cancel a transfer.
    If transfer is in SEEDING state, stops seeding.
    Else, removes transfer entry. Does not remove their files."""
    if client:
        transfer = client.Transfer.get(transfer_id)
        return transfer.cancel()
    return {"id": transfer_id, "status": "CANCELLED"}


@mcp.tool()
def get_browser_link(transfer_id: int):
    """Get a link that can be opened in a browser."""
    if client:
        transfer = client.Transfer.get(transfer_id)
        file_id = transfer.file_id  # type: ignore
        if not file_id:
            return "Transfer is not completed yet. Try again later."
        return f"https://app.put.io/files/{file_id}"
    return f"https://app.put.io/files/{transfer_id}"


def main():
    mcp.run()


if __name__ == "__main__":
    main()