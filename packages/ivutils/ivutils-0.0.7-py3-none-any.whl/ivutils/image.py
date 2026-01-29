import cv2
import numpy as np
from typing import Tuple, Optional

def resize_image(src_img_file:str,
                 dest_img_file:str,
                 resize_dim: Tuple[int, int]):
    in_img = cv2.imread(src_img_file)
    out_img = resize_image_array(in_img, resize_dim=resize_dim)
    cv2.imwrite(dest_img_file, out_img)

def resize_image_array(src_img: np.ndarray,
                       resize_dim: Tuple[int, int]) -> Optional[np.ndarray]:
    """
    Preprocesses a NumPy array image to a target size while maintaining
    aspect ratio via letterboxing (padding).


    Args:
        src_img: NumPy array of shape (H, W, C).
        resize_dim: Tuple (width, height) for the target size.

    Returns:
        A NumPy array of the target size, or None if an error occurred.
    """

    if src_img is None:
        return None

    oh, ow = src_img.shape[:2]
    target_w, target_h = resize_dim

    # take the minimum scale to ensure the image fits within target_dim
    scale = min(target_w / ow, target_h / oh)
    new_w = int(ow * scale)
    new_h = int(oh * scale)

    # 1. Faster Interpolation: INTER_LINEAR is usually 3-5x faster than CUBIC
    resized_image = cv2.resize(src_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)

    # 2. Optimized Padding: copyMakeBorder is faster than manual slicing
    # Calculate padding for all sides
    delta_w = target_w - new_w
    delta_h = target_h - new_h

    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    return cv2.copyMakeBorder(
        resized_image,
        top, bottom, left, right,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0]
    )


def calculate_crop_offsets(h: int, w: int,
                           top: float, bottom: float,
                           left: float, right: float) -> Tuple[int, int, int, int]:
    """
    Resolves crop parameters:
    - Floats (0.0 to 1.0): Percentage of the dimension.
    - Positive Ints: Absolute bounding box coordinates.
    - Negative Ints: Pixels to remove from that specific edge.
    """

    def resolve_dim(val, total, is_end_coord=False):
        # 1. Handle Percentages
        if isinstance(val, float) and -1.0 <= val <= 1.0 and val != 0:
            return abs(int(val * total))

        # 2. Handle Negative (Relative offsets)
        if val < 0:
            return abs(int(val))

        # 3. Handle Positive (Absolute coordinates)
        if val > 0:
            if is_end_coord:
                # If bottom/right is coordinate 950, remove (total - 950)
                return max(0, total - int(val))
            else:
                # If top/left is coordinate 470, remove 470
                return int(val)

        return 0

    t = resolve_dim(top, h, is_end_coord=False)
    b = resolve_dim(bottom, h, is_end_coord=True)
    l = resolve_dim(left, w, is_end_coord=False)
    r = resolve_dim(right, w, is_end_coord=True)

    return t, b, l, r


def crop_image(src_img_file: str,
               dest_img_file: str,
               top: float = 0, bottom: float = 0,
               left: float = 0, right: float = 0):
    in_img = cv2.imread(src_img_file)
    if in_img is None:
        print(f"Error: Could not open {src_img_file}")
        return

    h, w = in_img.shape[:2]
    t, b, l, r = calculate_crop_offsets(h, w, top, bottom, left, right)

    # Check if the crop is valid
    if (t + b) >= h or (l + r) >= w:
        print(f"Error: Crop logic resulted in 0 or negative dimensions.")
        print(f"Requested: Top/Bottom offsets {t}/{b} for height {h}")
        print(f"Requested: Left/Right offsets {l}/{r} for width {w}")
        return

    out_img = crop_image_array(in_img, t, b, l, r)
    cv2.imwrite(dest_img_file, out_img)


def crop_image_array(src_img: np.ndarray,
                     top: int = 0, bottom: int = 0,
                     left: int = 0, right: int = 0) -> Optional[np.ndarray]:
    """
    Crops a NumPy array image based on pixel offsets from the edges.
    """
    if src_img is None:
        return None

    h, w = src_img.shape[:2]

    # Calculate new boundaries
    # Using max(0, ...) and min(limit, ...) to prevent out-of-bounds errors
    start_y = max(0, top)
    end_y = min(h, h - bottom)
    start_x = max(0, left)
    end_x = min(w, w - right)

    # Perform the crop via slicing
    cropped_img = src_img[start_y:end_y, start_x:end_x]

    return cropped_img
