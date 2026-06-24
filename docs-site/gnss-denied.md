# UC3: GNSS-Denied Navigation

Visual positioning using CNN cross-view matching — fly without satellite signals.

## Results

| Metric | Value |
|--------|-------|
| **Median position error** | **5.8 m** |
| Mean error | 22.1 m (3 outliers) |
| Best case | 4.1 m |
| Under 25 m | 70% of tests |
| Model | EfficientNet-B2, 512-d embeddings |
| Training | 30 epochs, triplet loss, 500 pairs |
| Platform | Colab A100, ~10 min |
| Reference resolution | 768×768 px, 0.30 m/px |

## Cross-View Matching Visualization

![Cross-view matching results](images/crossview_matching_results.jpg)

*Green = true position, Red = CNN estimated position. Lines show error vector. Median: 5.8m.*

## How It Works

```
PRE-FLIGHT:
  Download satellite tiles of flight area
  → Embed each tile with CNN → build tile gallery (offline)

IN-FLIGHT:
  Downward camera frame
  → Embed with same CNN
  → Cosine similarity search against gallery
  → Best match = position estimate
  → Send VISION_POSITION_ESTIMATE to ArduPilot EKF3
  → Drone knows where it is WITHOUT GPS
```

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ Downward Camera │────→│ EfficientNet-B2  │────→│ 512-d embedding │
│ (live frame)    │     │ (feature extract) │     │                 │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │ cosine sim
┌─────────────────┐     ┌──────────────────┐     ┌────────▼────────┐
│ Satellite Tiles │────→│ Same CNN         │────→│ Tile Gallery    │
│ (pre-computed)  │     │ (offline)        │     │ (N×512 matrix)  │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                           │
                                                  ┌────────▼────────┐
                                                  │ Best match tile │
                                                  │ → lat/lon       │
                                                  └─────────────────┘
```

## Training Details

- **Backbone:** EfficientNet-B2 (pretrained ImageNet → fine-tuned)
- **Loss:** Triplet loss with hard negative mining
- **Embedding:** 512 dimensions (L2 normalized)
- **Augmentation:** Rotation (0-360°), scale (0.8-1.2×), brightness, blur
- **Data:** 500 satellite-drone image pairs + EuroSAT for pretraining
- **Inference:** <50ms per frame on GPU, <200ms on CPU

## Key Insights

- Cross-view matching provides **horizontal (2D) position only** — barometer handles altitude
- Works best at 30-80m AGL (ground features visible, not too much perspective distortion)
- Fails over: water, dense forest canopy, snow-covered terrain (no features)
- Combined with optical flow: cross-view provides absolute position, optical flow provides relative motion between matches

## Comparison: CNN vs ORB Baseline

| Method | Accuracy | Speed | Robustness |
|--------|----------|-------|------------|
| **CNN cross-view** | 5.8m median | 50ms/frame | Handles rotation, scale, seasonal change |
| ORB feature matching | 0.5m (same res) | 10ms/frame | Requires identical resolution, fails with rotation |

CNN is preferred for real-world use — ORB only works with pre-mapped identical-resolution imagery.

## Colab Notebook

- [GNSS-Denied Cross-View Training](https://colab.research.google.com/github/rwiren/drone-cv-detection/blob/main/notebooks/gnss_denied_crossview_training.ipynb) — EfficientNet-B2 + triplet loss, runs on A100

## Why This Matters

GPS/GNSS jamming is a daily reality in Nordic/Baltic airspace:

- Russian GNSS interference documented since 2017
- Finnish aviation advisories for eastern Finland
- Critical infrastructure (5G timing) depends on GPS

A drone that can navigate purely on camera enables operations in denied environments without any satellite dependency.
