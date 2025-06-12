"""
Mock implementation of pet detector for testing.
"""
import numpy as np
import datetime
from typing import List, Optional, Tuple
from unittest.mock import Mock

from backend.data.models import Detection, PerformanceSettings


class MockPetDetector:
    """Mock pet detector for testing purposes."""
    
    def __init__(self, model_path: str = "mock_model.pt", confidence_threshold: float = 0.5):
        self.model_path = model_path
        self.confidence_threshold = confidence_threshold
        self.pet_classes = {'cat': 15, 'dog': 16}
        
        # Detection simulation settings
        self.detection_probability = 0.8  # Probability of detecting a pet
        self.detection_patterns = []  # Pre-defined detection patterns
        self.current_pattern_index = 0
        
        # Performance settings
        self.performance_settings = PerformanceSettings.from_mode("balanced")
        
        # Detection caching (simulate the real detector behavior)
        self.last_detection_frame = None
        self.cached_detections = []
        self.detection_cache_frames = 3
        
        # Mock model properties
        self.model_loaded = True
        self.detection_count = 0
    
    def set_detection_patterns(self, patterns: List[List[Detection]]):
        """Set pre-defined detection patterns for testing."""
        self.detection_patterns = patterns
        self.current_pattern_index = 0
    
    def set_detection_probability(self, probability: float):
        """Set the probability of detecting pets in frames."""
        self.detection_probability = max(0.0, min(1.0, probability))
    
    def update_performance_settings(self, settings: PerformanceSettings):
        """Update performance optimization settings."""
        self.performance_settings = settings
        self.detection_cache_frames = settings.detection_cache_frames
    
    def update_confidence_threshold(self, threshold: float):
        """Update detection confidence threshold."""
        self.confidence_threshold = max(0.1, min(0.9, threshold))
    
    def detect_pets(self, frame: np.ndarray, frame_number: int) -> List[Detection]:
        """
        Mock pet detection that returns simulated detections.
        
        Args:
            frame: Input video frame (not actually processed)
            frame_number: Current frame number
            
        Returns:
            List of mock Detection objects
        """
        self.detection_count += 1
        
        # Check if we can use cached detections
        if self._can_use_cached_detections(frame_number):
            return self.cached_detections
        
        # Generate new detections
        detections = []
        
        if self.detection_patterns:
            # Use pre-defined patterns
            detections = self._get_pattern_detections(frame_number)
        else:
            # Generate random detections
            detections = self._generate_random_detections(frame, frame_number)
        
        # Filter by confidence threshold
        detections = [d for d in detections if d.confidence >= self.confidence_threshold]
        
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
    
    def _get_pattern_detections(self, frame_number: int) -> List[Detection]:
        """Get detections from pre-defined patterns."""
        if not self.detection_patterns:
            return []
        
        pattern_index = self.current_pattern_index % len(self.detection_patterns)
        detections = self.detection_patterns[pattern_index]
        
        # Update frame numbers and timestamps
        current_time = datetime.datetime.now()
        updated_detections = []
        
        for detection in detections:
            updated_detection = Detection(
                bbox=detection.bbox,
                pet_type=detection.pet_type,
                confidence=detection.confidence,
                timestamp=current_time,
                frame_number=frame_number
            )
            updated_detections.append(updated_detection)
        
        self.current_pattern_index += 1
        return updated_detections
    
    def _generate_random_detections(self, frame: np.ndarray, frame_number: int) -> List[Detection]:
        """Generate random detections for testing."""
        detections = []
        
        # Randomly decide if we should detect pets
        if np.random.random() > self.detection_probability:
            return detections
        
        # Generate 1-2 random detections
        num_detections = np.random.choice([1, 2], p=[0.8, 0.2])
        
        for _ in range(num_detections):
            # Random bounding box
            frame_height, frame_width = frame.shape[:2] if frame is not None else (480, 640)
            
            # Generate realistic bounding box
            box_width = np.random.randint(50, 150)
            box_height = np.random.randint(60, 180)
            
            x1 = np.random.randint(0, max(1, frame_width - box_width))
            y1 = np.random.randint(0, max(1, frame_height - box_height))
            x2 = x1 + box_width
            y2 = y1 + box_height
            
            # Random pet type and confidence
            pet_type = np.random.choice(['cat', 'dog'])
            confidence = np.random.uniform(0.3, 0.95)
            
            detection = Detection(
                bbox=(x1, y1, x2, y2),
                pet_type=pet_type,
                confidence=confidence,
                timestamp=datetime.datetime.now(),
                frame_number=frame_number
            )
            
            detections.append(detection)
        
        return detections
    
    def draw_detections(self, frame: np.ndarray, detections: List[Detection]) -> np.ndarray:
        """Mock drawing detections on frame (returns frame unchanged)."""
        # In a real implementation, this would draw bounding boxes
        # For testing, we just return the frame as-is
        return frame.copy() if frame is not None else np.zeros((480, 640, 3), dtype=np.uint8)
    
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
        """Get information about the mock model."""
        return {
            "model_path": self.model_path,
            "model_exists": True,  # Always true for mock
            "confidence_threshold": self.confidence_threshold,
            "supported_classes": self.pet_classes,
            "cache_frames": self.detection_cache_frames,
            "detection_count": self.detection_count,
            "is_mock": True
        }
    
    def create_test_detection(self, 
                            bbox: Tuple[int, int, int, int],
                            pet_type: str = "cat",
                            confidence: float = 0.8,
                            frame_number: int = 1) -> Detection:
        """Helper method to create test detections."""
        return Detection(
            bbox=bbox,
            pet_type=pet_type,
            confidence=confidence,
            timestamp=datetime.datetime.now(),
            frame_number=frame_number
        )
    
    @staticmethod
    def create_cat_detection(bbox: Tuple[int, int, int, int], 
                           confidence: float = 0.8,
                           frame_number: int = 1) -> Detection:
        """Create a cat detection for testing."""
        return Detection(
            bbox=bbox,
            pet_type="cat",
            confidence=confidence,
            timestamp=datetime.datetime.now(),
            frame_number=frame_number
        )
    
    @staticmethod
    def create_dog_detection(bbox: Tuple[int, int, int, int], 
                           confidence: float = 0.8,
                           frame_number: int = 1) -> Detection:
        """Create a dog detection for testing."""
        return Detection(
            bbox=bbox,
            pet_type="dog",
            confidence=confidence,
            timestamp=datetime.datetime.now(),
            frame_number=frame_number
        )
    
    @staticmethod
    def create_detection_sequence(pet_type: str = "cat", 
                                count: int = 5,
                                start_frame: int = 1) -> List[Detection]:
        """Create a sequence of detections for testing."""
        detections = []
        
        for i in range(count):
            # Create moving bounding box
            x_offset = i * 10
            bbox = (100 + x_offset, 100, 200 + x_offset, 200)
            
            detection = Detection(
                bbox=bbox,
                pet_type=pet_type,
                confidence=0.8 + (i * 0.02),  # Slightly varying confidence
                timestamp=datetime.datetime.now(),
                frame_number=start_frame + i
            )
            detections.append(detection)
        
        return detections