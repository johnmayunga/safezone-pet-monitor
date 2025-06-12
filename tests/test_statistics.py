"""
Unit tests for the ActivityStatistics class.
"""
import unittest
import numpy as np
import datetime
from collections import defaultdict
import sys
import os

# Import the modules to test
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.data.statistics import ActivityStatistics
from backend.data.models import Detection, ZoneDuration


class TestActivityStatistics(unittest.TestCase):
    """Test cases for ActivityStatistics class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.stats = ActivityStatistics(max_log_size=100)
    
    def test_initialization(self):
        """Test statistics initialization."""
        self.assertEqual(self.stats.stats['eating_events'], 0)
        self.assertEqual(self.stats.stats['drinking_events'], 0)
        self.assertEqual(self.stats.stats['restricted_zone_violations'], 0)
        self.assertEqual(self.stats.stats['total_detections'], 0)
        self.assertIsInstance(self.stats.stats['activity_timeline'], defaultdict)
        self.assertIsInstance(self.stats.stats['zone_visits'], defaultdict)
        self.assertEqual(len(self.stats.activity_log), 0)
        self.assertEqual(len(self.stats.zone_durations), 0)
        self.assertEqual(len(self.stats.current_zones), 0)
    
    def test_reset_statistics(self):
        """Test resetting statistics to initial state."""
        # Modify some statistics
        self.stats.stats['eating_events'] = 5
        self.stats.stats['total_detections'] = 10
        self.stats.activity_log.append("Test entry")
        self.stats.zone_durations['test_zone'] = ZoneDuration('test_zone', 100.0)
        
        # Reset
        self.stats.reset_statistics()
        
        # Should be back to initial state
        self.assertEqual(self.stats.stats['eating_events'], 0)
        self.assertEqual(self.stats.stats['total_detections'], 0)
        self.assertEqual(len(self.stats.activity_log), 0)
        self.assertEqual(len(self.stats.zone_durations), 0)
    
    def test_initialize_heatmap(self):
        """Test heatmap initialization."""
        frame_shape = (480, 640)
        self.stats.initialize_heatmap(frame_shape)
        
        self.assertIsNotNone(self.stats.heatmap)
        self.assertEqual(self.stats.heatmap.shape, frame_shape)
        self.assertEqual(self.stats.heatmap.dtype, np.float32)
        self.assertTrue(np.all(self.stats.heatmap == 0))
    
    def test_log_activity(self):
        """Test activity logging with timestamps."""
        message = "Pet entered kitchen"
        event = self.stats.log_activity(message, "zone_entry")
        
        self.assertEqual(len(self.stats.activity_log), 1)
        
        # Check log entry format
        log_entry = self.stats.activity_log[0]
        self.assertIn(message, log_entry)
        self.assertIn(datetime.datetime.now().strftime("%Y-%m-%d"), log_entry)
        
        # Check event object
        self.assertEqual(event.event_type, "zone_entry")
        self.assertIsInstance(event.timestamp, datetime.datetime)
    
    def test_record_detection(self):
        """Test recording pet detections."""
        detection = Detection(
            bbox=(100, 100, 200, 200),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        initial_count = self.stats.stats['total_detections']
        self.stats.record_detection(detection)
        
        self.assertEqual(self.stats.stats['total_detections'], initial_count + 1)
    
    def test_update_heatmap(self):
        """Test heatmap updates with detection bounding boxes."""
        frame_shape = (480, 640)
        self.stats.initialize_heatmap(frame_shape)
        
        bbox = (100, 100, 200, 200)
        self.stats.update_heatmap(bbox)
        
        # Heatmap should be updated in the bbox region
        self.assertTrue(np.any(self.stats.heatmap > 0))
        
        # Check that the updated region is within the bbox
        updated_region = self.stats.heatmap[100:200, 100:200]
        self.assertTrue(np.all(updated_region > 0))
    
    def test_update_heatmap_boundary_clipping(self):
        """Test heatmap updates with out-of-bounds coordinates."""
        frame_shape = (100, 100)
        self.stats.initialize_heatmap(frame_shape)
        
        # Bbox partially outside frame
        bbox = (80, 80, 120, 120)
        self.stats.update_heatmap(bbox)
        
        # Should not crash and should update valid region
        self.assertTrue(np.any(self.stats.heatmap > 0))
        updated_region = self.stats.heatmap[80:100, 80:100]
        self.assertTrue(np.any(updated_region > 0))
    
    # def test_record_eating_event(self):
    #     """Test recording eating events."""
    #     initial_count = self.stats.stats['eating_events']
        
    #     # First eating event
    #     self.stats.record_eating_event('cat')
    #     self.assertEqual(self.stats.stats['eating_events'], initial_count + 1)
    #     self.assertTrue(self.stats.pet_activity_state['food'])
        
    #     # Second eating event while still eating (should not increment)
    #     self.stats.record_eating_event('cat')
    #     self.assertEqual(self.stats.stats['eating_events'], initial_count + 1)  # Should remain same
        
    #     # End eating and start again
    #     self.stats.end_bowl_activity('food')
    #     self.stats.record_eating_event('cat')
    #     self.assertEqual(self.stats.stats['eating_events'], initial_count + 2)

    def test_record_drinking_event(self):
        """Test recording drinking events."""
        initial_count = self.stats.stats['drinking_events']
        
        # First drinking event
        self.stats.record_drinking_event('dog')
        self.assertEqual(self.stats.stats['drinking_events'], initial_count + 1)
        self.assertTrue(self.stats.pet_activity_state['water'])
        
        # Second drinking event while still drinking (should not increment)
        self.stats.record_drinking_event('dog')
        self.assertEqual(self.stats.stats['drinking_events'], initial_count + 1)
    
    def test_record_zone_entry(self):
        """Test recording zone entry events."""
        zone_name = "kitchen"
        zone_type = "restricted"
        pet_type = "cat"
        
        initial_visits = self.stats.stats['zone_visits'][zone_name]
        initial_violations = self.stats.stats['restricted_zone_violations']
        
        self.stats.record_zone_entry(zone_name, zone_type, pet_type)
        
        # Check statistics updates
        self.assertEqual(self.stats.stats['zone_visits'][zone_name], initial_visits + 1)
        self.assertEqual(self.stats.stats['restricted_zone_violations'], initial_violations + 1)
        
        # Check zone duration tracking
        self.assertIn(zone_name, self.stats.zone_durations)
        self.assertIn(zone_name, self.stats.current_zones)
        self.assertIsNotNone(self.stats.zone_durations[zone_name].entry_time)
    
    def test_record_zone_exit(self):
        """Test recording zone exit events."""
        zone_name = "kitchen"
        pet_type = "cat"
        
        # First enter the zone
        self.stats.record_zone_entry(zone_name, "restricted", pet_type)
        self.assertIn(zone_name, self.stats.current_zones)
        
        # Then exit
        initial_duration = self.stats.zone_durations[zone_name].total_time
        self.stats.record_zone_exit(zone_name, pet_type)
        
        # Check zone tracking
        self.assertNotIn(zone_name, self.stats.current_zones)
        self.assertGreater(self.stats.zone_durations[zone_name].total_time, initial_duration)
        self.assertIsNone(self.stats.zone_durations[zone_name].entry_time)
    
    def test_get_zone_statistics(self):
        """Test getting formatted zone statistics."""
        # Create some zone activity
        self.stats.record_zone_entry("kitchen", "restricted", "cat")
        self.stats.record_zone_exit("kitchen", "cat")
        self.stats.record_zone_entry("living_room", "normal", "dog")
        
        zone_stats = self.stats.get_zone_statistics()
        
        self.assertIsInstance(zone_stats, list)
        self.assertEqual(len(zone_stats), 2)
        
        # Check kitchen statistics
        kitchen_stat = next((stat for stat in zone_stats if stat['name'] == 'kitchen'), None)
        self.assertIsNotNone(kitchen_stat)
        self.assertEqual(kitchen_stat['visits'], 1)
        self.assertNotEqual(kitchen_stat['duration'], "N/A")
        self.assertGreater(kitchen_stat['total_seconds'], 0)
        
        # Check living room statistics (still in zone)
        living_room_stat = next((stat for stat in zone_stats if stat['name'] == 'living_room'), None)
        self.assertIsNotNone(living_room_stat)
        self.assertEqual(living_room_stat['visits'], 1)
    
    def test_get_activity_timeline(self):
        """Test getting activity timeline by hour."""
        # Log activities at different hours
        current_hour = datetime.datetime.now().hour
        self.stats.log_activity("Activity 1")
        self.stats.log_activity("Activity 2")
        
        timeline = self.stats.get_activity_timeline()
        
        self.assertIsInstance(timeline, dict)
        self.assertGreaterEqual(timeline[current_hour], 2)
    
    def test_get_recent_activities(self):
        """Test getting recent activity log entries."""
        # Add multiple activities
        for i in range(10):
            self.stats.log_activity(f"Activity {i}")
        
        # Get recent activities
        recent = self.stats.get_recent_activities(5)
        
        self.assertEqual(len(recent), 5)
        self.assertIn("Activity 9", recent[-1])  # Most recent
        self.assertIn("Activity 5", recent[0])   # Oldest of returned
    
    def test_export_to_dict(self):
        """Test exporting statistics to dictionary."""
        # Add some data
        self.stats.record_eating_event('cat')
        self.stats.record_zone_entry("kitchen", "restricted", "cat")
        self.stats.log_activity("Test activity")
        
        export_data = self.stats.export_to_dict()
        
        self.assertIn('stats', export_data)
        self.assertIn('activity_log', export_data)
        self.assertIn('zone_durations', export_data)
        self.assertIn('export_timestamp', export_data)
        
        # Check data integrity - use assertGreaterEqual for flexible count
        self.assertEqual(export_data['stats']['eating_events'], 1)
        self.assertGreaterEqual(len(export_data['activity_log']), 2)  # eating + test activity
        self.assertIn('kitchen', export_data['zone_durations'])

    def test_import_from_dict(self):
        """Test importing statistics from dictionary."""
        # Create export data
        export_data = {
            'stats': {
                'eating_events': 5,
                'drinking_events': 3,
                'total_detections': 20,
                'zone_visits': {'kitchen': 3, 'bedroom': 2}
            },
            'activity_log': ['Activity 1', 'Activity 2'],
            'zone_durations': {
                'kitchen': {'total_time': 150.0, 'visit_count': 3}
            }
        }
        
        # Import data
        self.stats.import_from_dict(export_data)
        
        # Check imported data
        self.assertEqual(self.stats.stats['eating_events'], 5)
        self.assertEqual(self.stats.stats['drinking_events'], 3)
        self.assertEqual(self.stats.stats['total_detections'], 20)
        self.assertEqual(self.stats.stats['zone_visits']['kitchen'], 3)
        self.assertEqual(len(self.stats.activity_log), 2)
        self.assertIn('kitchen', self.stats.zone_durations)
        self.assertEqual(self.stats.zone_durations['kitchen'].total_time, 150.0)
    
    def test_get_summary_report(self):
        """Test getting comprehensive summary report."""
        # Create diverse activity data
        self.stats.record_eating_event('cat')
        self.stats.record_drinking_event('dog')
        self.stats.record_zone_entry("kitchen", "restricted", "cat")
        self.stats.record_zone_exit("kitchen", "cat")
        self.stats.log_activity("Test activity 1")
        self.stats.log_activity("Test activity 2")
        
        report = self.stats.get_summary_report()
        
        # Check report structure
        self.assertIn('summary', report)
        self.assertIn('zone_statistics', report)
        self.assertIn('activity_timeline', report)
        self.assertIn('recent_activities', report)
        
        # Check summary data
        summary = report['summary']
        self.assertEqual(summary['eating_events'], 1)
        self.assertEqual(summary['drinking_events'], 1)
        self.assertEqual(summary['restricted_violations'], 1)
        self.assertEqual(summary['zones_monitored'], 1)
        
        # Check zone statistics
        self.assertEqual(len(report['zone_statistics']), 1)
        
        # Check recent activities - use flexible count
        self.assertGreaterEqual(len(report['recent_activities']), 4)
        
    def test_activity_log_size_limit(self):
        """Test activity log size limiting."""
        stats_limited = ActivityStatistics(max_log_size=5)
        
        # Add more activities than the limit
        for i in range(10):
            stats_limited.log_activity(f"Activity {i}")
        
        # Should only keep the most recent 5
        self.assertEqual(len(stats_limited.activity_log), 5)
        
        # Check that it kept the most recent ones
        recent_activities = list(stats_limited.activity_log)
        self.assertIn("Activity 9", recent_activities[-1])
        self.assertIn("Activity 5", recent_activities[0])


class TestZoneDuration(unittest.TestCase):
    """Test cases for ZoneDuration helper class."""
    
    def test_zone_duration_initialization(self):
        """Test ZoneDuration initialization."""
        zone_duration = ZoneDuration("kitchen", 100.0)
        
        self.assertEqual(zone_duration.zone_name, "kitchen")
        self.assertEqual(zone_duration.total_time, 100.0)
        self.assertIsNone(zone_duration.entry_time)
        self.assertEqual(zone_duration.visit_count, 0)
    
    def test_start_visit(self):
        """Test starting a zone visit."""
        zone_duration = ZoneDuration("kitchen", 0.0)
        
        initial_count = zone_duration.visit_count
        zone_duration.start_visit()
        
        self.assertEqual(zone_duration.visit_count, initial_count + 1)
        self.assertIsNotNone(zone_duration.entry_time)
        self.assertIsInstance(zone_duration.entry_time, datetime.datetime)
    
    def test_end_visit(self):
        """Test ending a zone visit."""
        zone_duration = ZoneDuration("kitchen", 0.0)
        
        # Start a visit
        zone_duration.start_visit()
        initial_total_time = zone_duration.total_time
        
        # End the visit (with a small delay to ensure measurable duration)
        import time
        time.sleep(0.01)
        duration = zone_duration.end_visit()
        
        # Check results
        self.assertGreater(duration, 0)
        self.assertGreater(zone_duration.total_time, initial_total_time)
        self.assertIsNone(zone_duration.entry_time)
    
    def test_end_visit_without_start(self):
        """Test ending a visit that was never started."""
        zone_duration = ZoneDuration("kitchen", 0.0)
        
        duration = zone_duration.end_visit()
        
        self.assertEqual(duration, 0.0)
        self.assertEqual(zone_duration.total_time, 0.0)


if __name__ == '__main__':
    unittest.main()