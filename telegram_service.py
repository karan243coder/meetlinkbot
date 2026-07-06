# ============ MeetLink Telegram MTProto Service ============
import os
import time
import threading
import requests
from config import BOT_TOKEN, CHANNEL_ID, API_ID, API_HASH
from store import fmt_size

pyro_client = None

def start_pyrogram_engine():
    global pyro_client
    try:
        if API_ID and API_HASH and BOT_TOKEN != "YOUR_BOT_TOKEN_HERE":
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            from pyrogram import Client
            pyro_client = Client("meetlink_mtproto", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
            pyro_client.start()
            print("🚀 [Pyrogram MTProto Engine] 2GB Direct Streaming & No-Split Uploads ACTIVATED!")
            loop.run_forever()
    except Exception as e:
        print(f"⚠️ [Pyrogram Note] Running in standard HTTP Bot API mode: {e}")

threading.Thread(target=start_pyrogram_engine, daemon=True).start()

def send_telegram_direct(chat_id, text):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}, timeout=10)
    except: pass

def send_telegram_message(text):
    send_telegram_direct(CHANNEL_ID, text)

def split_large_file(file_path, max_size=45*1024*1024):
    """Split a file into sub-parts of max_size."""
    parts = []
    file_size = os.path.getsize(file_path)
    if file_size <= max_size:
        return [file_path]

    total_parts = (file_size + max_size - 1) // max_size
    with open(file_path, 'rb') as f:
        for i in range(total_parts):
            part_path = f"{file_path}.part{i+1}"
            chunk = f.read(max_size)
            with open(part_path, 'wb') as pf:
                pf.write(chunk)
            parts.append(part_path)
    return parts

def send_telegram_file_smart(file_path, caption, is_video=False):
    """Smart Telegram Upload: Pyrogram MTProto (up to 1.9GB single complete file without split, auto-splits above 1.9GB) or HTTP Bot API."""
    try:
        import asyncio
        try:
            asyncio.get_event_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

        file_size = os.path.getsize(file_path)
        original_name = os.path.basename(file_path)
        
        # 1. MTProto Pyrogram Engine (2GB Limit per file)
        if pyro_client and pyro_client.is_connected:
            max_chunk_size = 1900 * 1024 * 1024  # 1.9 GB pro chunks
            if file_size <= max_chunk_size:
                print(f"🚀 [Pyrogram Upload] Sending full {fmt_size(file_size)} file as single unit without split!")
                if is_video and file_path.endswith(".mp4"):
                    pyro_client.send_video(chat_id=CHANNEL_ID, video=file_path, caption=caption, supports_streaming=True)
                else:
                    pyro_client.send_document(chat_id=CHANNEL_ID, document=file_path, caption=caption)
            else:
                send_telegram_message(f"📦 <b>MASSIVE FILE ({fmt_size(file_size)}) -> 2GB MTPROTO AUTO-SPLIT</b>\n📄 File: <code>{original_name}</code>\nSplitting into 1.9 GB pro-level parts...")
                parts = split_large_file(file_path, max_size=max_chunk_size)
                for i, part_path in enumerate(parts):
                    part_cap = f"📁 Part {i+1}/{len(parts)} (Pro 2GB Engine) of <code>{original_name}</code>\n{caption}"
                    pyro_client.send_document(chat_id=CHANNEL_ID, document=part_path, caption=part_cap)
                    try: os.remove(part_path)
                    except: pass
                send_telegram_message(f"✅ Pro 2GB Backup complete for: <code>{original_name}</code> ({len(parts)} parts sent)")
            return True

        # 2. Standard HTTP Bot API Fallback (50MB Limit per file)
        else:
            if file_size <= 45 * 1024 * 1024:
                with open(file_path, 'rb') as tf:
                    if is_video and file_path.endswith(".mp4"):
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendVideo", files={"video": (original_name, tf)}, data={"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML", "supports_streaming": True}, timeout=180)
                    else:
                        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", files={"document": (original_name, tf)}, data={"chat_id": CHANNEL_ID, "caption": caption, "parse_mode": "HTML"}, timeout=120)
            else:
                send_telegram_message(f"📦 <b>LARGE FILE ({fmt_size(file_size)}) -> HTTP 45MB AUTO-SPLIT</b>\n📄 File: <code>{original_name}</code>\nSplitting into 45 MB parts...")
                parts = split_large_file(file_path, max_size=45*1024*1024)
                for i, part_path in enumerate(parts):
                    part_cap = f"📁 Part {i+1}/{len(parts)} of <code>{original_name}</code>\n{caption}"
                    try:
                        with open(part_path, 'rb') as tf:
                            requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendDocument", files={"document": (f"{original_name}.part{i+1}", tf)}, data={"chat_id": CHANNEL_ID, "caption": part_cap, "parse_mode": "HTML"}, timeout=180)
                    except Exception as e: print(f"❌ Part upload error: {e}")
                    finally:
                        try: os.remove(part_path)
                        except: pass
                send_telegram_message(f"✅ Backup complete for: <code>{original_name}</code> ({len(parts)} parts sent)")
            return True
    except Exception as e:
        print(f"❌ Smart Telegram upload error: {e}")
        return False
