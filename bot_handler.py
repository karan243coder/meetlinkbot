# ============ MeetLink Bot Handler (Commands & Direct Media) ============
import os
import time
import threading
import requests
from datetime import datetime
from config import BOT_TOKEN, PORT, UPLOAD_DIR, API_ID, API_HASH, SERVER_URL
from store import file_store, active_rooms, generate_unique_id, fmt_size
from telegram_service import send_telegram_direct, pyro_client

def start_bot_handler():
    """Background polling loop allowing users to upload media or generate rooms directly from Telegram Bot."""
    offset = 0
    print("🤖 Telegram Bot Handler: Starting background command & media listener...")
    while True:
        try:
            if BOT_TOKEN == "YOUR_BOT_TOKEN_HERE" or not BOT_TOKEN:
                time.sleep(10)
                continue
            
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/getUpdates"
            res = requests.get(url, params={"offset": offset, "timeout": 20}, timeout=25)
            if res.status_code == 200:
                data = res.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    msg = update.get("message") or update.get("edited_message")
                    if not msg: continue
                    
                    chat_id = msg["chat"]["id"]
                    text = (msg.get("text") or msg.get("caption") or "").strip()
                    
                    # 1. Handle commands
                    if text.startswith("/start"):
                        send_telegram_direct(chat_id, "🚀 <b>Welcome to MeetLink Cloud Bot!</b>\n━━━━━━━━━━━━━━━━━━\n📁 <b>Direct Media Upload:</b> Just send me ANY photo, video, audio, or document directly! I will generate an instant high-speed link with 1-Hour TTL.\n🔒 <b>Password Protection:</b> Add caption <code>/pwd 1234</code> when sending media.\n🔥 <b>View Once Mode:</b> Add caption <code>/vo</code> when sending media.\n📹 <b>Create Video Room:</b> Send <code>/room</code> to generate an instant peer-to-peer WebRTC video room!")
                        continue
                    elif text.startswith("/room") or text.startswith("/create") or text.startswith("/call"):
                        room_id = generate_unique_id(7)
                        active_rooms[room_id] = {"created_at": time.time(), "expires_at": time.time() + 3600, "call_start": None, "messages": [], "files_sent": [], "participants": 0}
                        srv_url = SERVER_URL or f"http://localhost:{PORT}"
                        room_url = f"{srv_url}/?room={room_id}"
                        send_telegram_direct(chat_id, f"🟢 <b>MEETLINK VIDEO ROOM CREATED!</b>\n━━━━━━━━━━━━━━━━━━\n🆔 Room ID: <code>{room_id}</code>\n⏱️ TTL: 1 Hour (Auto-expires)\n━━━━━━━━━━━━━━━━━━\n🔗 <b>Link:</b> {room_url}\n\n👉 Share this link with anyone to start an instant peer-to-peer HD video call without login!")
                        continue
                    
                    # 2. Handle Media Uploads (Instant Direct CDN link generation without downloading to disk!)
                    media = msg.get("document") or msg.get("video") or msg.get("audio") or msg.get("voice")
                    if not media and msg.get("photo"):
                        media = msg["photo"][-1]
                    
                    if media:
                        file_id_tg = media["file_id"]
                        orig_name = media.get("file_name") or f"media_{int(time.time())}.dat"
                        file_size = media.get("file_size", 0)
                        
                        max_chat_limit = 2000 * 1024 * 1024 if ((API_ID and API_HASH) or (pyro_client and pyro_client.is_connected)) else 20 * 1024 * 1024
                        if file_size > max_chat_limit:
                            srv_url = SERVER_URL or f"http://localhost:{PORT}"
                            mode_str = "2 GB" if ((API_ID and API_HASH) or (pyro_client and pyro_client.is_connected)) else "20 MB (Standard Bot API)"
                            send_telegram_direct(chat_id, f"⚠️ <b>FILE TOO LARGE FOR BOT CHAT ({mode_str} Limit)</b>\n━━━━━━━━━━━━━━━━━━\nYour file is <b>{fmt_size(file_size)}</b>.\n\n🚀 <b>TO SHARE LARGE FILES (NO LIMIT!):</b>\nPlease upload directly on your MeetLink Website: <b>{srv_url}</b>\n\nThere is NO size limit on the website! You can upload multi-gigabyte files directly on the website and get instant high-speed View & Download links!")
                            continue
                        
                        uid = generate_unique_id(8)
                        pwd = ""
                        view_once = False
                        if "/pwd" in text or "/password" in text:
                            parts = text.split()
                            for idx, p in enumerate(parts):
                                if p in ["/pwd", "/password"] and idx + 1 < len(parts): pwd = parts[idx + 1]
                        if "/vo" in text or "/viewonce" in text: view_once = True
                        
                        file_store[uid] = {
                            "fileName": orig_name,
                            "fileSize": fmt_size(file_size),
                            "fileSizeBytes": file_size,
                            "mimeType": media.get("mime_type", "application/octet-stream"),
                            "telegram_file_id": file_id_tg,
                            "telegram_direct": True,
                            "uploaded": datetime.now().strftime("%d %b %Y, %I:%M %p"),
                            "expires_at": time.time() + 3600,
                            "password": pwd,
                            "view_once": view_once,
                            "downloads": 0
                        }
                        
                        srv_url = SERVER_URL or f"http://localhost:{PORT}"
                        share_url = f"{srv_url}/v/{uid}"
                        dl_url_clean = f"{srv_url}/d/{uid}"
                        
                        send_telegram_direct(chat_id, f"✅ <b>INSTANT CLOUD LINK GENERATED!</b>\n━━━━━━━━━━━━━━━━━━\n📄 File: <code>{orig_name}</code>\n📦 Size: {file_store[uid]['fileSize']}\n⚡ Speed: Instant Direct CDN\n🔑 Password: <b>{pwd or 'None'}</b>\n🔥 View Once: <b>{'Yes' if view_once else 'No'}</b>\n⏱️ TTL: 1 Hour\n━━━━━━━━━━━━━━━━━━\n🌐 <b>View Link:</b> {share_url}\n⬇️ <b>Direct DL:</b> {dl_url_clean}")
            time.sleep(1)
        except Exception as e:
            time.sleep(3)

threading.Thread(target=start_bot_handler, daemon=True).start()
