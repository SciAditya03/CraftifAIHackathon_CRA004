"""NVIDIA DeepStream Pipeline Runner with TensorRT Inference and Safety Pad Probe.

Represents Stage 5 (Run) of the CraftifAI PipeGen workflow.
Executes on x86_64 Linux with NVIDIA GPU or Jetson Orin with JetPack 6.
Extracts NvDsObjectMeta detections and dispatches directly to SentinelEngine.
Includes graceful fallback simulation for non-DeepStream development environments.
"""

from __future__ import annotations

import argparse
import datetime
import os
import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from safety_events.adapters import parse_deepstream_pyds_meta
from safety_events.engine import SentinelEngine
from safety_events.models import ZoneRuleType
from safety_events.zone_rules import create_rectangular_zone


def run_deepstream_native(
    video_path: str,
    output_jsonl: str = "demo/sample_events.jsonl",
) -> None:
    """Launch native NVIDIA DeepStream GStreamer pipeline with pyds pad probe."""
    import gi
    gi.require_version("Gst", "1.0")
    from gi.repository import GLib, Gst  # type: ignore
    import pyds  # type: ignore

    Gst.init(None)

    # Initialize Safety Sentinel Engine
    engine = SentinelEngine(output_jsonl_path=output_jsonl, enable_console_alerts=True)
    zone = create_rectangular_zone(
        zone_id="restricted-zone-01",
        x1=0.3,
        y1=0.3,
        x2=0.7,
        y2=0.7,
        name="Hazardous Machinery Area",
        rule_type=ZoneRuleType.FEET_POINT,
    )
    engine.add_zone(zone)
    engine.emit_system_health("video-demo-01", "Native DeepStream 7.0 pipeline active.")

    print(f"[*] Building DeepStream pipeline for: {video_path}")
    pipeline = Gst.Pipeline()

    # Elements: filesrc -> qtdemux -> h264parse -> nvv4l2decoder -> nvstreammux -> nvinfer -> nvtracker -> nvdsosd -> nveglglessink
    source = Gst.ElementFactory.make("filesrc", "file-source")
    source.set_property("location", video_path)

    demux = Gst.ElementFactory.make("qtdemux", "demuxer")
    parser = Gst.ElementFactory.make("h264parse", "h264-parser")
    decoder = Gst.ElementFactory.make("nvv4l2decoder", "nvv4l2-decoder")

    streammux = Gst.ElementFactory.make("nvstreammux", "stream-muxer")
    streammux.set_property("width", 1920)
    streammux.set_property("height", 1080)
    streammux.set_property("batch-size", 1)
    streammux.set_property("batched-push-timeout", 33333)

    pgie = Gst.ElementFactory.make("nvinfer", "primary-nvinference-engine")
    pgie.set_property("config-file-path", "pipegen-export/config_infer_primary.txt")

    tracker = Gst.ElementFactory.make("nvtracker", "tracker")
    tracker.set_property("ll-lib-file", "libnvds_nvmultiobjecttracker.so")
    tracker.set_property("ll-config-file", "pipegen-export/config_tracker_NvSORT.yml")
    tracker.set_property("tracker-width", 640)
    tracker.set_property("tracker-height", 384)

    osd = Gst.ElementFactory.make("nvdsosd", "onscreendisplay")
    sink = Gst.ElementFactory.make("fakesink", "fake-sink")

    for elem in [source, demux, parser, decoder, streammux, pgie, tracker, osd, sink]:
        if not elem:
            raise RuntimeError("Failed to create GStreamer element. Check DeepStream installation.")
        pipeline.add(elem)

    source.link(demux)
    parser.link(decoder)

    def on_pad_added(src, new_pad):
        sink_pad = parser.get_static_pad("sink")
        if not sink_pad.is_linked():
            new_pad.link(sink_pad)

    demux.connect("pad-added", on_pad_added)

    # Link decoder to streammux sink_0
    sinkpad = streammux.get_request_pad("sink_0")
    srcpad = decoder.get_static_pad("src")
    srcpad.link(sinkpad)

    streammux.link(pgie)
    pgie.link(tracker)
    tracker.link(osd)
    osd.link(sink)

    # Pad probe callback to extract NvDsObjectMeta and forward to SentinelEngine
    def osd_sink_pad_buffer_probe(pad, info, u_data):
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            return Gst.PadProbeReturn.OK

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

                if obj_meta.class_id == 0:  # person
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
                            },
                        },
                    )
                    if raw_det:
                        frame_detections.append(raw_det)

                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break

            # Forward to SentinelEngine
            engine.process_raw_detections(
                detections=frame_detections,
                frame_width=frame_meta.source_frame_width,
                frame_height=frame_meta.source_frame_height,
            )

            try:
                l_frame = l_frame.next
            except StopIteration:
                break

        return Gst.PadProbeReturn.OK

    osd_sink_pad = osd.get_static_pad("sink")
    osd_sink_pad.add_probe(Gst.PadProbeType.BUFFER, osd_sink_pad_buffer_probe, 0)

    # Run GStreamer main loop
    loop = GLib.MainLoop()
    pipeline.set_state(Gst.State.PLAYING)
    try:
        loop.run()
    except KeyboardInterrupt:
        pass
    finally:
        pipeline.set_state(Gst.State.NULL)


def run_pipeline_fallback(
    stream_path: str = "tests/samples/mock_pipegen_stream.jsonl",
    output_jsonl: str = "demo/sample_events.jsonl",
    fps: float = 15.0,
) -> None:
    """Fallback runner for environments without native DeepStream/GStreamer."""
    print("[*] Running in PipeGen perception stream ingestion mode (cross-platform).")
    from demo.simulate_live_run import run_simulation
    run_simulation(stream_path=stream_path, output_jsonl=output_jsonl, fps=fps)


def main() -> None:
    parser = argparse.ArgumentParser(description="PipeGen DeepStream Stage 5 Live Perception Runner")
    parser.add_argument("--source", default="test_assets/safety_video.mp4", help="Path to input video file")
    parser.add_argument("--stream", default="tests/samples/mock_pipegen_stream.jsonl", help="Fallback JSONL stream")
    parser.add_argument("--output", default="demo/sample_events.jsonl", help="Output JSONL path")
    parser.add_argument("--fps", type=float, default=15.0, help="Playback FPS")
    args = parser.parse_args()

    # Try native DeepStream first
    try:
        import pyds  # noqa: F401
        import gi    # noqa: F401
        print("[+] NVIDIA DeepStream SDK detected. Launching native GStreamer pipeline.")
        run_deepstream_native(video_path=args.source, output_jsonl=args.output)
    except (ImportError, RuntimeError) as e:
        print(f"[-] Native DeepStream not active in current environment ({e}).")
        print("[+] Falling back to PipeGen verified perception stream.")
        run_pipeline_fallback(stream_path=args.stream, output_jsonl=args.output, fps=args.fps)


if __name__ == "__main__":
    main()
