"""
Unit tests for I/O utilities and configuration management.
"""
import unittest
import tempfile
import os
import json
import shutil
from unittest.mock import Mock, patch, MagicMock

from backend.utils.io_utils import ConfigurationManager, ReportGenerator, DataExporter
from backend.data.models import Zone, BowlLocation, AppConfig, PerformanceSettings
from backend.data.statistics import ActivityStatistics


class TestConfigurationManager(unittest.TestCase):
    """Test configuration management functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        self.config_manager = ConfigurationManager(self.config_path)
        
        # Create test configuration
        self.test_zones = [
            Zone("test_zone", (100, 100, 200, 200), "restricted", (255, 0, 0))
        ]
        self.test_bowls = {
            "food": BowlLocation("food", (50, 50), 30, (255, 0, 0))
        }
        self.test_performance = PerformanceSettings.from_mode("balanced")
        self.test_config = AppConfig(
            zones=self.test_zones,
            bowls=self.test_bowls,
            performance=self.test_performance,
            confidence_threshold=0.7,
            alert_cooldown=120,
            model_path="models/test_model.pt"
        )
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_ensure_config_directory(self):
        """Test configuration directory creation."""
        # Directory should be created during initialization
        self.assertTrue(os.path.exists(os.path.dirname(self.config_path)))
    
    def test_save_config(self):
        """Test saving configuration to file."""
        result = self.config_manager.save_config(self.test_config)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(self.config_path))
        
        # Verify file contents
        with open(self.config_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn('zones', data)
        self.assertIn('bowls', data)
        self.assertIn('performance', data)
        self.assertEqual(data['confidence_threshold'], 0.7)
        self.assertEqual(data['alert_cooldown'], 120)
    
    def test_save_config_custom_path(self):
        """Test saving configuration to custom path."""
        custom_path = os.path.join(self.temp_dir, "custom_config.json")
        result = self.config_manager.save_config(self.test_config, custom_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(custom_path))
    
    def test_save_config_failure(self):
        """Test configuration save failure handling."""
        # Try to save to invalid path
        invalid_path = "/invalid/path/config.json"
        result = self.config_manager.save_config(self.test_config, invalid_path)
        
        self.assertFalse(result)
    
    def test_load_config(self):
        """Test loading configuration from file."""
        # First save a config
        self.config_manager.save_config(self.test_config)
        
        # Then load it back
        loaded_config = self.config_manager.load_config()
        
        self.assertIsNotNone(loaded_config)
        self.assertEqual(len(loaded_config.zones), 1)
        self.assertEqual(loaded_config.zones[0].name, "test_zone")
        self.assertEqual(len(loaded_config.bowls), 1)
        self.assertIn("food", loaded_config.bowls)
        self.assertEqual(loaded_config.confidence_threshold, 0.7)
        self.assertEqual(loaded_config.alert_cooldown, 120)
    
    def test_load_config_nonexistent_file(self):
        """Test loading configuration from nonexistent file."""
        nonexistent_path = os.path.join(self.temp_dir, "nonexistent.json")
        loaded_config = self.config_manager.load_config(nonexistent_path)
        
        self.assertIsNone(loaded_config)
    
    def test_load_config_invalid_json(self):
        """Test loading configuration from invalid JSON file."""
        # Create invalid JSON file
        with open(self.config_path, 'w') as f:
            f.write("invalid json content {")
        
        loaded_config = self.config_manager.load_config()
        
        self.assertIsNone(loaded_config)
    
    def test_config_to_dict_conversion(self):
        """Test converting AppConfig to dictionary."""
        config_dict = self.config_manager._config_to_dict(self.test_config)
        
        self.assertIn('zones', config_dict)
        self.assertIn('bowls', config_dict)
        self.assertIn('performance', config_dict)
        self.assertIn('version', config_dict)
        self.assertIn('created_at', config_dict)
        
        # Check zone conversion
        zone_data = config_dict['zones'][0]
        self.assertEqual(zone_data['name'], "test_zone")
        self.assertEqual(zone_data['zone_type'], "restricted")
        self.assertEqual(zone_data['coords'], (100, 100, 200, 200))
        self.assertEqual(zone_data['color'], (255, 0, 0))
        
        # Check bowl conversion
        bowl_data = config_dict['bowls']['food']
        self.assertEqual(bowl_data['name'], "food")
        self.assertEqual(bowl_data['position'], (50, 50))
        self.assertEqual(bowl_data['radius'], 30)
    
    def test_dict_to_config_conversion(self):
        """Test converting dictionary to AppConfig."""
        config_dict = self.config_manager._config_to_dict(self.test_config)
        converted_config = self.config_manager._dict_to_config(config_dict)
        
        self.assertEqual(len(converted_config.zones), 1)
        self.assertEqual(converted_config.zones[0].name, "test_zone")
        self.assertEqual(len(converted_config.bowls), 1)
        self.assertIn("food", converted_config.bowls)
        self.assertEqual(converted_config.confidence_threshold, 0.7)
    
    def test_create_default_config(self):
        """Test creating default configuration."""
        default_config = self.config_manager.create_default_config()
        
        self.assertIsInstance(default_config, AppConfig)
        self.assertEqual(len(default_config.zones), 0)
        self.assertEqual(len(default_config.bowls), 0)
        self.assertEqual(default_config.confidence_threshold, 0.5)
        self.assertEqual(default_config.alert_cooldown, 60)
        self.assertEqual(default_config.model_path, "models/yolo12n.pt")


class TestReportGenerator(unittest.TestCase):
    """Test report generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.statistics = ActivityStatistics()
        self.report_generator = ReportGenerator(self.statistics)
        
        # Add some test data
        self.statistics.stats['eating_events'] = 5
        self.statistics.stats['drinking_events'] = 3
        self.statistics.stats['restricted_zone_violations'] = 2
        self.statistics.stats['total_detections'] = 100
        
        # Add activity timeline data
        self.statistics.stats['activity_timeline'][9] = 10
        self.statistics.stats['activity_timeline'][14] = 15
        self.statistics.stats['activity_timeline'][18] = 8
        
        # Add zone statistics
        self.statistics.stats['zone_visits']['kitchen'] = 20
        self.statistics.stats['zone_visits']['bedroom'] = 5
        
        # Add activity log entries
        self.statistics.activity_log.extend([
            "2024-01-01 09:00:00: Pet detected",
            "2024-01-01 09:05:00: Pet entered kitchen",
            "2024-01-01 09:10:00: ALERT: Pet entered restricted zone"
        ])
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_generate_text_report(self):
        """Test generating text report."""
        file_path = os.path.join(self.temp_dir, "test_report.txt")
        result = self.report_generator.generate_text_report(file_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))
        
        # Check file contents
        with open(file_path, 'r') as f:
            content = f.read()
        
        self.assertIn("Pet Activity Tracker", content)
        self.assertIn("SUMMARY STATISTICS", content)
        self.assertIn("ZONE STATISTICS", content)
        self.assertIn("ACTIVITY TIMELINE", content)
        self.assertIn("RECENT ACTIVITIES", content)
        self.assertIn("Eating Events: 5", content)
        self.assertIn("kitchen", content)
    
    def test_generate_json_report(self):
        """Test generating JSON report."""
        file_path = os.path.join(self.temp_dir, "test_report.json")
        result = self.report_generator.generate_json_report(file_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))
        
        # Check file contents
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        self.assertIn('stats', data)
        self.assertIn('activity_log', data)
        self.assertIn('metadata', data)
        self.assertEqual(data['stats']['eating_events'], 5)
    
    @patch('backend.utils.io_utils.PANDAS_AVAILABLE', True)
    @patch('pandas.DataFrame')
    def test_generate_csv_report(self, mock_dataframe):
        """Test generating CSV report."""
        mock_df = Mock()
        mock_dataframe.return_value = mock_df
        
        file_path = os.path.join(self.temp_dir, "test_report.csv")
        result = self.report_generator.generate_csv_report(file_path)
        
        self.assertTrue(result)
        mock_dataframe.assert_called_once()
        mock_df.to_csv.assert_called_once_with(file_path, index=False)

    @patch('backend.utils.io_utils.PANDAS_AVAILABLE', False)
    def test_generate_csv_report_no_pandas(self):
        """Test CSV report generation without pandas."""
        # Create a new ReportGenerator with the mocked PANDAS_AVAILABLE
        new_report_generator = ReportGenerator(self.statistics)
        
        file_path = os.path.join(self.temp_dir, "test_report.csv")
        result = new_report_generator.generate_csv_report(file_path)
        
        self.assertFalse(result)

    def test_generate_html_report(self):
        """Test generating HTML report."""
        file_path = os.path.join(self.temp_dir, "test_report.html")
        result = self.report_generator.generate_html_report(file_path)
        
        self.assertTrue(result)
        self.assertTrue(os.path.exists(file_path))
        
        # Check file contents
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("<!DOCTYPE html>", content)
        self.assertIn("Pet Activity Report", content)
        self.assertIn("Summary Statistics", content)
        self.assertIn("Zone Activity", content)
        self.assertIn("Activity Timeline", content)
        self.assertIn("Eating Events", content)
        
    def test_generate_report_failure(self):
        """Test report generation failure handling."""
        invalid_path = "/invalid/path/report.txt"
        result = self.report_generator.generate_text_report(invalid_path)
        
        self.assertFalse(result)


class TestDataExporter(unittest.TestCase):
    """Test data export functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.statistics = ActivityStatistics()
        
        # Add test data
        self.statistics.stats['eating_events'] = 5
        self.statistics.stats['zone_visits']['kitchen'] = 10
        self.statistics.activity_log.extend([
            "2024-01-01 09:00:00: Pet detected",
            "2024-01-01 09:05:00: ALERT: Restricted zone entry"
        ])
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    @patch('backend.utils.io_utils.PANDAS_AVAILABLE', True)
    @patch('pandas.DataFrame')
    def test_export_statistics_csv(self, mock_dataframe):
        """Test exporting statistics to CSV."""
        mock_df = Mock()
        mock_dataframe.return_value = mock_df
        
        file_path = os.path.join(self.temp_dir, "stats.csv")
        result = DataExporter.export_statistics_csv(self.statistics, file_path)
        
        self.assertTrue(result)
        mock_dataframe.assert_called_once()
        mock_df.to_csv.assert_called_once_with(file_path, index=False)
    
    @patch('backend.utils.io_utils.PANDAS_AVAILABLE', False)
    def test_export_statistics_csv_no_pandas(self):
        """Test CSV export without pandas."""
        file_path = os.path.join(self.temp_dir, "stats.csv")
        result = DataExporter.export_statistics_csv(self.statistics, file_path)
        
        self.assertFalse(result)
    
    @patch('backend.utils.io_utils.PANDAS_AVAILABLE', True)
    @patch('pandas.DataFrame')
    def test_export_activity_log_csv(self, mock_dataframe):
        """Test exporting activity log to CSV."""
        mock_df = Mock()
        mock_dataframe.return_value = mock_df
        
        file_path = os.path.join(self.temp_dir, "activity.csv")
        result = DataExporter.export_activity_log_csv(self.statistics, file_path)
        
        self.assertTrue(result)
        mock_dataframe.assert_called_once()
        
        # Check that data was parsed correctly
        call_args = mock_dataframe.call_args[0][0]
        self.assertTrue(len(call_args) > 0)
        self.assertIn('timestamp', call_args[0])
        self.assertIn('message', call_args[0])
        self.assertIn('is_alert', call_args[0])
    
    def test_backup_application_data(self):
        """Test creating application data backup."""
        # Create test config
        zones = [Zone("test_zone", (0, 0, 100, 100), "restricted", (255, 0, 0))]
        bowls = {"food": BowlLocation("food", (50, 50), 30, (255, 0, 0))}
        performance = PerformanceSettings.from_mode("balanced")
        config = AppConfig(zones=zones, bowls=bowls, performance=performance)
        
        result = DataExporter.backup_application_data(config, self.statistics, self.temp_dir)
        
        self.assertTrue(result)
        
        # Check that backup directory was created
        backup_dirs = [d for d in os.listdir(self.temp_dir) if d.startswith("pet_tracker_backup_")]
        self.assertEqual(len(backup_dirs), 1)
        
        backup_path = os.path.join(self.temp_dir, backup_dirs[0])
        
        # Check that all expected files exist
        expected_files = ["config.json", "statistics.json", "backup_info.json"]
        for filename in expected_files:
            self.assertTrue(os.path.exists(os.path.join(backup_path, filename)))
        
        # Check backup info
        with open(os.path.join(backup_path, "backup_info.json"), 'r') as f:
            backup_info = json.load(f)
        
        self.assertIn('created_at', backup_info)
        self.assertIn('version', backup_info)
        self.assertIn('files', backup_info)
    
    def test_export_failure_handling(self):
        """Test export failure handling."""
        invalid_path = "/invalid/path/export.csv"
        
        # This should fail gracefully
        result = DataExporter.export_statistics_csv(self.statistics, invalid_path)
        self.assertFalse(result)


class TestIOUtilsIntegration(unittest.TestCase):
    """Integration tests for I/O utilities."""
    
    def setUp(self):
        """Set up integration test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_manager = ConfigurationManager()
        self.statistics = ActivityStatistics()
    
    def tearDown(self):
        """Clean up test fixtures."""
        shutil.rmtree(self.temp_dir)
    
    def test_complete_config_workflow(self):
        """Test complete configuration save/load workflow."""
        # Create test configuration
        zones = [
            Zone("kitchen", (0, 0, 100, 100), "kitchen", (255, 165, 0)),
            Zone("restricted", (200, 200, 300, 300), "restricted", (255, 0, 0))
        ]
        bowls = {
            "food": BowlLocation("food", (50, 50), 30, (255, 0, 0)),
            "water": BowlLocation("water", (100, 50), 25, (0, 0, 255))
        }
        performance = PerformanceSettings.from_mode("performance")
        
        original_config = AppConfig(
            zones=zones,
            bowls=bowls,
            performance=performance,
            confidence_threshold=0.8,
            alert_cooldown=90
        )
        
        # Save configuration
        config_path = os.path.join(self.temp_dir, "integration_test.json")
        save_result = self.config_manager.save_config(original_config, config_path)
        self.assertTrue(save_result)
        
        # Load configuration
        loaded_config = self.config_manager.load_config(config_path)
        self.assertIsNotNone(loaded_config)
        
        # Verify loaded configuration matches original
        self.assertEqual(len(loaded_config.zones), 2)
        self.assertEqual(len(loaded_config.bowls), 2)
        self.assertEqual(loaded_config.confidence_threshold, 0.8)
        self.assertEqual(loaded_config.alert_cooldown, 90)
        self.assertEqual(loaded_config.performance.mode, "performance")
        
        # Check zone details
        kitchen_zone = next(z for z in loaded_config.zones if z.name == "kitchen")
        self.assertEqual(kitchen_zone.zone_type, "kitchen")
        self.assertEqual(kitchen_zone.color, (255, 165, 0))
        
        # Check bowl details
        food_bowl = loaded_config.bowls["food"]
        self.assertEqual(food_bowl.position, (50, 50))
        self.assertEqual(food_bowl.radius, 30)
    
    def test_complete_reporting_workflow(self):
        """Test complete reporting workflow."""
        # Add comprehensive test data
        self.statistics.stats.update({
            'eating_events': 15,
            'drinking_events': 8,
            'restricted_zone_violations': 3,
            'total_detections': 250
        })
        
        # Add zone data
        self.statistics.stats['zone_visits'].update({
            'kitchen': 45,
            'bedroom': 12,
            'living_room': 28
        })
        
        # Add timeline data
        for hour in range(6, 22):
            self.statistics.stats['activity_timeline'][hour] = max(0, 10 - abs(hour - 14))
        
        # Generate multiple report formats
        report_generator = ReportGenerator(self.statistics)
        
        # Text report
        text_path = os.path.join(self.temp_dir, "complete_report.txt")
        text_result = report_generator.generate_text_report(text_path)
        self.assertTrue(text_result)
        
        # JSON report
        json_path = os.path.join(self.temp_dir, "complete_report.json")
        json_result = report_generator.generate_json_report(json_path)
        self.assertTrue(json_result)
        
        # HTML report
        html_path = os.path.join(self.temp_dir, "complete_report.html")
        html_result = report_generator.generate_html_report(html_path)
        self.assertTrue(html_result)
        
        # Verify all files exist and have content
        for path in [text_path, json_path, html_path]:
            self.assertTrue(os.path.exists(path))
            self.assertGreater(os.path.getsize(path), 100)  # Non-empty files


if __name__ == '__main__':
    unittest.main()