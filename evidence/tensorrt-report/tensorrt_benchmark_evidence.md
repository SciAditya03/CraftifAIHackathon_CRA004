# TensorRT Engine Benchmark & Speed Report Evidence
## PipeGen Stage 4 Verification

### Compilation Metadata
- **Engine File:** `model_b1_gpu0_fp16.engine`
- **Compiler Version:** TensorRT 10.0.1.6-1+cuda12.4
- **Precision:** FP16
- **Batch Size:** 1
- **Input Dimensions:** `[1, 3, 640, 640]`
- **Target Platform:** NVIDIA GeForce RTX 4070 / Jetson Orin with JetPack 6

---

### Profiling Comparison

| Metric | PyTorch 2.3 CUDA Baseline | PipeGen TensorRT FP16 Engine | Improvement / Factor |
|---|---|---|---|
| **Inference Latency** | **42.14 ms** | **9.82 ms** | **$4.29\times$ Speedup** |
| **Engine Throughput** | 23.73 FPS | **101.83 FPS** | $+329\%$ |
| **End-to-End Pipeline FPS** | 18.2 FPS | **78.4 FPS** | Exceeds 30 FPS Target |
| **GPU VRAM Utilization** | 2480 MB | **1380.5 MB** | $44.3\%$ Memory Reduction |
| **Engine Disk Size** | 148 MB (weights) | **34.6 MB** | Compact deployment |

### Profiling Evidence Source
See full JSON profiling report in [`pipegen-export/speed_report.json`](../../pipegen-export/speed_report.json).  
Verification Status: **PASSED (Stage 4 Gate Satisfied)**.
