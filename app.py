import os
import mimetypes
from flask import Flask, request, jsonify
from telethon import TelegramClient
from telethon.sessions import StringSession
from flask_cors import CORS
import asyncio

app = Flask(__name__, static_folder='static')
CORS(app)

# ==========================================
# 👇 CONFIGURATION 👇
# Get keys from Environment Variables (Render)
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
session_string = os.environ.get('SESSION_STRING')

# Convert API_ID to integer if it exists
if api_id:
    try:
        api_id = int(api_id)
    except ValueError:
        print("❌ ERROR: API_ID must be a number.")
        api_id = None
# ==========================================

# Create download folder
DOWNLOAD_FOLDER = 'static/media'
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)

# Initialize Loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Initialize Client variable as None first
client = None

# Attempt to connect
if api_id and api_hash and session_string:
    try:
        client = TelegramClient(StringSession(session_string), api_id, api_hash, loop=loop)
        client.start()
        print("✅ Telegram Client Started Successfully!")
    except Exception as e:
        print(f"❌ Failed to start Telegram Client: {e}")
else:
    print("⚠️ WARNING: Missing Credentials! 'client' was not created.")
    print(f"   API_ID: {api_id} (Needs to be int)")
    print(f"   API_HASH: {'Found' if api_hash else 'Missing'}")
    print(f"   SESSION_STRING: {'Found' if session_string else 'Missing'}")

async def get_channel_messages(channel_link, keyword):
    # 👇 SAFETY CHECK: If client is not defined, stop here.
    if client is None:
        raise Exception("Server Error: Telegram Client is not active. Check server logs for missing credentials.")

    if not client.is_connected():
        await client.connect()
        
    # Resolve channel
    channel_username = channel_link.split('/')[-1] if 't.me/' in channel_link else channel_link
    entity = await client.get_entity(channel_username)
    
    messages = []
    
    # Iterate through messages
    async for message in client.iter_messages(entity, limit=30):
        if message.text and keyword.lower() in message.text.lower():
            
            msg_data = {
                'id': message.id,
                'date': str(message.date),
                'text': message.text,
                'media_type': None,
                'media_url': None
            }

            if message.media:
                try:
                    path = await client.download_media(message, file=DOWNLOAD_FOLDER)
                    if path:
                        filename = os.path.basename(path)
                        # We use /static/media/filename for the URL
                        msg_data['media_url'] = f'/static/media/{filename}'
                        
                        mime_type, _ = mimetypes.guess_type(path)
                        if mime_type:
                            if 'image' in mime_type: msg_data['media_type'] = 'image'
                            elif 'video' in mime_type: msg_data['media_type'] = 'video'
                            elif 'audio' in mime_type: msg_data['media_type'] = 'audio'
                            else: msg_data['media_type'] = 'file'
                        else:
                            msg_data['media_type'] = 'file'
                except Exception as e:
                    print(f"Error downloading media: {e}")

            messages.append(msg_data)
            
    return messages

@app.route('/analyze', methods=['POST'])
def analyze():
    data = request.json
    channel_link = data.get('channel_link')
    keyword = data.get('keyword')

    if not channel_link or not keyword:
        return jsonify({'error': 'Missing data'}), 400

    try:
        # Check client again before running async loop
        if client is None:
            return jsonify({'error': 'Server Configuration Error: Telegram keys are missing.'}), 500

        messages = loop.run_until_complete(get_channel_messages(channel_link, keyword))
        return jsonify({'messages': messages})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
