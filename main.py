# pip install ultralytics
from ultralytics import YOLO
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Load a model
model = YOLO("runs\\detect\\train2\\weights\\best.pt")

# Train the model
#train_results = model.train(
#    data="config.yaml",  # path to dataset YAML
#    epochs=100,  # number of training epochs
#    imgsz=640,  # training image size
#    device="cpu",  # device to run on, i.e. device=0 or device=0,1,2,3 or device=cpu
#)

# Evaluate model performance on the validation set
#metrics = model.val()

# Perform object detection on an image
results = model("normal/IM-0002-0001.jpg")
results[0].show()

# Export the model to ONNX format
#path = model.export(format="onnx")  # return path to exported model


''' To-Do: 
Produce a Confusion Matrix for ALL unseen data. Produce a confusion matrix for each Type: Normal, Benign, Malignant




'''