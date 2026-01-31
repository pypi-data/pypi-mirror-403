import asyncio
import json
import aiohttp
import websockets
from typing import Callable, Dict, Any

class Intents:
    """Discord Intent Bitmask Hesaplayıcı"""
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    GUILD_BANS = 1 << 2
    GUILD_EMOJIS_AND_STICKERS = 1 << 3
    GUILD_INTEGRATIONS = 1 << 4
    GUILD_WEBHOOKS = 1 << 5
    GUILD_INVITES = 1 << 6
    GUILD_VOICE_STATES = 1 << 7
    GUILD_PRESENCES = 1 << 8
    GUILD_MESSAGES = 1 << 9
    GUILD_MESSAGE_REACTIONS = 1 << 10
    GUILD_MESSAGE_TYPING = 1 << 11
    DIRECT_MESSAGES = 1 << 12
    DIRECT_MESSAGE_REACTIONS = 1 << 13
    DIRECT_MESSAGE_TYPING = 1 << 14
    MESSAGE_CONTENT = 1 << 15

class Client:
    def __init__(self, token: str, intents: int):
        self.token = token
        self.intents = intents
        self.ws_url = "wss://gateway.discord.gg/?v=10&encoding=json"
        self.session: aiohttp.ClientSession = None
        self.events: Dict[str, Callable] = {}
        self.seq = None
        self.session_id = None
        self.heartbeat_interval = None
        self.running = False

    def on(self, event_name: str):
        """Event Listener Decorator"""
        def decorator(func: Callable):
            self.events[event_name] = func
            return func
        return decorator

    async def _http_request(self, method: str, endpoint: str, json_data: dict = None):
        """Ham HTTP İsteği (Cache yok, doğrudan API)"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        
        async with self.session.request(method, f"https://discord.com/api/v10{endpoint}", headers=headers, json=json_data) as resp:
            if resp.status == 204:
                return None
            return await resp.json()

    async def send_message(self, channel_id: int, content: str):
        """Mesaj Gönderme Yardımcısı"""
        return await self._http_request("POST", f"/channels/{channel_id}/messages", {"content": content})

    async def _heartbeat_loop(self, ws):
        """Discord Keep-Alive Döngüsü"""
        try:
            while self.running:
                await asyncio.sleep(self.heartbeat_interval / 1000)
                payload = {"op": 1, "d": self.seq}
                await ws.send(json.dumps(payload))
                print(f"[Heartbeat] Sequence {self.seq} gönderildi.")
        except Exception as e:
            print(f"[Heartbeat Error] {e}")

    async def _process_event(self, event_data: dict):
        """Gelen Olayları İşle ve Dispatch Et"""
        event_name = event_data.get("t")
        data = event_data.get("d")

        # Raw Event Mantığı: Cache yok, ham veriyi doğrudan user'a ver
        if event_name in self.events:
            await self.events[event_name](data)
        
        print(f"[Event] {event_name} alındı.")

    async def start(self):
        """Botu Başlat"""
        self.running = True
        async with websockets.connect(self.ws_url) as ws:
            print("[System] Discord Gateway'e bağlanılıyor...")
            
            async for message in ws:
                msg_data = json.loads(message)
                op_code = msg_data.get("op")

                if op_code == 10: # Hello
                    self.heartbeat_interval = msg_data["d"]["heartbeat_interval"]
                    asyncio.create_task(self._heartbeat_loop(ws))
                    
                    # Identify Payload (Giriş)
                    payload = {
                        "op": 2,
                        "d": {
                            "token": self.token,
                            "intents": self.intents,
                            "properties": {
                                "os": "linux",
                                "browser": "miracord-py",
                                "device": "miracord-py"
                            }
                        }
                    }
                    await ws.send(json.dumps(payload))

                elif op_code == 0: # Dispatch (Event)
                    self.seq = msg_data["s"]
                    await self._process_event(msg_data)
                
                elif op_code == 11: # Heartbeat ACK
                    pass # Heartbeat başarılı

    def run(self):
        """Async Loop Başlatıcı"""
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.running = False
            if self.session:
                asyncio.run(self.session.close())
            print("[System] Bot durduruldu.")

