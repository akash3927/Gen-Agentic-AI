from openai import OpenAI

client = OpenAI()


def transcribe_audio(audio_file) -> str:
    transcription = client.audio.transcriptions.create(
        model="gpt-4o-transcribe", file=audio_file
    )

    return transcription.text
