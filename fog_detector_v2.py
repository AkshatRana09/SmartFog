import cv2
import numpy as np
import csv
import os
from datetime import datetime
from twilio.rest import Client

# --- Twilio Config ---
# --- Twilio Config ---
TWILIO_SID   = "your_twilio_sid_here"
TWILIO_TOKEN = "your_twilio_token_here"
TWILIO_FROM  = "your_twilio_number_here"
ALERT_TO     = "your_mobile_number_here"
client = Client(TWILIO_SID, TWILIO_TOKEN)

# --- CSV Log Setup ---
LOG_FILE = "fog_alerts.csv"
if not os.path.exists(LOG_FILE):
    with open(LOG_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Timestamp", "Visibility Score", "Fog Level", "Alert Sent"])

def log_event(score, level, alert_sent):
    with open(LOG_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                         score, level, alert_sent])

# --- SMS Alert ---
last_alert_time = None
ALERT_COOLDOWN_SECONDS = 300  # 5 minutes between alerts

def send_alert(score, level):
    global last_alert_time
    now = datetime.now()
    if last_alert_time:
        elapsed = (now - last_alert_time).total_seconds()
        if elapsed < ALERT_COOLDOWN_SECONDS:
            return False

    try:
        msg = (f"SmartFog Alert - NH-503 Dharamshala Highway\n"
               f"Fog Level: {level}\n"
               f"Visibility Score: {score}%\n"
               f"Time: {now.strftime('%H:%M:%S')}\n"
               f"Action: Slow down to 20 KM/H")
        client.messages.create(body=msg, from_=TWILIO_FROM, to=ALERT_TO)
        last_alert_time = now
        print(f"\n SMS SENT at {now.strftime('%H:%M:%S')} — Score: {score}%")
        return True
    except Exception as e:
        print(f"\n SMS failed: {e}")
        return False

# --- Fog Detection ---
def get_visibility_score(frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.Laplacian(gray, cv2.CV_64F).var()
    contrast = gray.std()
    blur_norm = min(blur / 500.0 * 50, 50)
    contrast_norm = min(contrast / 80.0 * 50, 50)
    return round(min(blur_norm + contrast_norm, 100), 1)

def get_fog_level(score):
    if score >= 70:
        return "CLEAR", (0, 200, 80)
    elif score >= 40:
        return "MODERATE FOG", (0, 165, 255)
    else:
        return "DENSE FOG", (0, 0, 220)

def draw_overlay(frame, score, level, color, alert_sent):
    h, w = frame.shape[:2]
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    cv2.putText(frame, "SmartFog — NH-503 Dharamshala Highway",
                (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)
    cv2.putText(frame, level, (12, 58),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    bar_x, bar_y, bar_w, bar_h = w - 200, 15, 160, 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (60, 60, 60), -1)
    filled = int(bar_w * score / 100)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled, bar_y + bar_h), color, -1)
    cv2.putText(frame, f"Visibility: {score}%",
                (bar_x, bar_y + bar_h + 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    if alert_sent:
        cv2.putText(frame, "SMS SENT!", (w - 130, 72),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 200), 2)

    if score < 70:
        warn_overlay = frame.copy()
        cv2.rectangle(warn_overlay, (0, h - 60), (w, h), (0, 0, 180), -1)
        cv2.addWeighted(warn_overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, "ALERT: LOW VISIBILITY — SLOW DOWN TO 20 KM/H",
                    (12, h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (255, 255, 255), 2)
    return frame


# --- Main ---
def main():
    print("SmartFog Phase 2 — Fog Detection + SMS Alert")
    print("=" * 46)
    print("Press Q to quit | Press T to test SMS now")
    print()

    cap = cv2.VideoCapture(0)
    # cap = cv2.VideoCapture("road_video.mp4")

    if not cap.isOpened():
        print("ERROR: Could not open camera.")
        return

    frame_count = 0
    alert_sent = False
    score = 50
    level = "CLEAR"
    color = (0, 200, 80)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame_count += 1

        # Analyze every 15 frames (saves CPU)
        if frame_count % 15 == 0:
            score = get_visibility_score(frame)
            level, color = get_fog_level(score)

            # Send SMS if dense fog
            alert_sent = False
            if score < 40:
                alert_sent = False  # SMS disabled — limit reached
                print(f"\r[ALERT WOULD FIRE] Score: {score}%", end="")

            # Log every reading
            log_event(score, level, alert_sent)

            print(f"\rVisibility: {score:5.1f}% | {level:<15}", end="", flush=True)

        frame = draw_overlay(frame, score, level, color, alert_sent)
        cv2.imshow("SmartFog — Fog Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('t'):
            print("\nSending test SMS...")
            send_alert(0, "TEST ALERT")

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone. Alerts logged to {LOG_FILE}")

if __name__ == "__main__":
    main()