"""
Cost Explorer Tool - costul lunii curente
"""

import boto3
from datetime import datetime


def get_monthly_cost() -> dict:
    """
    Returnează costul total al lunii curente din Cost Explorer.
    
    Ce face:
    - get_cost_and_usage() cere date de billing
    - TimePeriod: de la prima zi a lunii până azi
    - Granularity MONTHLY = un singur total pe toată luna
    - Metrics "UnblendedCost" = costul real (nu amortizat)
    
    ATENȚIE: Cost Explorer trebuie activat manual în cont (Settings → Cost Explorer)
    și are un cost de $0.01 per request.
    """
    ce = boto3.client("ce", region_name="us-east-1")  # Cost Explorer e doar în us-east-1
    
    now = datetime.utcnow()
    start_of_month = now.strftime("%Y-%m-01")
    today = now.strftime("%Y-%m-%d")
    
    try:
        response = ce.get_cost_and_usage(
            TimePeriod={"Start": start_of_month, "End": today},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"]
        )
        
        amount = response["ResultsByTime"][0]["Total"]["UnblendedCost"]["Amount"]
        
        return {
            "month": now.strftime("%Y-%m"),
            "total_cost_usd": round(float(amount), 2),
        }
    except Exception as e:
        return {"error": True, "error_code": type(e).__name__, "error_message": str(e), "tool_name": "monthly_cost"}
