"""
backend/data/models.py
Data models for the Pet Activity Tracker application.
"""
from dataclasses import dataclass
from typing import Tuple, Dict, List, Optional
import datetime


@dataclass
class Zone:
    """Represents a monitored zone in the video feed."""
    name: str
    coords: Tuple[int, int, int, int]  # (x1, y1, x2, y2)
    zone_type: str  # 'restricted', 'normal', 'feeding', etc.
    color: Tuple[int, int, int]  # RGB color

    def point_in_zone(self, point: Tuple[float, float]) -> bool:
        """Check if a point is inside this zone."""
        x, y = point
        x1, y1, x2, y2 = self.coords
        return x1 <= x <= x2 and y1 <= y <= y2


@dataclass
class BowlLocation:
    """Represents a feeding/drinking bowl location."""
    name: str
    position: Tuple[int, int]
    radius: int = 30
    color: Tuple[int, int, int] = (255, 0, 0)

    def is_near(self, point: Tuple[float, float], threshold_factor: float = 1.0) -> bool:
        """Check if a point is near this bowl."""
        x, y = point
        bowl_x, bowl_y = self.position
        distance = ((x - bowl_x) ** 2 + (y - bowl_y) ** 2) ** 0.5
        return distance <= self.radius * threshold_factor


@dataclass
class Detection:
    """Represents a single pet detection."""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    pet_type: str  # 'cat' or 'dog'
    confidence: float
    timestamp: datetime.datetime
    frame_number: int

    @property
    def center(self) -> Tuple[float, float]:
        """Get the center point of the detection."""
        x1, y1, x2, y2 = self.bbox
        return ((x1 + x2) / 2, (y1 + y2) / 2)

    @property
    def size(self) -> float:
        """Get the approximate size of the detection."""
        x1, y1, x2, y2 = self.bbox
        return max(x2 - x1, y2 - y1)


@dataclass
class ActivityEvent:
    """Represents an activity event (eating, drinking, zone entry, etc.)."""
    event_type: str
    pet_type: str
    location: Optional[str]  # Zone name or bowl name
    timestamp: datetime.datetime
    details: Optional[Dict] = None


@dataclass
class ZoneDuration:
    """Tracks time spent in zones."""
    zone_name: str
    total_time: float  # seconds
    entry_time: Optional[datetime.datetime] = None
    visit_count: int = 0

    def start_visit(self) -> None:
        """Start a new visit to this zone."""
        self.entry_time = datetime.datetime.now()
        self.visit_count += 1

    def end_visit(self) -> float:
        """End the current visit and return duration."""
        if self.entry_time:
            duration = (datetime.datetime.now() - self.entry_time).total_seconds()
            self.total_time += duration
            self.entry_time = None
            return duration
        return 0.0


@dataclass
class PerformanceSettings:
    """Performance optimization settings."""
    mode: str = "balanced"  # quality, balanced, performance, ultra
    display_fps: float = 30.0
    detection_cache_frames: int = 3
    stats_update_frequency: int = 10
    heatmap_update_frequency: int = 10
    frame_skip_ratio: int = 1

    @classmethod
    def from_mode(cls, mode: str) -> 'PerformanceSettings':
        """Create settings from performance mode."""
        settings = {
            "quality": cls(
                mode="quality",
                display_fps=60.0,
                detection_cache_frames=1,
                stats_update_frequency=5,
                heatmap_update_frequency=5,
                frame_skip_ratio=1
            ),
            "balanced": cls(
                mode="balanced",
                display_fps=30.0,
                detection_cache_frames=3,
                stats_update_frequency=10,
                heatmap_update_frequency=10,
                frame_skip_ratio=1
            ),
            "performance": cls(
                mode="performance",
                display_fps=20.0,
                detection_cache_frames=5,
                stats_update_frequency=20,
                heatmap_update_frequency=15,
                frame_skip_ratio=2
            ),
            "ultra": cls(
                mode="ultra",
                display_fps=10.0,
                detection_cache_frames=10,
                stats_update_frequency=30,
                heatmap_update_frequency=20,
                frame_skip_ratio=5
            )
        }
        return settings.get(mode, settings["balanced"])


@dataclass
class AppConfig:
    """Application configuration."""
    zones: List[Zone]
    bowls: Dict[str, BowlLocation]
    performance: PerformanceSettings
    confidence_threshold: float = 0.5
    alert_cooldown: int = 60
    email_config: Optional[Dict] = None
    model_path: str = "models/yolo12n.pt"
    
    def get_email_config_object(self):
        """Get EmailConfig object from email_config dict."""
        if not self.email_config:
            return None
        
        # Import here to avoid circular imports
        from ..services.email_service import EmailConfig
        
        return EmailConfig(
            sender_email=self.email_config["sender_email"],
            sender_password=self.email_config["sender_password"],
            recipient_email=self.email_config["recipient_email"],
            smtp_server=self.email_config.get("smtp_server", "smtp.gmail.com"),
            smtp_port=self.email_config.get("smtp_port", 587),
            enabled=self.email_config.get("enabled", True),
            notification_types=self.email_config.get("notification_types", {}),
            cooldown_period=self.email_config.get("cooldown_period", 300)
        )