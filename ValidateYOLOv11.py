from ultralytics import YOLO
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Load recently trained model
model = YOLO("TrainedModel.pt")

# Evaluate model performance on the validation set, returns predictions.json (defines where the BBOXes are)
metrics = model.val(
    name="ReasonableModelName",
    data="config.yaml",
    imgsz=640,
    max_det=1,                  # Limits the number of bounding boxes per image to one (most confident prediction)
    plots=False,                # Controls if graph are generated
    save_json=True              # Creates predictions.json
)
