"""
MCP Server - AI DevOps Assistant
================================
Acest server expune tools AWS către AI Agent prin protocolul MCP (stdio).

Cum funcționează:
1. Agent-ul pornește acest server ca subprocess
2. Comunică prin stdin/stdout (stdio transport)
3. Agent-ul trimite cereri "apelează tool X cu argumente Y"
4. Server-ul execută boto3 call-ul și returnează JSON
"""

from mcp.server.fastmcp import FastMCP
from tools.ec2 import list_ec2_instances, get_ec2_metrics
from tools.s3 import list_s3_buckets
from tools.costs import get_monthly_cost
from tools.cloudwatch import get_cloudwatch_alarms

# Creăm server-ul MCP
mcp = FastMCP("ai-devops-assistant")


# ---- TOOLS ----
# Fiecare @mcp.tool() devine un tool pe care Agent-ul (Claude) îl poate apela

@mcp.tool()
def list_ec2() -> list[dict]:
    """Listează toate instanțele EC2 cu id, state, type și availability zone."""
    return list_ec2_instances()


@mcp.tool()
def list_buckets() -> list[dict]:
    """Listează toate bucket-urile S3 cu nume, regiune și public access status."""
    return list_s3_buckets()


@mcp.tool()
def monthly_cost() -> dict:
    """Returnează costul total din luna curentă în USD."""
    return get_monthly_cost()


@mcp.tool()
def cloudwatch_alarms() -> list[dict]:
    """Listează toate alarmele CloudWatch cu nume, stare și metric."""
    return get_cloudwatch_alarms()


@mcp.tool()
def ec2_metrics(instance_id: str) -> dict:
    """Returnează CPU avg, NetworkIn și NetworkOut pentru o instanță (ultimele 60 min)."""
    return get_ec2_metrics(instance_id)


# Pornește server-ul pe stdio (stdin/stdout)
if __name__ == "__main__":
    mcp.run(transport="stdio")
