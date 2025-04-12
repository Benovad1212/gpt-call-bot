from flask import Flask, request, Response
import os
import openai
from twilio.twiml.voice_response import VoiceResponse
import re

app = Flask(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")

conversation_state = {}

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
    gather.say("Hey, it’s Joey from Air Flo Cleaning. How can I help you today?", voice="man")
    return Response(str(response), mimetype="text/xml")

@app.route("/process", methods=["POST"])
def process():
    speech_text = request.form.get("SpeechResult")
    call_sid = request.form.get("CallSid")
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

    # Track conversation state by call SID
    if call_sid not in conversation_state:
        conversation_state[call_sid] = {}

    convo = conversation_state[call_sid]
    convo['last_input'] = speech_text

    # Basic extraction with regex for key details
    if 'zip' not in convo:
        zip_match = re.search(r'\b(\d{5})\b', speech_text)
        if zip_match:
            convo['zip'] = zip_match.group(1)

    if 'units' not in convo:
        units_match = re.search(r'(\d+)\s?(units?|AC|air)', speech_text, re.IGNORECASE)
        if units_match:
            convo['units'] = units_match.group(1)

    if 'type' not in convo:
        if "house" in speech_text.lower():
            convo['type'] = "house"
        elif "apartment" in speech_text.lower():
            convo['type'] = "apartment"

    if 'time' not in convo:
        if any(word in speech_text.lower() for word in ["morning", "afternoon", "evening"]):
            convo['time'] = speech_text

    if all(k in convo for k in ["zip", "units", "type", "time"]):
        response.say(f"Perfect. I’ve scheduled you for a free estimate at your {convo['type']} with {convo['units']} unit(s) in zip code {convo['zip']} during the {convo['time']}. We’ll see you then!", voice="man")
        conversation_state.pop(call_sid, None)
    else:
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
                            "Your goal is to collect the following details to schedule a free estimate: number of AC units, zip code, home type (house/apartment), and a preferred time (morning, afternoon, or evening). "
                            "Once you have all details, confirm the appointment. Keep the tone warm, casual and helpful."
                        )
                    },
                    {"role": "user", "content": speech_text}
                ]
            )
            answer = completion.choices[0].message["content"]
            response.say(answer, voice="man")
        except:
            response.say("Something went wrong while processing your request. Please try again.", voice="man")

        gather = response.gather(
            input="speech",
            action="/process",
            method="POST",
            timeout=5,
            speech_timeout="auto"
        )
        gather.say("Is there anything else you’d like me to note?", voice="man")

    return Response(str(response), mimetype='text/xml')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
