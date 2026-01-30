from __future__ import annotations

import json
import socket
import threading
import uuid
from dataclasses import dataclass
from typing import Any, Callable

from .exceptions import RestError
from .types import FeedEvent


def _json_dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


class _JsonLineStream:
    def __init__(self, sock: socket.socket):
        self._sock = sock
        self._buf = bytearray()
        self._send_lock = threading.Lock()

    def send(self, obj: dict[str, Any]) -> None:
        data = (_json_dumps(obj) + "\n").encode("utf-8")
        with self._send_lock:
            self._sock.sendall(data)

    def recv_obj(self) -> dict[str, Any] | None:
        while True:
            nl = self._buf.find(b"\n")
            if nl != -1:
                raw = self._buf[:nl]
                del self._buf[: nl + 1]
                if not raw:
                    continue
                try:
                    data = json.loads(raw.decode("utf-8"))
                except Exception:
                    continue
                if isinstance(data, dict):
                    return data
                continue

            chunk = self._sock.recv(4096)
            if not chunk:
                return None
            self._buf.extend(chunk)


class UnixSocketRpcClient:
    def __init__(
        self,
        *,
        socket_path: str,
        token: str,
        instance: str,
        timeout: float = 30.0,
    ):
        self.socket_path = socket_path
        self.token = token
        self.instance = instance
        self.timeout = float(timeout)

        self._sock: socket.socket | None = None
        self._stream: _JsonLineStream | None = None

        self._pending: dict[str, dict[str, Any]] = {}
        self._pending_events: dict[str, threading.Event] = {}
        self._pending_lock = threading.Lock()

        self._event_handlers: list[Callable[[dict[str, Any]], None]] = []
        self._reader_thread: threading.Thread | None = None
        self._closed = threading.Event()

    def connect(self) -> None:
        if self._sock is not None:
            return
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.connect(self.socket_path)
        self._sock = sock
        self._stream = _JsonLineStream(sock)

        self._reader_thread = threading.Thread(target=self._reader_loop, daemon=True)
        self._reader_thread.start()

        # Bind connection to a single instance.
        self.request(
            "auth",
            {
                "token": self.token,
                "instance": self.instance,
            },
            timeout=self.timeout,
        )

    def close(self) -> None:
        self._closed.set()
        try:
            if self._sock is not None:
                self._sock.close()
        except Exception:
            pass
        self._sock = None
        self._stream = None

    def add_event_handler(self, handler: Callable[[dict[str, Any]], None]) -> None:
        self._event_handlers.append(handler)

    def _reader_loop(self) -> None:
        assert self._stream is not None
        while not self._closed.is_set():
            obj = self._stream.recv_obj()
            if obj is None:
                break
            if obj.get("type") == "event":
                for h in list(self._event_handlers):
                    try:
                        h(obj)
                    except Exception:
                        pass
                continue
            if obj.get("type") != "resp":
                continue
            req_id = str(obj.get("id") or "")
            if not req_id:
                continue
            with self._pending_lock:
                self._pending[req_id] = obj
                ev = self._pending_events.get(req_id)
            if ev:
                ev.set()

    def request(self, method: str, params: dict[str, Any] | None = None, *, timeout: float | None = None) -> Any:
        self.connect()
        assert self._stream is not None

        req_id = uuid.uuid4().hex
        ev = threading.Event()
        with self._pending_lock:
            self._pending_events[req_id] = ev

        self._stream.send(
            {
                "type": "req",
                "id": req_id,
                "method": method,
                "params": params or {},
            }
        )

        if timeout is None:
            timeout = self.timeout
        if not ev.wait(timeout=float(timeout)):
            with self._pending_lock:
                self._pending_events.pop(req_id, None)
                self._pending.pop(req_id, None)
            raise RestError("Supervisor request timeout")

        with self._pending_lock:
            resp = self._pending.pop(req_id, None)
            self._pending_events.pop(req_id, None)
        if not isinstance(resp, dict):
            raise RestError("Bad supervisor response")
        if not resp.get("ok"):
            err = resp.get("error") or {}
            msg = err.get("message") if isinstance(err, dict) else str(err)
            raise RestError(msg or "Supervisor error")
        return resp.get("result")


@dataclass
class UnixSocketRestClient:
    rpc: UnixSocketRpcClient

    def whoami(self, *, instance: str | None = None) -> dict[str, Any]:
        # Instance is already bound at auth stage; allow override only if it matches.
        if instance and instance != self.rpc.instance:
            raise RestError("Instance mismatch")
        data = self.rpc.request("whoami", {})
        if not isinstance(data, dict):
            raise RestError("Unexpected response for whoami")
        return data

    def get_settings(self) -> dict[str, Any]:
        data = self.rpc.request("get_settings", {})
        if not isinstance(data, dict):
            raise RestError("Unexpected response for core/settings")
        return data

    def list_zones(self) -> list[dict[str, Any]]:
        data = self.rpc.request("list_zones", {})
        if not isinstance(data, list):
            raise RestError("Unexpected response for core/zones")
        return [x for x in data if isinstance(x, dict)]

    def list_categories(self) -> list[dict[str, Any]]:
        data = self.rpc.request("list_categories", {})
        if not isinstance(data, list):
            raise RestError("Unexpected response for core/categories")
        return [x for x in data if isinstance(x, dict)]

    def list_components(self) -> list[dict[str, Any]]:
        data = self.rpc.request("list_components", {})
        if not isinstance(data, list):
            raise RestError("Unexpected response for core/components")
        return [x for x in data if isinstance(x, dict)]

    def list_instance_users(self) -> list[dict[str, Any]]:
        data = self.rpc.request("list_instance_users", {})
        if not isinstance(data, list):
            raise RestError("Unexpected response for users/instance-users")
        return [x for x in data if isinstance(x, dict)]

    def list_users(self) -> list[dict[str, Any]]:
        data = self.rpc.request("list_users", {})
        if not isinstance(data, list):
            raise RestError("Unexpected response for users/users")
        return [x for x in data if isinstance(x, dict)]

    def get_component(self, component_id: int) -> dict[str, Any]:
        data = self.rpc.request("get_component", {"component_id": int(component_id)})
        if not isinstance(data, dict):
            raise RestError("Unexpected response for core/components/<id>")
        return data

    def call_component_method(
        self,
        component_id: int,
        method: str,
        *,
        subcomponent_id: int | None = None,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> Any:
        return self.rpc.request(
            "call_component_method",
            {
                "component_id": int(component_id),
                "method": method,
                "subcomponent_id": int(subcomponent_id) if subcomponent_id is not None else None,
                "args": args or [],
                "kwargs": kwargs or {},
            },
        )

    def send_notification(
        self,
        *,
        severity: str,
        title: str,
        body: str | None = None,
        component_id: int | None = None,
        instance_user_ids: list[int] | None = None,
    ) -> Any:
        payload: dict[str, Any] = {
            "severity": severity,
            "title": title,
            "body": body,
            "instance_user_ids": instance_user_ids or [],
        }
        if component_id is not None:
            payload["component_id"] = int(component_id)
        return self.rpc.request("send_notification", payload)


class UnixSocketMqttClient:
    def __init__(self, rpc: UnixSocketRpcClient):
        self._rpc = rpc
        self._connected = threading.Event()
        self._feed_handlers: list[Callable[[FeedEvent], None]] = []
        self._subscribed = False

        self._rpc.add_event_handler(self._on_event)

    @property
    def is_connected(self) -> bool:
        return self._connected.is_set()

    def connect(self) -> None:
        self._rpc.connect()
        self._connected.set()

    def disconnect(self) -> None:
        self._connected.clear()
        self._rpc.close()

    def add_feed_handler(self, handler: Callable[[FeedEvent], None]) -> None:
        self._feed_handlers.append(handler)

    def subscribe_control_responses(self, *, user_id: int) -> None:
        # Supervisor executes control requests synchronously.
        return

    def subscribe_feed(self, *, user_id: int, instance_uid: str) -> None:
        if self._subscribed:
            return
        self._rpc.request(
            "subscribe_feed",
            {"models": ["Component", "InstanceUser"]},
        )
        self._subscribed = True

    def call_component_method(
        self,
        *,
        user_id: int,
        instance_uid: str,
        component_id: int,
        subcomponent_id: int | None = None,
        method: str,
        args: list[Any] | None = None,
        kwargs: dict[str, Any] | None = None,
        timeout: float = 10.0,
    ) -> Any:
        return self._rpc.request(
            "call_component_method",
            {
                "component_id": int(component_id),
                "subcomponent_id": int(subcomponent_id) if subcomponent_id is not None else None,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {},
            },
            timeout=timeout,
        )

    def _on_event(self, obj: dict[str, Any]) -> None:
        if obj.get("topic") != "feed":
            return
        instance_uid = obj.get("instance_uid")
        model = obj.get("model")
        obj_id = obj.get("obj_id")
        payload = obj.get("payload")
        if not isinstance(instance_uid, str) or not isinstance(model, str):
            return
        try:
            obj_id_int = int(obj_id)
        except Exception:
            return
        if not isinstance(payload, dict):
            return
        event = FeedEvent(model=model, obj_id=obj_id_int, instance_uid=instance_uid, payload=payload)
        for h in list(self._feed_handlers):
            try:
                h(event)
            except Exception:
                pass
