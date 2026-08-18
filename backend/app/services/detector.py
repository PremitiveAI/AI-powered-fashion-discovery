# app/services/detector.py
from ultralytics import YOLO
import cv2
import numpy as np

model = YOLO("yolov8s.pt")

def detect(image):
    results = model(image)
    output = []
    for box in results[0].boxes:
        cls_id = int(box.cls[0])
        output.append({
            "label": model.names[cls_id].lower(),
            "bbox": box.xyxy[0].tolist(),
            "confidence": float(box.conf[0])
        })
    return output

# def decode_image(file_bytes: bytes):
#     arr = np.frombuffer(file_bytes, np.uint8)
#     return cv2.imdecode(arr, cv2.IMREAD_COLOR)


def decode_image(file_bytes: bytes):
    if not file_bytes:
        raise ValueError("Empty image bytes")

    np_arr = np.frombuffer(file_bytes, dtype=np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("cv2.imdecode failed — invalid image bytes")

    return img

def crop(image, bbox, pad=10):
    h, w = image.shape[:2]
    x1, y1, x2, y2 = map(int, bbox)
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)
    return image[y1:y2, x1:x2]

# NEW FUNCTION: Calculate Intersection over Union
def calculate_iou(box1, box2):
    """
    Calculate IoU between two bounding boxes
    box format: {"x1": int, "y1": int, "x2": int, "y2": int}
    """
    # Determine coordinates of intersection rectangle
    x_left = max(box1["x1"], box2["x1"])
    y_top = max(box1["y1"], box2["y1"])
    x_right = min(box1["x2"], box2["x2"])
    y_bottom = min(box1["y2"], box2["y2"])
    
    if x_right < x_left or y_bottom < y_top:
        return 0.0
    
    # Area of intersection
    intersection_area = (x_right - x_left) * (y_bottom - y_top)
    
    # Area of both boxes
    box1_area = (box1["x2"] - box1["x1"]) * (box1["y2"] - box1["y1"])
    box2_area = (box2["x2"] - box2["x1"]) * (box2["y2"] - box2["y1"])
    
    # Union area
    union_area = box1_area + box2_area - intersection_area
    
    # IoU
    iou = intersection_area / union_area if union_area > 0 else 0.0
    
    return iou

# NEW FUNCTION: Filter overlapping detections
def filter_overlapping_boxes(detections, iou_threshold=0.5):
    """
    Filter out overlapping bounding boxes
    """
    if not detections:
        return detections
    
    # Sort by confidence (highest first)
    detections.sort(key=lambda x: x.get("confidence", 0), reverse=True)
    
    filtered = []
    used_indices = set()
    
    for i in range(len(detections)):
        if i in used_indices:
            continue
            
        current = detections[i]
        filtered.append(current)
        used_indices.add(i)
        
        # Check overlap with remaining boxes
        for j in range(i + 1, len(detections)):
            if j in used_indices:
                continue
                
            if "bbox" in current and "bbox" in detections[j]:
                iou = calculate_iou(current["bbox"], detections[j]["bbox"])
                if iou > iou_threshold:
                    used_indices.add(j)
    
    return filtered