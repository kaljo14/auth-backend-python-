import torch, detectron2
import detectron2
from detectron2.utils.logger import setup_logger
from detectron2.checkpoint import DetectionCheckpointer
from detectron2.config import get_cfg
from detectron2.modeling import build_model

# Load the configuration for the model
cfg = get_cfg()
cfg.merge_from_file('/path/to/model/config.yaml')

# Build the model
model = build_model(cfg)

# Load the saved weights into the model
checkpointer = DetectionCheckpointer(model)
checkpointer.load('/path/to/model/file.pth')