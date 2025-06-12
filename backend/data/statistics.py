"""
backend/data/statistics.py
Statistics tracking and management for pet activity.
"""
import datetime
import time
import numpy as np
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import json

from .models import ActivityEvent, ZoneDuration, Detection


class ActivityStatistics:
    """Manages and tracks pet activity statistics."""
    
    def __init__(self, max_log_size: int = 1000):
        self.max_log_size = max_log_size
        self.reset_statistics()
    
    def reset_statistics(self):
        """Reset all statistics to initial state."""
        self.stats = {
            'eating_events': 0,
            'drinking_events': 0,
            'restricted_zone_violations': 0,
            'total_detections': 0,
            'activity_timeline': defaultdict(int),
            'zone_visits': defaultdict(int)
        }
        
        self.activity_log = deque(maxlen=self.max_log_size)
        self.zone_durations = {}
        self.current_zones = set()
        self.pet_activity_state = {}
        self.heatmap = None
        
        # For timeline tracking
        self.last_activity_hour = None
    
    def initialize_heatmap(self, frame_shape: Tuple[int, int]):
        """Initialize the movement heatmap."""
        height, width = frame_shape
        self.heatmap = np.zeros((height, width), dtype=np.float32)
    
    def log_activity(self, message: str, event_type: str = "general"):
        """Log an activity with timestamp."""
        timestamp = datetime.datetime.now()
        log_entry = f"{timestamp.strftime('%Y-%m-%d %H:%M:%S')}: {message}"
        
        # Add to activity log
        self.activity_log.append(log_entry)
        
        # Update timeline
        hour = timestamp.hour
        self.stats['activity_timeline'][hour] += 1
        
        # Create activity event
        event = ActivityEvent(
            event_type=event_type,
            pet_type="unknown",  # Will be updated by caller if known
            location=None,
            timestamp=timestamp
        )
        
        return event
    
    def record_detection(self, detection: Detection):
        """Record a new pet detection."""
        self.stats['total_detections'] += 1
        
        # Update heatmap if initialized
        if self.heatmap is not None:
            self.update_heatmap(detection.bbox)
    
    def update_heatmap(self, bbox: Tuple[float, float, float, float]):
        """Update the movement heatmap with detection."""
        if self.heatmap is None:
            return
        
        x1, y1, x2, y2 = map(int, bbox)
        
        # Clip coordinates to frame boundaries
        height, width = self.heatmap.shape
        y1 = max(0, min(y1, height - 1))
        y2 = max(0, min(y2, height - 1))
        x1 = max(0, min(x1, width - 1))
        x2 = max(0, min(x2, width - 1))
        
        if y2 > y1 and x2 > x1:
            self.heatmap[y1:y2, x1:x2] += 1
    
    def record_eating_event(self, pet_type: str):
        """Record an eating event (session-based counting)."""
        current_time = time.time()
        
        # Check if this is a new eating session (cooldown-based)
        last_eating_time = getattr(self, '_last_eating_time', 0)
        if current_time - last_eating_time > 30:  # 30 second cooldown between sessions
            self.stats['eating_events'] += 1
            self.log_activity(f"{pet_type} started eating session #{self.stats['eating_events']}", "eating")
            self._last_eating_time = current_time
        
        # Update activity state
        self.pet_activity_state["food"] = True
    
    def record_drinking_event(self, pet_type: str):
        """Record a drinking event (session-based counting)."""
        current_time = time.time()
        
        # Check if this is a new drinking session (cooldown-based)
        last_drinking_time = getattr(self, '_last_drinking_time', 0)
        if current_time - last_drinking_time > 30:  # 30 second cooldown between sessions
            self.stats['drinking_events'] += 1
            self.log_activity(f"{pet_type} started drinking session #{self.stats['drinking_events']}", "drinking")
            self._last_drinking_time = current_time
        
        # Update activity state
        self.pet_activity_state["water"] = True
    
    def record_zone_entry(self, zone_name: str, zone_type: str, pet_type: str):
        """Record entry into a zone."""
        self.stats['zone_visits'][zone_name] += 1
        
        # Initialize zone duration tracking if needed
        if zone_name not in self.zone_durations:
            self.zone_durations[zone_name] = ZoneDuration(zone_name, 0.0)
        
        # Start zone visit if not already in zone
        if zone_name not in self.current_zones:
            self.zone_durations[zone_name].start_visit()
            self.current_zones.add(zone_name)
            
            # Log the entry
            self.log_activity(f"{pet_type} entered {zone_name}", "zone_entry")
            
            # Record restricted zone violation
            if zone_type == "restricted":
                self.stats['restricted_zone_violations'] += 1
                self.log_activity(f"ALERT: {pet_type} entered restricted zone: {zone_name}", "alert")
    
    def record_zone_exit(self, zone_name: str, pet_type: str):
        """Record exit from a zone."""
        if zone_name in self.current_zones:
            # End zone visit
            if zone_name in self.zone_durations:
                duration = self.zone_durations[zone_name].end_visit()
                
            self.current_zones.remove(zone_name)
            self.log_activity(f"{pet_type} left {zone_name}", "zone_exit")
    
    def end_bowl_activity(self, bowl_name: str):
        """End activity at a bowl."""
        if bowl_name in self.pet_activity_state:
            self.pet_activity_state[bowl_name] = False
    
    def get_zone_statistics(self) -> List[Dict]:
        """Get formatted zone statistics."""
        zone_stats = []
        
        for zone_name, visits in self.stats['zone_visits'].items():
            duration_info = "N/A"
            total_seconds = 0
            
            if zone_name in self.zone_durations:
                zone_duration = self.zone_durations[zone_name]
                total_seconds = zone_duration.total_time
                
                # Add current duration if pet is still in zone
                if zone_name in self.current_zones and zone_duration.entry_time:
                    current_duration = (datetime.datetime.now() - zone_duration.entry_time).total_seconds()
                    total_seconds += current_duration
                
                # Format duration
                minutes, seconds = divmod(int(total_seconds), 60)
                hours, minutes = divmod(minutes, 60)
                
                if hours > 0:
                    duration_info = f"{hours}h {minutes}m {seconds}s"
                elif minutes > 0:
                    duration_info = f"{minutes}m {seconds}s"
                else:
                    duration_info = f"{seconds}s"
            
            zone_stats.append({
                'name': zone_name,
                'visits': visits,
                'duration': duration_info,
                'total_seconds': total_seconds
            })
        
        return zone_stats
    
    def get_activity_timeline(self) -> Dict[int, int]:
        """Get activity timeline by hour."""
        return dict(self.stats['activity_timeline'])
    
    def get_recent_activities(self, count: int = 50) -> List[str]:
        """Get recent activity log entries."""
        return list(self.activity_log)[-count:]
    
    def export_to_dict(self) -> Dict:
        """Export statistics to dictionary for saving."""
        return {
            'stats': dict(self.stats),
            'activity_log': list(self.activity_log),
            'zone_durations': {
                name: {
                    'total_time': duration.total_time,
                    'visit_count': duration.visit_count
                } for name, duration in self.zone_durations.items()
            },
            'export_timestamp': datetime.datetime.now().isoformat()
        }
    
    def import_from_dict(self, data: Dict):
        """Import statistics from dictionary."""
        if 'stats' in data:
            # Convert defaultdict back to regular dict and then to defaultdict
            for key, value in data['stats'].items():
                if isinstance(value, dict):
                    self.stats[key] = defaultdict(int, value)
                else:
                    self.stats[key] = value
        
        if 'activity_log' in data:
            self.activity_log.extend(data['activity_log'])
        
        if 'zone_durations' in data:
            for name, duration_data in data['zone_durations'].items():
                self.zone_durations[name] = ZoneDuration(
                    zone_name=name,
                    total_time=duration_data.get('total_time', 0.0),
                    visit_count=duration_data.get('visit_count', 0)
                )
    
    def get_summary_report(self) -> Dict:
        """Get a comprehensive summary report."""
        zone_stats = self.get_zone_statistics()
        timeline = self.get_activity_timeline()
        
        # Find peak activity hour
        peak_hour = max(timeline.items(), key=lambda x: x[1]) if timeline else (0, 0)
        
        return {
            'summary': {
                'total_detections': self.stats['total_detections'],
                'eating_events': self.stats['eating_events'],
                'drinking_events': self.stats['drinking_events'],
                'restricted_violations': self.stats['restricted_zone_violations'],
                'zones_monitored': len(self.zone_durations),
                'peak_activity_hour': peak_hour[0] if peak_hour[1] > 0 else None
            },
            'zone_statistics': zone_stats,
            'activity_timeline': timeline,
            'recent_activities': self.get_recent_activities(20)
        }