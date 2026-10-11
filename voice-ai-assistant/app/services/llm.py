import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(Path(__file__).parents[1] / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_response(message: str) -> str:
    response = client.responses.create(model="gpt-4o-mini", input=message)

    return response.output_text


def stream_response(message: str):

    stream = client.responses.create(model="gpt-4o-mini", input=message, stream=True)

    for event in stream:

        # Only text deltas belong in the browser response; other events carry SDK metadata.
        if event.type == "response.output_text.delta":
            yield event.delta
