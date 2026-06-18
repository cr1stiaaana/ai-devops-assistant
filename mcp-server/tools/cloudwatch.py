"""
CloudWatch Tool - listare alarme
"""

import boto3


def get_cloudwatch_alarms() -> list[dict]:
    """
    Listează toate alarmele CloudWatch din regiune.
    
    Ce face:
    - describe_alarms() returnează toate alarmele configurate
    - Extragem: nume, stare (OK/ALARM/INSUFFICIENT_DATA), metric monitorizat
    """
    cw = boto3.client("cloudwatch", region_name="eu-west-1")
    
    try:
        response = cw.describe_alarms()
    except Exception as e:
        return [{"error": True, "error_code": type(e).__name__, "error_message": str(e), "tool_name": "cloudwatch_alarms"}]
    
    alarms = []
    for alarm in response["MetricAlarms"]:
        alarms.append({
            "alarm_name": alarm["AlarmName"],
            "state": alarm["StateValue"],
            "metric": alarm["MetricName"],
        })
    
    return alarms
