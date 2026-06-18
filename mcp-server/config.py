"""
Configuration module - Secret retrieval with environment variable precedence.

LOGICA:
1. Verifică mai întâi environment variables (au prioritate maximă)
2. Dacă nu există env var, încearcă SSM Parameter Store
3. Dacă niciunul nu are valoarea, termină cu eroare explicită

DE CE env vars au prioritate?
- În Docker/CodeBuild, secrets se pasează ca env vars
- SSM e fallback-ul pentru runtime pe EC2 (unde secrets sunt stocate securizat)
- Env vars permit override rapid fără a modifica SSM
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError


def get_secret(key: str, ssm_path: str | None = None, required: bool = True) -> str | None:
    """
    Recuperează un secret din env var sau SSM Parameter Store.
    
    Args:
        key: Numele environment variable-ei (ex: "AWS_DEFAULT_REGION")
        ssm_path: Calea SSM Parameter Store (ex: "/ai-devops-assistant/aws-region")
        required: Dacă True și secretul lipsește, termină procesul
    
    Returns:
        Valoarea secretului sau None dacă nu e required
    """
    # PASUL 1: Verifică environment variable (prioritate maximă)
    value = os.environ.get(key)
    if value:
        return value
    
    # PASUL 2: Încearcă SSM Parameter Store (fallback)
    if ssm_path:
        try:
            ssm = boto3.client("ssm", region_name=os.environ.get("AWS_DEFAULT_REGION", "eu-west-1"))
            response = ssm.get_parameter(Name=ssm_path, WithDecryption=True)
            return response["Parameter"]["Value"]
        except ClientError as e:
            # SSM nu a găsit parametrul - continuă la pasul 3
            pass
        except Exception:
            # Orice altă eroare (network, permissions) - continuă la pasul 3
            pass
    
    # PASUL 3: Secretul nu există nicăieri
    if required:
        print(f"ERROR: Required configuration '{key}' not found in environment variables"
              f"{f' or SSM path {ssm_path}' if ssm_path else ''}. "
              f"Cannot start server.", file=sys.stderr)
        sys.exit(1)
    
    return None


def load_config() -> dict:
    """
    Încarcă toată configurația necesară pentru MCP Server.
    
    Returnează un dict cu:
        - aws_region: regiunea AWS
        - anthropic_api_key: cheia API Anthropic (opțional pentru MCP server)
    """
    config = {
        "aws_region": get_secret(
            key="AWS_DEFAULT_REGION",
            ssm_path="/ai-devops-assistant/aws-region",
            required=True
        ),
    }
    return config
