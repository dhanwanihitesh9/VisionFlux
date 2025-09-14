"""
AI Detection Service for VisionFlux
Handles AI model inference for image analysis and event detection
"""

import asyncio
import logging
import numpy as np
from typing import List, Optional, Dict, Any
from datetime import datetime
import cv2
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel
from ultralytics import YOLO

from app.models.schemas import DetectionResult, CustomPrompt
from app.config import settings

logger = logging.getLogger(__name__)


class AIDetector:
    """AI-powered detection service"""
    
    def __init__(self):
        self.clip_model = None
        self.clip_processor = None
        self.yolo_model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.custom_prompts: Dict[str, CustomPrompt] = {}
        
        logger.info(f"Initializing AI Detector on device: {self.device}")
    
    async def initialize(self):
        """Initialize AI models"""
        try:
            logger.info("Loading CLIP model for custom prompt detection...")
            self.clip_model = CLIPModel.from_pretrained(settings.ai_model_name)
            self.clip_processor = CLIPProcessor.from_pretrained(settings.ai_model_name)
            self.clip_model.to(self.device)
            
            logger.info("Loading YOLO model for object detection...")
            self.yolo_model = YOLO(settings.yolo_model)
            
            logger.info("✅ AI models loaded successfully")
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize AI models: {e}")
            raise
    
    def add_custom_prompt(self, prompt: CustomPrompt):
        """Add a custom detection prompt"""
        self.custom_prompts[prompt.id] = prompt
        logger.info(f"Added custom prompt: {prompt.name}")
    
    def remove_custom_prompt(self, prompt_id: str):
        """Remove a custom detection prompt"""
        if prompt_id in self.custom_prompts:
            del self.custom_prompts[prompt_id]
            logger.info(f"Removed custom prompt: {prompt_id}")
    
    def get_custom_prompts(self) -> List[CustomPrompt]:
        """Get all custom prompts"""
        return list(self.custom_prompts.values())
    
    async def detect_objects(self, frame: np.ndarray) -> List[DetectionResult]:
        """Detect objects using YOLO model"""
        try:
            if self.yolo_model is None:
                await self.initialize()
            
            # Run YOLO inference
            results = self.yolo_model(frame, verbose=False)
            detections = []
            
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for box in boxes:
                        confidence = float(box.conf[0])
                        if confidence >= settings.detection_confidence:
                            # Get class name
                            class_id = int(box.cls[0])
                            class_name = self.yolo_model.names[class_id]
                            
                            # Get bounding box
                            bbox = box.xyxy[0].cpu().numpy().tolist()
                            
                            detection = DetectionResult(
                                confidence=confidence,
                                description=f"Detected {class_name}",
                                bbox=bbox,
                                timestamp=datetime.now()
                            )
                            detections.append(detection)
            
            return detections
            
        except Exception as e:
            logger.error(f"Object detection failed: {e}")
            return []
    
    async def analyze_with_custom_prompts(
        self, 
        frame: np.ndarray, 
        camera_id: str
    ) -> List[DetectionResult]:
        """Analyze frame using custom prompts"""
        try:
            if self.clip_model is None or self.clip_processor is None:
                await self.initialize()
            
            # Filter prompts for this camera
            applicable_prompts = [
                prompt for prompt in self.custom_prompts.values()
                if prompt.enabled and (
                    prompt.camera_ids is None or camera_id in prompt.camera_ids
                )
            ]
            
            if not applicable_prompts:
                return []
            
            # Convert frame to PIL Image
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame_rgb)
            
            detections = []
            
            for prompt in applicable_prompts:
                try:
                    # Prepare text prompts
                    text_queries = [
                        f"a photo of {prompt.prompt}",
                        f"a photo without {prompt.prompt}"
                    ]
                    
                    # Process inputs
                    inputs = self.clip_processor(
                        text=text_queries,
                        images=image,
                        return_tensors="pt",
                        padding=True
                    )
                    
                    # Move to device
                    inputs = {k: v.to(self.device) for k, v in inputs.items()}
                    
                    # Get predictions
                    with torch.no_grad():
                        outputs = self.clip_model(**inputs)
                        logits_per_image = outputs.logits_per_image
                        probs = logits_per_image.softmax(dim=1)
                    
                    # Check if the positive prompt has higher probability
                    positive_prob = float(probs[0][0])
                    
                    if positive_prob >= prompt.confidence_threshold:
                        detection = DetectionResult(
                            confidence=positive_prob,
                            description=f"Custom prompt matched: {prompt.name}",
                            timestamp=datetime.now()
                        )
                        detections.append(detection)
                        logger.info(f"Custom prompt '{prompt.name}' matched with confidence {positive_prob:.2f}")
                
                except Exception as e:
                    logger.error(f"Failed to process custom prompt '{prompt.name}': {e}")
                    continue
            
            return detections
            
        except Exception as e:
            logger.error(f"Custom prompt analysis failed: {e}")
            return []
    
    async def analyze_frame(
        self, 
        frame: np.ndarray, 
        camera_id: str,
        enable_object_detection: bool = True,
        enable_custom_prompts: bool = True
    ) -> List[DetectionResult]:
        """Analyze a frame with all enabled detection methods"""
        all_detections = []
        
        try:
            # Run object detection
            if enable_object_detection:
                object_detections = await self.detect_objects(frame)
                all_detections.extend(object_detections)
            
            # Run custom prompt analysis
            if enable_custom_prompts:
                prompt_detections = await self.analyze_with_custom_prompts(frame, camera_id)
                all_detections.extend(prompt_detections)
            
            logger.debug(f"Frame analysis complete: {len(all_detections)} detections")
            return all_detections
            
        except Exception as e:
            logger.error(f"Frame analysis failed: {e}")
            return []
    
    def is_initialized(self) -> bool:
        """Check if models are initialized"""
        return (self.clip_model is not None and 
                self.clip_processor is not None and 
                self.yolo_model is not None)
