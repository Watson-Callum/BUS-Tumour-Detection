from ultralytics import YOLO
import os

os.environ['KMP_DUPLICATE_LIB_OK']='True'

# Load a model

model = YOLO("yolo11m.pt")
#model = YOLO("V1best.pt")

# Train the model
train_results = model.train(
    data="config.yaml",  # path to dataset YAML
    epochs=100,  # number of training epochs
    imgsz=640,  # training image size
    #device="cpu",  # device to run on, i.e. device=0 or device=0,1,2,3 or device=cpu
    #RuntimeError: Expected one of cpu, cuda, ipu, xpu, mkldnn, opengl, opencl, ideep, hip, ve, fpga, maia, xla, lazy, vulkan, mps, meta, hpu, mtia, privateuseone device type at start of device string: gpu
)

# Evaluate model performance on the validation set
#metrics = model.val(name="V1bestVal", max_det=1, plots=True, save_json=True)
# MAX DETECTIONS



# Perform object detection on an image
#results = model("images/validation/IM-0141-0001.jpg")

#print(f"##################\n\n\n\n{results}")
#results[0].show()

# Export the model to ONNX format
#path = model.export(format="onnx")  # return path to exported model

''' To-Do: 
Produce a Confusion Matrix for ALL unseen data. Produce a confusion matrix for each Type: Normal, Benign, Malignant




'''