"""
Mock objects for testing Pet Activity Tracker components.

This module provides mock implementations of various components
for isolated unit testing.
"""

from .mock_detector import MockPetDetector
from .mock_video_capture import MockVideoCapture

__all__ = [
    'MockPetDetector',
    'MockVideoCapture'
]