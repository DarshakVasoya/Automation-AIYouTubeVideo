import os
import cv2
import numpy as np
from PIL import Image
from Step_1_downloadingimages import fetch_one_chapter

def split_manhwa_panels(pil_img, min_gap_height=30):
    # Convert to grayscale (OpenCV needs NumPy)
    img = np.array(pil_img.convert("L"))

    # Normalize brightness
    _, thresh = cv2.threshold(img, 250, 255, cv2.THRESH_BINARY)

    # Sum pixel values row by row (horizontal projection)
    row_sums = np.sum(thresh == 255, axis=1)

    # Find gaps where most pixels are white
    gaps = []
    in_gap = False
    for i, val in enumerate(row_sums):
        if val > 0.95 * thresh.shape[1]:  # row is ~95% white
            if not in_gap:
                start = i
                in_gap = True
        else:
            if in_gap:
                end = i
                if end - start > min_gap_height:
                    gaps.append((start, end))
                in_gap = False

    # Split panels between gaps
    panels = []
    last_cut = 0
    for (start, end) in gaps:
        panel = pil_img.crop((0, last_cut, pil_img.width, start))
        if panel.height > 50:  # filter small cuts
            panels.append(panel)
        last_cut = end

    # Final panel (bottom part)
    if last_cut < pil_img.height:
        panel = pil_img.crop((0, last_cut, pil_img.width, pil_img.height))
        panels.append(panel)

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
panels = split_manhwa_panels(chapter_images[0])
print(f"Split into {len(panels)} panels")


save_panels(chapter_num=1, page_index=1, panels=panels)