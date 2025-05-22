from ultralytics import YOLO

# Load a YOLO model
model = YOLO("yolo11n.pt")  # or any other YOLO model
data = '/home/saiful/Rintu/projects/snake-detection/dataset/snake classification.v2i.yolov7pytorch/data.yaml'

# Train the model on custom dataset
results = model.train(data=data, epochs=3, imgsz=640)