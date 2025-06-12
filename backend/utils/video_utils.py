"""
backend/utils/video_utils.py
Video processing utilities for the Pet Activity Tracker.
"""
import cv2
import numpy as np
from typing import Tuple, Optional, Union
import time
import threading
import queue


class VideoCapture:
    """Enhanced video capture with threading and buffering."""
    
    def __init__(self, source: Union[str, int], buffer_size: int = 10):
        self.source = source
        self.buffer_size = buffer_size
        self.cap = None
        self.frame_queue = queue.Queue(maxsize=buffer_size)
        self.running = False
        self.capture_thread = None
        
        # Video properties
        self.width = 0
        self.height = 0
        self.fps = 0
        self.total_frames = 0
        
    def open(self) -> bool:
        """Open the video source."""
        try:
            self.cap = cv2.VideoCapture(self.source)
            
            if not self.cap.isOpened():
                return False
            
            # Get video properties
            self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            return True
            
        except Exception as e:
            print(f"Error opening video source: {e}")
            return False
    
    def start_capture(self):
        """Start threaded frame capture."""
        if self.cap and self.cap.isOpened():
            self.running = True
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
    
    def stop_capture(self):
        """Stop threaded frame capture."""
        self.running = False
        if self.capture_thread:
            self.capture_thread.join(timeout=1.0)
        
        # Clear the queue
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
    
    def _capture_loop(self):
        """Threaded frame capture loop."""
        while self.running and self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            
            if not ret:
                break
            
            # Add frame to queue, removing old frames if full
            if self.frame_queue.full():
                try:
                    self.frame_queue.get_nowait()
                except queue.Empty:
                    pass
            
            try:
                self.frame_queue.put(frame, timeout=0.01)
            except queue.Full:
                pass
            
            time.sleep(0.001)  # Small delay to prevent CPU overload
    
    def read(self) -> Tuple[bool, Optional[np.ndarray]]:
        """Read the latest frame."""
        if not self.running:
            # Direct read for non-threaded mode
            if self.cap and self.cap.isOpened():
                return self.cap.read()
            return False, None
        
        # Get latest frame from queue
        try:
            frame = self.frame_queue.get(timeout=0.1)
            return True, frame
        except queue.Empty:
            return False, None
    
    def release(self):
        """Release the video capture."""
        self.stop_capture()
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_position(self) -> int:
        """Get current frame position."""
        if self.cap:
            return int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
        return 0
    
    def set_position(self, frame_number: int) -> bool:
        """Set frame position (for video files)."""
        if self.cap and self.source != 0:  # Not for camera
            return self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
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


class FrameProcessor:
    """Processes video frames with various optimizations."""
    
    @staticmethod
    def resize_frame(frame: np.ndarray, scale: float) -> np.ndarray:
        """Resize frame by scale factor."""
        if scale == 1.0:
            return frame
        
        height, width = frame.shape[:2]
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return cv2.resize(frame, (new_width, new_height))
    
    @staticmethod
    def resize_to_dimensions(frame: np.ndarray, width: int, height: int) -> np.ndarray:
        """Resize frame to specific dimensions."""
        return cv2.resize(frame, (width, height))
    
    @staticmethod
    def crop_frame(frame: np.ndarray, x: int, y: int, width: int, height: int) -> np.ndarray:
        """Crop frame to specified region."""
        h, w = frame.shape[:2]
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, w - 1))
        y = max(0, min(y, h - 1))
        width = min(width, w - x)
        height = min(height, h - y)
        
        return frame[y:y+height, x:x+width]
    
    @staticmethod
    def apply_gaussian_blur(frame: np.ndarray, kernel_size: int = 5) -> np.ndarray:
        """Apply Gaussian blur to reduce noise."""
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    
    @staticmethod
    def enhance_contrast(frame: np.ndarray, alpha: float = 1.5, beta: int = 0) -> np.ndarray:
        """Enhance frame contrast and brightness."""
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)
    
    @staticmethod
    def convert_colorspace(frame: np.ndarray, conversion: int) -> np.ndarray:
        """Convert frame colorspace."""
        return cv2.cvtColor(frame, conversion)
    
    @staticmethod
    def add_timestamp(frame: np.ndarray, timestamp: str, 
                     position: Tuple[int, int] = (10, 30)) -> np.ndarray:
        """Add timestamp overlay to frame."""
        frame_copy = frame.copy()
        
        # Add background for better readability
        text_size = cv2.getTextSize(timestamp, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        cv2.rectangle(frame_copy, 
                     (position[0] - 5, position[1] - text_size[1] - 5),
                     (position[0] + text_size[0] + 5, position[1] + 5),
                     (0, 0, 0), -1)
        
        # Add timestamp text
        cv2.putText(frame_copy, timestamp, position,
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        return frame_copy
    
    @staticmethod
    def add_overlay_text(frame: np.ndarray, text: str, 
                        position: Tuple[int, int],
                        font_scale: float = 0.7,
                        color: Tuple[int, int, int] = (255, 255, 255),
                        background_color: Optional[Tuple[int, int, int]] = (0, 0, 0)) -> np.ndarray:
        """Add text overlay with optional background."""
        frame_copy = frame.copy()
        
        if background_color:
            # Add background
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, font_scale, 2)[0]
            cv2.rectangle(frame_copy,
                         (position[0] - 5, position[1] - text_size[1] - 5),
                         (position[0] + text_size[0] + 5, position[1] + 5),
                         background_color, -1)
        
        # Add text
        cv2.putText(frame_copy, text, position,
                   cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, 2)
        
        return frame_copy


class VideoWriter:
    """Enhanced video writer for saving processed videos."""
    
    def __init__(self, output_path: str, fps: float, frame_size: Tuple[int, int]):
        self.output_path = output_path
        self.fps = fps
        self.frame_size = frame_size
        self.writer = None
        
        # Video codec (try different codecs for compatibility)
        self.codecs = [
            cv2.VideoWriter_fourcc(*'mp4v'),
            cv2.VideoWriter_fourcc(*'XVID'),
            cv2.VideoWriter_fourcc(*'MJPG'),
        ]
    
    def open(self) -> bool:
        """Open video writer."""
        for codec in self.codecs:
            try:
                self.writer = cv2.VideoWriter(
                    self.output_path, codec, self.fps, self.frame_size
                )
                if self.writer.isOpened():
                    return True
            except Exception:
                continue
        
        return False
    
    def write_frame(self, frame: np.ndarray) -> bool:
        """Write a frame to the video."""
        if self.writer and self.writer.isOpened():
            # Ensure frame is the correct size
            if frame.shape[:2][::-1] != self.frame_size:
                frame = cv2.resize(frame, self.frame_size)
            
            self.writer.write(frame)
            return True
        return False
    
    def release(self):
        """Release the video writer."""
        if self.writer:
            self.writer.release()
            self.writer = None


def calculate_display_scale(frame_size: Tuple[int, int], 
                          display_size: Tuple[int, int]) -> Tuple[float, int, int]:
    """
    Calculate optimal scale and offsets for displaying frame in given size.
    
    Args:
        frame_size: (width, height) of source frame
        display_size: (width, height) of display area
        
    Returns:
        (scale, offset_x, offset_y)
    """
    frame_width, frame_height = frame_size
    display_width, display_height = display_size
    
    # Calculate scale to fit frame in display area
    scale_width = display_width / frame_width
    scale_height = display_height / frame_height
    scale = min(scale_width, scale_height)
    
    # Calculate scaled dimensions and offsets for centering
    scaled_width = int(frame_width * scale)
    scaled_height = int(frame_height * scale)
    
    offset_x = (display_width - scaled_width) // 2
    offset_y = (display_height - scaled_height) // 2
    
    return scale, offset_x, offset_y


def convert_coordinates(x: float, y: float, 
                       from_size: Tuple[int, int], 
                       to_size: Tuple[int, int],
                       offset: Tuple[int, int] = (0, 0)) -> Tuple[float, float]:
    """
    Convert coordinates between different coordinate systems.
    
    Args:
        x, y: Input coordinates
        from_size: (width, height) of source coordinate system
        to_size: (width, height) of target coordinate system
        offset: (offset_x, offset_y) in target system
        
    Returns:
        (new_x, new_y) in target coordinate system
    """
    from_width, from_height = from_size
    to_width, to_height = to_size
    offset_x, offset_y = offset
    
    # Calculate scale
    scale_x = to_width / from_width
    scale_y = to_height / from_height
    
    # Apply scale and offset
    new_x = x * scale_x + offset_x
    new_y = y * scale_y + offset_y
    
    return new_x, new_y


def estimate_video_memory_usage(width: int, height: int, fps: float, 
                               duration_seconds: float) -> dict:
    """
    Estimate memory usage for video processing.
    
    Returns:
        Dictionary with memory estimates in MB
    """
    # Bytes per frame (3 channels, 8 bits each)
    bytes_per_frame = width * height * 3
    
    # Estimates
    single_frame_mb = bytes_per_frame / (1024 * 1024)
    total_frames = fps * duration_seconds
    total_video_mb = (bytes_per_frame * total_frames) / (1024 * 1024)
    
    # Buffer estimates (assuming 30 frame buffer)
    buffer_mb = (bytes_per_frame * 30) / (1024 * 1024)
    
    return {
        'single_frame_mb': round(single_frame_mb, 2),
        'total_video_mb': round(total_video_mb, 2),
        'buffer_mb': round(buffer_mb, 2),
        'recommended_ram_mb': round(total_video_mb * 0.1 + buffer_mb + 100, 2)  # 10% of video + buffer + overhead
    }