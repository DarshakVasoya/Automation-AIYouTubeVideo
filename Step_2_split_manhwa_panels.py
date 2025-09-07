import os
import cv2
import numpy as np
from PIL import Image
from downloadingimages import fetch_one_chapter


def split_manhwa_panels(
    pil_img: Image.Image,
    min_panel_height: int = 80,
    min_panel_width: int = 80,
    canny1: int = 50,
    canny2: int = 150,
    morph_kernel: int = 5,
    dilate_iters: int = 2,
) -> list[Image.Image]:
    """Detect and crop panel regions from a tall manhwa page.

    Approach (robust for vertical-scroll pages):
      1) Convert to grayscale, mild blur.
      2) Canny edges -> dilate to close gaps in panel borders.
      3) Find contours, keep large rectangular-like areas.
      4) Sort by top-to-bottom, then left-to-right.

    Returns a list of PIL Images for panels in reading order.
    """

    # Convert PIL image to OpenCV BGR
    img_rgb = np.array(pil_img.convert("RGB"))
    img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    h, w = img.shape[:2]

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)

    edges = cv2.Canny(gray, canny1, canny2)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (morph_kernel, morph_kernel))
    dilated = cv2.dilate(edges, kernel, iterations=dilate_iters)

    cnts, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    panels = []
    boxes = []
    for c in cnts:
        x, y, cw, ch = cv2.boundingRect(c)
        # Filter out tiny regions and near-border noise
        if cw < min_panel_width or ch < min_panel_height:
            continue

        # Optional: expand a bit to include full panel area
        pad = 6
        x0 = max(0, x - pad)
        y0 = max(0, y - pad)
        x1 = min(w, x + cw + pad)
        y1 = min(h, y + ch + pad)

        boxes.append((y0, x0, y1, x1))  # store as (top, left, bottom, right)

    if not boxes:
        # Fallback: split by horizontal gaps (old approach)
        gray2 = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        _, thresh = cv2.threshold(gray2, 240, 255, cv2.THRESH_BINARY_INV)
        horizontal_sum = np.sum(thresh, axis=1)
        gaps = []
        in_gap = False
        gap_start = 0
        for i, val in enumerate(horizontal_sum):
            if val < 10 and not in_gap:
                gap_start = i
                in_gap = True
            elif val >= 10 and in_gap:
                gap_end = i
                if gap_end - gap_start > 30:
                    gaps.append((gap_start, gap_end))
                in_gap = False
        if in_gap:
            gap_end = len(horizontal_sum) - 1
            if gap_end - gap_start > 30:
                gaps.append((gap_start, gap_end))

        last = 0
        for gs, ge in gaps:
            if gs - last > 20:
                boxes.append((last, 0, gs, w))
            last = ge
        if last < h - 1:
            boxes.append((last, 0, h - 1, w))

    # Merge overlapping/contained boxes to avoid duplicates
    boxes = _merge_boxes(boxes)

    # Sort reading order: top-to-bottom, then left-to-right within bands
    boxes.sort(key=lambda b: (b[0], b[1]))

    for top, left, bottom, right in boxes:
        crop = pil_img.crop((left, top, right, bottom))
        if crop.width >= min_panel_width and crop.height >= min_panel_height:
            panels.append(crop)

    return panels


def _merge_boxes(boxes: list[tuple[int, int, int, int]], iou_thresh: float = 0.3) -> list[tuple[int, int, int, int]]:
    if not boxes:
        return []
    # Simple NMS-like merge by removing boxes largely contained in others
    boxes = sorted(boxes, key=lambda b: (-(b[2]-b[0]) * (b[3]-b[1])))  # larger first
    kept = []
    for b in boxes:
        keep = True
        for kb in kept:
            if _iou(b, kb) > iou_thresh or _is_contained(b, kb):
                keep = False
                break
        if keep:
            kept.append(b)
    return kept


def _iou(a, b):
    ay0, ax0, ay1, ax1 = a
    by0, bx0, by1, bx1 = b
    inter_left = max(ax0, bx0)
    inter_top = max(ay0, by0)
    inter_right = min(ax1, bx1)
    inter_bottom = min(ay1, by1)
    if inter_right <= inter_left or inter_bottom <= inter_top:
        return 0.0
    inter = (inter_right - inter_left) * (inter_bottom - inter_top)
    a_area = (ax1 - ax0) * (ay1 - ay0)
    b_area = (bx1 - bx0) * (by1 - by0)
    return inter / float(a_area + b_area - inter + 1e-6)


def _is_contained(a, b, pad: int = 4):
    ay0, ax0, ay1, ax1 = a
    by0, bx0, by1, bx1 = b
    return ax0 >= bx0 - pad and ay0 >= by0 - pad and ax1 <= bx1 + pad and ay1 <= by1 + pad


def save_panels(chapter_num, page_index, panels, output_dir="output"):
    chapter_folder = os.path.join(output_dir, f"chapter_{chapter_num}")
    os.makedirs(chapter_folder, exist_ok=True)
    for i, panel in enumerate(panels, start=1):
        filename = f"page_{page_index:02d}_panel_{i:02d}.png"
        path = os.path.join(chapter_folder, filename)
        panel.save(path, format="PNG")
        print(f"✅ Saved {path}")


if __name__ == "__main__":
    # Fetch one page to test
    chapter_images = fetch_one_chapter(
        "https://kingofshojo.com/manga/after-the-school-belle-dumped-me-i-became-a-martial-arts-god/",
        "Chapter 1",
    )

    # Process first page as demo
    page_idx = 1
    pil_page = chapter_images[page_idx]
    panels = split_manhwa_panels(pil_page)
    print(f"Split into {len(panels)} panels")
    save_panels(chapter_num=1, page_index=page_idx, panels=panels)