from flask import Flask, request, Response
import os
import openai
from twilio.twiml.voice_response import VoiceResponse
from gtts import gTTS
import tempfile

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/voice", methods=["POST"])
def voice():
    speech_text = request.form.get("SpeechResult")
    response = VoiceResponse()

    if not speech_text:
        response.say("Sorry, I didn't hear anything.")
        return Response(str(response), mimetype='text/xml')

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": speech_text}
        ]
    )

    answer = completion.choices[0].message["content"]

    # Convert to speech
    tts = gTTS(answer)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        response.play(fp.name)

    return Response(str(response), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
