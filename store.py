# ============ MeetLink Central State & TTL Engine ============
import os
import time
import random
import string
import threading
from config import UPLOAD_DIR, RECORDING_DIR

file_store = {}
active_rooms = {}
last_user_file = {}  # Map user/chat_id to their last uploaded file_id for quick /pwd and /vo commands

def generate_unique_id(length=8):
    """Generate clean, unique alphanumeric IDs (e.g. 'ML-7k9P2mXz')."""
    chars = string.ascii_letters + string.digits
    while True:
        uid = ''.join(random.choice(chars) for _ in range(length))
        if uid not in file_store and uid not in active_rooms:
            return uid

def refresh_ttl(info):
    """Extend item expiration by 1 hour (3600 seconds) on activity."""
    if isinstance(info, dict):
        info["expires_at"] = time.time() + 3600

def fmt_size(b):
    if b == 0: return "0 B"
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    k = 1024; i = 0; s = float(b)
    while s >= k and i < len(units) - 1: s /= k; i += 1
    return f"{s:.1f} {units[i]}"

def background_ttl_cleaner():
    """Background loop that cleans up expired files, rooms, and orphaned disk files every 60 seconds."""
    while True:
        try:
            time.sleep(60)
            now = time.time()
            
            # 1. Clean expired file_store items
            expired_files = [fid for fid, info in list(file_store.items()) if info.get("expires_at", 0) < now]
            for fid in expired_files:
                info = file_store.pop(fid, None)
                if info:
                    fp = info.get("path", "")
                    if fp and os.path.exists(fp):
                        try: os.remove(fp)
                        except Exception: pass
                print(f"🧹 [TTL Cleaner] Auto-expired & deleted file link: {fid}")

            # 2. Clean expired active_rooms
            expired_rooms = [rid for rid, r in list(active_rooms.items()) if r.get("expires_at", 0) < now]
            for rid in expired_rooms:
                active_rooms.pop(rid, None)
                print(f"🧹 [TTL Cleaner] Auto-expired room: {rid}")

            # 3. Clean orphaned disk files older than 1 hour (3600s)
            for folder in [UPLOAD_DIR, RECORDING_DIR]:
                if os.path.exists(folder):
                    for fname in os.listdir(folder):
                        fpath = os.path.join(folder, fname)
                        if os.path.isfile(fpath):
                            if now - os.path.getmtime(fpath) > 3600:
                                try:
                                    os.remove(fpath)
                                    print(f"🧹 [TTL Cleaner] Removed orphaned disk file: {fname}")
                                except Exception: pass
        except Exception as e:
            print(f"⚠️ [TTL Cleaner Error] {e}")

# Start background auto-expiration daemon thread
threading.Thread(target=background_ttl_cleaner, daemon=True).start()
