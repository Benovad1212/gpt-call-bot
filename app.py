from flask import Flask, request, Response
import os
import openai
from twilio.twiml.voice_response import VoiceResponse

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

    if not speech_text or speech_text.strip() == "":
        gather = response.gather(
            input="speech",
            action="/process",
            method="POST",
            timeout=5,
            speech_timeout="auto"
        )
        gather.say("I didn’t catch that. Can you say it again, maybe a bit slower?", voice="man")
        return Response(str(response), mimetype='text/xml')

    # Echo what the user said
    response.say(f"You said: {speech_text}", voice="man")

    try:
        completion = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are Joey, a friendly and professional phone agent working for Air Flo Cleaning. "
                        "You help customers in Tampa and Orlando with air duct and dryer vent cleaning. "
                        "The standard cleaning price is $99 per AC unit. "
                        "If the customer mentions mold or mildew, let them know a technician can visit for a free inspection. "
                        "Always ask how many units they have, if it's a house or apartment, and their zip code. "
                        "Tell them service can often be done the same day. "
                        "You do not book appointments on Saturdays. Working hours are 9 AM to 6 PM. "
                        "Keep the tone polite, efficient, and helpful."
                    )
                },
                {"role": "user", "content": speech_text}
            ]
        )

        answer = completion.choices[0].message["content"]
        response.say(answer, voice="man")

    except Exception as e:
        response.say("Sorry, there was a problem processing your request. Please try again later.", voice="man")

    # Keep the conversation going
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
