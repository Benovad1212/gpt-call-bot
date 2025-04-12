
from flask import Flask, request, Response
import openai
import os
from twilio.twiml.voice_response import VoiceResponse
from gtts import gTTS
import tempfile

app = Flask(__name__)

openai.api_key = os.getenv("OPENAI_API_KEY")

@app.route("/voice", methods=["POST"])
def voice():
    speech_text = request.form.get("SpeechResult")
    if not speech_text:
        response = VoiceResponse()
        response.say("Sorry, I did not hear anything.")
        return Response(str(response), mimetype='text/xml')

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "system", "content": "You are a helpful assistant."},
                  {"role": "user", "content": speech_text}]
    )

    reply_text = completion['choices'][0]['message']['content']

    response = VoiceResponse()
    response.say(reply_text)
    return Response(str(response), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
