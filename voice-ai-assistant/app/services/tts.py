from openai import OpenAI

client = OpenAI()


def generate_speech(text: str) -> bytes:
    response = client.audio.speech.create(
        model="gpt-4o-mini-tts", voice="coral", input=text
    )

    return response.read()
