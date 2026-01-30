import os
import cv2
import numpy as np


# =====================================================
# VIDEO LOADING
# =====================================================

def extract_frames_from_video(video_path: str):
    if not os.path.isfile(video_path):
        raise FileNotFoundError(f"ERROR: Video not found:\n{video_path}")

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError("ERROR: Cannot open video file with OpenCV.")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps <= 0:
        fps = 30.0  # fallback razonable

    frames = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))

    cap.release()

    if not frames:
        raise ValueError("ERROR: No frames read from the video.")

    return frames, fps


# =====================================================
# INTERACTIVE ROI SELECTION
# =====================================================

def select_roi_interactive(first_gray):
    """
    Returns ROI as (x, y, w, h) in original image coordinates.
    """
    bgr = cv2.cvtColor(first_gray, cv2.COLOR_GRAY2BGR)

    # OpenCV GUI ROI selector
    roi = cv2.selectROI(
        "Select ROI (drag with mouse, ENTER to confirm, ESC to cancel)",
        bgr,
        showCrosshair=True,
        fromCenter=False
    )
    cv2.destroyWindow("Select ROI (drag with mouse, ENTER to confirm, ESC to cancel)")

    x, y, w, h = roi
    if w == 0 or h == 0:
        raise ValueError("ERROR: ROI selection cancelled or empty.")

    return (int(x), int(y), int(w), int(h))


# =====================================================
# INTERACTIVE POINT CLICKS INSIDE ROI
# =====================================================

def get_two_clicks_in_roi(first_gray, roi_xywh, window_name="Calibration (click 2 points)"):
    """
    User clicks 2 points on ROI-cropped view.
    Returns points in FULL IMAGE coordinates: [(x0,y0), (x1,y1)]
    """
    x, y, w, h = roi_xywh
    roi_img = first_gray[y:y+h, x:x+w]
    view = cv2.cvtColor(roi_img, cv2.COLOR_GRAY2BGR)

    clicks = []

    def on_mouse(event, mx, my, flags, param):
        nonlocal view, clicks
        if event == cv2.EVENT_LBUTTONDOWN:
            clicks.append((mx, my))
            cv2.circle(view, (mx, my), 4, (0, 255, 0), -1)
            cv2.putText(view, str(len(clicks)), (mx + 6, my - 6),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            cv2.imshow(window_name, view)

    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, view)
    cv2.setMouseCallback(window_name, on_mouse)

    print("\nCalibration clicks:")
    print("  1) Click the BLACK marker (0 mm)")
    print("  2) Click the reference point (known distance in mm)")
    print("Close window automatically after 2 clicks.")

    while len(clicks) < 2:
        key = cv2.waitKey(20) & 0xFF
        if key == 27:  # ESC
            cv2.destroyWindow(window_name)
            raise ValueError("ERROR: Calibration cancelled (ESC).")

    cv2.destroyWindow(window_name)

    # Convert ROI-local clicks to full-image coords
    pts_full = [(x + cx, y + cy) for (cx, cy) in clicks]
    return pts_full


# =====================================================
# DETECTION
# =====================================================

def detect_black_marker_in_region(img_gray, bounds_xyxy, black_threshold):
    """
    Detect centroid of dark blob (marker) inside given bounds.
    bounds: (x1, y1, x2, y2) in image coords.
    Returns (x, y) or None.
    """
    h, w = img_gray.shape
    x1, y1, x2, y2 = bounds_xyxy

    x1 = max(0, int(x1)); y1 = max(0, int(y1))
    x2 = min(w, int(x2)); y2 = min(h, int(y2))

    if x1 >= x2 or y1 >= y2:
        return None

    roi = img_gray[y1:y2, x1:x2]
    _, bin_img = cv2.threshold(roi, black_threshold, 255, cv2.THRESH_BINARY_INV)

    ys, xs = np.where(bin_img == 255)
    if xs.size == 0:
        return None

    cx = int(xs.mean())
    cy = int(ys.mean())
    return (x1 + cx, y1 + cy)


# =====================================================
# TRACKING
# =====================================================

def track_marker(frames_gray, initial_xy, roi_xywh,
                 black_threshold=130,
                 search_left=10, search_right=30, search_up=20, search_down=20):
    """
    Tracks marker in each frame. Search region is centered on last known position,
    but also clamped to ROI.
    Returns list of (x,y).
    """
    rx, ry, rw, rh = roi_xywh
    roi_x1, roi_y1 = rx, ry
    roi_x2, roi_y2 = rx + rw, ry + rh

    x, y = initial_xy
    positions = []

    for frame in frames_gray:
        # Proposed local search bounds around last position
        x1 = x - search_left
        y1 = y - search_up
        x2 = x + search_right
        y2 = y + search_down

        # Clamp to ROI
        x1 = max(x1, roi_x1); y1 = max(y1, roi_y1)
        x2 = min(x2, roi_x2); y2 = min(y2, roi_y2)

        detected = detect_black_marker_in_region(frame, (x1, y1, x2, y2), black_threshold)
        if detected is not None:
            x, y = detected

        positions.append((x, y))

    return positions


# =====================================================
# ANALYSIS
# =====================================================

def analyze_video_interactive_roi(
    video_path: str,
    reference_distance_mm: float,
    black_threshold: int = 130
):
    """
    Interactive workflow:
      1) user selects ROI on first frame
      2) user clicks marker (0mm) and reference point (known mm) inside ROI
      3) tracks marker and computes displacement in mm

    Returns dict with max displacement and per-frame series.
    """
    frames, fps = extract_frames_from_video(video_path)
    first = frames[0]

    roi = select_roi_interactive(first)
    marker_pt, ref_pt = get_two_clicks_in_roi(first, roi)

    # Calibration: using X distance like your original approach
    px_dist = abs(ref_pt[0] - marker_pt[0])
    if px_dist == 0:
        raise ValueError("ERROR: Calibration points have zero pixel distance in X.")

    mm_per_px = reference_distance_mm / float(px_dist)
    x0 = marker_pt[0]

    # Initial center refinement (optional): search tiny region near marker click
    init = detect_black_marker_in_region(first,
                                         (marker_pt[0]-10, marker_pt[1]-10, marker_pt[0]+10, marker_pt[1]+10),
                                         black_threshold) or marker_pt

    positions = track_marker(frames, init, roi, black_threshold=black_threshold)

    results = []
    max_disp = 0.0
    for i, (x, y) in enumerate(positions):
        dx_raw = (x - x0) * mm_per_px

        # Monotonic constraint (like your original): never decreases
        if dx_raw > max_disp:
            max_disp = dx_raw

        results.append({
            "frame": i,
            "time_s": i / fps,
            "displacement_mm": max_disp
        })

    return {
        "fps": fps,
        "roi": roi,
        "mm_per_px": mm_per_px,
        "max_displacement_mm": max_disp,
        "data": results
    }


# =====================================================
# CLI MAIN
# =====================================================

def analyze(video_path, reference_distance_mm):

    out = analyze_video_interactive_roi(
        video_path=video_path,
        reference_distance_mm=reference_distance_mm,
        black_threshold=130
    )

    return out
