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
    response = VoiceResponse()
    gather = response.gather(
        input="speech",
        action="/process",
        method="POST",
        timeout=5,
        speech_timeout="auto"
    )
    gather.say("Hey, it's Joey from Air Flo Cleaning. How can I help you today?", voice="man")
    return Response(str(response), mimetype="text/xml")

@app.route("/process", methods=["POST"])
def process():
    speech_text = request.form.get("SpeechResult")
    response = VoiceResponse()

    if not speech_text:
        gather = response.gather(
            input="speech",
            action="/process",
            method="POST",
            timeout=5,
            speech_timeout="auto"
        )
        gather.say("Sorry, I didn’t hear anything. Can you repeat that?", voice="man")
        return Response(str(response), mimetype='text/xml')

    completion = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a friendly and professional phone agent working for Air Flo Cleaning. "
                    "You only handle incoming phone calls from potential customers in Tampa and Orlando. "
                    "You offer air duct and dryer vent cleaning services. The standard cleaning price is $99 per AC unit. "
                    "If the customer mentions mold or black dirt, explain that it could be mildew or bacteria and that a technician can come for a free inspection. "
                    "Never diagnose. Always ask how many units they have, if it's a home or apartment, and the zip code or address. "
                    "Let them know the technician can do both the estimate and the service on the same day. "
                    "Mention that the deep cleaning and additional services (sanitizing, UV light) will be priced on-site. "
                    "You do not schedule appointments on Saturdays and only between 9AM–6PM. "
                    "Keep the tone polite, informative, and efficient. Keep the conversation going until the caller is satisfied or ends the call."
                )
            },
            {"role": "user", "content": speech_text}
        ]
    )

    answer = completion.choices[0].message["content"]

    # Convert to speech
    tts = gTTS(answer)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        tts.save(fp.name)
        response.play(fp.name)

    # Ask follow-up question to keep call alive
    gather = response.gather(
        input="speech",
        action="/process",
        method="POST",
        timeout=5,
        speech_timeout="auto"
    )
    gather.say("Is there anything else I can help you with?", voice="man")

    return Response(str(response), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
