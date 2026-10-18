"""Unit tests for PipeGen and DeepStream metadata adapters."""

import unittest
from safety_events.adapters import (
    parse_deepstream_msgbroker,
    parse_deepstream_pyds_meta,
    parse_pipegen_frame,
    parse_single_detection,
)


class TestAdapters(unittest.TestCase):

    def test_parse_pipegen_frame(self):
        payload = {
            "camera_id": "video-forklift-area",
            "frame_id": 128,
            "timestamp_utc": "2026-10-18T12:05:00.500Z",
            "detections": [
                {
                    "track_id": 5,
                    "class_name": "person",
                    "confidence": 0.89,
                    "bbox": [0.3, 0.4, 0.5, 0.8],
                },
                {
                    "track_id": None,
                    "class_name": "person",
                    "confidence": 0.72,
                    "bbox": [0.6, 0.6, 0.8, 0.95],
                },
            ],
        }

        parsed = parse_pipegen_frame(payload)
        self.assertEqual(len(parsed), 2)

        det1 = parsed[0]
        self.assertEqual(det1.camera_id, "video-forklift-area")
        self.assertEqual(det1.frame_id, 128)
        self.assertEqual(det1.track_id, 5)
        self.assertAlmostEqual(det1.confidence, 0.89)
        self.assertAlmostEqual(det1.bbox.left, 0.3)
        self.assertAlmostEqual(det1.bbox.bottom, 0.8)

        det2 = parsed[1]
        self.assertIsNone(det2.track_id)
        self.assertAlmostEqual(det2.confidence, 0.72)

    def test_parse_deepstream_msgbroker_topleft_format(self):
        payload = {
            "version": "4.0",
            "sensorId": "camera-entry",
            "@timestamp": "2026-10-18T12:00:00.000Z",
            "frame_id": 400,
            "objects": [
                {
                    "id": "19",
                    "type": "person",
                    "confidence": 0.91,
                    "bbox": {
                        "topleftx": 100.0,
                        "toplefty": 150.0,
                        "bottomrightx": 250.0,
                        "bottomrighty": 450.0,
                    },
                }
            ],
        }

        parsed = parse_deepstream_msgbroker(payload)
        self.assertEqual(len(parsed), 1)
        det = parsed[0]
        self.assertEqual(det.camera_id, "camera-entry")
        self.assertEqual(det.track_id, 19)
        self.assertAlmostEqual(det.bbox.width, 150.0)
        self.assertAlmostEqual(det.bbox.height, 300.0)

    def test_parse_deepstream_pyds_meta(self):
        obj_meta = {
            "object_id": 8,
            "obj_label": "person",
            "confidence": 0.85,
            "rect_params": {
                "left": 50.0,
                "top": 100.0,
                "width": 120.0,
                "height": 260.0,
            },
        }
        det = parse_deepstream_pyds_meta(frame_num=50, camera_id="cam-01", obj_meta_dict=obj_meta)
        self.assertIsNotNone(det)
        self.assertEqual(det.track_id, 8)
        self.assertEqual(det.class_name, "person")
        self.assertAlmostEqual(det.bbox.right, 170.0)
        self.assertAlmostEqual(det.bbox.bottom, 360.0)

    def test_malformed_records_handled_gracefully(self):
        # Empty bbox
        bad_item = {"class_name": "person", "bbox": []}
        self.assertIsNone(parse_single_detection(bad_item))

        # None bbox
        bad_item2 = {"class_name": "person"}
        self.assertIsNone(parse_single_detection(bad_item2))


if __name__ == "__main__":
    unittest.main()
