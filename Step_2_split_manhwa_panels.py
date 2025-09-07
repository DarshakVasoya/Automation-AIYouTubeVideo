import os
import cv2
import numpy as np
from PIL import Image
from Step_1_downloadingimages import fetch_one_chapter

def split_manhwa_panels(pil_img):

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