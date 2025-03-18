from ultralytics import YOLO
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Load recently trained model
model = YOLO("V2best.pt")

# Evaluate model performance on the validation set, returns predictions.json (defines where the BBOXes are)
metrics = model.val(
    name="V2bestVal",
    data="config.yaml",
    imgsz=640,
    max_det=1,
    plots=True, 
    save_json=True
)

'''
JSON Annotation Outputs
{
SINGLE 
    "image_id": "bus_0680-s",   # IMG id
    "category_id": 1,           # 1 = benign(0), 2 = malignant(1)
    "bbox": [
        234.062,            # x top left corner
        140.077,            # y top left corner
        160.971,            # width
        78.016              # height
    ],
    "score": 0.86259        # Confidence
},

image_id = image name   category_id = config.yaml class number + 1 
x_y coordinates:    x1, y1, x2, y2
'''

''' To-Do: 
Produce a Confusion Matrix for ALL unseen data. Produce a confusion matrix for each Type: Normal, Benign, Malignant
'''