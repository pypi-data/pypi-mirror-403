import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForZeroShotObjectDetection
from accelerate import Accelerator
import logging
import time
import os
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# __init__ to load the model only once
# Will only load the grounding dino model when the class is called and not during the import of this file 
class GroundingDINO:
    def __init__(self, model_id="IDEA-Research/grounding-dino-tiny", cache_dir="./cache"): 
        self.model_id = model_id
        self.cache_dir = cache_dir

        self.device = Accelerator().device

        self.processor = AutoProcessor.from_pretrained(self.model_id, use_fast=False,
                                                       cache_dir=self.cache_dir)
        self.model = AutoModelForZeroShotObjectDetection.from_pretrained(
            self.model_id,
            cache_dir=self.cache_dir).to(self.device)

    def detect(self, image, text_labels, image_path, results_folder = "detector_results",box_threhsold=0.4, text_threshold=0.3):
        inputs = self.processor(images=image, text=text_labels, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.model(**inputs)

        results = self.processor.post_process_grounded_object_detection(
            outputs,
            inputs.input_ids,
            threshold=box_threhsold,
            text_threshold=text_threshold,
            target_sizes=[image.size[::-1]]
            )
        self.save_results_txt(results, results_folder, image_path)
        return results
    
    def save_results_txt(self, results, results_folder, image_path):
        if results: #There are detections and no empty detections there
            os.makedirs(results_folder, exist_ok=True)
            file_name = Path(image_path).name.split(".")[0]
            label_path = os.path.join(results_folder, file_name+".txt")
            bboxes = results[0]["boxes"].cpu().numpy()
            conf_scores = results[0]["scores"].cpu().numpy()
            text_labels = results[0]["text_labels"]
            labels = results[0]["labels"] #Should return integer labels in the future as per the warnings currently 
            for index, box in enumerate(bboxes):
                x1, y1, x2, y2 = map(int, box)
                confidence_score = conf_scores[index]
                text_class = text_labels[index]
                with open(label_path, "a") as f:
                    line = text_class + "\t" + str(x1) + "\t" + str(y1) + "\t" + str(x2) + "\t" + str(y2) + str(confidence_score)
                    f.write(line)
        else:
            logging.info(f"Detections missed by Grounding Dino Tiny\t{time.time()}")