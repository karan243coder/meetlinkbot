# ============ MeetLink Server Configuration ============
import os

# BotFather se mila hua token
_BOT = "YOUR_BOT_TOKEN_HERE"
_CH = "@YOUR_CHANNEL_USERNAME"
_PORT = 8080
_API_ID = 0
_API_HASH = ""
_SRV = ""

BOT_TOKEN = os.environ.get("BOT_TOKEN", _BOT)
CHANNEL_ID = os.environ.get("CHANNEL_ID", _CH)
PORT = int(os.environ.get("PORT", str(_PORT)))
API_ID = int(os.environ.get("API_ID", str(_API_ID or 0)))
API_HASH = os.environ.get("API_HASH", _API_HASH or "")
SERVER_URL = os.environ.get("SERVER_URL", _SRV).rstrip("/")

UPLOAD_DIR = '/tmp/meetlink_uploads'
RECORDING_DIR = '/tmp/meetlink_recordings'

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(RECORDING_DIR, exist_ok=True)
