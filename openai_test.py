from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-5-mini",
    tools=[
        {
            "type": "web_search"
        }
    ],
    input=(
        "Search the web for today's important IT news. "
        "Summarize the top five developments for a non-technical audience. "
        "Include the source citations."
    ),
)


print(response.output_text)  