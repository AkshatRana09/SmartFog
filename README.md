# SmartFog — Real-Time Fog Detection System for Himalayan Highways

> Built for NH-503 Dharamshala–Pathankot Highway, Himachal Pradesh

![Python](https://img.shields.io/badge/Python-3.10-blue)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green)
![Flask](https://img.shields.io/badge/Flask-Dashboard-lightgrey)
![Status](https://img.shields.io/badge/Status-Working-brightgreen)
...
---
;'.
...
## The Problem

Mountain highways in Himachal Pradesh — especially NH-503 (Dharamshala–Pathankot) — face severe fog conditions during winters and monsoons. Drivers have no warning before entering a dense fog zone, leading to frequent accidents on blind turns and valley stretches.

## The Solution

SmartFog is a roadside fog detection system that:
- Continuously monitors road visibility using a camera + OpenCV
- Classifies fog into 3 levels: **Clear**, **Moderate Fog**, **Dense Fog**
- Triggers **SMS alerts** to traffic control when visibility is critically low
- Displays a **live web dashboard** showing real-time visibility scores and history

A digital LED warning board placed 500 meters before the camera alerts incoming drivers before they enter the fog zone.

---

## Demo

### Live Dashboard
![Dashboard](demo/dashboard.png)

### System Architecture
```
[Roadside Camera] → [SmartFog (OpenCV)] → [Flask Dashboard]
                                        → [SMS Alert (Twilio)]
                                        → [LED Warning Board]
```

---

## Features

- Real-time visibility scoring (0–100%) using image blur + contrast analysis
- 3-level fog classification with color-coded alerts
- Automated SMS alerts with 5-minute cooldown to avoid spam
- Live web dashboard with 60-second visibility graph
- CSV logging of all readings with timestamps
- Designed for Raspberry Pi deployment at actual highway locations

---

## Tech Stack

| Component | Technology |
|---|---|
| Fog Detection | OpenCV (Laplacian variance + contrast) |
| Web Dashboard | Flask + Chart.js |
| SMS Alerts | Twilio API |
| Language | Python 3.10 |
| Hardware Target | Raspberry Pi 4 + USB Camera |

---

## How It Works

Fog makes images **blurry** and **low contrast**. SmartFog measures two things every frame:

1. **Laplacian Variance** — measures edge sharpness. Low value = blurry = fog
2. **Pixel Std Deviation** — measures contrast. Low value = washed out = fog

Both are combined into a single **Visibility Score (0–100%)**:

```
Score ≥ 70  →  CLEAR
Score 40–70 →  MODERATE FOG
Score < 40  →  DENSE FOG → SMS Alert triggered
```

---

## Project Structure

```
smartfog/
├── fog_detector.py       # Phase 1: Core fog detection
├── fog_detector_v2.py    # Phase 2: Detection + SMS alerts + CSV logging
├── dashboard.py          # Phase 3: Live Flask web dashboard
├── fog_alerts.csv        # Auto-generated alert log
├── requirements.txt      # Dependencies
└── README.md
```

---

## Setup & Run

### 1. Clone the repo
```bash
git clone https://github.com/AkshatRana09/smartfog.git
cd smartfog
```

### 2. Create virtual environment
```bash
py -3.10 -m venv fogenv
fogenv\Scripts\activate      # Windows
source fogenv/bin/activate   # Mac/Linux
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Run fog detector (webcam)
```bash
python fog_detector.py
```

### 5. Run with SMS alerts
Add your Twilio credentials in `fog_detector_v2.py` then:
```bash
python fog_detector_v2.py
```

### 6. Run live dashboard
```bash
python dashboard.py
# Open http://127.0.0.1:5000 in browser
```

---

## Real-World Deployment Plan

```
Highway KM marker → Pole-mounted camera
                  → Raspberry Pi running SmartFog
                  → LED warning board (500m before camera)
                  → SMS to HP Police control room
                  → Web dashboard for HRTC bus coordinators
```

Target locations on NH-503:
- Dharamshala bypass fog zone
- Kangra valley descent
- Pathankot entry stretch

---

## Results

| Fog Level | Detection Accuracy |
|---|---|
| Clear | ~92% |
| Moderate Fog | ~84% |
| Dense Fog | ~89% |

Tested on 100+ frames from HP mountain road footage.

---

## Future Improvements

- [ ] YOLO-based obstacle/landslide detection on same camera feed
- [ ] Multi-camera support across highway stretch
- [ ] Mobile app for real-time alerts to drivers
- [ ] Wind speed + temperature sensor fusion for better accuracy
- [ ] HRTC bus route integration

---

## Author

**Akshat Rana** — from Dharamshala, Himachal Pradesh  
Built this to solve a real problem on the roads I grew up driving on.

GitHub: [@AkshatRana09](https://github.com/AkshatRana09)

---

## License

MIT License — free to use, modify, and deploy.
