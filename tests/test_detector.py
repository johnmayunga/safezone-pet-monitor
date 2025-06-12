"""
Unit tests for the PetDetector class.
"""
import unittest
import numpy as np
import cv2
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
import datetime

# Import the modules to test
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.core.detector import PetDetector
from backend.data.models import Detection, PerformanceSettings


class TestPetDetector(unittest.TestCase):
    """Test cases for PetDetector class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        # Create a temporary model file
        self.temp_model_file = tempfile.NamedTemporaryFile(suffix='.pt', delete=False)
        self.temp_model_file.write(b'dummy model data')
        self.temp_model_file.close()
        
        # Mock the YOLO model to avoid loading actual model
        self.yolo_mock = Mock()
        
    def tearDown(self):
        """Clean up after each test method."""
        # Remove temporary model file
        os.unlink(self.temp_model_file.name)
    
    @patch('backend.core.detector.YOLO')
    def test_detector_initialization(self, mock_yolo):
        """Test detector initialization with valid model path."""
        # Setup mock
        mock_yolo.return_value = self.yolo_mock
        
        # Test initialization
        detector = PetDetector(self.temp_model_file.name, confidence_threshold=0.6)
        
        # Assertions
        self.assertEqual(detector.model_path, self.temp_model_file.name)
        self.assertEqual(detector.confidence_threshold, 0.6)
        self.assertEqual(detector.pet_classes, {'cat': 15, 'dog': 16})
        mock_yolo.assert_called_once_with(self.temp_model_file.name)
    
    def test_detector_initialization_missing_model(self):
        """Test detector initialization with missing model file."""
        with self.assertRaises(FileNotFoundError):
            PetDetector("nonexistent_model.pt")
    
    @patch('backend.core.detector.YOLO')
    def test_update_confidence_threshold(self, mock_yolo):
        """Test updating confidence threshold."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Test valid threshold updates
        detector.update_confidence_threshold(0.8)
        self.assertEqual(detector.confidence_threshold, 0.8)
        
        # Test boundary conditions
        detector.update_confidence_threshold(0.05)  # Below minimum
        self.assertEqual(detector.confidence_threshold, 0.1)  # Should be clamped
        
        detector.update_confidence_threshold(0.95)  # Above maximum
        self.assertEqual(detector.confidence_threshold, 0.9)   # Should be clamped
    
    @patch('backend.core.detector.YOLO')
    def test_update_performance_settings(self, mock_yolo):
        """Test updating performance settings."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Create test performance settings
        perf_settings = PerformanceSettings.from_mode("performance")
        detector.update_performance_settings(perf_settings)
        
        self.assertEqual(detector.performance_settings.mode, "performance")
        self.assertEqual(detector.detection_cache_frames, perf_settings.detection_cache_frames)
    
    @patch('backend.core.detector.YOLO')
    def test_detect_pets_with_cache(self, mock_yolo):
        """Test pet detection with caching enabled."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Create dummy frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock detection results
        mock_box = Mock()
        mock_box.cls = [15]  # Cat class
        mock_box.conf = [0.8]
        mock_box.xyxy = [Mock()]
        mock_box.xyxy[0].cpu.return_value.numpy.return_value = np.array([100, 100, 200, 200])
        
        mock_result = Mock()
        mock_result.boxes = [mock_box]
        
        self.yolo_mock.return_value = [mock_result]
        
        # First detection (should run YOLO)
        detections1 = detector.detect_pets(frame, frame_number=1)
        
        # Verify detection
        self.assertEqual(len(detections1), 1)
        self.assertEqual(detections1[0].pet_type, 'cat')
        self.assertEqual(detections1[0].confidence, 0.8)
        
        # Second detection within cache window (should use cache)
        detections2 = detector.detect_pets(frame, frame_number=2)
        
        # Should be same as cached detection
        self.assertEqual(len(detections2), 1)
        self.assertEqual(detections2[0].pet_type, 'cat')
    
    @patch('backend.core.detector.YOLO')
    def test_detect_pets_no_detections(self, mock_yolo):
        """Test pet detection when no pets are found."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock empty detection results
        mock_result = Mock()
        mock_result.boxes = None
        self.yolo_mock.return_value = [mock_result]
        
        detections = detector.detect_pets(frame, frame_number=1)
        
        self.assertEqual(len(detections), 0)
        self.assertEqual(detector.cached_detections, [])
    
    @patch('backend.core.detector.YOLO')
    def test_detect_pets_multiple_animals(self, mock_yolo):
        """Test detection of multiple pets in same frame."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Mock detection results for cat and dog
        mock_box1 = Mock()
        mock_box1.cls = [15]  # Cat
        mock_box1.conf = [0.8]
        mock_box1.xyxy = [Mock()]
        mock_box1.xyxy[0].cpu.return_value.numpy.return_value = np.array([100, 100, 200, 200])
        
        mock_box2 = Mock()
        mock_box2.cls = [16]  # Dog
        mock_box2.conf = [0.7]
        mock_box2.xyxy = [Mock()]
        mock_box2.xyxy[0].cpu.return_value.numpy.return_value = np.array([300, 300, 400, 400])
        
        mock_result = Mock()
        mock_result.boxes = [mock_box1, mock_box2]
        self.yolo_mock.return_value = [mock_result]
        
        detections = detector.detect_pets(frame, frame_number=1)
        
        self.assertEqual(len(detections), 2)
        self.assertEqual(detections[0].pet_type, 'cat')
        self.assertEqual(detections[1].pet_type, 'dog')
        self.assertEqual(detections[0].confidence, 0.8)
        self.assertEqual(detections[1].confidence, 0.7)
    
    @patch('backend.core.detector.YOLO')
    def test_draw_detections(self, mock_yolo):
        """Test drawing detection overlays on frame."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Create test frame and detections
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        detection = Detection(
            bbox=(100, 100, 200, 200),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        result_frame = detector.draw_detections(frame, [detection])
        
        # Frame should be modified (not identical to original)
        self.assertFalse(np.array_equal(frame, result_frame))
        self.assertEqual(result_frame.shape, frame.shape)
    
    @patch('backend.core.detector.YOLO')
    def test_get_detection_summary(self, mock_yolo):
        """Test detection summary statistics."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Test empty detections
        summary = detector.get_detection_summary([])
        expected = {"total": 0, "cats": 0, "dogs": 0, "avg_confidence": 0.0}
        self.assertEqual(summary, expected)
        
        # Test with detections
        detections = [
            Detection((100, 100, 200, 200), 'cat', 0.8, datetime.datetime.now(), 1),
            Detection((300, 300, 400, 400), 'dog', 0.7, datetime.datetime.now(), 1),
            Detection((500, 500, 600, 600), 'cat', 0.9, datetime.datetime.now(), 1)
        ]
        
        summary = detector.get_detection_summary(detections)
        
        self.assertEqual(summary["total"], 3)
        self.assertEqual(summary["cats"], 2)
        self.assertEqual(summary["dogs"], 1)
        self.assertAlmostEqual(summary["avg_confidence"], 0.8, places=2)
    
    @patch('backend.core.detector.YOLO')
    def test_clear_cache(self, mock_yolo):
        """Test clearing detection cache."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Set some cache data
        detector.last_detection_frame = 5
        detector.cached_detections = [Mock()]
        
        # Clear cache
        detector.clear_cache()
        
        self.assertIsNone(detector.last_detection_frame)
        self.assertEqual(detector.cached_detections, [])
    
    @patch('backend.core.detector.YOLO')
    def test_get_model_info(self, mock_yolo):
        """Test getting model information."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name, confidence_threshold=0.6)
        
        info = detector.get_model_info()
        
        self.assertEqual(info["model_path"], self.temp_model_file.name)
        self.assertEqual(info["confidence_threshold"], 0.6)
        self.assertTrue(info["model_exists"])
        self.assertEqual(info["supported_classes"], {'cat': 15, 'dog': 16})
    
    @patch('backend.core.detector.YOLO')
    def test_performance_scaling(self, mock_yolo):
        """Test processing scale based on performance mode."""
        mock_yolo.return_value = self.yolo_mock
        detector = PetDetector(self.temp_model_file.name)
        
        # Test different performance modes
        modes_and_scales = [
            ("quality", 0.75),
            ("balanced", 0.5),
            ("performance", 0.4),
            ("ultra", 0.25)
        ]
        
        for mode, expected_scale in modes_and_scales:
            perf_settings = PerformanceSettings.from_mode(mode)
            detector.update_performance_settings(perf_settings)
            
            # Access private method for testing
            actual_scale = detector._get_processing_scale()
            self.assertEqual(actual_scale, expected_scale, f"Failed for mode: {mode}")


class TestDetectorIntegration(unittest.TestCase):
    """Integration tests for detector with real-like scenarios."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_model_file = tempfile.NamedTemporaryFile(suffix='.pt', delete=False)
        self.temp_model_file.write(b'dummy model data')
        self.temp_model_file.close()
    
    def tearDown(self):
        """Clean up integration test fixtures."""
        os.unlink(self.temp_model_file.name)
    
    @patch('backend.core.detector.YOLO')
    def test_detection_workflow(self, mock_yolo):
        """Test complete detection workflow."""
        # Setup
        mock_yolo_instance = Mock()
        mock_yolo.return_value = mock_yolo_instance
        detector = PetDetector(self.temp_model_file.name)
        
        # Create sequence of frames
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8) for _ in range(5)]
        
        # Define detection results for each frame
        detection_configs = [
            None,  # Frame 0: No pets
            "one_pet",  # Frame 1: One pet
            "two_pets",  # Frame 2: Two pets
            None,  # Frame 3: No pets (or use cache)
            None   # Frame 4: No pets
        ]
        
        all_detections = []
        
        for i, frame in enumerate(frames):
            # Configure mock before each detection call
            if detection_configs[i] == "one_pet":
                # Configure for one pet detection
                mock_box = Mock()
                mock_box.cls = [15]  # Cat class
                mock_box.conf = [0.8]
                mock_box.xyxy = [Mock()]
                mock_box.xyxy[0].cpu.return_value.numpy.return_value = np.array([100, 100, 200, 200])
                
                mock_result = Mock()
                mock_result.boxes = [mock_box]
                mock_yolo_instance.return_value = [mock_result]
                
            elif detection_configs[i] == "two_pets":
                # Configure for two pet detections
                mock_boxes = []
                for j in range(2):
                    mock_box = Mock()
                    mock_box.cls = [15]  # Cat class
                    mock_box.conf = [0.8]
                    mock_box.xyxy = [Mock()]
                    mock_box.xyxy[0].cpu.return_value.numpy.return_value = np.array([100+j*50, 100, 200+j*50, 200])
                    mock_boxes.append(mock_box)
                
                mock_result = Mock()
                mock_result.boxes = mock_boxes
                mock_yolo_instance.return_value = [mock_result]
                
            else:
                # Configure for no detections
                mock_result = Mock()
                mock_result.boxes = None
                mock_yolo_instance.return_value = [mock_result]
            
            # Clear cache to ensure fresh detection for each frame
            if i > 0:  # Don't clear on first frame
                detector.clear_cache()
            
            # Perform detection
            detections = detector.detect_pets(frame, frame_number=i)
            all_detections.append(detections)
            
            print(f"Frame {i}: Expected {len(detections) if detection_configs[i] else 0} detections, got {len(detections)}")
        
        # Verify results
        self.assertEqual(len(all_detections), 5)
        self.assertEqual(len(all_detections[0]), 0, "Frame 0 should have no pets")
        self.assertEqual(len(all_detections[1]), 1, "Frame 1 should have one pet")
        self.assertEqual(len(all_detections[2]), 2, "Frame 2 should have two pets")
        
if __name__ == '__main__':
    unittest.main()