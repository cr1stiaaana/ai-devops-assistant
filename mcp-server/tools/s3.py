"""
S3 Tool - listare buckets cu public access status
"""

import boto3


def list_s3_buckets() -> list[dict]:
    """
    Listează toate S3 buckets și verifică dacă au Block Public Access activat.
    
    Ce face:
    - list_buckets() = toate bucket-urile din cont
    - get_public_access_block() per bucket = verifică dacă accesul public e blocat
    - Dacă get_public_access_block dă eroare = probabil nu e configurat (nu e blocat)
    """
    s3 = boto3.client("s3", region_name="eu-west-1")
    
    try:
        response = s3.list_buckets()
    except Exception as e:
        return [{"error": True, "error_code": type(e).__name__, "error_message": str(e), "tool_name": "list_buckets"}]
    
    buckets = []
    for bucket in response["Buckets"]:
        bucket_name = bucket["Name"]
        
        # Verifică Block Public Access
        try:
            pab = s3.get_public_access_block(Bucket=bucket_name)
            public_access_blocked = all([
                pab["PublicAccessBlockConfiguration"]["BlockPublicAcls"],
                pab["PublicAccessBlockConfiguration"]["IgnorePublicAcls"],
                pab["PublicAccessBlockConfiguration"]["BlockPublicPolicy"],
                pab["PublicAccessBlockConfiguration"]["RestrictPublicBuckets"],
            ])
        except Exception:
            public_access_blocked = False
        
        # Verifică regiunea bucket-ului
        try:
            loc = s3.get_bucket_location(Bucket=bucket_name)
            region = loc["LocationConstraint"] or "us-east-1"
        except Exception:
            region = "unknown"
        
        buckets.append({
            "bucket_name": bucket_name,
            "region": region,
            "public_access_blocked": public_access_blocked,
        })
    
    return buckets
