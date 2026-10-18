"""Adapters for PipeGen and DeepStream pipeline outputs.

Translates metadata from PipeGen JSON streams, DeepStream nvmsgbroker payloads,
and direct GstBuffer / pyds probe metadata into standardized RawDetection models.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional, Tuple, Union

from safety_events.models import BoundingBox, RawDetection


def parse_pipegen_frame(
    payload: Dict[str, Any],
    default_camera_id: str = "video-demo-01",
) -> List[RawDetection]:
    """Parse standard PipeGen JSON frame output payload.
    
    Expected format:
    {
        "camera_id": "video-demo-01",
        "frame_id": 105,
        "timestamp_utc": "2026-10-18T12:00:01.200Z",
        "detections": [
            {
                "track_id": 7,
                "class_name": "person",
                "confidence": 0.94,
                "bbox": [0.42, 0.35, 0.58, 0.85]  # [left, top, right, bottom]
            }
        ]
    }
    """
    camera_id = payload.get("camera_id", default_camera_id)
    frame_id = payload.get("frame_id", 0)
    timestamp_utc = payload.get(
        "timestamp_utc",
        datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    detections: List[RawDetection] = []
    raw_list = payload.get("detections", [])

    for item in raw_list:
        parsed = parse_single_detection(
            item,
            camera_id=camera_id,
            frame_id=frame_id,
            timestamp_utc=timestamp_utc,
            source="pipegen",
        )
        if parsed:
            detections.append(parsed)

    return detections


def parse_deepstream_msgbroker(
    payload: Dict[str, Any],
    default_camera_id: str = "camera-01",
) -> List[RawDetection]:
    """Parse DeepStream nvmsgbroker standard JSON payload (schema 4.0/minimal).
    
    DeepStream schemas often provide 'sensorId', '@timestamp', and 'objects' list.
    """
    camera_id = payload.get("sensorId", payload.get("camera_id", default_camera_id))
    timestamp_utc = payload.get(
        "@timestamp",
        payload.get("timestamp_utc", datetime.datetime.now(datetime.timezone.utc).isoformat()),
    )
    frame_id = payload.get("frame_id", 0)

    detections: List[RawDetection] = []
    objects = payload.get("objects", [])

    for obj in objects:
        bbox_raw = obj.get("bbox", {})
        # Support dict format: {"topleftx": ..., "toplefty": ..., "bottomrightx": ..., "bottomrighty": ...}
        # or {"left": ..., "top": ..., "width": ..., "height": ...}
        bbox: Optional[BoundingBox] = None
        if isinstance(bbox_raw, dict):
            if "topleftx" in bbox_raw and "bottomrightx" in bbox_raw:
                bbox = BoundingBox(
                    left=float(bbox_raw["topleftx"]),
                    top=float(bbox_raw["toplefty"]),
                    right=float(bbox_raw["bottomrightx"]),
                    bottom=float(bbox_raw["bottomrighty"]),
                )
            elif "left" in bbox_raw and "width" in bbox_raw:
                bbox = BoundingBox(
                    left=float(bbox_raw["left"]),
                    top=float(bbox_raw["top"]),
                    right=float(bbox_raw["left"] + bbox_raw["width"]),
                    bottom=float(bbox_raw["top"] + bbox_raw["height"]),
                )
        elif isinstance(bbox_raw, (list, tuple)) and len(bbox_raw) == 4:
            bbox = BoundingBox(
                left=float(bbox_raw[0]),
                top=float(bbox_raw[1]),
                right=float(bbox_raw[2]),
                bottom=float(bbox_raw[3]),
            )

        if bbox is None:
            continue

        raw_track_id = obj.get("id", obj.get("track_id"))
        track_id = int(raw_track_id) if raw_track_id is not None and str(raw_track_id).isdigit() else None
        class_name = obj.get("type", obj.get("class_name", "person"))
        confidence = obj.get("confidence")
        if confidence is not None:
            confidence = float(confidence)

        detections.append(
            RawDetection(
                camera_id=camera_id,
                frame_id=frame_id,
                timestamp_utc=timestamp_utc,
                class_name=class_name,
                bbox=bbox,
                track_id=track_id,
                confidence=confidence,
                source="deepstream-msgbroker",
            )
        )

    return detections


def parse_deepstream_pyds_meta(
    frame_num: int,
    camera_id: str,
    obj_meta_dict: Dict[str, Any],
) -> Optional[RawDetection]:
    """Adapter for Python DeepStream bindings (pyds) NvDsObjectMeta extracted fields.
    
    Used when attaching a probe callback directly to GStreamer/DeepStream pipeline pads.
    """
    rect = obj_meta_dict.get("rect_params", {})
    if not rect:
        return None

    left = float(rect.get("left", 0.0))
    top = float(rect.get("top", 0.0))
    width = float(rect.get("width", 0.0))
    height = float(rect.get("height", 0.0))

    bbox = BoundingBox(left=left, top=top, right=left + width, bottom=top + height)
    obj_id = obj_meta_dict.get("object_id")
    track_id = int(obj_id) if obj_id is not None and obj_id != -1 else None

    return RawDetection(
        camera_id=camera_id,
        frame_id=frame_num,
        timestamp_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        class_name=obj_meta_dict.get("obj_label", "person"),
        bbox=bbox,
        track_id=track_id,
        confidence=obj_meta_dict.get("confidence"),
        source="pyds-probe",
    )


def parse_single_detection(
    item: Dict[str, Any],
    camera_id: str = "video-demo-01",
    frame_id: int = 0,
    timestamp_utc: Optional[str] = None,
    source: str = "generic",
) -> Optional[RawDetection]:
    """Parse a single detection record with robust error tolerance."""
    if timestamp_utc is None:
        timestamp_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

    bbox_val = item.get("bbox")
    if not bbox_val:
        return None

    bbox: Optional[BoundingBox] = None
    if isinstance(bbox_val, (list, tuple)) and len(bbox_val) == 4:
        bbox = BoundingBox(
            left=float(bbox_val[0]),
            top=float(bbox_val[1]),
            right=float(bbox_val[2]),
            bottom=float(bbox_val[3]),
        )
    elif isinstance(bbox_val, dict):
        if "left" in bbox_val and "right" in bbox_val:
            bbox = BoundingBox(
                left=float(bbox_val["left"]),
                top=float(bbox_val["top"]),
                right=float(bbox_val["right"]),
                bottom=float(bbox_val["bottom"]),
            )
        elif "x" in bbox_val and "width" in bbox_val:
            bbox = BoundingBox(
                left=float(bbox_val["x"]),
                top=float(bbox_val["y"]),
                right=float(bbox_val["x"] + bbox_val["width"]),
                bottom=float(bbox_val["y"] + bbox_val["height"]),
            )

    if bbox is None:
        return None

    raw_track = item.get("track_id")
    track_id = int(raw_track) if raw_track is not None else None

    raw_conf = item.get("confidence")
    confidence = float(raw_conf) if raw_conf is not None else None

    return RawDetection(
        camera_id=camera_id,
        frame_id=frame_id,
        timestamp_utc=timestamp_utc,
        class_name=item.get("class_name", item.get("label", "person")),
        bbox=bbox,
        track_id=track_id,
        confidence=confidence,
        source=source,
    )
