"""Overnight evaluation — run with: python3 scripts/overnight_eval.py
Shows progress in real-time. Safe to run in tmux/screen or with nohup."""
import cv2, numpy as np, sys, json, os, time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

from avata360_monitor import extract_perspective, parse_avata_srt
from lateral_distance import parse_srt, calculate_lateral_distance
from ultralytics import YOLO

os.makedirs('outputs/evaluation', exist_ok=True)
start = time.time()

print("=" * 60)
print("  OVERNIGHT EVALUATION — VisDrone YOLOv8s 1280")
print("  Started:", time.strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)
print(flush=True)

print("Loading model...", flush=True)
model = YOLO('models/visdrone_yolov8s_1280_best.pt')
print(f"Model loaded in {time.time()-start:.1f}s\n", flush=True)

# ─────────────────────────────────────────────────────────────
# TASK 1: Avata 360 — per-second (197 seconds × 24 views)
# ─────────────────────────────────────────────────────────────
print("━" * 60)
print("TASK 1/4: Avata 360 — every second, 24 views each")
print("━" * 60, flush=True)

telem = parse_avata_srt(os.path.expanduser('~/DJI_20260612150146_0003_D.SRT'))
cap = cv2.VideoCapture(os.path.expanduser('~/DJI_20260612150146_0003_D.LRF'))
fps = cap.get(cv2.CAP_PROP_FPS)
duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps)

avata_data = []
for t in range(0, duration):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ret, frame = cap.read()
    if not ret:
        break
    srt_idx = min(int(t * 60), len(telem) - 1)
    alt = telem[srt_idx]['altitude'] if srt_idx < len(telem) else 0

    best_conf, best_yaw, best_pitch = 0, 0, 0
    for pitch in [30, 50, 70]:
        for yaw in range(0, 360, 45):
            view = extract_perspective(frame, fov_deg=90, yaw_deg=yaw, pitch_deg=pitch)
            r = model(view, conf=0.2, classes=[0, 1], imgsz=1280, verbose=False)[0]
            if len(r.boxes) > 0:
                c = max(float(b.conf) for b in r.boxes)
                if c > best_conf:
                    best_conf, best_yaw, best_pitch = c, yaw, pitch

    avata_data.append({'t': t, 'alt': alt, 'conf': round(best_conf, 3), 'yaw': best_yaw, 'pitch': best_pitch})

    # Progress every 10s
    if t % 10 == 0:
        pct = t / duration * 100
        eta = (time.time() - start) / max(t, 1) * (duration - t) / 60
        det = "✓" if best_conf > 0.25 else "·"
        print(f"  [{pct:5.1f}%] t={t:3d}s alt={alt:5.1f}m conf={best_conf:.2f} {det}  (ETA: {eta:.0f}min)", flush=True)

cap.release()
with open('outputs/evaluation/avata360_persecond_full.json', 'w') as f:
    json.dump(avata_data, f)
detected = sum(1 for d in avata_data if d['conf'] > 0.25)
print(f"\n  ✅ TASK 1 DONE: {len(avata_data)}s scanned, {detected} with person detected")
print(f"  Time: {(time.time()-start)/60:.1f} min\n", flush=True)

# ─────────────────────────────────────────────────────────────
# TASK 2: DJI M2EA — every second
# ─────────────────────────────────────────────────────────────
print("━" * 60)
print("TASK 2/4: DJI M2EA — per-second scan")
print("━" * 60, flush=True)

for vpath in ['data/DJI_0398_W.MP4', 'data/DJI_0111_W.MP4']:
    if not os.path.exists(vpath):
        print(f"  SKIP: {vpath} not found", flush=True)
        continue
    cap = cv2.VideoCapture(vpath)
    fps_v = cap.get(cv2.CAP_PROP_FPS)
    total_v = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    n_frames = total_v // int(fps_v)

    print(f"  Processing {vpath} ({n_frames} frames)...", flush=True)
    vid_results = []
    for i, fi in enumerate(range(0, total_v, int(fps_v))):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, conf=0.2, imgsz=1280, verbose=False)[0]
        classes = {}
        for b in results.boxes:
            n = results.names[int(b.cls)]
            classes[n] = classes.get(n, 0) + 1
        vid_results.append({'frame': fi, 'time': round(fi/fps_v, 1), 'dets': classes})

        if i % 20 == 0:
            print(f"    frame {i}/{n_frames} — {sum(classes.values())} objects", flush=True)

    cap.release()
    out = f'outputs/evaluation/{os.path.basename(vpath).replace(".MP4","")}_persecond.json'
    with open(out, 'w') as f:
        json.dump(vid_results, f)
    print(f"  ✅ {vpath}: {len(vid_results)} frames saved\n", flush=True)

# ─────────────────────────────────────────────────────────────
# TASK 3: Autel — every 2s across all RGB videos
# ─────────────────────────────────────────────────────────────
print("━" * 60)
print("TASK 3/4: Autel MAX 4T — all RGB videos, every 2s")
print("━" * 60, flush=True)

vdir = 'data/autel_20260612/video/rgb'
for vname in sorted(os.listdir(vdir)):
    if not vname.endswith('.MP4'):
        continue
    vpath = os.path.join(vdir, vname)
    cap = cv2.VideoCapture(vpath)
    fps_v = cap.get(cv2.CAP_PROP_FPS)
    total_v = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    n_frames = total_v // int(fps_v * 2)

    print(f"  {vname} ({n_frames} frames)...", end=" ", flush=True)
    vid_results = []
    for fi in range(0, total_v, int(fps_v * 2)):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fi)
        ret, frame = cap.read()
        if not ret:
            break
        results = model(frame, conf=0.2, imgsz=1280, verbose=False)[0]
        classes = {}
        for b in results.boxes:
            n = results.names[int(b.cls)]
            classes[n] = classes.get(n, 0) + 1
        vid_results.append({'frame': fi, 'time': round(fi/fps_v, 1), 'dets': classes})

    cap.release()
    out = f'outputs/evaluation/autel_{vname.replace(".MP4","")}_dense.json'
    with open(out, 'w') as f:
        json.dump(vid_results, f)
    print(f"✅ {len(vid_results)} frames", flush=True)

print(flush=True)

# ─────────────────────────────────────────────────────────────
# TASK 4: Pitch optimization (descent only, fine 5° sweep)
# ─────────────────────────────────────────────────────────────
print("━" * 60)
print("TASK 4/4: Avata 360 pitch sweep (160-197s, every 5°)")
print("━" * 60, flush=True)

cap = cv2.VideoCapture(os.path.expanduser('~/DJI_20260612150146_0003_D.LRF'))
fps = cap.get(cv2.CAP_PROP_FPS)
pitch_data = []
for t in range(160, 197):
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
    ret, frame = cap.read()
    if not ret:
        continue
    srt_idx = min(int(t * 60), len(telem) - 1)
    alt = telem[srt_idx]['altitude']
    row = {'t': t, 'alt': alt}
    for pitch in range(10, 90, 5):
        best = 0
        for yaw in range(0, 360, 45):
            view = extract_perspective(frame, fov_deg=90, yaw_deg=yaw, pitch_deg=pitch)
            r = model(view, conf=0.15, classes=[0], imgsz=1280, verbose=False)[0]
            if len(r.boxes) > 0:
                best = max(best, max(float(b.conf) for b in r.boxes))
        row[f'p{pitch}'] = round(best, 3)
    pitch_data.append(row)
    best_p = max(range(10, 90, 5), key=lambda p: row[f'p{p}'])
    print(f"  t={t}s alt={alt:.1f}m best_pitch={best_p}° conf={row[f'p{best_p}']:.2f}", flush=True)

cap.release()
with open('outputs/evaluation/avata360_pitch_sweep.json', 'w') as f:
    json.dump(pitch_data, f)
print(f"  ✅ Pitch sweep done\n", flush=True)

# ─────────────────────────────────────────────────────────────
elapsed = time.time() - start
print("=" * 60)
print(f"  ALL TASKS COMPLETE — {elapsed/3600:.1f} hours total")
print(f"  Finished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 60, flush=True)
