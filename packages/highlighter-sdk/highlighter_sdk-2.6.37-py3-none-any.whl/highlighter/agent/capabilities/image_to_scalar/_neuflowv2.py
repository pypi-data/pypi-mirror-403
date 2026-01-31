"""NeuFlowV2 optical flow estimation with built-in preprocessing."""

import logging
import os
from pathlib import Path
from typing import Optional

import numpy as np
import onnxruntime
import requests
import tqdm

__all__ = ["NeuFlowV2", "flow_to_image"]

MAX_KERNEL_SIZE = 7

AVAILABLE_MODELS = ["neuflow_mixed", "neuflow_sintel", "neuflow_things"]
MODEL_BASE_URL = "https://github.com/ibaiGorordo/ONNX-NeuFlowV2-Optical-Flow/releases/download/0.1.0"


def _download_model(url: str, path: str):
    """Download a model from URL."""
    print(f"Downloading model from {url} to {path}")
    r = requests.get(url, stream=True, timeout=30)
    with open(path, "wb") as f:
        total_length = int(r.headers.get("content-length", 0))
        for chunk in tqdm.tqdm(
            r.iter_content(chunk_size=1024 * 1024),
            total=max(1, total_length // (1024 * 1024)),
            bar_format="{l_bar}{bar:10}",
        ):
            if chunk:
                f.write(chunk)
                f.flush()


def _get_preprocessed_path(original_path: str) -> str:
    """Get path for preprocessed model variant."""
    path = Path(original_path)
    return str(path.parent / f"{path.stem}_preprocessed{path.suffix}")


def _ensure_preprocessed_model(original_path: str) -> str:
    """Ensure preprocessed model exists, creating it if necessary."""
    from ._neuflow_preprocessing import prepend_preprocessing_to_neuflow

    original_path = str(original_path)
    preprocessed_path = _get_preprocessed_path(original_path)

    # Download original model if needed
    if not os.path.exists(original_path):
        Path(original_path).parent.mkdir(parents=True, exist_ok=True)
        model_name = Path(original_path).stem
        if model_name not in AVAILABLE_MODELS:
            raise ValueError(f"Unknown model: {model_name}. Available: {AVAILABLE_MODELS}")
        url = f"{MODEL_BASE_URL}/{model_name}.onnx"
        _download_model(url, original_path)

    # Create preprocessed version if needed
    if not os.path.exists(preprocessed_path):
        print(f"Creating preprocessed model: {preprocessed_path}")
        prepend_preprocessing_to_neuflow(original_path, preprocessed_path)

    return preprocessed_path


class NeuFlowV2:
    """
    Optical flow estimator with built-in preprocessing.

    The model includes Gaussian blur and resize operations, with the blur
    kernel configurable at runtime. On first use, automatically downloads
    the base model and creates a preprocessed version.

    Args:
        path: Path to the NeuFlow ONNX model (preprocessed version auto-created)
        use_gpu: Whether to use GPU for inference
        blur_kernel_size: Gaussian blur kernel size (3, 5, 7) or None for no blur
    """

    def __init__(self, path: str, use_gpu: bool = True, blur_kernel_size: Optional[int] = 3):
        self.logger = logging.getLogger(__name__)

        # Ensure preprocessed model exists (downloads and creates if needed)
        preprocessed_path = _ensure_preprocessed_model(path)

        # Select execution provider
        if use_gpu:
            providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        else:
            providers = ["CPUExecutionProvider"]

        self.session = onnxruntime.InferenceSession(preprocessed_path, providers=providers)
        self.logger.info(f"NeuFlowV2 initialized with providers: {providers}")

        # Set initial blur kernel
        self.set_blur_kernel(blur_kernel_size)

    def set_blur_kernel(self, kernel_size: Optional[int]):
        """
        Set Gaussian blur kernel size.

        Args:
            kernel_size: Kernel size (3, 5, 7) or None to disable blur
        """
        if kernel_size is None:
            self._blur_kernel = self._make_identity_kernel()
            self.logger.info("Blur disabled (identity kernel)")
        else:
            if kernel_size > MAX_KERNEL_SIZE:
                raise ValueError(f"Max kernel size is {MAX_KERNEL_SIZE}, got {kernel_size}")
            if kernel_size % 2 == 0:
                raise ValueError(f"Kernel size must be odd, got {kernel_size}")
            sigma = (kernel_size - 1) / 6.0
            self._blur_kernel = self._make_gaussian_kernel(kernel_size, sigma)
            self.logger.info(f"Blur kernel set to {kernel_size}x{kernel_size} (sigma={sigma:.2f})")

    @staticmethod
    def _make_gaussian_kernel(size: int, sigma: float) -> np.ndarray:
        """Create Gaussian kernel for depthwise convolution, zero-padded to MAX_KERNEL_SIZE."""
        coords = np.arange(size) - size // 2
        g = np.exp(-(coords**2) / (2 * sigma**2))
        kernel_2d = np.outer(g, g)
        kernel_2d = kernel_2d / kernel_2d.sum()
        # Shape for depthwise conv: (out_channels=3, in_channels/groups=1, H, W)
        kernel_4d = np.tile(kernel_2d[np.newaxis, np.newaxis, :, :], (3, 1, 1, 1))
        # Zero-pad to max kernel size
        if size < MAX_KERNEL_SIZE:
            pad = (MAX_KERNEL_SIZE - size) // 2
            kernel_4d = np.pad(kernel_4d, ((0, 0), (0, 0), (pad, pad), (pad, pad)))
        return kernel_4d.astype(np.float32)

    @staticmethod
    def _make_identity_kernel() -> np.ndarray:
        """Create identity kernel (no-op convolution)."""
        kernel = np.zeros((MAX_KERNEL_SIZE, MAX_KERNEL_SIZE), dtype=np.float32)
        kernel[MAX_KERNEL_SIZE // 2, MAX_KERNEL_SIZE // 2] = 1.0
        return np.tile(kernel[np.newaxis, np.newaxis, :, :], (3, 1, 1, 1))

    def __call__(self, prev_frame: np.ndarray, curr_frame: np.ndarray) -> np.ndarray:
        """
        Compute optical flow between two frames.

        Args:
            prev_frame: Previous frame (H, W, 3) uint8 array
            curr_frame: Current frame (H, W, 3) uint8 array

        Returns:
            Optical flow (H, W, 2) float32 array
        """
        outputs = self.session.run(
            None,
            {
                "prev_image": prev_frame,
                "curr_image": curr_frame,
                "blur_kernel": self._blur_kernel,
            },
        )
        return outputs[0]


# --- Flow visualization utilities ---
# Ref: https://github.com/liruoteng/OpticalFlowToolkit/blob/5cf87b947a0032f58c922bbc22c0afb30b90c418/lib/flowlib.py#L249


def make_color_wheel():
    """
    Generate color wheel according Middlebury color code
    :return: Color wheel
    """
    RY = 15
    YG = 6
    GC = 4
    CB = 11
    BM = 13
    MR = 6

    ncols = RY + YG + GC + CB + BM + MR

    colorwheel = np.zeros([ncols, 3])

    col = 0

    # RY
    colorwheel[0:RY, 0] = 255
    colorwheel[0:RY, 1] = np.transpose(np.floor(255 * np.arange(0, RY) / RY))
    col += RY

    # YG
    colorwheel[col : col + YG, 0] = 255 - np.transpose(np.floor(255 * np.arange(0, YG) / YG))
    colorwheel[col : col + YG, 1] = 255
    col += YG

    # GC
    colorwheel[col : col + GC, 1] = 255
    colorwheel[col : col + GC, 2] = np.transpose(np.floor(255 * np.arange(0, GC) / GC))
    col += GC

    # CB
    colorwheel[col : col + CB, 1] = 255 - np.transpose(np.floor(255 * np.arange(0, CB) / CB))
    colorwheel[col : col + CB, 2] = 255
    col += CB

    # BM
    colorwheel[col : col + BM, 2] = 255
    colorwheel[col : col + BM, 0] = np.transpose(np.floor(255 * np.arange(0, BM) / BM))
    col += +BM

    # MR
    colorwheel[col : col + MR, 2] = 255 - np.transpose(np.floor(255 * np.arange(0, MR) / MR))
    colorwheel[col : col + MR, 0] = 255

    return colorwheel


colorwheel = make_color_wheel()


def compute_color(u, v):
    """
    compute optical flow color map
    :param u: optical flow horizontal map
    :param v: optical flow vertical map
    :return: optical flow in color code
    """
    [h, w] = u.shape
    img = np.zeros([h, w, 3])
    nanIdx = np.isnan(u) | np.isnan(v)
    u[nanIdx] = 0
    v[nanIdx] = 0

    ncols = np.size(colorwheel, 0)

    rad = np.sqrt(u**2 + v**2)

    a = np.arctan2(-v, -u) / np.pi

    fk = (a + 1) / 2 * (ncols - 1) + 1

    k0 = np.floor(fk).astype(int)

    k1 = k0 + 1
    k1[k1 == ncols + 1] = 1
    f = fk - k0

    for i in range(0, np.size(colorwheel, 1)):
        tmp = colorwheel[:, i]
        col0 = tmp[k0 - 1] / 255
        col1 = tmp[k1 - 1] / 255
        col = (1 - f) * col0 + f * col1

        idx = rad <= 1
        col[idx] = 1 - rad[idx] * (1 - col[idx])
        notidx = np.logical_not(idx)

        col[notidx] *= 0.75
        img[:, :, i] = np.uint8(np.floor(255 * col * (1 - nanIdx)))

    return img


def flow_to_image(flow, maxrad=None):
    """
    Convert flow into middlebury color code image
    :param flow: optical flow map
    :return: optical flow image in middlebury color
    """
    u = flow[:, :, 0]
    v = flow[:, :, 1]

    rad = np.sqrt(u**2 + v**2)
    if maxrad is None:
        maxrad = max(-1, np.max(rad))

    eps = np.finfo(float).eps
    u = np.clip(u, -maxrad + 5, maxrad - 5)
    v = np.clip(v, -maxrad + 5, maxrad - 5)

    u = u / (maxrad + eps)
    v = v / (maxrad + eps)

    img = compute_color(u, v)

    return np.uint8(img)
