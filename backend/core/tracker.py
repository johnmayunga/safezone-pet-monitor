"""
backend/core/tracker.py
Pet activity tracking and zone monitoring.
"""
import cv2
import numpy as np
import time
from typing import List, Dict, Set, Tuple, Optional
import datetime

from ..data.models import Detection, Zone, BowlLocation, ZoneDuration
from ..data.statistics import ActivityStatistics


class PetActivityTracker:
    """Tracks pet activities, zone visits, and feeding behavior."""
    
    def __init__(self, statistics: ActivityStatistics):
        self.statistics = statistics
        self.zones: List[Zone] = []
        self.bowls: Dict[str, BowlLocation] = {}
        
        # Current state tracking
        self.current_zones: Set[str] = set()
        self.pet_activity_state: Dict[str, bool] = {}
        
        # Zone masks for efficient processing
        self.zone_mask = None
        self.frame_shape = None
    
    def update_zones(self, zones: List[Zone]):
        """Update the list of monitored zones."""
        self.zones = zones
        self.zone_mask = None  # Invalidate cache
    
    def update_bowls(self, bowls: Dict[str, BowlLocation]):
        """Update the bowl locations."""
        self.bowls = bowls
    
    def set_frame_shape(self, shape: Tuple[int, int]):
        """Set the video frame shape for heatmap initialization."""
        if self.frame_shape != shape:
            self.frame_shape = shape
            self.statistics.initialize_heatmap(shape)
            self.zone_mask = None  # Invalidate zone mask
    
    def process_detections(self, detections: List[Detection]) -> Dict:
        """
        Process a list of detections and update activity tracking.
        
        Args:
            detections: List of pet detections
            
        Returns:
            Dictionary with processing results
        """
        results = {
            'zone_activities': [],
            'bowl_activities': [],
            'alerts': [],
            'detections_processed': len(detections)
        }
        
        if not detections:
            # Check for zone exits when no pets detected
            self._check_zone_exits_all()
            self._end_all_bowl_activities()
            return results
        
        # Track which zones are currently occupied
        current_frame_zones = set()
        
        for detection in detections:
            # Record the detection
            self.statistics.record_detection(detection)
            
            # Check zone activities
            zone_results = self._check_zone_activities(detection)
            results['zone_activities'].extend(zone_results)
            current_frame_zones.update([r['zone'] for r in zone_results if r['action'] == 'entry'])
            
            # Check bowl activities
            bowl_results = self._check_bowl_activities(detection)
            results['bowl_activities'].extend(bowl_results)
        
        # Check for zone exits
        exited_zones = self.current_zones - current_frame_zones
        for zone_name in exited_zones:
            self.statistics.record_zone_exit(zone_name, "pet")  # Generic pet type
            results['zone_activities'].append({
                'action': 'exit',
                'zone': zone_name,
                'pet_type': 'pet'
            })
        
        # Update current zones
        self.current_zones = current_frame_zones
        
        return results
    
    def _check_zone_activities(self, detection: Detection) -> List[Dict]:
        """Check for zone-related activities."""
        activities = []
        center = detection.center
        
        for zone in self.zones:
            if zone.point_in_zone(center):
                # Pet is in this zone
                if zone.name not in self.current_zones:
                    # New zone entry
                    self.statistics.record_zone_entry(zone.name, zone.zone_type, detection.pet_type)
                    
                    activity = {
                        'action': 'entry',
                        'zone': zone.name,
                        'zone_type': zone.zone_type,
                        'pet_type': detection.pet_type,
                        'timestamp': detection.timestamp
                    }
                    
                    # Check if it's a restricted zone for alerts
                    if zone.zone_type == "restricted":
                        activity['alert'] = True
                    
                    activities.append(activity)
        
        return activities
    
    def _check_bowl_activities(self, detection: Detection) -> List[Dict]:
        """Check for feeding/drinking activities."""
        activities = []
        center = detection.center
        pet_size = detection.size
        current_time = time.time()
        
        for bowl_name, bowl in self.bowls.items():
            # Calculate interaction threshold based on pet size
            threshold_factor = 1.0 + (pet_size / 100.0)  # Adjust based on pet size
            
            if bowl.is_near(center, threshold_factor):
                # Pet is near the bowl
                if bowl_name == "food":
                    self.statistics.record_eating_event(detection.pet_type)
                    activities.append({
                        'action': 'eating',
                        'bowl': bowl_name,
                        'pet_type': detection.pet_type,
                        'timestamp': detection.timestamp
                    })
                elif bowl_name == "water":
                    self.statistics.record_drinking_event(detection.pet_type)
                    activities.append({
                        'action': 'drinking',
                        'bowl': bowl_name,
                        'pet_type': detection.pet_type,
                        'timestamp': detection.timestamp
                    })
            else:
                # Pet is away from the bowl - end activity
                if bowl_name in self.pet_activity_state and self.pet_activity_state[bowl_name]:
                    self.statistics.end_bowl_activity(bowl_name)
                    activities.append({
                        'action': 'finished',
                        'bowl': bowl_name,
                        'pet_type': detection.pet_type,
                        'timestamp': detection.timestamp
                    })
        
        return activities
    
    def _check_zone_exits_all(self):
        """Check for zone exits when no pets are detected."""
        for zone_name in list(self.current_zones):
            self.statistics.record_zone_exit(zone_name, "pet")
        self.current_zones.clear()
    
    def _end_all_bowl_activities(self):
        """End all bowl activities when no pets are detected."""
        for bowl_name in self.bowls:
            if bowl_name in self.pet_activity_state and self.pet_activity_state[bowl_name]:
                self.statistics.end_bowl_activity(bowl_name)
    
    def create_zone_overlay(self, frame_shape: Tuple[int, int]) -> np.ndarray:
        """Create overlay mask for zones."""
        if not self.zones or self.zone_mask is not None:
            return self.zone_mask
        
        height, width = frame_shape
        self.zone_mask = np.zeros((height, width, 3), dtype=np.uint8)
        
        for zone in self.zones:
            x1, y1, x2, y2 = zone.coords
            
            # Ensure coordinates are within frame bounds
            x1 = max(0, min(x1, width - 1))
            x2 = max(0, min(x2, width - 1))
            y1 = max(0, min(y1, height - 1))
            y2 = max(0, min(y2, height - 1))
            
            if x2 > x1 and y2 > y1:
                # Draw semi-transparent rectangle
                overlay = self.zone_mask.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), zone.color, -1)
                cv2.addWeighted(overlay, 0.3, self.zone_mask, 0.7, 0, self.zone_mask)
                
                # Draw border
                cv2.rectangle(self.zone_mask, (x1, y1), (x2, y2), zone.color, 2)
        
        return self.zone_mask
    
    def draw_zones(self, frame: np.ndarray) -> np.ndarray:
        """Draw zones on the frame."""
        frame_copy = frame.copy()
        
        for zone in self.zones:
            x1, y1, x2, y2 = zone.coords
            
            # Draw zone rectangle
            cv2.rectangle(frame_copy, (x1, y1), (x2, y2), zone.color, 2)
            
            # Draw zone label with background
            label = f"{zone.name} ({zone.zone_type})"
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            # Background for text
            cv2.rectangle(frame_copy, (x1, y1 - 20), 
                         (x1 + label_size[0], y1), zone.color, -1)
            
            # Text
            cv2.putText(frame_copy, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame_copy
    
    def draw_bowls(self, frame: np.ndarray) -> np.ndarray:
        """Draw bowl locations on the frame."""
        frame_copy = frame.copy()
        
        for bowl_name, bowl in self.bowls.items():
            x, y = bowl.position
            
            # Draw bowl circle
            cv2.circle(frame_copy, (int(x), int(y)), bowl.radius, bowl.color, 2)
            
            # Draw bowl label with background
            label = bowl_name.title()
            label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            
            label_x = int(x - label_size[0] // 2)
            label_y = int(y - bowl.radius - 10)
            
            # Background for text
            cv2.rectangle(frame_copy, 
                         (label_x - 2, label_y - label_size[1] - 2),
                         (label_x + label_size[0] + 2, label_y + 2), 
                         bowl.color, -1)
            
            # Text
            cv2.putText(frame_copy, label, (label_x, label_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return frame_copy
    
    def get_zone_by_name(self, name: str) -> Optional[Zone]:
        """Get a zone by its name."""
        for zone in self.zones:
            if zone.name == name:
                return zone
        return None
    
    def get_bowl_by_name(self, name: str) -> Optional[BowlLocation]:
        """Get a bowl by its name."""
        return self.bowls.get(name)
    
    def clear_zones(self):
        """Clear all zones."""
        self.zones.clear()
        self.zone_mask = None
        self.current_zones.clear()
    
    def clear_bowls(self):
        """Clear all bowls."""
        self.bowls.clear()
        self.pet_activity_state.clear()
    
    def invalidate_cache(self):
        """Invalidate cached overlays."""
        self.zone_mask = None