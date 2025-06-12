"""
Mock implementation of video capture for testing.
"""
import numpy as np
import cv2
import time
from typing import Tuple, Optional, Union, List
from unittest.mock import Mock
import threading
import queue


class MockVideoCapture:
    """Mock video capture for testing purposes."""
    
    def __init__(self, source: Union[str, int], buffer_size: int = 10):
        self.source = source
        self.buffer_size = buffer_size
        self.is_opened = False
        
        # Video properties
        self.width = 640
        self.height = 480
        self.fps = 30.0
        self.total_frames = 1000
        self.current_frame = 0
        
        # Frame generation settings
        self.frame_pattern = "solid"  # "solid", "gradient", "checkerboard", "noise", "moving_rectangle"
        self.frame_color = (100, 150, 200)  # BGR color
        self.add_timestamp = True
        self.add_frame_number = True
        
        # Video simulation
        self.simulate_end_of_video = False
        self.end_at_frame = None
        self.frame_data = []  # Pre-loaded frames for testing
        
        # Error simulation
        self.simulate_read_errors = False
        self.error_probability = 0.1
        self.read_count = 0
        
        # Threading simulation
        self.running = False
        self.capture_thread = None
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        
        # Pet simulation (for testing pet detection)
        self.simulate_pets = False
        self.pet_positions = []  # List of (x, y, width, height) for simulated pets
        self.pet_colors = [(0, 255, 0), (255, 0, 0), (0, 0, 255)]  # Green, Red, Blue
        
        # Animation settings
        self.animation_speed = 1.0
        self.movement_amplitude = 100
    
    def open(self) -> bool:
        """Open the mock video source."""
        self.is_opened = True
        self.current_frame = 0
        return True
    
    def release(self):
        """Release the mock video capture."""
        self.is_opened = False
        self.running = False
        self.current_frame = 0
        
        # Clear frame queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
    
    def start_capture(self):
        """Start threaded frame capture (mock)."""
        self.running = True
        self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.capture_thread.start()
    
    def stop_capture(self):
        """Stop threaded frame capture (mock)."""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
    
    def _capture_loop(self):
        """Threaded capture loop for mock video."""
        while self.running:
            ret, frame = self.read()
            if ret and frame is not None:
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()  # Remove oldest frame
                    except queue.Empty:
                        pass
                
                try:
                    self.frame_queue.put(frame, timeout=0.01)
                except queue.Full:
                    pass
            
            time.sleep(1.0 / self.fps)  # Simulate frame rate
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """
        Read the next frame from the mock video source.
        
        Returns:
            Tuple of (success, frame) where success is bool and frame is ndarray or None
        """
        self.read_count += 1
        
        if not self.is_opened:
            return False, None
        
        # Simulate read errors
        if self.simulate_read_errors and np.random.random() < self.error_probability:
            return False, None
        
        # Check for end of video
        if self.simulate_end_of_video:
            if self.end_at_frame and self.current_frame >= self.end_at_frame:
                return False, None
            if self.current_frame >= self.total_frames:
                return False, None
        
        # Generate or retrieve frame
        if self.frame_data and self.current_frame < len(self.frame_data):
            frame = self.frame_data[self.current_frame].copy()
        else:
            frame = self._generate_frame()
        
        self.current_frame += 1
        return True, frame
    
    def _generate_frame(self) -> np.ndarray:
        """Generate a mock video frame."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        if self.frame_pattern == "solid":
            frame[:] = self.frame_color
            
        elif self.frame_pattern == "gradient":
            for y in range(self.height):
                intensity = int((y / self.height) * 255)
                frame[y, :] = [intensity, intensity // 2, 255 - intensity]
                
        elif self.frame_pattern == "checkerboard":
            square_size = 50
            for y in range(0, self.height, square_size):
                for x in range(0, self.width, square_size):
                    if ((y // square_size) + (x // square_size)) % 2 == 0:
                        frame[y:y+square_size, x:x+square_size] = [255, 255, 255]
                    else:
                        frame[y:y+square_size, x:x+square_size] = [0, 0, 0]
                        
        elif self.frame_pattern == "noise":
            frame = np.random.randint(0, 256, (self.height, self.width, 3), dtype=np.uint8)
            
        elif self.frame_pattern == "moving_rectangle":
            frame[:] = [50, 50, 50]  # Dark gray background
            # Create moving rectangle
            rect_size = 80
            center_x = int(self.width // 2 + self.movement_amplitude * 
                          np.sin(self.current_frame * self.animation_speed * 0.1))
            center_y = int(self.height // 2 + self.movement_amplitude * 0.5 * 
                          np.cos(self.current_frame * self.animation_speed * 0.05))
            
            # Ensure rectangle stays within frame
            x1 = max(0, center_x - rect_size // 2)
            y1 = max(0, center_y - rect_size // 2)
            x2 = min(self.width, x1 + rect_size)
            y2 = min(self.height, y1 + rect_size)
            
            frame[y1:y2, x1:x2] = self.frame_color
        
        # Add simulated pets
        if self.simulate_pets:
            self._add_simulated_pets(frame)
        
        # Add timestamp if enabled
        if self.add_timestamp:
            self._add_timestamp(frame)
        
        # Add frame number if enabled
        if self.add_frame_number:
            self._add_frame_number(frame)
        
        return frame
    
    def _add_simulated_pets(self, frame: np.ndarray):
        """Add simulated pet shapes to the frame."""
        for i, (x, y, w, h) in enumerate(self.pet_positions):
            # Animate pet movement
            animated_x = int(x + 30 * np.sin(self.current_frame * 0.1 + i))
            animated_y = int(y + 20 * np.cos(self.current_frame * 0.05 + i))
            
            # Ensure pet stays within frame
            animated_x = max(w//2, min(self.width - w//2, animated_x))
            animated_y = max(h//2, min(self.height - h//2, animated_y))
            
            # Draw pet as ellipse (more realistic than rectangle)
            color = self.pet_colors[i % len(self.pet_colors)]
            cv2.ellipse(frame, 
                       (animated_x, animated_y), 
                       (w//2, h//2), 
                       0, 0, 360, 
                       color, -1)
            
            # Add simple "eyes" for more realistic appearance
            eye_color = (255, 255, 255)
            eye_size = max(2, w // 10)
            eye_offset_x = w // 6
            eye_offset_y = h // 4
            
            cv2.circle(frame, 
                      (animated_x - eye_offset_x, animated_y - eye_offset_y), 
                      eye_size, eye_color, -1)
            cv2.circle(frame, 
                      (animated_x + eye_offset_x, animated_y - eye_offset_y), 
                      eye_size, eye_color, -1)
    
    def _add_timestamp(self, frame: np.ndarray):
        """Add timestamp to the frame."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        cv2.putText(frame, timestamp, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    
    def _add_frame_number(self, frame: np.ndarray):
        """Add frame number to the frame."""
        frame_text = f"Frame: {self.current_frame}"
        cv2.putText(frame, frame_text, (10, self.height - 20), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
    
    def get_position(self) -> int:
        """Get current frame position."""
        return self.current_frame
    
    def set_position(self, frame_number: int) -> bool:
        """Set frame position."""
        if 0 <= frame_number <= self.total_frames:
            self.current_frame = frame_number
            return True
        return False
    
    def get_properties(self) -> dict:
        """Get video properties."""
        return {
            'width': self.width,
            'height': self.height,
            'fps': self.fps,
            'total_frames': self.total_frames,
            'is_camera': self.source == 0,
            'source': self.source
        }
    
    def set_property(self, prop_id: int, value):
        """Set video capture property (OpenCV compatibility)."""
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            self.width = int(value)
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            self.height = int(value)
        elif prop_id == cv2.CAP_PROP_FPS:
            self.fps = float(value)
        elif prop_id == cv2.CAP_PROP_FRAME_COUNT:
            self.total_frames = int(value)
        elif prop_id == cv2.CAP_PROP_POS_FRAMES:
            self.current_frame = int(value)
    
    def get(self, prop_id: int):
        """Get video capture property (OpenCV compatibility)."""
        if prop_id == cv2.CAP_PROP_FRAME_WIDTH:
            return self.width
        elif prop_id == cv2.CAP_PROP_FRAME_HEIGHT:
            return self.height
        elif prop_id == cv2.CAP_PROP_FPS:
            return self.fps
        elif prop_id == cv2.CAP_PROP_FRAME_COUNT:
            return self.total_frames
        elif prop_id == cv2.CAP_PROP_POS_FRAMES:
            return self.current_frame
        else:
            return 0.0
    
    def isOpened(self) -> bool:
        """Check if video capture is opened (OpenCV compatibility)."""
        return self.is_opened
    
    # Convenience methods for testing
    def add_pet(self, x: int, y: int, width: int = 60, height: int = 40):
        """Add a simulated pet at the specified position."""
        self.pet_positions.append((x, y, width, height))
        self.simulate_pets = True
    
    def remove_all_pets(self):
        """Remove all simulated pets."""
        self.pet_positions.clear()
        self.simulate_pets = False
    
    def load_test_frames(self, frames: List[np.ndarray]):
        """Load pre-generated frames for testing."""
        self.frame_data = frames
        self.total_frames = len(frames)
    
    def create_test_sequence(self, pattern: str = "moving_rectangle", 
                           num_frames: int = 100) -> List[np.ndarray]:
        """Create a sequence of test frames."""
        original_pattern = self.frame_pattern
        original_frame = self.current_frame
        
        self.frame_pattern = pattern
        self.current_frame = 0
        
        frames = []
        for i in range(num_frames):
            frame = self._generate_frame()
            frames.append(frame.copy())
            self.current_frame += 1
        
        # Restore original state
        self.frame_pattern = original_pattern
        self.current_frame = original_frame
        
        return frames
    
    def simulate_camera_disconnect(self):
        """Simulate camera disconnection."""
        self.is_opened = False
    
    def simulate_camera_reconnect(self):
        """Simulate camera reconnection."""
        self.is_opened = True
    
    def set_error_rate(self, probability: float):
        """Set the probability of read errors (0.0 to 1.0)."""
        self.error_probability = max(0.0, min(1.0, probability))
        self.simulate_read_errors = probability > 0.0


class MockVideoWriter:
    """Mock video writer for testing video output."""
    
    def __init__(self, filename: str, fourcc, fps: float, frame_size: Tuple[int, int]):
        self.filename = filename
        self.fourcc = fourcc
        self.fps = fps
        self.frame_size = frame_size
        self.is_opened = False
        self.frames_written = 0
        self.written_frames = []  # Store frames for testing
    
    def isOpened(self) -> bool:
        """Check if video writer is opened."""
        return self.is_opened
    
    def open(self) -> bool:
        """Open the video writer."""
        self.is_opened = True
        return True
    
    def write(self, frame: np.ndarray):
        """Write a frame to the video."""
        if self.is_opened:
            # Resize frame if necessary
            if frame.shape[:2][::-1] != self.frame_size:
                frame = cv2.resize(frame, self.frame_size)
            
            self.written_frames.append(frame.copy())
            self.frames_written += 1
    
    def release(self):
        """Release the video writer."""
        self.is_opened = False
    
    def get_written_frames(self) -> List[np.ndarray]:
        """Get all frames that were written (for testing)."""
        return self.written_frames.copy()
    
    def get_frame_count(self) -> int:
        """Get number of frames written."""
        return self.frames_written


# Utility functions for creating test scenarios
def create_pet_detection_scenario() -> MockVideoCapture:
    """Create a mock video capture with simulated pets for testing detection."""
    mock_cap = MockVideoCapture(source="test_pet_video.mp4")
    mock_cap.frame_pattern = "solid"
    mock_cap.frame_color = (240, 240, 240)  # Light gray background
    
    # Add multiple pets
    mock_cap.add_pet(200, 150, 80, 50)  # Pet 1
    mock_cap.add_pet(400, 300, 70, 45)  # Pet 2
    
    mock_cap.total_frames = 300
    return mock_cap


def create_zone_violation_scenario() -> MockVideoCapture:
    """Create a scenario where pets move through different zones."""
    mock_cap = MockVideoCapture(source="test_zone_video.mp4")
    mock_cap.frame_pattern = "solid"
    mock_cap.frame_color = (200, 220, 200)  # Light green background
    
    # Add a pet that will move across the frame
    mock_cap.add_pet(50, 240, 60, 40)
    mock_cap.movement_amplitude = 200  # Increase movement range
    mock_cap.animation_speed = 2.0
    
    mock_cap.total_frames = 200
    return mock_cap


def create_feeding_scenario() -> MockVideoCapture:
    """Create a scenario with pets near feeding areas."""
    mock_cap = MockVideoCapture(source="test_feeding_video.mp4")
    mock_cap.frame_pattern = "solid"
    mock_cap.frame_color = (220, 200, 180)  # Warm background
    
    # Add pets near typical bowl locations
    mock_cap.add_pet(150, 350, 65, 42)  # Near food bowl
    mock_cap.add_pet(250, 350, 55, 38)  # Near water bowl
    
    # Reduce movement to simulate feeding behavior
    mock_cap.movement_amplitude = 20
    mock_cap.animation_speed = 0.5
    
    mock_cap.total_frames = 150
    return mock_cap