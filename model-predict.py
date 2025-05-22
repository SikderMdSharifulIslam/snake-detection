from ultralytics import YOLO

# Load a pretrained YOLO11n model
model = YOLO("/home/saiful/Rintu/projects/snake-detection/runs/detect/train2/weights/best.pt")

# Run inference on 'bus.jpg' with arguments
model.predict("/home/saiful/Rintu/projects/snake-detection/images.jpeg", save=True, conf=0.0001)