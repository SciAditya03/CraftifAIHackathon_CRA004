"""Unit tests for resilient event dispatchers."""

import os
import shutil
import tempfile
import unittest
from safety_events.dispatchers import (
    CompositeDispatcher,
    ConsoleAlertDispatcher,
    JsonlDispatcher,
    MqttDispatcher,
    WebhookDispatcher,
)
from safety_events.event_writer import JsonlEventWriter
from safety_events.models import EventStatus, EventType, SafetyEvent, Severity


class TestDispatchers(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.test_dir, "dispatch_test.jsonl")
        self.writer = JsonlEventWriter(output_path=self.output_file)
        self.event = SafetyEvent(
            camera_id="cam-01",
            class_name="person",
            zone_id="restricted-zone-01",
            event_type=EventType.ZONE_INTRUSION,
            severity=Severity.HIGH,
            status=EventStatus.ACTIVE,
            track_id=1,
            confidence=0.94,
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_jsonl_dispatcher(self):
        disp = JsonlDispatcher(self.writer)
        success = disp.dispatch(self.event)
        self.assertTrue(success)
        self.assertEqual(self.writer.count_events(), 1)

    def test_console_dispatcher(self):
        disp = ConsoleAlertDispatcher(color_enabled=False)
        success = disp.dispatch(self.event)
        self.assertTrue(success)

    def test_webhook_non_blocking_failure(self):
        # Point to unreachable port/IP
        disp = WebhookDispatcher(webhook_url="http://127.0.0.1:59999/unreachable", timeout_seconds=0.2)
        # Should fail gracefully and return False, without throwing exception
        success = disp.dispatch(self.event)
        self.assertFalse(success)

    def test_mqtt_non_blocking_failure(self):
        # Point to unreachable broker
        disp = MqttDispatcher(broker_host="127.0.0.1", broker_port=59998)
        # Should fail gracefully without throwing exception
        success = disp.dispatch(self.event)
        self.assertFalse(success)

    def test_composite_dispatcher_fault_isolation(self):
        # Composite has valid JSONL writer AND failing webhook
        composite = CompositeDispatcher([
            JsonlDispatcher(self.writer),
            WebhookDispatcher(webhook_url="http://127.0.0.1:59999/unreachable", timeout_seconds=0.2),
        ])

        # Overall dispatch succeeds because JSONL wrote successfully
        res = composite.dispatch(self.event)
        self.assertTrue(res)

        # JSONL must contain the logged event despite network failure
        self.assertEqual(self.writer.count_events(), 1)


if __name__ == "__main__":
    unittest.main()
