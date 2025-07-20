import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from segment import segment_characters
from PIL import Image
import argparse
import numpy as np

# 📐 Config
IMG_SIZE = 28
MODEL_PATH = "symbol_cnn_model.pt"
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

display_map = {
    'plus': '+',
    'minus': '-',
    'mul': '*',
    '0': '0',
    '1': '1',
    '2': '2',
    '3': '3',
    '4': '4',
    '5': '5',
    '6': '6',
    '7': '7',
    '8': '8',
    '9': '9',
}

# 🧠 CNN model class (train.py dagi bilan bir xil)
class SymbolCNN(nn.Module):
    def __init__(self, num_classes):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 32, 3, 1)
        self.conv2 = nn.Conv2d(32, 64, 3, 1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 5 * 5, 128)
        self.fc2 = nn.Linear(128, num_classes)
        self.relu = nn.ReLU()

    def forward(self, x):
        x = self.pool(self.relu(self.conv1(x)))
        x = self.pool(self.relu(self.conv2(x)))
        x = x.view(-1, 64 * 5 * 5)
        x = self.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# 🔄 Transform - train.py dagi bilan bir xil
transform = transforms.Compose([
    transforms.Grayscale(),
    transforms.Resize((IMG_SIZE, IMG_SIZE)),
    transforms.ToTensor()
])

# 📦 Model va mappinglarni yuklash (bir marta)
checkpoint = torch.load(MODEL_PATH, map_location=DEVICE)
class_to_idx = checkpoint['class_to_idx']
idx_to_class = {v: k for k, v in class_to_idx.items()}

model = SymbolCNN(num_classes=len(class_to_idx))
model.load_state_dict(checkpoint['model_state_dict'])
model.to(DEVICE)
model.eval()

# 📤 Bitta belgini bashorat qilish
def predict_single(image):
    image = transform(image).unsqueeze(0).to(DEVICE)
    with torch.no_grad():
        output = model(image)
        _, predicted = output.max(1)
        return idx_to_class[predicted.item()]

# 📤 To‘liq captcha rasmni bashorat qilish
def predict_full_captcha(image_input):
    if isinstance(image_input, str):
        image = cv2.imread(image_input)
    elif isinstance(image_input, (bytes, bytearray)):
        # Raw image bytes
        image_bytes = np.asarray(bytearray(image_input), dtype=np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    elif hasattr(image_input, 'read'):
        # file-like (BytesIO)
        image_bytes = np.asarray(bytearray(image_input.read()), dtype=np.uint8)
        image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)
    else:
        raise ValueError("Unsupported image input format")

    if image is None:
        raise ValueError("Image could not be decoded or read")
    segments = segment_characters(image)

    prediction = ""
    i = 0
    for seg in segments:
        i += 1
        # cv2.imwrite(f"segment{i}.png", seg)
        # OpenCV segment -> PIL image
        seg_pil = Image.fromarray(seg)
        label = predict_single(seg_pil)
        prediction += display_map.get(label, "?")
    return prediction

# ▶️ CLI ishlatish
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", help="Path to image file")
    args = parser.parse_args()

    result = predict_full_captcha(args.image)
    print(f"🔮 Predict: {result}")
