import os
import glob
import json
from datetime import datetime

import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# =========================
# CONFIG
# =========================

BASE_DIR = r""  # carpeta del ensayo
PICS_SUBDIR = "pics"
IMG_PATTERN = "image-*.tif"

RAW_DATA_FILENAME = "raw_data.csv"
RAW_IN_BASE_DIR = True

GAGE_LENGTH_MM = 35.0

WIDTH_MM = 5.0
THICKNESS_MM = 3.0

# Detección (tuyos)
BLUR_KSIZE = (5, 5)
SOBEL_KSIZE = 3
PROFILE_SMOOTH = 31
PEAK_PERCENTILE = 90
MAX_GAP = 15
USE_TRACKING = True
TRACK_WIN = 35
MIN_SEP = 40

# Debug/video
SAVE_DEBUG_EVERY = 10
SAVE_DEBUG_FRAMES = {0, 52, 105}
VIDEO_FPS = 5

# ======= Curva mejorada =======
# Suavizado strain (Savitzky–Golay simple con numpy)
SG_WINDOW = 11   # impar: 9, 11, 15...
SG_POLY = 2      # 2 o 3

# Recorte post-rotura: cortar cuando F cae por debajo de % de Fmax tras el pico
CROP_AFTER_PEAK = True
DROP_FRAC = 0.55  # cortar cuando force < DROP_FRAC * Fmax después del pico

# Si hay Displacement [mm] en raw_data: alineación por desplazamiento
USE_DISPLACEMENT_ALIGNMENT = True


# =========================
# ROI interactivo
# =========================
def select_roi_on_image(gray, window_name="Selecciona ROI (arrastra y Enter)"):
    if gray is None:
        raise ValueError("Imagen inválida para seleccionar ROI.")
    if gray.dtype != np.uint8:
        gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

    r = cv2.selectROI(window_name, gray, showCrosshair=True, fromCenter=False)
    cv2.destroyWindow(window_name)

    x, y, w, h = r
    if w == 0 or h == 0:
        raise RuntimeError("ROI vacío.")
    return int(x), int(x + w), int(y), int(y + h)


def roi_pixels_to_fractions(x1, x2, y1, y2, W, H):
    return (x1 / W, x2 / W, y1 / H, y2 / H)


def save_roi_fractions(path, roi_fracs):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            {"ROI_X1": roi_fracs[0], "ROI_X2": roi_fracs[1], "ROI_Y1": roi_fracs[2], "ROI_Y2": roi_fracs[3]},
            f,
            indent=2
        )


def load_roi_fractions(path):
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    return d["ROI_X1"], d["ROI_X2"], d["ROI_Y1"], d["ROI_Y2"]


# =========================
# Detect helpers
# =========================
def local_maxima_1d(a: np.ndarray) -> np.ndarray:
    if len(a) < 3:
        return np.array([], dtype=int)
    return np.where((a[1:-1] > a[:-2]) & (a[1:-1] > a[2:]))[0] + 1


def group_peaks(peaks: np.ndarray, max_gap: int) -> list[list[int]]:
    if peaks.size == 0:
        return []
    peaks = np.sort(peaks)
    groups = []
    cur = [int(peaks[0])]
    for p in peaks[1:]:
        p = int(p)
        if p - cur[-1] <= max_gap:
            cur.append(p)
        else:
            groups.append(cur)
            cur = [p]
    groups.append(cur)
    return groups


def weighted_center(profile: np.ndarray, idxs: list[int]) -> tuple[float, float]:
    g = np.array(idxs, dtype=float)
    w = profile[np.array(idxs)] + 1e-9
    y = float((g * w).sum() / w.sum())
    strength = float(w.sum())
    return y, strength


def pick_two_marks(marks: list[tuple[float, float]], min_sep: float) -> tuple[float, float] | None:
    if len(marks) < 2:
        return None
    marks_sorted = sorted(marks, key=lambda t: t[1], reverse=True)
    best = None
    best_score = -1.0
    for i in range(len(marks_sorted)):
        for j in range(i + 1, len(marks_sorted)):
            y1, s1 = marks_sorted[i]
            y2, s2 = marks_sorted[j]
            if abs(y2 - y1) < min_sep:
                continue
            score = s1 + s2
            if score > best_score:
                best_score = score
                best = (min(y1, y2), max(y1, y2))
    return best


def detect_extensometer_lines(gray: np.ndarray,
                              roi_fracs: tuple[float, float, float, float],
                              prev_marks_roi: tuple[float, float] | None):
    ROI_X1, ROI_X2, ROI_Y1, ROI_Y2 = roi_fracs
    H, W = gray.shape[:2]
    x1, x2 = int(ROI_X1 * W), int(ROI_X2 * W)
    y1, y2 = int(ROI_Y1 * H), int(ROI_Y2 * H)

    roi = gray[y1:y2, x1:x2]
    if roi.size == 0:
        return None

    roi_blur = cv2.GaussianBlur(roi, BLUR_KSIZE, 0)
    sobel_y = cv2.Sobel(roi_blur, cv2.CV_32F, 0, 1, ksize=SOBEL_KSIZE)
    edges = np.abs(sobel_y)

    profile = edges.mean(axis=1)
    profile_smooth = cv2.GaussianBlur(profile[:, None], (1, PROFILE_SMOOTH), 0).ravel()

    peaks = local_maxima_1d(profile_smooth)
    if peaks.size == 0:
        return None

    thr = np.percentile(profile_smooth, PEAK_PERCENTILE)
    peaks = peaks[profile_smooth[peaks] >= thr]
    if peaks.size == 0:
        return None

    if USE_TRACKING and prev_marks_roi is not None:
        y_prev_top, y_prev_bot = prev_marks_roi
        near = peaks[(np.abs(peaks - y_prev_top) <= TRACK_WIN) | (np.abs(peaks - y_prev_bot) <= TRACK_WIN)]
        peaks_use = near if near.size >= 2 else peaks
    else:
        peaks_use = peaks

    groups = group_peaks(peaks_use, MAX_GAP)
    if len(groups) == 0:
        return None

    marks = [weighted_center(profile_smooth, g) for g in groups]
    pair = pick_two_marks(marks, min_sep=MIN_SEP)
    if pair is None:
        return None

    y_top_roi, y_bot_roi = pair
    y_top = y1 + y_top_roi
    y_bot = y1 + y_bot_roi
    return (y_top_roi, y_bot_roi), (y_top, y_bot), (x1, x2, y1, y2)


# =========================
# Vídeo + plots
# =========================
def make_debug_video(debug_dir: str, out_video_path: str, fps: int = 5) -> bool:
    imgs = sorted(glob.glob(os.path.join(debug_dir, "dbg_*.png")))
    if not imgs:
        return False
    first = cv2.imread(imgs[0])
    if first is None:
        return False
    H, W, _ = first.shape
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video = cv2.VideoWriter(out_video_path, fourcc, fps, (W, H))
    for p in imgs:
        frame = cv2.imread(p)
        if frame is None:
            continue
        if frame.shape[:2] != (H, W):
            frame = cv2.resize(frame, (W, H), interpolation=cv2.INTER_AREA)
        video.write(frame)
    video.release()
    return True


# =========================
# Savitzky–Golay (numpy)
# =========================
def savgol_numpy(y: np.ndarray, window: int = 11, poly: int = 2) -> np.ndarray:
    """
    Suavizado tipo Savitzky–Golay sin SciPy (ajuste polinómico local por mínimos cuadrados).
    window impar.
    """
    y = np.asarray(y, dtype=float)
    n = len(y)
    if window % 2 == 0 or window < 3:
        raise ValueError("window debe ser impar y >=3")
    if poly >= window:
        raise ValueError("poly debe ser < window")

    half = window // 2
    x = np.arange(-half, half + 1, dtype=float)

    # Matriz de Vandermonde para ajuste polinómico
    A = np.vander(x, N=poly + 1, increasing=True)  # (window, poly+1)

    # Coeficientes para estimar el valor en x=0:
    # c = e0^T * (A^+), donde e0 selecciona el término constante en la base
    pinv = np.linalg.pinv(A)  # (poly+1, window)
    c = pinv[0]               # fila que da el intercepto => valor en x=0

    # Padding por reflejo
    ypad = np.r_[y[half:0:-1], y, y[-2:-half-2:-1]]
    out = np.empty(n, dtype=float)

    for i in range(n):
        seg = ypad[i:i + window]
        out[i] = np.dot(c, seg)
    return out


# =========================
# raw_data load + merge mejorado
# =========================
def load_raw_data(path: str) -> pd.DataFrame:
    try:
        df = pd.read_csv(path)
    except Exception:
        df = pd.read_csv(path, sep=";")

    # estandarizar nombres
    cols = df.columns.tolist()
    if "Time [s]" not in cols or "Force [N]" not in cols:
        raise ValueError(f"raw_data debe tener 'Time [s]' y 'Force [N]'. Columnas: {cols}")

    out = df.copy()
    out["time_s"] = pd.to_numeric(out["Time [s]"], errors="coerce")
    out["force_N"] = pd.to_numeric(out["Force [N]"], errors="coerce")

    # displacement opcional
    if "Displacement [mm]" in cols:
        out["disp_mm"] = pd.to_numeric(out["Displacement [mm]"], errors="coerce")
    else:
        out["disp_mm"] = np.nan

    out = out.dropna(subset=["time_s", "force_N"]).sort_values("time_s").reset_index(drop=True)
    out["time_s"] = out["time_s"] - out["time_s"].iloc[0]
    if np.isfinite(out["disp_mm"]).any():
        out["disp_mm"] = out["disp_mm"] - out["disp_mm"].iloc[0]
    return out


def assign_time_linear(n_frames: int, total_time_s: float) -> np.ndarray:
    if n_frames <= 1:
        return np.zeros(n_frames, dtype=float)
    dt = total_time_s / (n_frames - 1)
    return np.arange(n_frames, dtype=float) * dt


def crop_after_peak_force(df: pd.DataFrame, drop_frac: float = 0.55) -> pd.DataFrame:
    """
    Recorta después del pico: busca el primer punto (después del pico)
    donde force < drop_frac*Fmax y corta ahí.
    """
    if df.empty or "force_N_interp" not in df.columns:
        return df
    f = df["force_N_interp"].to_numpy()
    if len(f) < 5:
        return df
    imax = int(np.argmax(f))
    fmax = float(f[imax])
    if fmax <= 0:
        return df
    thr = drop_frac * fmax
    idx = None
    for i in range(imax + 1, len(f)):
        if f[i] < thr:
            idx = i
            break
    if idx is None:
        return df
    return df.iloc[:idx].copy()


def build_stress_strain(df_res: pd.DataFrame, df_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Construye stress–strain con sincronización mejorada:
    - si hay disp_mm en raw_data y está disponible => alinear por desplazamiento
    - si no => interpolación por tiempo
    """
    res = df_res.dropna(subset=["strain"]).copy().reset_index(drop=True)
    if res.empty:
        return res

    # strain suavizado (mejor curva)
    res["strain_smooth"] = savgol_numpy(res["strain"].to_numpy(), window=SG_WINDOW, poly=SG_POLY)

    # ----- 1) si hay displacement en raw_data: mapear "tiempo por disp" -----
    use_disp = USE_DISPLACEMENT_ALIGNMENT and np.isfinite(df_raw["disp_mm"]).any()

    if use_disp:
        # Creamos una variable "pseudo-tiempo" basada en desplazamiento:
        # - pasamos res->dL_mm (óptico) y lo alineamos con disp_mm (máquina)
        # Nota: dL_mm = strain * GAGE_LENGTH_MM
        res["dL_mm_opt"] = res["strain_smooth"] * GAGE_LENGTH_MM

        # raw: disp_mm vs time_s, force_N
        raw = df_raw.dropna(subset=["disp_mm", "force_N", "time_s"]).copy()
        raw = raw.sort_values("disp_mm").reset_index(drop=True)

        # res: dL_mm_opt debe ser creciente, así que lo ordenamos por dL_mm_opt
        # (si hay ruido, el SavGol lo mejora)
        res_sorted = res.sort_values("dL_mm_opt").reset_index(drop=True)

        # interpolar fuerza en función de disp (más estable que por tiempo)
        res_sorted["force_N_interp"] = np.interp(
            res_sorted["dL_mm_opt"].to_numpy(),
            raw["disp_mm"].to_numpy(),
            raw["force_N"].to_numpy()
        )

        # devolver al orden original de frames
        res = res_sorted.sort_index()

    else:
        # ----- 2) fallback: interpolación por tiempo -----
        total_time_s = float(df_raw["time_s"].max())
        res["time_s"] = assign_time_linear(len(res), total_time_s)

        raw = df_raw.copy()
        res["force_N_interp"] = np.interp(
            res["time_s"].to_numpy(),
            raw["time_s"].to_numpy(),
            raw["force_N"].to_numpy()
        )

    # stress
    A0_m2 = (WIDTH_MM * THICKNESS_MM) * 1e-6
    res["stress_MPa"] = (res["force_N_interp"] / A0_m2) / 1e6
    return res


# =========================
# MAIN: calcula strain desde imágenes, luego curva mejorada
# =========================
def analyze(base, ):

    pics_dir = os.path.join(base, PICS_SUBDIR)
    if not os.path.isdir(pics_dir):
        raise FileNotFoundError(f"No existe la carpeta de fotos: {pics_dir}")

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = os.path.join(base, f"output_{stamp}")
    debug_dir = os.path.join(out_dir, "debug")
    os.makedirs(debug_dir, exist_ok=True)

    roi_json = os.path.join(base, "roi.json")

    paths = sorted(glob.glob(os.path.join(pics_dir, IMG_PATTERN)))
    if not paths:
        raise FileNotFoundError(f"No hay imágenes {IMG_PATTERN} en {pics_dir}")

    gray0 = cv2.imread(paths[0], cv2.IMREAD_GRAYSCALE)
    if gray0 is None:
        raise RuntimeError("No pude leer el primer frame.")
    H0, W0 = gray0.shape[:2]

    if os.path.exists(roi_json):
        roi_fracs = load_roi_fractions(roi_json)
        print(f"[ROI] Cargado: {roi_json}")
    else:
        x1, x2, y1, y2 = select_roi_on_image(gray0)
        roi_fracs = roi_pixels_to_fractions(x1, x2, y1, y2, W0, H0)
        save_roi_fractions(roi_json, roi_fracs)
        print(f"[ROI] Seleccionado y guardado: {roi_json}")

    # raw_data
    raw_path = os.path.join(base, RAW_DATA_FILENAME) if RAW_IN_BASE_DIR else os.path.join(pics_dir, RAW_DATA_FILENAME)
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Falta raw_data: {raw_path}")
    df_raw = load_raw_data(raw_path)
    print(f"[RAW] Cargado: {raw_path} | cols={list(pd.read_csv(raw_path).columns)}")

    prev_marks_roi = None
    L0_px = None
    mm_per_px = None

    rows = []

    for i, p in enumerate(paths):
        gray = cv2.imread(p, cv2.IMREAD_GRAYSCALE)
        if gray is None:
            continue

        det = detect_extensometer_lines(gray, roi_fracs, prev_marks_roi)
        if det is None:
            continue

        (y_top_roi, y_bot_roi), (y_top, y_bot), (rx1, rx2, ry1, ry2) = det
        prev_marks_roi = (y_top_roi, y_bot_roi)

        L_px = float(y_bot - y_top)
        if L0_px is None:
            L0_px = L_px
            mm_per_px = GAGE_LENGTH_MM / L0_px

        dL_px = L_px - L0_px
        dL_mm = dL_px * mm_per_px
        strain = dL_mm / GAGE_LENGTH_MM

        rows.append([i, os.path.basename(p), L_px, dL_px, dL_mm, strain])

        # debug
        if (i % SAVE_DEBUG_EVERY == 0) or (i in SAVE_DEBUG_FRAMES) or (i == len(paths) - 1):
            dbg = cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
            cv2.rectangle(dbg, (rx1, ry1), (rx2, ry2), (255, 0, 0), 2)
            cv2.line(dbg, (0, int(round(y_top))), (dbg.shape[1] - 1, int(round(y_top))), (0, 255, 0), 2)
            cv2.line(dbg, (0, int(round(y_bot))), (dbg.shape[1] - 1, int(round(y_bot))), (0, 0, 255), 2)
            cv2.imwrite(os.path.join(debug_dir, f"dbg_{i:04d}.png"), dbg)

    if not rows:
        raise RuntimeError("No hay frames válidos del extensómetro óptico.")

    df_res = pd.DataFrame(rows, columns=["frame_idx", "filename", "L_px", "dL_px", "dL_mm", "strain"])
    out_csv = os.path.join(out_dir, "results_extensometer.csv")
    df_res.to_csv(out_csv, index=False)

    # Vídeo
    out_video = os.path.join(out_dir, "extensometer_check.mp4")
    make_debug_video(debug_dir, out_video, fps=VIDEO_FPS)

    # Curva mejorada
    df_curve = build_stress_strain(df_res, df_raw)

    if CROP_AFTER_PEAK:
        df_curve = crop_after_peak_force(df_curve, drop_frac=DROP_FRAC)

    out_curve_csv = os.path.join(out_dir, "results_merged_force_stress.csv")
    df_curve.to_csv(out_curve_csv, index=False)

    # Plot strain-time (si hay time)
    if "time_s" in df_curve.columns and df_curve["time_s"].notna().any():
        plt.figure(figsize=(11, 4))
        plt.plot(df_curve["time_s"], df_curve["strain"], alpha=0.35, label="Raw")
        plt.plot(df_curve["time_s"], df_curve["strain_smooth"], linewidth=2.5, label="SavGol")
        plt.xlabel("Time (s)")
        plt.ylabel("Strain (-)")
        plt.title("Strain vs time (raw + Savitzky–Golay)")
        plt.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(out_dir, "strain_vs_time.png"), dpi=200)
        plt.close()

    # Plot stress-strain (mejor)
    plt.figure(figsize=(6, 5))
    plt.plot(df_curve["strain_smooth"], df_curve["stress_MPa"], linewidth=2.5)
    plt.xlabel("Strain (-)")
    plt.ylabel("Stress (MPa)")
    plt.title("Stress–strain (improved alignment + smoothing)")
    plt.tight_layout()
    plt.savefig(os.path.join(out_dir, "stress_strain.png"), dpi=200)
    plt.close()

    print("\n=== DONE ===")
    print(f"Salida: {out_dir}")
    print(f"CSV extensómetro: {out_csv}")
    print(f"CSV curva: {out_curve_csv}")
    print(f"Vídeo: {out_video}")
    print(f"L0_px={L0_px:.3f} px -> mm/px={mm_per_px:.6f}")
    print("Nota: si raw_data tiene Displacement [mm], se alineó por desplazamiento (mejor que por tiempo).")


    # =========================
    # RESUMEN DESPLAZAMIENTO ENTRE LÍNEAS
    # =========================
    if not df_res.empty:
        # último frame útil
        dL_px_final = float(df_res["dL_px"].iloc[-1])
        dL_mm_final = float(df_res["dL_mm"].iloc[-1])
        strain_final = float(df_res["strain"].iloc[-1])

        # máximos (en valor absoluto por si hay pequeñas bajadas por ruido)
        idx_max = int(df_res["dL_mm"].abs().idxmax())
        dL_px_max = float(df_res.loc[idx_max, "dL_px"])
        dL_mm_max = float(df_res.loc[idx_max, "dL_mm"])
        strain_max = float(df_res.loc[idx_max, "strain"])
        frame_max = int(df_res.loc[idx_max, "frame_idx"])
        file_max = str(df_res.loc[idx_max, "filename"])

        print("\n=== DESPLAZAMIENTO ENTRE LÍNEAS ===")
        print(f"ΔL final: {dL_px_final:+.3f} px  ->  {dL_mm_final:+.4f} mm   (strain={strain_final:.6f})")
        print(f"ΔL máximo: {dL_px_max:+.3f} px  ->  {dL_mm_max:+.4f} mm   (strain={strain_max:.6f})")
        print(f"  en frame {frame_max}  ({file_max})")
    else:
        print("\n[INFO] No hay datos en df_res para calcular desplazamiento.")


if __name__ == "__main__":
    main()
