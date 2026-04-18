import cv2
import numpy as np

# --- Fog Detection Functions ---

def get_laplacian_score(gray):
    """Blur score — low value = blurry = fog."""
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def get_contrast_score(gray):
    """Contrast score — low std = washed out = fog."""
    return gray.std()

def get_visibility_score(frame):
    """Combined score 0-100. Higher = clearer."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blur   = get_laplacian_score(gray)
    contrast = get_contrast_score(gray)

    # Normalize blur (0-500 typical range) to 0-50
    blur_norm = min(blur / 500.0 * 50, 50)
    # Normalize contrast (0-80 typical range) to 0-50
    contrast_norm = min(contrast / 80.0 * 50, 50)

    score = blur_norm + contrast_norm
    return round(min(score, 100), 1)

def get_fog_level(score):
    """Classify score into fog level."""
    if score >= 70:
        return "CLEAR", (0, 200, 80)       # green
    elif score >= 40:
        return "MODERATE FOG", (0, 165, 255)  # orange
    else:
        return "DENSE FOG", (0, 0, 220)    # red

def draw_overlay(frame, score, level, color):
    """Draw visibility info on frame."""
    h, w = frame.shape[:2]

    # Dark top bar
    overlay = frame.copy()
    cv2.rectangle(overlay, (0, 0), (w, 80), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.5, frame, 0.5, 0, frame)

    # Project name
    cv2.putText(frame, "SmartFog — NH-503 Dharamshala Highway",
                (12, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

    # Fog level label
    cv2.putText(frame, level, (12, 55),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 2)

    # Visibility score bar (right side)
    bar_x, bar_y, bar_w, bar_h = w - 200, 15, 160, 20
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h),
                  (60, 60, 60), -1)
    filled = int(bar_w * score / 100)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + filled, bar_y + bar_h),
                  color, -1)
    cv2.putText(frame, f"Visibility: {score}%",
                (bar_x, bar_y + bar_h + 18),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    # Warning box if fog detected
    if score < 70:
        warn_overlay = frame.copy()
        cv2.rectangle(warn_overlay, (0, h - 60), (w, h), (0, 0, 180), -1)
        cv2.addWeighted(warn_overlay, 0.6, frame, 0.4, 0, frame)
        cv2.putText(frame, "⚠  ALERT: LOW VISIBILITY — SLOW DOWN TO 20 KM/H",
                    (12, h - 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

    return frame


# --- Main ---

def main():
    print("SmartFog — Fog Detection System")
    print("================================")
    print("Press Q to quit")
    print("Press S to save a screenshot")
    print()

    # Change to a video file path if you have one:
    # cap = cv2.VideoCapture("road_video.mp4")
    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("ERROR: Could not open camera/video.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Video ended or camera disconnected.")
            break

        score = get_visibility_score(frame)
        level, color = get_fog_level(score)
        frame = draw_overlay(frame, score, level, color)

        # Print to terminal too
        print(f"\rVisibility: {score:5.1f}% | Level: {level:<15}", end="", flush=True)

        cv2.imshow("SmartFog — Fog Detection", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('s'):
            filename = f"screenshot_{int(cv2.getTickCount())}.jpg"
            cv2.imwrite(filename, frame)
            print(f"\nScreenshot saved: {filename}")

    cap.release()
    cv2.destroyAllWindows()
    print("\nDone.")

if __name__ == "__main__":
    main()