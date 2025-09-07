import os
import cv2
import numpy as np
from PIL import Image
from Step_1_downloadingimages import fetch_one_chapter

def split_manhwa_panels(pil_img, min_gap_height=30):
   

    # Convert PIL image to OpenCV format
    img = np.array(pil_img)
    if img.shape[2] == 4:
        img = cv2.cvtColor(img, cv2.COLOR_RGBA2RGB)
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # Binarize image (invert so panels are white, borders are black)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)

    # Sum pixels along horizontal axis to find horizontal gaps
    horizontal_sum = np.sum(thresh, axis=1)
    gaps = []
    in_gap = False
    for i, val in enumerate(horizontal_sum):
        if val < 10 and not in_gap:
            gap_start = i
            in_gap = True
        elif val >= 10 and in_gap:
            gap_end = i
            if gap_end - gap_start > min_gap_height:
                gaps.append((gap_start, gap_end))
            in_gap = False
    # Add last gap if image ends with a gap
    if in_gap:
        gap_end = len(horizontal_sum)-1
        if gap_end - gap_start > min_gap_height:
            gaps.append((gap_start, gap_end))

    # Use gaps to determine panel boundaries
    panel_bounds = []
    last = 0
    for gap_start, gap_end in gaps:
        if gap_start - last > 20:
            panel_bounds.append((last, gap_start))
        last = gap_end
    if last < img.shape[0]-1:
        panel_bounds.append((last, img.shape[0]-1))

    # Crop panels
    panels = []
    for top, bottom in panel_bounds:
        panel_img = pil_img.crop((0, top, pil_img.width, bottom))
        # Filter out very small panels
        if panel_img.height > 40:
            panels.append(panel_img)
    return panels

def save_panels(chapter_num, page_index, panels, output_dir="output"):
    # Create chapter folder if not exists
    chapter_folder = os.path.join(output_dir, f"chapter_{chapter_num}")
    os.makedirs(chapter_folder, exist_ok=True)

    # Save each panel
    for i, panel in enumerate(panels, start=1):
        filename = f"page_{page_index:02d}_panel_{i:02d}.png"
        path = os.path.join(chapter_folder, filename)
        panel.save(path, format="PNG")
        print(f"✅ Saved {path}")
        
        
chapter_images = fetch_one_chapter(
    "https://kingofshojo.com/manga/after-the-school-belle-dumped-me-i-became-a-martial-arts-god/",
    "Chapter 1"
)
        
# Example
panels = split_manhwa_panels(chapter_images[1])
print(f"Split into {len(panels)} panels")


save_panels(chapter_num=1, page_index=1, panels=panels)