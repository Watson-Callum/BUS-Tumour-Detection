from ultralytics import YOLO
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Load a starting model
model = YOLO("yolo11m.pt")

# Train the model
train_results = model.train(
    data="config.yaml",  # path to dataset YAML
    name="ReasonableModelName",
    epochs=100,     # number of training epochs
    imgsz=640,      # training image size
    val=False,      # enables/disables Ultralytics validation and metrics
    augment=False   # enables/disables image augmentations
)
