import cv2
import numpy as np

def segment_characters(image):
    if isinstance(image, np.ndarray):
        img_cv = image
    else:
        img_cv = np.array(image)
        if img_cv.shape[-1] == 4:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGBA2BGR)
        elif img_cv.shape[-1] == 3:
            img_cv = cv2.cvtColor(img_cv, cv2.COLOR_RGB2BGR)

    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    blur = cv2.medianBlur(gray, 5)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    bounding_boxes = [cv2.boundingRect(c) for c in contours]

    # Sort by x coordinate (chapdan o‘ngga)
    sorted_contours = sorted(zip(contours, bounding_boxes), key=lambda b: b[1][0])

    characters = []
    for c, (x, y, w, h) in sorted_contours:
        aspect_ratio = w / float(h)
        area = cv2.contourArea(c)

        if 15 < w < 100 and 0.8 < aspect_ratio < 1.2 and area > 100:
            char_img = img_cv[y:y+h, x:x+w]
            resized = cv2.resize(char_img, (28, 28))
            resized = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
            characters.append(resized)

    return characters

