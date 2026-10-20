import numpy as np
from skimage.metrics import structural_similarity as skimage_ssim


def rgba_to_rgb_mask(rgba):
    rgb = rgba[:, :, :3].astype(np.float32) / 255.0
    alpha = rgba[:, :, 3].astype(np.float32) / 255.0
    mask = alpha > 0.0
    rgb_masked = rgb * alpha[..., None]
    return rgb_masked, alpha, mask


def crop_to_union_mask(img1, img2, mask1, mask2, pad=12):
    union = mask1 | mask2
    ys, xs = np.where(union)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("Union mask is empty; nothing was rendered.")

    h, w = union.shape
    x0 = max(int(xs.min()) - pad, 0)
    y0 = max(int(ys.min()) - pad, 0)
    x1 = min(int(xs.max()) + pad + 1, w)
    y1 = min(int(ys.max()) + pad + 1, h)

    img1_c = img1[y0:y1, x0:x1]
    img2_c = img2[y0:y1, x0:x1]
    mask1_c = mask1[y0:y1, x0:x1]
    mask2_c = mask2[y0:y1, x0:x1]
    union_c = union[y0:y1, x0:x1]

    return img1_c, img2_c, mask1_c, mask2_c, union_c


# ============================================================
# Perceptual Metrics
# ============================================================


def masked_psnr(gt_img, rm_img, mask):
    """
    PSNR over masked pixels only.
    Images are float32 in [0,1].
    """
    mask3 = mask[..., None].astype(np.float32)
    denom = np.sum(mask3)
    if denom <= 0:
        return np.nan

    mse = np.sum(((gt_img - rm_img) ** 2) * mask3) / (denom + 1e-12)
    if mse <= 1e-12:
        return np.inf
    return 10.0 * np.log10(1.0 / mse)


def masked_ssim(gt_img, rm_img):
    """
    SSIM on a masked crop where background has already been zeroed.
    """
    return skimage_ssim(
        gt_img,
        rm_img,
        channel_axis=-1,
        data_range=1.0
    )


def masked_lpips(lpips_model, gt_img, rm_img, device):
    """
    LPIPS on masked crop with background zeroed.
    """
    import torch

    gt_t = torch.from_numpy(gt_img).permute(2, 0, 1).unsqueeze(0).to(device=device, dtype=torch.float32)
    rm_t = torch.from_numpy(rm_img).permute(2, 0, 1).unsqueeze(0).to(device=device, dtype=torch.float32)

    gt_t = gt_t * 2.0 - 1.0
    rm_t = rm_t * 2.0 - 1.0

    with torch.no_grad():
        val = lpips_model(gt_t, rm_t)
    return float(val.item())


def summarize_stats(values):
    arr = np.asarray(values, dtype=np.float64)
    finite = arr[np.isfinite(arr)]

    if len(finite) == 0:
        return {
            "min": np.nan, "max": np.nan, "p25": np.nan, "p75": np.nan,
            "median": np.nan, "mean": np.nan
        }

    return {
        "min": float(np.min(finite)),
        "max": float(np.max(finite)),
        "p25": float(np.percentile(finite, 25)),
        "p75": float(np.percentile(finite, 75)),
        "median": float(np.median(finite)),
        "mean": float(np.mean(finite)),
    }
