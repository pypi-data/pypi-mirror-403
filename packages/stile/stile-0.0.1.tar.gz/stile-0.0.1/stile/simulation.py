#!/usr/bin/env python3
"""
TMA Point Dataset with Rich Artifacts:
- Multiple slits per core (linear gaps)
- Elliptical cores (eccentricity + orientation)
- Grid defects (random + block missingness)
- Global affine + optional non-rigid TPS warp (if SciPy available)
- Edge crop (truncate at canvas border)
- Bubbles (circular holes), folds/tears (curved bands), pen marks (preview-only)
- Spurious dust points (preview-only)
- Noisy, vignetted, stained preview rendering

Outputs:
  - tma_cores.csv
  - tma_points.csv
  - tma_points_preview.png
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import scanpy as sc
# ---- Optional deps (fallbacks if missing) ----
try:
    from scipy.interpolate import Rbf
    from scipy.ndimage import gaussian_filter
    SCIPY_OK = True
except Exception:
    SCIPY_OK = False

try:
    from shapely.geometry import Point as SPoint, Polygon
    SHAPELY_OK = True
except Exception:
    SHAPELY_OK = False

try:
    from stile.conf import SIMULATED_DATASET_DIR, DATASET_DIR
except Exception as e:
    raise ImportError(f"{e}\nPlease create a stile/conf.py file with SIMULATED_DATASET_DIR defined.")

# rng = np.random.default_rng(SEED)

# -----------------------
# Helper functions
# -----------------------
def affine_transform(points_yx, rotation_deg, scale_xy, shear_x_deg, translate_xy):
    sy, sx = scale_xy[1], scale_xy[0]
    th = np.deg2rad(rotation_deg)
    sh = np.deg2rad(shear_x_deg)
    R = np.array([[np.cos(th), -np.sin(th)],
                  [np.sin(th),  np.cos(th)]])
    S = np.diag([sy, sx])
    Sh = np.array([[1.0, np.tan(sh)],
                   [0.0, 1.0]])
    A = Sh @ R @ S
    pts = points_yx @ A.T
    pts += np.array([translate_xy[1], translate_xy[0]])  # (ty, tx)
    return pts

def thin_plate_warp(points_yx, canvas_hw, amp=25.0, n_ctrl=6, seed=0):
    if not SCIPY_OK or amp <= 0 or n_ctrl <= 0:
        return points_yx.copy()
    H, W = canvas_hw
    rng_local = np.random.default_rng(seed)
    ctrl = [(0,0), (0,W-1), (H-1,0), (H-1,W-1), (H//2, W//2)]
    for _ in range(n_ctrl):
        ctrl.append((rng_local.uniform(0, H), rng_local.uniform(0, W)))
    ctrl = np.array(ctrl)
    dy = rng_local.normal(0, amp, size=len(ctrl))
    dx = rng_local.normal(0, amp, size=len(ctrl))
    rbf_y = Rbf(ctrl[:,0], ctrl[:,1], dy, function='thin_plate')
    rbf_x = Rbf(ctrl[:,0], ctrl[:,1], dx, function='thin_plate')
    disp_y = rbf_y(points_yx[:,0], points_yx[:,1])
    disp_x = rbf_x(points_yx[:,0], points_yx[:,1])
    return points_yx + np.stack([disp_y, disp_x], axis=1)

def sample_points_in_ellipse(n, a, b, jitter_std, bias=0.0, rng=None):
    # sample in circle then scale to ellipse (a,b are semi-axes)
    u = rng.random(n)
    r = (u ** (1.0 / (2.0 + bias)))
    th = rng.uniform(0, 2*np.pi, size=n)
    x = r * np.cos(th)
    y = r * np.sin(th)
    # scale to ellipse, then add jitter
    x = a * x + rng.normal(0, jitter_std, size=n)
    y = b * y + rng.normal(0, jitter_std, size=n)
    return x, y

def rotate_xy(x, y, angle_deg):
    ang = np.deg2rad(angle_deg)
    xr = x*np.cos(ang) - y*np.sin(ang)
    yr = x*np.sin(ang) + y*np.cos(ang)
    return xr, yr

def make_slit_descriptor(center_xy, radius, angle_deg, width):
    cx, cy = center_xy
    L = radius * 2.2
    W = width
    rect = np.array([[-L/2, -W/2],
                     [ L/2, -W/2],
                     [ L/2,  W/2],
                     [-L/2,  W/2]])
    ang = np.deg2rad(angle_deg)
    Rm = np.array([[np.cos(ang), -np.sin(ang)],
                   [np.sin(ang),  np.cos(ang)]])
    rect_rot = rect @ Rm.T
    rect_rot[:, 0] += cx
    rect_rot[:, 1] += cy
    if SHAPELY_OK:
        return Polygon(rect_rot)
    else:
        return (angle_deg, width, cx, cy, L/2)

def band_membership(x, y, slit_desc):
    angle_deg, width, cx, cy, halfL = slit_desc
    ang = np.deg2rad(angle_deg)
    xr = (x - cx)*np.cos(ang) + (y - cy)*np.sin(ang)
    yr = -(x - cx)*np.sin(ang) + (y - cy)*np.cos(ang)
    return (np.abs(yr) <= width/2) & (np.abs(xr) <= halfL)

def bubbles_mask(x, y, centers_r):
    # centers_r: list of (cx, cy, r)
    mask = np.zeros_like(x, dtype=bool)
    for (cx, cy, r) in centers_r:
        mask |= ((x - cx)**2 + (y - cy)**2) <= (r**2)
    return mask

def fold_band_mask(x, y, params):
    """
    Remove points within |offset(x,y)| <= width/2 of a curved band.
    params: dict with keys orientation ('h' or 'v'), center, width, wavy(bool), amp, wlen
    """
    ori = params["orientation"]
    width = params["width"]
    if ori == 'h':
        y0 = params["center"]
        if params["wavy"]:
            # sinusoidal offset along x
            y0 = y0 + params["amp"] * np.sin(2*np.pi * x / (params["wlen"] + 1e-6))
        return np.abs(y - y0) <= width/2
    else:
        x0 = params["center"]
        if params["wavy"]:
            x0 = x0 + params["amp"] * np.sin(2*np.pi * y / (params["wlen"] + 1e-6))
        return np.abs(x - x0) <= width/2

def apply_missingness(core_df, missing_frac, block_drop_prob, rng):
    keep = np.ones(len(core_df), dtype=bool)
    if rng.random() < block_drop_prob:
        if rng.random() < 0.5:
            r = int(rng.integers(core_df["row"].min(), core_df["row"].max()+1))
            keep &= core_df["row"].values != r
        else:
            c = int(rng.integers(core_df["col"].min(), core_df["col"].max()+1))
            keep &= core_df["col"].values != c
    keep &= rng.random(len(core_df)) > missing_frac
    return core_df.loc[keep].reset_index(drop=True)

def render_preview(cores_df, points_df, canvas_hw, blur_sigma, noise_sigma,
                   vignette_strength, stain_strength, pen_marks, dust_points):
    H, W = canvas_hw
    img = np.full((H, W), 240, dtype=np.float32)

    # faint core outlines
    tt = np.linspace(0, 2*np.pi, 240)
    for _, row in cores_df.iterrows():
        cx, cy = row["center_x"], row["center_y"]
        a, b = row["semi_a"], row["semi_b"]
        ang = row["ellipse_angle_deg"]
        xs = a*np.cos(tt)
        ys = b*np.sin(tt)
        xs, ys = rotate_xy(xs, ys, ang)
        xs += cx; ys += cy
        xs = np.clip(xs, 0, W-1).astype(int)
        ys = np.clip(ys, 0, H-1).astype(int)
        img[ys, xs] = 160

    # draw points
    xs = np.clip(points_df["x"].to_numpy(), 0, W-1).astype(int)
    ys = np.clip(points_df["y"].to_numpy(), 0, H-1).astype(int)
    img[ys, xs] = 60

    # pen marks (visual only)
    for seg in pen_marks:
        xs, ys = seg
        xs = np.clip(xs, 0, W-1).astype(int)
        ys = np.clip(ys, 0, H-1).astype(int)
        img[ys, xs] = 40

    # dust points (visual only)
    if dust_points is not None and len(dust_points) > 0:
        dx = np.clip(dust_points[:,0], 0, W-1).astype(int)
        dy = np.clip(dust_points[:,1], 0, H-1).astype(int)
        img[dy, dx] = 80

    # illumination: vignette + stain gradient
    yy, xx = np.meshgrid(np.linspace(-1,1,H), np.linspace(-1,1,W), indexing="ij")
    rad2 = xx**2 + yy**2
    vign = 1.0 + vignette_strength * (rad2 - rad2.min()) / (rad2.max() - rad2.min() + 1e-6)
    stain = 1.0 + stain_strength * (0.6*xx + 0.4*yy)
    img = img * vign * stain

    if SCIPY_OK and blur_sigma and blur_sigma > 0:
        img = gaussian_filter(img, sigma=blur_sigma)
    if noise_sigma and noise_sigma > 0:
        img += np.random.default_rng(SEED+999).normal(0, noise_sigma, size=img.shape)

    img = np.clip(img, 0, 255).astype(np.uint8)
    return img

# -----------------------
# Main
# -----------------------
def simulate(
    SEED = 23,
    OUTDIR = ".",
    # Grid
    ROWS = 8, 
    COLS = 7,
    PITCH = 220.0,
    RADIUS = 85.0,
    ORIGIN = (240.0, 240.0),  # (x0, y0)
    # Core geometry jitter (ellipses)
    RADIUS_JITTER_FRAC = 0.07,
    CENTER_JITTER_STD = 3.0,
    ELLIPTICITY_MEAN = 0.15,          # 0 -> circle, e.g. 0.25 means ~25% axis difference on average,
    ELLIPTICITY_STD = 0.08,
    ELLIPSE_ANGLE_JITTER = 30.0,      # deg
    # Points (cells)
    MEAN_CELLS_PER_CORE = 650,
    RADIAL_DENSITY_BIAS = 0.25,
    POINT_JITTER_STD = 0.4,
    # Slits
    SLIT_CORE_PROB = 0.6,
    SLIT_COUNT_RANGE = (1, 3),        # min/max number of slits in a slit-bearing core,
    SLIT_WIDTH = 10.0,
    SLIT_BASE_ANGLES = [0, 45, 90, 135],
    SLIT_ANGLE_JITTER = 22.0,
    # Grid defects
    MISSING_FRAC = 0.18,          # random cores removed,
    BLOCK_DROP_PROB = 0.25,       # maybe drop a whole row/col
    # Global affine
    ROTATION_DEG = 9.0,
    SCALE_XY = (1.02, 0.98),      # (sx, sy),
    SHEAR_X_DEG = 5.0,
    TRANSLATE = (25.0, -10.0),    # (tx, ty)
    # Non-rigid warp (TPS) of centers
    TPS_ENABLE = True,
    TPS_AMP = 25.0,
    TPS_N_CTRL = 6,
    TPS_SEED = 777,
    # Canvas & preview
    CANVAS = (2200, 2200),        # (H, W) pixels,
    PREVIEW_BLUR_SIGMA = 1.6,     # needs SciPy; set 0 to disable,
    NOISE_SIGMA = 4.0,
    VIGNETTE_STRENGTH = 0.15,
    STAIN_GRAD_STRENGTH = 0.18,   # multiplicative low-frequency gradient
    # Extra artifacts (global; affect points)
    EDGE_CROP = True,
    BUBBLES_N = 8,
    BUBBLE_R_RANGE = (50, 140),   # radius px,
    FOLDS_N = 3,                   # number of curved bands removing points,
    FOLD_WIDTH = 24.0,            # full band width px,
    FOLD_WAVY = True,
    FOLD_WAVELEN = 400.0,         # px,
    FOLD_AMP = 18.0,              # px
    # Visual-only artifacts (do not remove points)
    PEN_MARKS_N = 4,
    DUST_POINTS_N = 1200):

    rng = np.random.default_rng(SEED)
    H, W = CANVAS

    # 1) Build initial grid centers with jitter and ellipse params
    rows, cols = np.arange(ROWS), np.arange(COLS)
    centers = []
    for r in rows:
        for c in cols:
            cx = ORIGIN[0] + c*PITCH + rng.normal(0, CENTER_JITTER_STD)
            cy = ORIGIN[1] + r*PITCH + rng.normal(0, CENTER_JITTER_STD)
            # ellipse axes
            rad = RADIUS * (1.0 + rng.normal(0, RADIUS_JITTER_FRAC))
            ecc = max(0.0, rng.normal(ELLIPTICITY_MEAN, ELLIPTICITY_STD))
            a = rad*(1.0 + ecc)  # semi-major
            b = rad*(1.0 - ecc)  # semi-minor
            ell_ang = rng.normal(0, ELLIPSE_ANGLE_JITTER)
            centers.append([cy, cx, r, c, a, b, ell_ang])
    centers = np.array(centers)  # y x r c a b ang

    # 2) Global affine
    pts_yx = centers[:, :2]
    pts_yx = affine_transform(pts_yx, ROTATION_DEG, SCALE_XY, SHEAR_X_DEG, TRANSLATE)

    # 3) TPS warp
    if TPS_ENABLE:
        pts_yx = thin_plate_warp(pts_yx, CANVAS, amp=TPS_AMP, n_ctrl=TPS_N_CTRL, seed=TPS_SEED)
    centers[:, :2] = pts_yx

    # 4) Core table (before missingness)
    cores_df = pd.DataFrame({
        "core_id": [f"{int(r)}_{int(c)}" for r, c in centers[:, 2:4]],
        "row": centers[:, 2].astype(int),
        "col": centers[:, 3].astype(int),
        "center_x": centers[:, 1],
        "center_y": centers[:, 0],
        "semi_a": centers[:, 4],
        "semi_b": centers[:, 5],
        "ellipse_angle_deg": centers[:, 6]
    })

    # 5) Grid defects
    cores_df = apply_missingness(cores_df, MISSING_FRAC, BLOCK_DROP_PROB, rng)

    # 6) Slits per core
    has_slit = rng.random(len(cores_df)) < SLIT_CORE_PROB
    slit_counts = np.where(has_slit, rng.integers(SLIT_COUNT_RANGE[0], SLIT_COUNT_RANGE[1]+1), 0)
    all_slits = []  # list of lists of slit descriptors per core
    for i, row in cores_df.iterrows():
        slits_i = []
        for _ in range(int(slit_counts[i])):
            base = rng.choice(SLIT_BASE_ANGLES)
            ang = base + rng.normal(0, SLIT_ANGLE_JITTER)
            slits_i.append(make_slit_descriptor((row["center_x"], row["center_y"]),
                                                max(row["semi_a"], row["semi_b"]),
                                                ang, SLIT_WIDTH))
        all_slits.append(slits_i)
    cores_df["has_slit"] = has_slit
    cores_df["slit_count"] = slit_counts
    # For convenience, store first slit angle if any (for preview)
    first_angles = []
    for sl in all_slits:
        if len(sl) == 0:
            first_angles.append(np.nan)
        else:
            # If shapely, we didn't store angle, so keep NaN; otherwise store analytic angle
            if SHAPELY_OK:
                first_angles.append(np.nan)
            else:
                first_angles.append(sl[0][0])  # angle_deg
    cores_df["slit_angle_deg"] = first_angles
    cores_df["slit_width"] = np.where(has_slit, SLIT_WIDTH, 0.0)

    # 7) Extra global artifacts (masks that remove points): bubbles + folds
    bubble_specs = []
    for _ in range(BUBBLES_N):
        br = rng.uniform(*BUBBLE_R_RANGE)
        bx = rng.uniform(0.1*W, 0.9*W)
        by = rng.uniform(0.1*H, 0.9*H)
        bubble_specs.append((bx, by, br))

    fold_params = []
    for k in range(FOLDS_N):
        orientation = 'h' if rng.random() < 0.5 else 'v'
        center = rng.uniform(0.2*(H if orientation=='h' else W),
                             0.8*(H if orientation=='h' else W))
        fold_params.append({
            "orientation": orientation,
            "center": center,
            "width": FOLD_WIDTH,
            "wavy": FOLD_WAVY,
            "amp": FOLD_AMP,
            "wlen": FOLD_WAVELEN
        })

    # 8) Sample points per core and apply artifacts
    points = []
    for i, row in cores_df.iterrows():
        cx, cy = row["center_x"], row["center_y"]
        a, b = row["semi_a"], row["semi_b"]
        ang = row["ellipse_angle_deg"]
        n_cells = rng.poisson(MEAN_CELLS_PER_CORE)

        xr, yr = sample_points_in_ellipse(n_cells, a, b, POINT_JITTER_STD, RADIAL_DENSITY_BIAS, rng=rng)
        xr, yr = rotate_xy(xr, yr, ang)
        x = xr + cx
        y = yr + cy

        # Edge crop
        if EDGE_CROP:
            in_bounds = (x >= 0) & (x < W) & (y >= 0) & (y < H)
        else:
            in_bounds = np.ones_like(x, dtype=bool)

        # Slits (remove points)
        if int(row["slit_count"]) > 0:
            mask_slit = np.zeros_like(x, dtype=bool)
            for sdesc in all_slits[i]:
                if SHAPELY_OK and isinstance(sdesc, Polygon):
                    # approximate by sampling — keep fallback to band test for speed
                    # (Polygon.contains for thousands of points is slower)
                    # We'll use analytic band test by reconstructing params when shapely is used:
                    # Here we approximate by computing a rotated band around center:
                    # reconstruct angle/width from polygon bbox (rough)
                    bounds = sdesc.bounds  # (minx, miny, maxx, maxy)
                    # fallback crude: use band around line through core center at unknown angle
                    # safer: compute min area rect (requires shapely ops); to keep simple, skip & do point-in-poly
                    mask_slit |= np.array([sdesc.contains(SPoint(xj, yj)) for xj, yj in zip(x, y)])
                else:
                    mask_slit |= band_membership(x, y, sdesc)
        else:
            mask_slit = np.zeros_like(x, dtype=bool)

        # Bubbles
        mask_bub = bubbles_mask(x, y, bubble_specs) if BUBBLES_N > 0 else np.zeros_like(x, dtype=bool)

        # Folds/tears
        mask_fold = np.zeros_like(x, dtype=bool)
        for fp in fold_params:
            mask_fold |= fold_band_mask(x, y, fp)

        # Combine removals
        kill = (~in_bounds) | mask_slit | mask_bub | mask_fold
        keep = ~kill
        for xj, yj in zip(x[keep], y[keep]):
            points.append({
                "core_id": row["core_id"],
                "row": int(row["row"]),
                "col": int(row["col"]),
                "x": float(xj),
                "y": float(yj),
                "in_artifact": False
            })

    points_df = pd.DataFrame(points)

    # 9) Save CSVs
    os.makedirs(OUTDIR, exist_ok=True)
    cores_csv = os.path.join(OUTDIR, "tma_cores.csv")
    points_csv = os.path.join(OUTDIR, "tma_points.csv")
    cores_df.to_csv(cores_csv, index=False)
    points_df.to_csv(points_csv, index=False)

    # 10) Preview rendering using scatter plot
    fig, ax = plt.subplots(figsize=(8,8), dpi=300)
    plt.scatter(points_df["x"], points_df["y"], s=1, c='k', alpha=0.3)
    ax.set_axis_off()
    plt.savefig(os.path.join(OUTDIR, "tma_points_scatter.png"))
    plt.close(fig)

def run():
    # -----------------------
    # Configuration
    # -----------------------
    SEED = 23
    for SEED in [23]:
        for PITCH in range(325, 500, 50):
            for RADIUS_JITTER_FRAC in np.linspace(0, 1, num=11):
                for RADIAL_DENSITY_BIAS in np.linspace(0, 1, num=6):
                    for MISSING_FRAC in np.linspace(0, 0.5, num=6):
                        OUTDIR = f"{DATASET_DIR}/simulated/seed{SEED}_pitch{int(PITCH)}_rj{RADIUS_JITTER_FRAC:.2f}_rb{RADIAL_DENSITY_BIAS:.2f}_mf{MISSING_FRAC:.2f}"
                        OUTDIR = Path(OUTDIR)
                        OUTDIR.mkdir(parents=True, exist_ok=True)
                        print(f"Simulating dataset in {OUTDIR} with seed {SEED}")
                        # Grid
                        ROWS, COLS = 4, 3
                        RADIUS = 100.0 # clusters become dense when radius is low
                        ORIGIN = (240.0, 240.0)  # (x0, y0)

                        # Core geometry jitter (ellipses)
                        CENTER_JITTER_STD = 3.0
                        ELLIPTICITY_MEAN = 0.15          # 0 -> circle, e.g. 0.25 means ~25% axis difference on average
                        ELLIPTICITY_STD = 0.08
                        ELLIPSE_ANGLE_JITTER = 30.0      # deg

                        # Points (cells)
                        MEAN_CELLS_PER_CORE = 650
                        # RADIAL_DENSITY_BIAS = 0.25
                        POINT_JITTER_STD = 0.4

                        # Slits
                        SLIT_CORE_PROB = 0.5
                        SLIT_COUNT_RANGE = (1, 3)        # min/max number of slits in a slit-bearing core
                        SLIT_WIDTH = 10.0
                        SLIT_BASE_ANGLES = [0, 45, 90, 135]
                        SLIT_ANGLE_JITTER = 22.0

                        # Grid defects
                        # MISSING_FRAC = 0.18          # random cores removed
                        BLOCK_DROP_PROB = 0.25       # maybe drop a whole row/col

                        # Global affine
                        ROTATION_DEG = 1.0
                        SCALE_XY = (1.02, 0.98)      # (sx, sy)
                        SHEAR_X_DEG = 5.0
                        TRANSLATE = (25.0, -10.0)    # (tx, ty)

                        # Non-rigid warp (TPS) of centers
                        TPS_ENABLE = True
                        TPS_AMP = 100.0
                        TPS_N_CTRL = 6
                        TPS_SEED = 777

                        # Canvas & preview
                        CANVAS = (2200, 2200)        # (H, W) pixels
                        PREVIEW_BLUR_SIGMA = 1.6     # needs SciPy; set 0 to disable
                        NOISE_SIGMA = 4.0
                        VIGNETTE_STRENGTH = 0.15
                        STAIN_GRAD_STRENGTH = 0.18   # multiplicative low-frequency gradient

                        # Extra artifacts (global; affect points)
                        EDGE_CROP = True
                        BUBBLES_N = 8
                        BUBBLE_R_RANGE = (50, 140)   # radius px
                        FOLDS_N = 3                   # number of curved bands removing points
                        FOLD_WIDTH = 24.0            # full band width px
                        FOLD_WAVY = True
                        FOLD_WAVELEN = 400.0         # px
                        FOLD_AMP = 18.0              # px

                        # Visual-only artifacts (do not remove points)
                        PEN_MARKS_N = 4
                        DUST_POINTS_N = 1200
                        simulate(
                            SEED = SEED,
                            OUTDIR = OUTDIR,
                            ROWS = ROWS,
                            COLS = COLS,
                            PITCH = PITCH,
                            RADIUS = RADIUS,
                            ORIGIN = ORIGIN,
                            RADIUS_JITTER_FRAC = RADIUS_JITTER_FRAC,
                            CENTER_JITTER_STD = CENTER_JITTER_STD,
                            ELLIPTICITY_MEAN = ELLIPTICITY_MEAN,
                            ELLIPTICITY_STD = ELLIPTICITY_STD,
                            ELLIPSE_ANGLE_JITTER = ELLIPSE_ANGLE_JITTER,
                            MEAN_CELLS_PER_CORE = MEAN_CELLS_PER_CORE,
                            RADIAL_DENSITY_BIAS = RADIAL_DENSITY_BIAS,
                            POINT_JITTER_STD = POINT_JITTER_STD,
                            SLIT_CORE_PROB = SLIT_CORE_PROB,
                            SLIT_COUNT_RANGE = SLIT_COUNT_RANGE,
                            SLIT_WIDTH = SLIT_WIDTH,
                            SLIT_BASE_ANGLES = SLIT_BASE_ANGLES,
                            SLIT_ANGLE_JITTER = SLIT_ANGLE_JITTER,
                            MISSING_FRAC = MISSING_FRAC,
                            BLOCK_DROP_PROB = BLOCK_DROP_PROB,
                            ROTATION_DEG = ROTATION_DEG,
                            SCALE_XY = SCALE_XY,
                            SHEAR_X_DEG = SHEAR_X_DEG,
                            TRANSLATE = TRANSLATE,
                            TPS_ENABLE = TPS_ENABLE,
                            TPS_AMP = TPS_AMP,
                            TPS_N_CTRL = TPS_N_CTRL,
                            TPS_SEED = TPS_SEED,
                            CANVAS = CANVAS,
                            PREVIEW_BLUR_SIGMA = PREVIEW_BLUR_SIGMA,
                            NOISE_SIGMA = NOISE_SIGMA,
                            VIGNETTE_STRENGTH = VIGNETTE_STRENGTH,
                            STAIN_GRAD_STRENGTH = STAIN_GRAD_STRENGTH,
                            EDGE_CROP = EDGE_CROP,
                            BUBBLES_N = BUBBLES_N,
                            BUBBLE_R_RANGE = BUBBLE_R_RANGE,
                            FOLDS_N = FOLDS_N,
                            FOLD_WIDTH = FOLD_WIDTH,
                            FOLD_WAVY = FOLD_WAVY,
                            FOLD_WAVELEN = FOLD_WAVELEN,
                            FOLD_AMP = FOLD_AMP,
                            PEN_MARKS_N = PEN_MARKS_N,
                            DUST_POINTS_N = DUST_POINTS_N)

                        all_parameters = {
                            "SEED": SEED,
                            "ROWS": ROWS,
                            "COLS": COLS,
                            "PITCH": PITCH,
                            "RADIUS": RADIUS,
                            "ORIGIN": ORIGIN,
                            "RADIUS_JITTER_FRAC": RADIUS_JITTER_FRAC,
                            "CENTER_JITTER_STD": CENTER_JITTER_STD,
                            "ELLIPTICITY_MEAN": ELLIPTICITY_MEAN,
                            "ELLIPTICITY_STD": ELLIPTICITY_STD,
                            "ELLIPSE_ANGLE_JITTER": ELLIPSE_ANGLE_JITTER,
                            "MEAN_CELLS_PER_CORE": MEAN_CELLS_PER_CORE,
                            "RADIAL_DENSITY_BIAS": RADIAL_DENSITY_BIAS,
                            "POINT_JITTER_STD": POINT_JITTER_STD,
                            "SLIT_CORE_PROB": SLIT_CORE_PROB,
                            "SLIT_COUNT_RANGE": SLIT_COUNT_RANGE,
                            "SLIT_WIDTH": SLIT_WIDTH,
                            "SLIT_BASE_ANGLES": SLIT_BASE_ANGLES,

                            "SLIT_ANGLE_JITTER": SLIT_ANGLE_JITTER,
                            "MISSING_FRAC": MISSING_FRAC,
                            "BLOCK_DROP_PROB": BLOCK_DROP_PROB,
                            "ROTATION_DEG": ROTATION_DEG,
                            "SCALE_XY": SCALE_XY,
                            "SHEAR_X_DEG": SHEAR_X_DEG,
                            "TRANSLATE": TRANSLATE,
                            "TPS_ENABLE": TPS_ENABLE,
                            "TPS_AMP": TPS_AMP,
                            "TPS_N_CTRL": TPS_N_CTRL,
                            "TPS_SEED": TPS_SEED,
                            "CANVAS": CANVAS,
                            "PREVIEW_BLUR_SIGMA": PREVIEW_BLUR_SIGMA,
                            "NOISE_SIGMA": NOISE_SIGMA,
                            "VIGNETTE_STRENGTH": VIGNETTE_STRENGTH,
                            "STAIN_GRAD_STRENGTH": STAIN_GRAD_STRENGTH,
                            "EDGE_CROP": EDGE_CROP,
                            "BUBBLES_N": BUBBLES_N,
                            "BUBBLE_R_RANGE": BUBBLE_R_RANGE,
                            "FOLDS_N": FOLDS_N,
                            "FOLD_WIDTH": FOLD_WIDTH,
                            "FOLD_WAVY": FOLD_WAVY,
                            "FOLD_WAVELEN": FOLD_WAVELEN,
                            "FOLD_AMP": FOLD_AMP,
                            "PEN_MARKS_N": PEN_MARKS_N,
                            "DUST_POINTS_N": DUST_POINTS_N
                        }

                        with open(OUTDIR / "parameters.json", "w") as f:
                            import json
                            json.dump(all_parameters, f, indent=2)

def create_simulated_adata(dataset_folder):
    points_df = pd.read_csv(f"{dataset_folder}/tma_points.csv")
    adata = sc.AnnData(points_df[['x', 'y']].values)
    adata.obs['core_id'] = points_df['core_id'].astype(str).values
    adata.obs['x_centroid'] = points_df['x'].values
    adata.obs['y_centroid'] = points_df['y'].values
    adata.write_h5ad(f"{dataset_folder}/adata.h5ad")

def create_adata(dataset_folder):
    from tqdm import tqdm
    total_datasets = len(list(Path(dataset_folder).iterdir()))
    for dataset in tqdm(Path(dataset_folder).iterdir(), total=total_datasets):
        # print(f"Checking dataset: {dataset.name}")
        if dataset.is_dir():
            dataset_folder = dataset
            create_simulated_adata(dataset_folder)

if __name__ == "__main__":
    run()
    create_adata(SIMULATED_DATASET_DIR)    
