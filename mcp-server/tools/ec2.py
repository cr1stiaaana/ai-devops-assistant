"""
EC2 Tools - listare instanțe și metrici
"""

import boto3
from datetime import datetime, timedelta


def list_ec2_instances() -> list[dict]:
    """
    Apelează ec2.describe_instances() și extrage info-ul relevant.
    
    Ce face boto3 aici:
    - describe_instances() returnează TOATE instanțele din regiune
    - Răspunsul e structurat ca Reservations -> Instances
    - Extragem doar câmpurile utile (id, state, type, az)
    """
    ec2 = boto3.client("ec2", region_name="eu-west-1")
    
    try:
        response = ec2.describe_instances()
    except Exception as e:
        return [{"error": True, "error_code": type(e).__name__, "error_message": str(e), "tool_name": "list_ec2"}]
    
    instances = []
    for reservation in response["Reservations"]:
        for instance in reservation["Instances"]:
            instances.append({
                "instance_id": instance["InstanceId"],
                "state": instance["State"]["Name"],
                "type": instance["InstanceType"],
                "availability_zone": instance["Placement"]["AvailabilityZone"],
            })
    
    return instances


def get_ec2_metrics(instance_id: str) -> dict:
    """
    Ia metrici CloudWatch pentru o instanță: CPU, NetworkIn, NetworkOut.
    Perioada: ultimele 60 minute, medie.
    
    Ce face:
    - get_metric_statistics() cere date de la CloudWatch
    - Period=3600 = o singură valoare medie pe toată ora
    - Statistics=["Average"] = media, nu max/min
    """
    cw = boto3.client("cloudwatch", region_name="eu-west-1")
    
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=60)
    
    try:
        # CPU Utilization
        cpu = cw.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="CPUUtilization",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"]
        )
        
        # Network In
        net_in = cw.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="NetworkIn",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"]
        )
        
        # Network Out
        net_out = cw.get_metric_statistics(
            Namespace="AWS/EC2",
            MetricName="NetworkOut",
            Dimensions=[{"Name": "InstanceId", "Value": instance_id}],
            StartTime=start_time,
            EndTime=end_time,
            Period=3600,
            Statistics=["Average"]
        )
        
        return {
            "instance_id": instance_id,
            "cpu_avg_percent": cpu["Datapoints"][0]["Average"] if cpu["Datapoints"] else 0.0,
            "network_in_bytes": int(net_in["Datapoints"][0]["Average"]) if net_in["Datapoints"] else 0,
            "network_out_bytes": int(net_out["Datapoints"][0]["Average"]) if net_out["Datapoints"] else 0,
        }
    except Exception as e:
        return {"error": True, "error_code": type(e).__name__, "error_message": str(e), "tool_name": "ec2_metrics"}
