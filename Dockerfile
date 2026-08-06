FROM public.ecr.aws/docker/library/python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ai_news_agent.py .

EXPOSE 8080

CMD ["python", "ai_news_agent.py"]
