"""
AI DevOps Agent
===============
CLI care întreabă despre infrastructura AWS.

Două moduri:
1. Fără AI (direct) - parsează comenzi simple și apelează tools
2. Cu Groq AI (gratis) - interpretare natural language via Llama 3

Setează GROQ_API_KEY pentru modul AI, altfel merge în modul direct.
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
    if isinstance(instances[0], dict) and instances[0].get("error"):
        return f"Eroare EC2: {instances[0]['error_message']}"
    lines = ["EC2 Instances:"]
    for i in instances:
        lines.append(f"  • {i['instance_id']} | {i['state']} | {i['type']} | {i['availability_zone']}")
    return "\n".join(lines)


def format_s3(buckets):
    if not buckets:
        return "Nu am găsit bucket-uri S3."
    if isinstance(buckets[0], dict) and buckets[0].get("error"):
        return f"Eroare S3: {buckets[0]['error_message']}"
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
    if isinstance(alarms[0], dict) and alarms[0].get("error"):
        return f"Eroare CloudWatch: {alarms[0]['error_message']}"
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


# ---- MODUL GROQ (free) ----

def run_groq_mode():
    """Modul cu Groq AI - natural language via Llama 3."""
    from openai import OpenAI
    import json

    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )

    tools_map = {
        "list_ec2_instances": list_ec2_instances,
        "list_s3_buckets": list_s3_buckets,
        "get_monthly_cost": get_monthly_cost,
        "get_cloudwatch_alarms": get_cloudwatch_alarms,
        "get_ec2_metrics": get_ec2_metrics,
    }

    # Tool definitions in OpenAI format
    tool_definitions = [
        {
            "type": "function",
            "function": {
                "name": "list_ec2_instances",
                "description": "Listează toate instanțele EC2 cu id, state, type și availability zone",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "list_s3_buckets",
                "description": "Listează toate bucket-urile S3 cu nume, regiune și public access status",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_monthly_cost",
                "description": "Returnează costul total din luna curentă în USD",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_cloudwatch_alarms",
                "description": "Listează toate alarmele CloudWatch cu nume, stare și metric",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_ec2_metrics",
                "description": "Returnează CPU avg, NetworkIn și NetworkOut pentru o instanță EC2 (ultimele 60 min)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "instance_id": {"type": "string", "description": "ID-ul instanței EC2"}
                    },
                    "required": ["instance_id"],
                },
            },
        },
    ]

    messages = [
        {"role": "system", "content": (
            "Ești un DevOps Assistant. Folosește tools-urile disponibile pentru a răspunde cu date reale din AWS.\n"
            "Reguli:\n"
            "1. Pentru întrebări generale (ex: 'ec2', 's3') apelează DOAR tool-ul relevant (list_ec2 sau list_s3) - NU apela alte tools.\n"
            "2. Răspunde concis: arată doar un rezumat scurt (câte instanțe sunt, câte active/oprite, sau câte bucket-uri).\n"
            "3. La final întreabă ÎNTOTDEAUNA: 'Dorești mai multe detalii?'\n"
            "4. Apelează tools suplimentare (metrics, alarms, costs) DOAR dacă utilizatorul cere explicit mai multe detalii.\n"
            "5. Nu repeta apeluri la același tool în aceeași conversație dacă datele nu s-au schimbat."
        )}
    ]

    print("🤖 DevOps Assistant (Groq AI - Llama 3)")
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

        messages.append({"role": "user", "content": user_input})

        # Loop pentru tool calling (max 5 runde)
        tool_rounds = 0
        while tool_rounds < 5:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                tools=tool_definitions,
                tool_choice="auto",
            )

            msg = response.choices[0].message
            messages.append(msg)

            if msg.tool_calls:
                tool_rounds += 1
                for tool_call in msg.tool_calls:
                    fn_name = tool_call.function.name
                    fn_args = json.loads(tool_call.function.arguments) if tool_call.function.arguments and tool_call.function.arguments.strip() != "null" else {}

                    result = tools_map[fn_name](**fn_args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    })
            else:
                # No tool calls - print final response
                print(f"\n🤖 {msg.content}\n")
                break
        else:
            # Hit the limit - force a response without tools
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
            )
            print(f"\n🤖 {response.choices[0].message.content}\n")


# ---- ENTRY POINT ----

if __name__ == "__main__":
    if os.environ.get("GROQ_API_KEY"):
        run_groq_mode()
    else:
        print("💡 Tip: Setează GROQ_API_KEY pentru modul AI (Groq, gratis)")
        print("   export GROQ_API_KEY='cheia-ta'")
        print("   Obține de la: https://console.groq.com\n")
        run_direct_mode()
