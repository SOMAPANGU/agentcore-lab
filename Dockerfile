# syntax=docker/dockerfile:1
FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY agent.py tools.py server.py ./

# AgentCore expects the container to listen on port 8080
EXPOSE 8080

# Run the AgentCore HTTP server
CMD ["python", "server.py"]
