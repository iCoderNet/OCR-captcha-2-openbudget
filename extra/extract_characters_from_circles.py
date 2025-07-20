import cv2
import os
import numpy as np
from pathlib import Path

input_dir = "dataset/.mixed"
output_dir = "dataset/.characters"
os.makedirs(output_dir, exist_ok=True)

def sort_contours(cnts):
    bounding_boxes = [cv2.boundingRect(c) for c in cnts]
    return [x for _, x in sorted(zip(bounding_boxes, cnts), key=lambda b: (b[0][1], b[0][0]))]

def extract_circular_characters(image_path, image_id):
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ O'qib bo'lmadi: {image_path}")
        return

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Konturlarni topish
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = sort_contours(contours)

    count = 0
    for i, c in enumerate(contours):
        (x, y, w, h) = cv2.boundingRect(c)
        aspect_ratio = w / float(h)
        area = cv2.contourArea(c)

        # Faqat dumaloq belgilarni qabul qilish (radius, area, aspect_ratio)
        if 15 < w < 100 and 0.8 < aspect_ratio < 1.2 and area > 100:
            crop = image[y:y+h, x:x+w]
            out_path = os.path.join(output_dir, f"{image_id}_{count}.png")
            cv2.imwrite(out_path, crop)
            count += 1

    print(f"📎 {image_id}: {count} belgi saqlandi.")

# Barcha rasmlarni qayta ishlash
for img_path in Path(input_dir).glob("*.png"):
    img_id = img_path.stem
    extract_circular_characters(str(img_path), img_id)
