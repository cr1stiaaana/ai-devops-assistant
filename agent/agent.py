"""
AI DevOps Agent
===============
CLI care întreabă despre infrastructura AWS.

Două moduri:
1. Fără AI (direct) - parsează comenzi simple și apelează tools
2. Cu Gemini AI (gratis) - interpretare natural language

Setează GOOGLE_API_KEY pentru modul AI, altfel merge în modul direct.
"""

import sys
import os

# Adaugă mcp-server la path ca să putem importa tools direct
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "mcp-server"))

from tools.ec2 import list_ec2_instances, get_ec2_metrics
from tools.s3 import list_s3_buckets
from tools.costs import get_monthly_cost
from tools.cloudwatch import get_cloudwatch_alarms


# ---- MODUL DIRECT (fără AI) ----

HELP_TEXT = """
Comenzi disponibile:
  ec2          - Listează instanțele EC2
  s3           - Listează bucket-urile S3
  cost         - Costul lunii curente
  alarms       - Alarme CloudWatch
  metrics <id> - Metrici EC2 (CPU, network)
  help         - Afișează acest mesaj
  exit         - Ieșire
"""


def format_ec2(instances):
    if not instances:
        return "Nu am găsit instanțe EC2."
    lines = ["EC2 Instances:"]
    for i in instances:
        lines.append(f"  • {i['instance_id']} | {i['state']} | {i['type']} | {i['availability_zone']}")
    return "\n".join(lines)


def format_s3(buckets):
    if not buckets:
        return "Nu am găsit bucket-uri S3."
    lines = ["S3 Buckets:"]
    for b in buckets:
        status = "🔒 blocked" if b['public_access_blocked'] else "⚠️  public"
        lines.append(f"  • {b['bucket_name']} | {b['region']} | {status}")
    return "\n".join(lines)


def format_cost(data):
    if "error" in data:
        return f"Eroare: {data['error_message']}"
    return f"Cost {data['month']}: ${data['total_cost_usd']} USD"


def format_alarms(alarms):
    if not alarms:
        return "Nu există alarme CloudWatch configurate."
    lines = ["CloudWatch Alarms:"]
    for a in alarms:
        lines.append(f"  • {a['alarm_name']} | {a['state']} | {a['metric']}")
    return "\n".join(lines)


def format_metrics(data):
    if "error" in data:
        return f"Eroare: {data['error_message']}"
    return (f"Metrici EC2 ({data['instance_id']}) - ultimele 60 min:\n"
            f"  CPU avg: {data['cpu_avg_percent']:.2f}%\n"
            f"  Network In: {data['network_in_bytes']} bytes\n"
            f"  Network Out: {data['network_out_bytes']} bytes")


def run_direct_mode():
    """Modul fără AI - comenzi directe."""
    print("🛠️  DevOps Assistant (mod direct - fără AI)")
    print(HELP_TEXT)
    
    while True:
        try:
            user_input = input("devops> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 La revedere!")
            break
        
        if not user_input:
            continue
        if user_input in ("exit", "quit"):
            print("👋 La revedere!")
            break
        
        parts = user_input.split()
        cmd = parts[0]
        
        if cmd == "ec2":
            print(format_ec2(list_ec2_instances()))
        elif cmd == "s3":
            print(format_s3(list_s3_buckets()))
        elif cmd == "cost":
            print(format_cost(get_monthly_cost()))
        elif cmd == "alarms":
            print(format_alarms(get_cloudwatch_alarms()))
        elif cmd == "metrics":
            if len(parts) < 2:
                print("Folosire: metrics <instance-id>")
            else:
                print(format_metrics(get_ec2_metrics(parts[1])))
        elif cmd == "help":
            print(HELP_TEXT)
        else:
            print(f"Comandă necunoscută: '{cmd}'. Scrie 'help' pentru opțiuni.")
        
        print()


# ---- MODUL GEMINI (free) ----

def run_gemini_mode():
    """Modul cu Google Gemini AI - natural language."""
    import google.generativeai as genai
    
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
    
    # Definim tools ca funcții pe care Gemini le poate apela
    tools_map = {
        "list_ec2_instances": list_ec2_instances,
        "list_s3_buckets": list_s3_buckets,
        "get_monthly_cost": get_monthly_cost,
        "get_cloudwatch_alarms": get_cloudwatch_alarms,
        "get_ec2_metrics": get_ec2_metrics,
    }
    
    # Tool declarations pentru Gemini
    tool_declarations = [
        genai.protos.Tool(function_declarations=[
            genai.protos.FunctionDeclaration(
                name="list_ec2_instances",
                description="Listează toate instanțele EC2 cu id, state, type și availability zone",
                parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={}),
            ),
            genai.protos.FunctionDeclaration(
                name="list_s3_buckets",
                description="Listează toate bucket-urile S3 cu nume, regiune și public access status",
                parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={}),
            ),
            genai.protos.FunctionDeclaration(
                name="get_monthly_cost",
                description="Returnează costul total din luna curentă în USD",
                parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={}),
            ),
            genai.protos.FunctionDeclaration(
                name="get_cloudwatch_alarms",
                description="Listează toate alarmele CloudWatch",
                parameters=genai.protos.Schema(type=genai.protos.Type.OBJECT, properties={}),
            ),
            genai.protos.FunctionDeclaration(
                name="get_ec2_metrics",
                description="Returnează CPU, NetworkIn, NetworkOut pentru o instanță EC2 (ultimele 60 min)",
                parameters=genai.protos.Schema(
                    type=genai.protos.Type.OBJECT,
                    properties={"instance_id": genai.protos.Schema(type=genai.protos.Type.STRING)},
                    required=["instance_id"],
                ),
            ),
        ])
    ]
    
    model = genai.GenerativeModel(
        "gemini-2.0-flash",
        tools=tool_declarations,
        system_instruction="Ești un DevOps Assistant. Folosește tools-urile disponibile pentru a răspunde cu date reale din AWS. Răspunde concis.",
    )
    
    chat = model.start_chat()
    
    print("🤖 DevOps Assistant (Gemini AI)")
    print("   Pune o întrebare despre infrastructura ta AWS (sau 'exit'):\n")
    
    while True:
        try:
            user_input = input("Tu: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 La revedere!")
            break
        
        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("👋 La revedere!")
            break
        
        response = chat.send_message(user_input)
        
        # Procesează tool calls dacă sunt
        while response.candidates[0].content.parts:
            has_function_call = False
            for part in response.candidates[0].content.parts:
                if part.function_call:
                    has_function_call = True
                    fn_name = part.function_call.name
                    fn_args = dict(part.function_call.args) if part.function_call.args else {}
                    
                    print(f"  🔧 Apelează: {fn_name}")
                    
                    # Execută tool-ul
                    result = tools_map[fn_name](**fn_args)
                    
                    # Trimite rezultatul înapoi
                    response = chat.send_message(
                        genai.protos.Content(parts=[
                            genai.protos.Part(function_response=genai.protos.FunctionResponse(
                                name=fn_name,
                                response={"result": str(result)},
                            ))
                        ])
                    )
            
            if not has_function_call:
                break
        
        # Afișează răspunsul final
        print(f"\n🤖 {response.text}\n")


# ---- ENTRY POINT ----

if __name__ == "__main__":
    if os.environ.get("GOOGLE_API_KEY"):
        run_gemini_mode()
    else:
        print("💡 Tip: Setează GOOGLE_API_KEY pentru modul AI (Gemini, gratis)")
        print("   export GOOGLE_API_KEY='cheia-ta'")
        print("   Obține de la: https://aistudio.google.com/apikey\n")
        run_direct_mode()
