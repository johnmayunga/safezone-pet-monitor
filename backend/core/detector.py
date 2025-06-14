"""
backend/core/detector.py
YOLO-based pet detection module.
"""
import cv2
import numpy as np
from ultralytics import YOLO
from typing import List, Optional, Tuple
import datetime
import os

from ..data.models import Detection, PerformanceSettings


class PetDetector:
    """YOLO-based pet detection system."""
    
    def __init__(self, model_path: str = "models/yolo12n.pt", confidence_threshold: float = 0.5):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.pet_classes = {'cat': 15, 'dog': 16}
        
        # Detection caching for performance
        self.last_detection_frame = None
        self.cached_detections = []
        self.detection_cache_frames = 3
        
        # Performance settings
        self.performance_settings = PerformanceSettings.from_mode("balanced")
        
        # Initialize YOLO model
        self.model = self._load_model()
    
    def _load_model(self) -> YOLO:
        """Load the YOLO model."""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        
        try:
            model = YOLO(self.model_path)
            print(f"✓ YOLO model loaded successfully: {self.model_path}")
            return model
        except Exception as e:
            raise RuntimeError(f"Failed to load YOLO model: {e}")
    
    def update_performance_settings(self, settings: PerformanceSettings):
        """Update performance optimization settings."""
        self.performance_settings = settings
        self.detection_cache_frames = settings.detection_cache_frames
    
    def update_confidence_threshold(self, threshold: float):
        """Update detection confidence threshold."""
        self.confidence_threshold = max(0.1, min(0.9, threshold))
    
    def detect_pets(self, frame: np.ndarray, frame_number: int) -> List[Detection]:
        """
        Detect pets in the given frame.
        
        Args:
            frame: Input video frame
            frame_number: Current frame number for caching

        Returns:
            List of Detection objects
        """
        # Level 1: Processing-level frame skipping
        mode = self.performance_settings.mode

        if mode == "ultra":
            if frame_number % 10 != 0:  # Process only every 10th frame
                return self.cached_detections
        elif mode == "performance":
            if frame_number % 5 != 0:  # Process every 5th frame
                return self.cached_detections
        elif mode == "balanced":
            if frame_number % 3 != 0:  # Process every 3rd frame
                return self.cached_detections
        
        # Check if we can use cached detections
        if self._can_use_cached_detections(frame_number):
            return self.cached_detections
        
        # Determine processing scale based on performance mode
        scale = self._get_processing_scale()
        
        # Resize frame for processing if needed
        if scale < 1.0:
            small_frame = cv2.resize(frame, (0, 0), fx=scale, fy=scale)
        else:
            small_frame = frame
        
        # Run YOLO detection
        try:
            results = self.model(small_frame, conf=self.confidence_threshold, verbose=False)
        except Exception as e:
            print(f"Detection error: {e}")
            return []
        
        # Process results
        detections = []
        current_time = datetime.datetime.now()
        
        for result in results:
            if result.boxes is not None:
                boxes = result.boxes
                for box in boxes:
                    class_id = int(box.cls[0])
                    confidence = float(box.conf[0])
                    
                    # Check if it's a pet (cat or dog)
                    if class_id in self.pet_classes.values():
                        # Scale coordinates back to original frame size if needed
                        bbox = box.xyxy[0].cpu().numpy()
                        if scale < 1.0:
                            bbox = bbox / scale
                        
                        # Determine pet type
                        pet_type = 'cat' if class_id == 15 else 'dog'
                        
                        # Create detection object
                        detection = Detection(
                            bbox=tuple(bbox),
                            pet_type=pet_type,
                            confidence=confidence,
                            timestamp=current_time,
                            frame_number=frame_number
                        )
                        
                        detections.append(detection)
        
        # Update cache
        self.cached_detections = detections
        self.last_detection_frame = frame_number
        
        return detections
    
    def _can_use_cached_detections(self, frame_number: int) -> bool:
        """Check if cached detections can be used."""
        if self.last_detection_frame is None:
            return False
        
        frame_diff = frame_number - self.last_detection_frame
        return frame_diff < self.detection_cache_frames
    
    def _get_processing_scale(self) -> float:
        """Get frame processing scale based on performance mode."""
        scale_map = {
            "quality": 0.75,
            "balanced": 0.5,
            "performance": 0.4,
            "ultra": 0.25
        }
        return scale_map.get(self.performance_settings.mode, 0.5)
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """
        Draw detection bounding boxes and labels on frame.
        
        Args:
            frame: Input frame
            detections: List of detections to draw
            
        Returns:
            Frame with drawn detections
        """
        frame_copy = frame.copy()
        
        for detection in detections:
            x1, y1, x2, y2 = map(int, detection.bbox)
            
            # Draw bounding box
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), (0, 255, 0), 2)
            
            # Prepare label
            label = f"{detection.pet_type} {detection.confidence:.2f}"
            
            # Get label size for background
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Draw label background
            cv2.rectangle(frame_copy, (x1, y1 - 20), 
                         (x1 + label_size[0], y1), (0, 255, 0), -1)
            
            # Draw label text
            cv2.putText(frame_copy, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        return frame_copy
    
    def get_detection_summary(self, detections: List[Detection]) -> dict:
        """Get summary information about detections."""
        if not detections:
            return {"total": 0, "cats": 0, "dogs": 0, "avg_confidence": 0.0}
        
        cats = sum(1 for d in detections if d.pet_type == 'cat')
        dogs = sum(1 for d in detections if d.pet_type == 'dog')
        avg_confidence = sum(d.confidence for d in detections) / len(detections)
        
        return {
            "total": len(detections),
            "cats": cats,
            "dogs": dogs,
            "avg_confidence": avg_confidence
        }
    
    def clear_cache(self):
        """Clear detection cache."""
        self.last_detection_frame = None
        self.cached_detections = []
    
    def get_model_info(self) -> dict:
        """Get information about the loaded model."""
        return {
            "model_path": self.model_path,
            "model_exists": os.path.exists(self.model_path),
            "confidence_threshold": self.confidence_threshold,
            "supported_classes": self.pet_classes,
            "cache_frames": self.detection_cache_frames
        }