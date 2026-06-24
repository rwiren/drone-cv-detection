# Roadmap

### Completed ✅
- [x] **360° full pipeline** — dual-fisheye extraction with correct equidistant projection
- [x] **Colab A100 training** — YOLOv8s (mAP50 0.532) and YOLOv8m (mAP50 0.581) at imgsz=1280
- [x] **Dual-model ensemble** — v8m (aerial >3m) + COCO (close <3m), validated on Avata 360 at ~2-7m
- [x] **DJI M2EA person re-validation** — VisDrone 1280 detects pedestrians at 70m (0.86 conf with v8s)
- [x] **3-platform validation** — all drones tested with 1280 models for both use cases
- [x] **Combined 3-platform training** — VisDrone + 1246 Avata 360 crops (mAP50 0.580, domain-adapted)
- [x] **3D Gaussian Splatting (UC4)** — PSNR 34.2 dB, 432/432 images, photorealistic novel views
- [x] **GNSS-Denied Navigation (UC3)** — CNN cross-view matching, median 5.8m accuracy
- [x] **Codebase quality** — 48 unit tests, unified CLI, centralized config, structured logging

### Near-term
- [ ] **Voice-controlled flight** — LLM (Llama 3.1) → MCP → MAVLink (droneserver)
- [ ] **GNSS spoofing resilience** — SITL-based attack simulation + defense validation
- [ ] **Thermal person detection** — fine-tune YOLOv8 on IR video frames
- [ ] **Real-time MQTT monitor** — validate live 1:1 rule alerting during flight

### Research directions
- [ ] **MCP drone interface** — Model Context Protocol for LLM→drone tool calling
- [ ] **SecuringSkies fusion** — publish detections to multi-agent tactical picture
- [ ] **Splat-based localization** — use trained Gaussian Splat for cm-level visual positioning
- [ ] **Edge deployment** — run YOLO on Jetson/RPi connected to drone RTSP stream
- [ ] **Multi-drone collaborative detection** — networked swarm with shared detections

