"""Actionable event dispatchers: JSONL, Console, Webhook, and optional MQTT.

Ensures that failure in optional network destinations (MQTT, HTTP) NEVER blocks
or fails the primary local JSONL incident log.
"""

from __future__ import annotations

import json
import logging
import urllib.request
import urllib.error
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from safety_events.event_writer import JsonlEventWriter
from safety_events.models import SafetyEvent

logger = logging.getLogger("SafetySentinel")


class BaseEventDispatcher(ABC):
    @abstractmethod
    def dispatch(self, event: SafetyEvent) -> bool:
        """Dispatch event. Returns True if successful, False otherwise."""
        pass


class JsonlDispatcher(BaseEventDispatcher):
    """Primary durable dispatcher writing to JSONL log."""

    def __init__(self, writer: JsonlEventWriter) -> None:
        self.writer = writer

    def dispatch(self, event: SafetyEvent) -> bool:
        try:
            self.writer.write_event(event)
            return True
        except Exception as e:
            logger.error(f"[JSONL Dispatcher] Failed to write event: {e}")
            return False


class ConsoleAlertDispatcher(BaseEventDispatcher):
    """Live terminal alert dispatcher with formatted visual cues for judges."""

    def __init__(self, color_enabled: bool = True) -> None:
        self.color_enabled = color_enabled

    def dispatch(self, event: SafetyEvent) -> bool:
        badge = "[ALERT]" if event.event_type == "ZONE_INTRUSION" else f"[{event.event_type.value}]"
        sev_color = "\033[91m" if event.severity == "high" or event.severity == "critical" else "\033[93m"
        reset_color = "\033[0m"

        track_str = f"Track #{event.track_id}" if event.track_id is not None else "Untracked"
        conf_str = f"({event.confidence * 100:.1f}%)" if event.confidence is not None else ""
        dwell_str = f"dwell={event.dwell_time_seconds:.1f}s" if event.dwell_time_seconds is not None else ""

        if self.color_enabled:
            print(
                f"{sev_color}{badge} [{event.severity.upper()}]{reset_color} "
                f"Zone='{event.zone_id}' | {track_str} {conf_str} | "
                f"{event.timestamp_utc} {dwell_str}"
            )
        else:
            print(
                f"{badge} [{event.severity.upper()}] "
                f"Zone='{event.zone_id}' | {track_str} {conf_str} | "
                f"{event.timestamp_utc} {dwell_str}"
            )
        return True


class WebhookDispatcher(BaseEventDispatcher):
    """Optional HTTP POST webhook dispatcher using Python standard library."""

    def __init__(self, webhook_url: str, timeout_seconds: float = 2.0) -> None:
        self.webhook_url = webhook_url
        self.timeout_seconds = timeout_seconds

    def dispatch(self, event: SafetyEvent) -> bool:
        try:
            payload = json.dumps(event.to_dict()).encode("utf-8")
            req = urllib.request.Request(
                self.webhook_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_seconds) as resp:
                return resp.status in (200, 201, 202, 204)
        except Exception as e:
            logger.warning(f"[Webhook Dispatcher] Non-fatal delivery failure to {self.webhook_url}: {e}")
            return False


class MqttDispatcher(BaseEventDispatcher):
    """Optional MQTT dispatcher. Degrades gracefully if paho-mqtt or broker is unavailable."""

    def __init__(
        self,
        broker_host: str = "localhost",
        broker_port: int = 1883,
        topic: str = "sentinel/events",
        client_id: str = "pipegen-sentinel",
    ) -> None:
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.topic = topic
        self.client_id = client_id
        self._client: Any = None
        self._connected: bool = False

        self._initialize_client()

    def _initialize_client(self) -> None:
        try:
            import paho.mqtt.client as mqtt  # type: ignore

            self._client = mqtt.Client(client_id=self.client_id)
            self._client.connect_async(self.broker_host, self.broker_port, keepalive=30)
            self._client.loop_start()
            self._connected = True
        except ImportError:
            logger.info("[MQTT Dispatcher] 'paho-mqtt' not installed. MQTT dispatch is in mock/bypass mode.")
        except Exception as e:
            logger.warning(f"[MQTT Dispatcher] Broker connection failed ({self.broker_host}:{self.broker_port}): {e}")

    def dispatch(self, event: SafetyEvent) -> bool:
        if not self._connected or self._client is None:
            # Degrade gracefully without error
            return False
        try:
            payload = json.dumps(event.to_dict())
            self._client.publish(self.topic, payload, qos=1)
            return True
        except Exception as e:
            logger.warning(f"[MQTT Dispatcher] Non-fatal publish failure: {e}")
            return False


class CompositeDispatcher(BaseEventDispatcher):
    """Multiplexes events to multiple dispatchers with fault isolation."""

    def __init__(self, dispatchers: Optional[List[BaseEventDispatcher]] = None) -> None:
        self.dispatchers: List[BaseEventDispatcher] = dispatchers or []

    def add_dispatcher(self, dispatcher: BaseEventDispatcher) -> None:
        self.dispatchers.append(dispatcher)

    def dispatch(self, event: SafetyEvent) -> bool:
        any_success = False
        for disp in self.dispatchers:
            try:
                res = disp.dispatch(event)
                if res:
                    any_success = True
            except Exception as e:
                logger.error(f"[Composite Dispatcher] Unhandled error in {disp.__class__.__name__}: {e}")
        return any_success
