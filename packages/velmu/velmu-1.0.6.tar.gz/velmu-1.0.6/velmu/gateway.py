"""
velmu.gateway
~~~~~~~~~~~~~

WebSocket Gateway connection manager.
"""
import asyncio
import logging
import time
import socketio
import aiohttp
from typing import Optional, TYPE_CHECKING
from .errors import GatewayError

if TYPE_CHECKING:
    from .client import Client
    from .state import ConnectionState
    from .flags import Intents

_log = logging.getLogger(__name__)

class GatewayOp:
    DISPATCH = 0
    HEARTBEAT = 1
    IDENTIFY = 2
    PRESENCE_UPDATE = 3
    VOICE_STATE_UPDATE = 4
    RESUME = 6
    RECONNECT = 7
    REQUEST_GUILD_MEMBERS = 8
    INVALID_SESSION = 9
    HELLO = 10
    HEARTBEAT_ACK = 11

class VelmuGateway:
    """Manages the WebSocket connection to the Velmu Gateway."""

    def __init__(self, state: 'ConnectionState', token: str, intents: 'Intents'):
        self.state = state
        self.token = token
        self.intents = intents
        
        # Socket Config
        self._sio = socketio.AsyncClient(
            logger=False, 
            engineio_logger=False,
            reconnection=True,
            reconnection_attempts=0, # Infinite
            reconnection_delay=1,
            reconnection_delay_max=5
        )
        
        # Connection State
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._connected = False
        self._closing = False
        self._session_id: Optional[str] = None
        self._sequence: Optional[int] = None
        
        # Latency State
        self._last_heartbeat_send: float = 0.0
        self._latency: float = float('inf')
        
        # SIO Globals
        self._sio.on('connect', self.on_connect, namespace='/gateway-bot')
        self._sio.on('disconnect', self.on_disconnect, namespace='/gateway-bot')
        self._sio.on('payload', self.on_payload, namespace='/gateway-bot')
        self._sio.on('connect_error', self.on_connect_error, namespace='/gateway-bot')

    @property
    def latency(self) -> float:
        """Latency in seconds."""
        return self._latency

    async def connect(self, url: str):
        """Connect to the Gateway."""
        backoff = 1.0
        while not self._closing:
            _log.info(f'Connecting to Gateway: {url}')
            try:
                await self._sio.connect(url, namespaces=['/gateway-bot'], transports=['websocket', 'polling'])
                # Reset backoff on successful connect? 
                # SocketIO handles internals, but we manage the loop if disconnect occurs.
                await self._sio.wait()
            except asyncio.CancelledError:
                await self.close()
                break
            except Exception as e:
                import random
                _log.error(f"Gateway connection failed: {e}. Retrying in {backoff:.2f}s")
                await asyncio.sleep(backoff)
                # Jittered exponential backoff: (base * 2) + random[0, 1]
                backoff = min(backoff * 2, 60.0) + random.random()
            
            if self._closing:
                break

    async def close(self):
        """Close the connection."""
        self._closing = True
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
        
        if self._sio.connected:
            await self._sio.disconnect()
        
        _log.info("Gateway closed.")

    async def send(self, op: int, data: dict):
        """Send a payload to the Gateway."""
        payload = {'op': op, 'd': data}
        await self._sio.emit('payload', payload, namespace='/gateway-bot')

    # --- Events ---

    async def on_connect(self):
        self._connected = True
        _log.info('Gateway connection established.')

    async def on_disconnect(self):
        self._connected = False
        if not self._closing:
            _log.warning('Gateway disconnected unexpectedly. Reconnecting...')
            # SocketIO handles reconnection, but we might want to clear tasks?
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
        else:
            _log.info('Gateway disconnected.')

    async def on_connect_error(self, data):
        _log.error(f'Gateway Connection Error: {data}')

    async def on_payload(self, data):
        op = data.get('op')
        d = data.get('d')
        t = data.get('t')
        
        # Update sequence
        if data.get('s'):
            self._sequence = data.get('s')

        if op == GatewayOp.HELLO:
            interval = d['heartbeat_interval'] / 1000
            self._heartbeat_task = asyncio.create_task(self.heartbeat_loop(interval))
            
            # Resume or Identify
            if self._session_id and self._sequence:
                _log.info('Attempting to RESUME session...')
                await self.resume()
            else:
                _log.info('Identifying new session...')
                await self.identify()
        
        elif op == GatewayOp.HEARTBEAT_ACK:
            # Calculate Latency
            ack_time = time.perf_counter()
            self._latency = ack_time - self._last_heartbeat_send
            # _log.debug(f'Heartbeat ACK. Latency: {self._latency*1000:.2f}ms')
            
        elif op == GatewayOp.DISPATCH:
            if t == 'READY':
                self._session_id = d.get('sessionId')
                _log.info(f'Session Ready: {self._session_id}')
                # Explicitly set status online after Ready
                await self.update_presence(status='online')
            self.state.dispatch(t, d)
            
        elif op == 7: # RECONNECT request
            _log.info('Gateway requested RECONNECT.')
            await self.close() # Will trigger client loop to restart? No, we need logic.
            # Actually, socketio auto-reconnect handles it if we just disconnect logic but keep socket retry?
            # Or we strictly follow Discord op 7 -> Resume.
            await self.resume()
            
        elif op == 9: # INVALID SESSION
            _log.warning('Session Invalid. Re-identifying...')
            self._session_id = None
            self._sequence = None
            await self.identify()

    async def identify(self):
        """Send IDENTIFY payload."""
        payload = {
            'token': self.token,
            'intents': self.intents.value,
            'properties': {
                'os': 'linux',
                'browser': 'velmu.py',
                'device': 'velmu.py'
            },
            'presence': {
                'status': 'online',
                'afk': False
            }
        }
        await self.send(GatewayOp.IDENTIFY, payload)
        
    async def resume(self):
        """Send RESUME payload."""
        payload = {
            'token': self.token,
            'sessionId': self._session_id,
            'seq': self._sequence
        }
        await self.send(GatewayOp.RESUME, payload)

    async def heartbeat_loop(self, interval: float):
        _log.debug(f'Heartbeat started (interval: {interval}s)')
        try:
            while True:
                self._last_heartbeat_send = time.perf_counter()
                await self.send(GatewayOp.HEARTBEAT, {'s': self._sequence})
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            pass

    async def update_presence(self, status: str = 'online', activities: list = [], afk: bool = False):
        """Updates the presence status."""
        payload = {
            'since': None,
            'activities': activities,
            'status': status,
            'afk': afk
        }
        await self.send(3, payload) # Opcode 3: Prevence Update
