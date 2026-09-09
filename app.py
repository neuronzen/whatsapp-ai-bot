import os
import requests
from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Environment Variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_secret_token")

# Gemini Config
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

@app.route('/webhook', methods=['GET'])
def verify():
    mode = request.args.get('hub.mode')
    token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge, 200
    return 'Forbidden', 403

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.get_json()
    try:
        if data.get('entry') and data['entry'][0].get('changes'):
            value = data['entry'][0]['changes'][0]['value']
            if 'messages' in value:
                message = value['messages'][0]
                from_number = message['from']
                msg_body = message.get('text', {}).get('body', '')

                if msg_body:
                    # AI prompt
                    prompt = f"You are a helpful AI replying on WhatsApp. Reply naturally and concisely in the same language as the user: {msg_body}"
                    response = model.generate_content(prompt)
                    ai_reply = response.text

                    send_whatsapp_msg(from_number, ai_reply)
    except Exception as e:
        print("Error:", e)
    return jsonify({"status": "ok"}), 200

def send_whatsapp_msg(phone_number, text):
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        "type": "text",
        "text": {"body": text}
    }
    requests.post(url, json=payload, headers=headers)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))

