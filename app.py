import os
from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from flask_cors import CORS
import asyncio

app = Flask(__name__)
CORS(app)

# ==========================================
# 👇 RENDER CONFIGURATION 👇
# We get these values from Render's "Environment Variables" section
# This keeps your keys secure and allows the code to run in the cloud.

# 1. API ID (Must be an integer)
api_id = os.environ.get('39075546')
if api_id:
    api_id = int(api_id)

# 2. API HASH
api_hash = os.environ.get('7f3c6f5a4102feb04019f2998348d29f')

# 3. SESSION STRING
session_string = os.environ.get('1BVtsOIQBu7rejII9bVEvOtgmyr6ZwNFH7qmSHEr23IghEQPklhOle8h25lW2owtTA6EjFaYmDt3SDOMcsriQtKtRfyVcCXXWhnU9Cw0bncGiyhnuTO3mZvzykvvMsw3K8AW88_Str11Ni5FayPFXstvmioFy86d56K_ZUnhZu77WLWcjqgntB1HO5CbKpcPwUjqybcTaYWF6gRLw7u6LPexT24GkHyuSWH43_kWG3-dVVTTF_z5Skt5sxzGSb5k5i69nyzPRUE8DAx4NQaorLwbq_EdAhHK8CiaRvJAIQ3Iih--ZoJPsI4USzZ-PjROKhlOlLCgOGPFubmV5KXQqr384ZgQ5gnQ=')
# ==========================================

# Initialize Loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Connect to Telegram
# We check if keys exist to prevent crashing during the build process
if api_id and api_hash and session_string:
    client = TelegramClient(StringSession(session_string), api_id, api_hash, loop=loop)
    client.start()
else:
    print("⚠️ WARNING: Credentials missing. This is normal during the 'Build' phase on Render.")

async def get_channel_messages(channel_link, keyword):
    if not client.is_connected():
        await client.connect()
        
    # Resolve channel (handle both t.me/links and usernames)
    channel_username = channel_link.split('/')[-1] if 't.me/' in channel_link else channel_link
    entity = await client.get_entity(channel_username)
    
    messages = []
    # Fetch last 100 messages
    async for message in client.iter_messages(entity, limit=100):
        if message.text and keyword.lower() in message.text.lower():
            messages.append({
                'id': message.id,
                'date': str(message.date),
                'text': message.text
            })
    return messages

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    channel_link = data.get('channel_link')
    keyword = data.get('keyword')

    if not channel_link or not keyword:
        return jsonify({'error': 'Missing data'}), 400

    try:
        # Run the async telethon function
        messages = loop.run_until_complete(get_channel_messages(channel_link, keyword))
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Render assigns a port automatically via the PORT environment variable
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)