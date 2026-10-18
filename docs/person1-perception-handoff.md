# Person 1 (Perception) to Person 2 (Safety Logic) — Interface & Handoff Contract

## 1. Overview
This document specifies the exact contract and metadata structures emitted by Person 1's **PipeGen / DeepStream Perception Pipeline** and consumed by Person 2's **Safety Events Engine**.

By freezing this interface, Person 2 can develop and unit-test safety rules, debouncers, and JSONL writers completely independently using mock data, while Person 1 configures the video decoder, TensorRT engine, and tracker.

---

## 2. Ingestion Modes

Person 1's pipeline delivers detection metadata through two supported paths:
1. **Mode A (In-Process GStreamer Pad Probe):** Attaches a callback probe directly to the GStreamer pad downstream of `nvinfer` / `nvtracker`. Emits Python dictionary structures directly to `safety_events.engine.SentinelEngine`.
2. **Mode B (Inter-Process JSON Stream):** PipeGen pipeline emits line-delimited JSON payloads over standard output, a named pipe, or a file stream, parsed via `safety_events.adapters.parse_pipegen_frame`.
3. **Mode C (DeepStream Message Broker `nvmsgbroker`):** Formatted Kafka/MQTT/file payloads following DeepStream schema 4.0, parsed via `safety_events.adapters.parse_deepstream_msgbroker`.

---

## 3. Metadata Specification (Mode B — PipeGen Frame Payload)

Each frame payload emitted by Person 1 follows this schema:

```json
{
  "camera_id": "video-demo-01",
  "frame_id": 105,
  "timestamp_utc": "2026-10-18T12:00:03.500Z",
  "source": "pipegen-deepstream",
  "dimensions": {
    "width": 1920,
    "height": 1080
  },
  "detections": [
    {
      "track_id": 12,
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.934,
      "bbox": [0.412, 0.355, 0.518, 0.612]
    }
  ]
}
```

### Field Definitions

| Field Name | Type | Value Range / Constraints | Nullable | Description |
|---|---|---|---|---|
| `camera_id` | String | e.g. `"video-demo-01"` | No | Identifier for the video stream or camera. |
| `frame_id` | Integer | $\ge 0$, monotonically increasing | No | Sequence number of the video frame. |
| `timestamp_utc` | String | ISO-8601 UTC string | No | Capture/processing timestamp. |
| `source` | String | `"pipegen-deepstream"` | No | Perception pipeline source identifier. |
| `dimensions` | Object | `width`, `height` (positive integers) | No | Native resolution of video frame. |
| `detections` | Array | List of detection objects | No | Objects detected in the frame. Empty if no objects. |

### Detection Object Fields

| Field Name | Type | Value Range / Constraints | Nullable | Description |
|---|---|---|---|---|
| `track_id` | Integer | $\ge 0$ | **Yes** | Persistent tracking ID assigned by NvSORT/NvDCF. **Null if tracker is disabled or unassigned**. |
| `class_id` | Integer | `0` | No | Numeric class ID from model label map (`0 = person`). |
| `class_name` | String | `"person"` | No | Human-readable class name. |
| `confidence` | Float | $0.0 \dots 1.0$ | **Yes** | Detection confidence from TensorRT engine. |
| `bbox` | Array[4] | `[left, top, right, bottom]` | No | Normalized coordinates in $[0.0, 1.0]$ relative to frame width and height. |

---

## 4. Bounding Box Coordinate Conventions

1. **Normalized Space $[0.0 \dots 1.0]$:**
   - `left` = $x_{\text{min}} / \text{frame\_width}$
   - `top` = $y_{\text{min}} / \text{frame\_height}$
   - `right` = $x_{\text{max}} / \text{frame\_width}$
   - `bottom` = $y_{\text{max}} / \text{frame\_height}$
2. **Absolute Pixel Space (Fallback):**
   - If `bbox` coordinates exceed $1.0$, Person 2's `normalize_bbox` automatically divides by `frame_width` (1920) and `frame_height` (1080).
3. **Ground-Plane Feet Contact Rule:**
   - Person 2 calculates the worker's foot contact point as:
     $$\text{feet\_x} = \frac{\text{left} + \text{right}}{2}, \quad \text{feet\_y} = \text{bottom}$$
   - This point is evaluated against the restricted zone polygon using ray casting.

---

## 5. Mode A — DeepStream Pad Probe C/Python Integration

When running inside the DeepStream GStreamer pipeline, Person 1 extracts metadata from `NvDsFrameMeta` and `NvDsObjectMeta` using Python bindings (`pyds`):

```python
import pyds
from safety_events.adapters import parse_deepstream_pyds_meta

def osd_sink_pad_buffer_probe(pad, info, u_data):
    gst_buffer = info.get_buffer()
    batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
    l_frame = batch_meta.frame_meta_list
    
    while l_frame is not None:
        try:
            frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
        except StopIteration:
            break
            
        frame_num = frame_meta.frame_num
        l_obj = frame_meta.obj_meta_list
        frame_detections = []
        
        while l_obj is not None:
            try:
                obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
            except StopIteration:
                break
                
            # Filter for person class (class_id == 0)
            if obj_meta.class_id == 0:
                rect = obj_meta.rect_params
                raw_det = parse_deepstream_pyds_meta(
                    frame_num=frame_num,
                    camera_id="video-demo-01",
                    obj_meta_dict={
                        "object_id": obj_meta.object_id,
                        "obj_label": obj_meta.obj_label,
                        "confidence": obj_meta.confidence,
                        "rect_params": {
                            "left": rect.left,
                            "top": rect.top,
                            "width": rect.width,
                            "height": rect.height,
                        }
                    }
                )
                if raw_det:
                    frame_detections.append(raw_det)
            
            try:
                l_obj = l_obj.next
            except StopIteration:
                break
                
        # Forward directly to Person 2's SentinelEngine
        sentinel_engine.process_raw_detections(
            detections=frame_detections,
            frame_width=frame_meta.source_frame_width,
            frame_height=frame_meta.source_frame_height,
        )
        
        try:
            l_frame = l_frame.next
        except StopIteration:
            break
            
    return Gst.PadProbeReturn.OK
```

---

## 6. How Person 2 Verifies Handoff

Person 2 can test against this exact format using:
```bash
# Verify parsing of Person 1's mock stream:
python run_sentinel.py --stream tests/samples/mock_pipegen_stream.jsonl

# Verify parsing of DeepStream nvmsgbroker payload:
python run_sentinel.py --deepstream-json tests/samples/deepstream_sample.json
```
Both commands validate schema conformance, per-track state transitions, and JSONL output.
