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
        Detect pets in the given frame with improved caching logic.

        Args:
            frame: Input video frame
            frame_number: Current frame number for caching
            
        Returns:
            List of Detection objects
        """
        # Check if we can use cached detections (but with stricter conditions)
        if self._can_use_cached_detections(frame_number):
            # Only use cache if we're in a performance mode that allows it
            if self.performance_settings.mode in ["performance", "ultra"]:
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
        
        # Update cache with more intelligent logic
        self._update_detection_cache(detections, frame_number)
        
        return detections

    def _update_detection_cache(self, detections: List[Detection], frame_number: int):
        """Update detection cache with intelligent invalidation."""
        # If we have new detections, check if they're significantly different from cached ones
        if detections and self.cached_detections:
            # Calculate position changes
            significant_change = self._detect_significant_movement(detections, self.cached_detections)
            
            if significant_change:
                # Clear cache if significant movement detected
                self.cached_detections = detections
                self.last_detection_frame = frame_number
                print(f"Cache invalidated due to significant movement at frame {frame_number}")
            else:
                # Update cache normally
                self.cached_detections = detections
                self.last_detection_frame = frame_number
        else:
            # Normal cache update
            self.cached_detections = detections
            self.last_detection_frame = frame_number

    def _detect_significant_movement(self, new_detections: List[Detection], 
                                cached_detections: List[Detection]) -> bool:
        """Detect if there's significant movement between detections."""
        if len(new_detections) != len(cached_detections):
            return True
        
        # Check if any detection has moved significantly
        movement_threshold = 50  # pixels
        
        for new_det in new_detections:
            new_center = new_det.center
            
            # Find closest cached detection
            min_distance = float('inf')
            for cached_det in cached_detections:
                cached_center = cached_det.center
                distance = ((new_center[0] - cached_center[0])**2 + 
                        (new_center[1] - cached_center[1])**2)**0.5
                min_distance = min(min_distance, distance)
            
            if min_distance > movement_threshold:
                return True
        
        return False

    def _can_use_cached_detections(self, frame_number: int) -> bool:
        """Check if cached detections can be used - with stricter conditions."""
        if self.last_detection_frame is None:
            return False
        
        frame_diff = frame_number - self.last_detection_frame
        
        # Reduce cache usage for better detection accuracy
        # Only use cache for 1-2 frames maximum
        max_cache_frames = 2 if self.performance_settings.mode == "ultra" else 1
        
        return frame_diff < max_cache_frames

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