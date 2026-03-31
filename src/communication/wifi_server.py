import asyncio
import json
import threading
import time
from queue import Empty, Queue
from typing import Any

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse


class AppCommandQueue:
    def __init__(self):
        self._queue = Queue()

    def put(self, cmd: dict):
        self._queue.put(cmd)

    def get_nowait(self):
        try:
            return self._queue.get_nowait()
        except Empty:
            return None


class WiFiServer:
    """
    앱 <-> RPi 통신 서버
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8000):
        self.host = host
        self.port = port

        self.command_queue = AppCommandQueue()

        self.latest_status_payload: dict[str, Any] = {}
        self.latest_report_payload: dict[str, Any] = {}
        self.latest_meta_payload: dict[str, Any] = {
            "type": "meta",
            "connected": True,
            "backend": "wifi",
            "stage": "boot_completed",
            "ws_clients": 0,
            "timestamp": int(time.time()),
        }

        self._app: FastAPI | None = None
        self._server: uvicorn.Server | None = None
        self._server_thread: threading.Thread | None = None

        self._loop: asyncio.AbstractEventLoop | None = None
        self._outgoing_queue: asyncio.Queue | None = None
        self._clients: set[WebSocket] = set()
        self._dispatcher_task: asyncio.Task | None = None

        self._running = False

        # dedup cache
        self._last_meta_json: str | None = None
        self._last_status_json: str | None = None
        self._last_report_json: str | None = None

        # health state
        self._uart_link_ready = False

    # -------------------------------------------------
    # public API
    # -------------------------------------------------
    def start(self):
        if self._running:
            return

        self._running = True
        self._app = FastAPI()
        server_ref = self

        @self._app.on_event("startup")
        async def on_startup():
            server_ref._loop = asyncio.get_running_loop()
            server_ref._outgoing_queue = asyncio.Queue()
            server_ref._dispatcher_task = asyncio.create_task(
                server_ref._broadcast_dispatcher()
            )

        @self._app.on_event("shutdown")
        async def on_shutdown():
            if server_ref._dispatcher_task is not None:
                server_ref._dispatcher_task.cancel()
                try:
                    await server_ref._dispatcher_task
                except asyncio.CancelledError:
                    pass

        @self._app.get("/meta")
        async def get_meta():
            return JSONResponse(content=server_ref.latest_meta_payload)

        @self._app.get("/status")
        async def get_status():
            return JSONResponse(content=server_ref.latest_status_payload)

        @self._app.get("/report")
        async def get_report():
            return JSONResponse(content=server_ref.latest_report_payload)

        @self._app.get("/health")
        async def get_health():
            current_stage = server_ref.latest_meta_payload.get("stage")
            uart_link = server_ref._uart_link_ready or (current_stage != "boot_completed")

            return JSONResponse(
                content={
                    "ok": True,
                    "service": "posture_rpi",
                    "backend": "wifi",
                    "uart_link": uart_link,
                    "ws_clients": len(server_ref._clients),
                    "stage": current_stage,
                }
            )

        @self._app.post("/command")
        async def post_command(cmd: dict):
            if not isinstance(cmd, dict):
                print("[APP -> RPi] invalid_json_object:", cmd)
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "accepted": False,
                        "error": "invalid_json_object",
                        "stage": server_ref.latest_meta_payload.get("stage"),
                    },
                )

            if "cmd" not in cmd:
                print("[APP -> RPi] missing_cmd:", cmd)
                return JSONResponse(
                    status_code=400,
                    content={
                        "ok": False,
                        "accepted": False,
                        "error": "missing_cmd",
                        "stage": server_ref.latest_meta_payload.get("stage"),
                    },
                )

            print(
                "[APP -> RPi] command received | "
                f"stage={server_ref.latest_meta_payload.get('stage')} | payload={json.dumps(cmd, ensure_ascii=False)}"
            )

            server_ref.command_queue.put(cmd)

            return {
                "ok": True,
                "accepted": True,
                "message": "command_received",
                "stage": server_ref.latest_meta_payload.get("stage"),
            }

        @self._app.websocket("/ws")
        async def websocket_endpoint(ws: WebSocket):
            await ws.accept()
            server_ref._clients.add(ws)
            server_ref._refresh_ws_client_count()
            print("[WIFI][WS] client connected")

            try:
                await server_ref._send_snapshot_to_client(ws)

                while True:
                    _ = await ws.receive_text()

            except WebSocketDisconnect:
                pass
            except Exception as e:
                print(f"[WIFI][WS] client error: {e}")
            finally:
                if ws in server_ref._clients:
                    server_ref._clients.remove(ws)
                server_ref._refresh_ws_client_count()
                print("[WIFI][WS] client disconnected")

        config = uvicorn.Config(
            app=self._app,
            host=self.host,
            port=self.port,
            log_level="warning",
        )
        self._server = uvicorn.Server(config=config)

        self._server_thread = threading.Thread(
            target=self._server.run,
            daemon=True,
        )
        self._server_thread.start()

        print(f"[WIFI] server started on http://{self.host}:{self.port}")

    def stop(self):
        self._running = False

        if self._server is not None:
            self._server.should_exit = True

        if self._server_thread is not None and self._server_thread.is_alive():
            self._server_thread.join(timeout=2.0)

        self._server = None
        self._server_thread = None
        print("[WIFI] server stopped")

    def get_next_command(self):
        cmd = self.command_queue.get_nowait()
        if cmd is not None:
            print(f"[RPi CMD QUEUE] pop -> {json.dumps(cmd, ensure_ascii=False)}")
        return cmd

    def update_status(self, payload: dict):
        payload = dict(payload)
        payload.setdefault("timestamp", int(time.time()))
        self.latest_status_payload = payload

        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if payload_json == self._last_status_json:
            return

        self._last_status_json = payload_json

        print("[WIFI][STATUS]")
        print(json.dumps(payload, ensure_ascii=False))
        self._enqueue_broadcast(payload)

    def update_report(self, payload: dict):
        payload = dict(payload)
        payload.setdefault("timestamp", int(time.time()))
        self.latest_report_payload = payload

        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        if payload_json == self._last_report_json:
            return

        self._last_report_json = payload_json

        print("[WIFI][REPORT]")
        print(json.dumps(payload, ensure_ascii=False))
        self._enqueue_broadcast(payload)

    def update_meta(self, payload: dict):
        self.latest_meta_payload.update(payload)
        self.latest_meta_payload["type"] = "meta"
        self.latest_meta_payload["ws_clients"] = len(self._clients)
        self.latest_meta_payload["timestamp"] = int(time.time())

        if self.latest_meta_payload.get("stage") == "uart_link_ready":
            self._uart_link_ready = True

        meta_json = json.dumps(self.latest_meta_payload, ensure_ascii=False, sort_keys=True)
        if meta_json == self._last_meta_json:
            return

        self._last_meta_json = meta_json

        print("[WIFI][META]")
        print(json.dumps(self.latest_meta_payload, ensure_ascii=False))
        self._enqueue_broadcast(self.latest_meta_payload)

    def on_control_write(self, raw_json: str):
        try:
            cmd = json.loads(raw_json)
            self.command_queue.put(cmd)
            print("[WIFI] RX console command:", cmd)
        except Exception as e:
            print(f"[WIFI] invalid console command: {e}")

    # -------------------------------------------------
    # internal
    # -------------------------------------------------
    async def _send_snapshot_to_client(self, ws: WebSocket):
        if self.latest_meta_payload:
            await ws.send_json(self.latest_meta_payload)

        if self.latest_status_payload:
            await ws.send_json(self.latest_status_payload)

        if self.latest_report_payload:
            await ws.send_json(self.latest_report_payload)

    def _refresh_ws_client_count(self):
        self.latest_meta_payload["ws_clients"] = len(self._clients)
        self.latest_meta_payload["timestamp"] = int(time.time())

        meta_json = json.dumps(self.latest_meta_payload, ensure_ascii=False, sort_keys=True)
        if meta_json == self._last_meta_json:
            return

        self._last_meta_json = meta_json
        self._enqueue_broadcast(self.latest_meta_payload)

    def _enqueue_broadcast(self, payload: dict):
        if self._loop is None or self._outgoing_queue is None:
            return

        try:
            self._loop.call_soon_threadsafe(self._outgoing_queue.put_nowait, payload)
        except Exception as e:
            print(f"[WIFI] enqueue broadcast failed: {e}")

    async def _broadcast_dispatcher(self):
        while True:
            payload = await self._outgoing_queue.get()
            dead_clients = []

            for ws in list(self._clients):
                try:
                    await ws.send_json(payload)
                except Exception:
                    dead_clients.append(ws)

            for ws in dead_clients:
                if ws in self._clients:
                    self._clients.remove(ws)

            if dead_clients:
                self._refresh_ws_client_count()