"""
Unit tests for the PetActivityTracker class.
"""
import unittest
import numpy as np
import datetime
from unittest.mock import Mock, patch
import sys
import os

# Import the modules to test
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.core.tracker import PetActivityTracker
from backend.data.models import Detection, Zone, BowlLocation
from backend.data.statistics import ActivityStatistics


class TestPetActivityTracker(unittest.TestCase):
    """Test cases for PetActivityTracker class."""
    
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.statistics = ActivityStatistics()
        self.tracker = PetActivityTracker(self.statistics)
        
        # Create test zones
        self.test_zones = [
            Zone("kitchen", (100, 100, 300, 200), "restricted", (255, 0, 0)),
            Zone("living_room", (400, 100, 600, 300), "normal", (0, 255, 0)),
            Zone("bedroom", (100, 400, 300, 500), "bedroom", (0, 0, 255))
        ]
        
        # Create test bowls
        self.test_bowls = {
            "food": BowlLocation("food", (150, 250), 30, (255, 0, 0)),
            "water": BowlLocation("water", (200, 250), 25, (0, 0, 255))
        }
        
        # Create test detections
        self.test_detection_kitchen = Detection(
            bbox=(150, 150, 200, 180),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        self.test_detection_bowl = Detection(
            bbox=(140, 240, 160, 260),
            pet_type='dog',
            confidence=0.7,
            timestamp=datetime.datetime.now(),
            frame_number=2
        )
    
    def test_initialization(self):
        """Test tracker initialization."""
        self.assertIsInstance(self.tracker.statistics, ActivityStatistics)
        self.assertEqual(len(self.tracker.zones), 0)
        self.assertEqual(len(self.tracker.bowls), 0)
        self.assertEqual(len(self.tracker.current_zones), 0)
    
    def test_update_zones(self):
        """Test updating zones configuration."""
        self.tracker.update_zones(self.test_zones)
        
        self.assertEqual(len(self.tracker.zones), 3)
        self.assertEqual(self.tracker.zones[0].name, "kitchen")
        self.assertEqual(self.tracker.zones[0].zone_type, "restricted")
        self.assertIsNone(self.tracker.zone_mask)  # Should be invalidated
    
    def test_update_bowls(self):
        """Test updating bowl locations."""
        self.tracker.update_bowls(self.test_bowls)
        
        self.assertEqual(len(self.tracker.bowls), 2)
        self.assertIn("food", self.tracker.bowls)
        self.assertIn("water", self.tracker.bowls)
        self.assertEqual(self.tracker.bowls["food"].position, (150, 250))
    
    def test_set_frame_shape(self):
        """Test setting frame shape for heatmap initialization."""
        frame_shape = (480, 640)
        self.tracker.set_frame_shape(frame_shape)
        
        self.assertEqual(self.tracker.frame_shape, frame_shape)
        self.assertIsNotNone(self.tracker.statistics.heatmap)
        self.assertEqual(self.tracker.statistics.heatmap.shape, frame_shape)
    
    def test_process_detections_empty(self):
        """Test processing empty detection list."""
        results = self.tracker.process_detections([])
        
        expected = {
            'zone_activities': [],
            'bowl_activities': [],
            'alerts': [],
            'detections_processed': 0
        }
        self.assertEqual(results, expected)
    
    def test_process_detections_zone_entry(self):
        """Test processing detection that enters a zone."""
        self.tracker.update_zones(self.test_zones)
        
        results = self.tracker.process_detections([self.test_detection_kitchen])
        
        self.assertEqual(results['detections_processed'], 1)
        self.assertEqual(len(results['zone_activities']), 1)
        
        zone_activity = results['zone_activities'][0]
        self.assertEqual(zone_activity['action'], 'entry')
        self.assertEqual(zone_activity['zone'], 'kitchen')
        self.assertEqual(zone_activity['pet_type'], 'cat')
        self.assertTrue(zone_activity.get('alert', False))  # Restricted zone should trigger alert
    
    def test_process_detections_bowl_interaction(self):
        """Test processing detection near a bowl."""
        self.tracker.update_bowls(self.test_bowls)
        
        results = self.tracker.process_detections([self.test_detection_bowl])
        
        self.assertEqual(results['detections_processed'], 1)
        self.assertEqual(len(results['bowl_activities']), 1)
        
        bowl_activity = results['bowl_activities'][0]
        self.assertEqual(bowl_activity['action'], 'eating')
        self.assertEqual(bowl_activity['bowl'], 'food')
        self.assertEqual(bowl_activity['pet_type'], 'dog')
    
    def test_zone_exit_detection(self):
        """Test detection of zone exits."""
        self.tracker.update_zones(self.test_zones)
        
        # First, enter the zone
        self.tracker.process_detections([self.test_detection_kitchen])
        self.assertIn('kitchen', self.tracker.current_zones)
        
        # Then, process empty detections (pet left)
        results = self.tracker.process_detections([])
        
        self.assertEqual(len(self.tracker.current_zones), 0)
        # Note: Zone exit would be recorded in statistics
    
    def test_bowl_interaction_threshold(self):
        """Test bowl interaction distance threshold calculation."""
        self.tracker.update_bowls(self.test_bowls)
        
        # Detection very close to bowl (should trigger)
        close_detection = Detection(
            bbox=(148, 248, 152, 252),  # Very small, close to bowl
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        results = self.tracker.process_detections([close_detection])
        self.assertEqual(len(results['bowl_activities']), 1)
        
        # Detection far from bowl (should not trigger)
        far_detection = Detection(
            bbox=(300, 300, 320, 320),  # Far from bowl
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=2
        )
        
        results = self.tracker.process_detections([far_detection])
        self.assertEqual(len(results['bowl_activities']), 0)
    
    def test_multiple_zones_interaction(self):
        """Test pet interacting with multiple zones simultaneously."""
        # Create overlapping zones
        overlapping_zones = [
            Zone("zone1", (100, 100, 200, 200), "normal", (255, 0, 0)),
            Zone("zone2", (150, 150, 250, 250), "feeding_area", (0, 255, 0))
        ]
        self.tracker.update_zones(overlapping_zones)
        
        # Detection in overlapping area
        overlap_detection = Detection(
            bbox=(170, 170, 180, 180),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        results = self.tracker.process_detections([overlap_detection])
        
        # Should detect entry into both zones
        self.assertEqual(len(results['zone_activities']), 2)
        zone_names = [activity['zone'] for activity in results['zone_activities']]
        self.assertIn('zone1', zone_names)
        self.assertIn('zone2', zone_names)
    
    def test_statistics_updates(self):
        """Test that statistics are properly updated."""
        self.tracker.update_zones(self.test_zones)
        self.tracker.update_bowls(self.test_bowls)
        
        initial_detections = self.statistics.stats['total_detections']
        initial_violations = self.statistics.stats['restricted_zone_violations']
        
        # Process detection in restricted zone
        self.tracker.process_detections([self.test_detection_kitchen])
        
        # Check statistics were updated
        self.assertEqual(
            self.statistics.stats['total_detections'], 
            initial_detections + 1
        )
        self.assertEqual(
            self.statistics.stats['restricted_zone_violations'], 
            initial_violations + 1
        )
    
    def test_get_zone_by_name(self):
        """Test retrieving zone by name."""
        self.tracker.update_zones(self.test_zones)
        
        kitchen_zone = self.tracker.get_zone_by_name("kitchen")
        self.assertIsNotNone(kitchen_zone)
        self.assertEqual(kitchen_zone.name, "kitchen")
        self.assertEqual(kitchen_zone.zone_type, "restricted")
        
        nonexistent_zone = self.tracker.get_zone_by_name("nonexistent")
        self.assertIsNone(nonexistent_zone)
    
    def test_get_bowl_by_name(self):
        """Test retrieving bowl by name."""
        self.tracker.update_bowls(self.test_bowls)
        
        food_bowl = self.tracker.get_bowl_by_name("food")
        self.assertIsNotNone(food_bowl)
        self.assertEqual(food_bowl.name, "food")
        
        nonexistent_bowl = self.tracker.get_bowl_by_name("nonexistent")
        self.assertIsNone(nonexistent_bowl)
    
    def test_clear_zones(self):
        """Test clearing all zones."""
        self.tracker.update_zones(self.test_zones)
        self.tracker.current_zones.add("kitchen")
        
        self.tracker.clear_zones()
        
        self.assertEqual(len(self.tracker.zones), 0)
        self.assertEqual(len(self.tracker.current_zones), 0)
        self.assertIsNone(self.tracker.zone_mask)
    
    def test_clear_bowls(self):
        """Test clearing all bowls."""
        self.tracker.update_bowls(self.test_bowls)
        self.tracker.pet_activity_state["food"] = True
        
        self.tracker.clear_bowls()
        
        self.assertEqual(len(self.tracker.bowls), 0)
        self.assertEqual(len(self.tracker.pet_activity_state), 0)
    
    def test_invalidate_cache(self):
        """Test cache invalidation."""
        # Set up some cached data
        self.tracker.zone_mask = np.zeros((480, 640, 3), dtype=np.uint8)
        
        self.tracker.invalidate_cache()
        
        self.assertIsNone(self.tracker.zone_mask)
    
    @patch('cv2.rectangle')
    @patch('cv2.putText')
    def test_draw_zones(self, mock_puttext, mock_rectangle):
        """Test drawing zones on frame."""
        self.tracker.update_zones(self.test_zones)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result_frame = self.tracker.draw_zones(frame)
        
        # Should have called cv2 functions for each zone
        self.assertEqual(mock_rectangle.call_count, 6)  # 3 zones * 2 calls each (bg + border)
        self.assertEqual(mock_puttext.call_count, 3)    # 3 zone labels
        
        # Frame should be modified
        self.assertIsInstance(result_frame, np.ndarray)
    
    @patch('cv2.circle')
    @patch('cv2.rectangle')
    @patch('cv2.putText')
    def test_draw_bowls(self, mock_puttext, mock_rectangle, mock_circle):
        """Test drawing bowls on frame."""
        self.tracker.update_bowls(self.test_bowls)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        result_frame = self.tracker.draw_bowls(frame)
        
        # Should have called cv2 functions for each bowl
        self.assertEqual(mock_circle.call_count, 2)     # 2 bowl circles
        self.assertEqual(mock_rectangle.call_count, 2)  # 2 label backgrounds
        self.assertEqual(mock_puttext.call_count, 2)    # 2 bowl labels
        
        # Frame should be modified
        self.assertIsInstance(result_frame, np.ndarray)


class TestTrackerIntegration(unittest.TestCase):
    """Integration tests for tracker with realistic scenarios."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.statistics = ActivityStatistics()
        self.tracker = PetActivityTracker(self.statistics)
        
        # Set up a realistic home layout
        self.home_zones = [
            Zone("kitchen", (50, 50, 200, 150), "restricted", (255, 0, 0)),
            Zone("living_room", (250, 50, 500, 300), "normal", (0, 255, 0)),
            Zone("bedroom", (50, 200, 200, 350), "bedroom", (0, 0, 255)),
            Zone("feeding_area", (520, 50, 600, 150), "feeding_area", (255, 255, 0))
        ]
        
        self.home_bowls = {
            "food": BowlLocation("food", (550, 100), 30, (255, 0, 0)),
            "water": BowlLocation("water", (570, 120), 25, (0, 0, 255))
        }
        
        self.tracker.update_zones(self.home_zones)
        self.tracker.update_bowls(self.home_bowls)
        self.tracker.set_frame_shape((400, 650))
    
    def test_pet_daily_routine(self):
        """Test a realistic pet daily routine."""
        # Morning: Pet goes to feeding area
        morning_detection = Detection(
            bbox=(540, 90, 560, 110),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        results = self.tracker.process_detections([morning_detection])
        
        # Should detect feeding area entry and eating
        zone_activities = results['zone_activities']
        bowl_activities = results['bowl_activities']
        
        self.assertTrue(any(activity['zone'] == 'feeding_area' for activity in zone_activities))
        self.assertTrue(any(activity['action'] == 'eating' for activity in bowl_activities))
        
        # Afternoon: Pet explores living room
        afternoon_detection = Detection(
            bbox=(350, 150, 370, 170),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=100
        )
        
        results = self.tracker.process_detections([afternoon_detection])
        
        # Should detect zone change (exit feeding area, enter living room)
        self.assertIn('living_room', self.tracker.current_zones)
        self.assertNotIn('feeding_area', self.tracker.current_zones)
        
        # Evening: Pet tries to enter kitchen (restricted)
        evening_detection = Detection(
            bbox=(100, 90, 120, 110),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=200
        )
        
        results = self.tracker.process_detections([evening_detection])
        
        # Should trigger restricted zone alert
        kitchen_entries = [
            activity for activity in results['zone_activities'] 
            if activity['zone'] == 'kitchen' and activity.get('alert', False)
        ]
        self.assertEqual(len(kitchen_entries), 1)
        
        # Check statistics
        self.assertGreater(self.statistics.stats['total_detections'], 0)
        self.assertGreater(self.statistics.stats['eating_events'], 0)
        self.assertGreater(self.statistics.stats['restricted_zone_violations'], 0)
    
    def test_multiple_pets_scenario(self):
        """Test scenario with multiple pets."""
        # Two pets detected simultaneously
        cat_detection = Detection(
            bbox=(100, 100, 120, 120),
            pet_type='cat',
            confidence=0.8,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        dog_detection = Detection(
            bbox=(540, 90, 570, 120),
            pet_type='dog',
            confidence=0.7,
            timestamp=datetime.datetime.now(),
            frame_number=1
        )
        
        results = self.tracker.process_detections([cat_detection, dog_detection])
        
        # Should process both detections
        self.assertEqual(results['detections_processed'], 2)
        
        # Cat should trigger kitchen violation, dog should start eating
        zone_activities = results['zone_activities']
        bowl_activities = results['bowl_activities']
        
        kitchen_alerts = [
            activity for activity in zone_activities 
            if activity['zone'] == 'kitchen' and activity.get('alert', False)
        ]
        eating_activities = [
            activity for activity in bowl_activities 
            if activity['action'] == 'eating'
        ]
        
        self.assertEqual(len(kitchen_alerts), 1)
        self.assertEqual(len(eating_activities), 1)
        self.assertEqual(kitchen_alerts[0]['pet_type'], 'cat')
        self.assertEqual(eating_activities[0]['pet_type'], 'dog')


if __name__ == '__main__':
    unittest.main()