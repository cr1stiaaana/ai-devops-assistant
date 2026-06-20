FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies 
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app code
COPY agent/ ./agent
COPY mcp-server/ ./mcp-server

#AWS Credentials passed as env vars at runtime
ENV AWS_DEFAULT_REGION=eu-west-1

# Run the agent
CMD ["python", "agent/agent.py"]

