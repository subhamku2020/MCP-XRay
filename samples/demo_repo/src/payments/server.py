from fastmcp import FastMCP
import requests

mcp = FastMCP("payments-mcp")


@mcp.tool(
    name="create_refund",
    annotations={
        "permission": "payments.refund.create",
        "action": "create",
        "resource": "refund",
        "risk": "high",
    },
)
def create_refund(customer_id: str, amount: float):
    """Create a customer refund."""
    return requests.post("https://payments.example.com/refunds", json={
        "customer_id": customer_id,
        "amount": amount,
    }).json()


@mcp.tool()
def read_refund(refund_id: str):
    """Read refund status."""
    return requests.get(f"https://payments.example.com/refunds/{refund_id}").json()


@mcp.tool()
def cancel_refund(refund_id: str):
    """Cancel an existing refund."""
    return requests.delete(f"https://payments.example.com/refunds/{refund_id}").json()
