"""
backend/utils/io_utils.py
Input/Output utilities for configuration and data management.
"""
import cv2
import json
import pickle
import os
import datetime
from typing import Dict, List, Any, Optional
import pandas as pd

from ..data.models import Zone, BowlLocation, AppConfig, PerformanceSettings
from ..data.statistics import ActivityStatistics

# Check if pandas is available
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

class ConfigurationManager:
    """Manages application configuration saving and loading."""
    
    def __init__(self, default_config_path: str = "config/default_config.json"):
        self.default_config_path = default_config_path
        self.ensure_config_directory()
    
    def ensure_config_directory(self):
        """Ensure configuration directory exists."""
        config_dir = os.path.dirname(self.default_config_path)
        if config_dir and not os.path.exists(config_dir):
            os.makedirs(config_dir)
    
    def save_config(self, config: AppConfig, file_path: Optional[str] = None) -> bool:
        """
        Save application configuration to JSON file.
        
        Args:
            config: AppConfig object to save
            file_path: Optional custom file path
            
        Returns:
            True if saved successfully
        """
        if file_path is None:
            file_path = self.default_config_path
        
        try:
            config_dict = self._config_to_dict(config)
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=4, default=str)
            
            print(f"✓ Configuration saved to {file_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to save configuration: {e}")
            return False
    
    def load_config(self, file_path: Optional[str] = None) -> Optional[AppConfig]:
        """
        Load application configuration from JSON file.
        
        Args:
            file_path: Optional custom file path
            
        Returns:
            AppConfig object or None if loading failed
        """
        if file_path is None:
            file_path = self.default_config_path
        
        if not os.path.exists(file_path):
            print(f"Configuration file not found: {file_path}")
            return None
        
        try:
            with open(file_path, 'r') as f:
                config_dict = json.load(f)
            
            config = self._dict_to_config(config_dict)
            print(f"✓ Configuration loaded from {file_path}")
            return config
            
        except Exception as e:
            print(f"✗ Failed to load configuration: {e}")
            return None
    
    def _config_to_dict(self, config: AppConfig) -> Dict:
        """Convert AppConfig to dictionary."""
        return {
            'zones': [
                {
                    'name': zone.name,
                    'coords': zone.coords,
                    'zone_type': zone.zone_type,
                    'color': zone.color
                } for zone in config.zones
            ],
            'bowls': {
                name: {
                    'name': bowl.name,
                    'position': bowl.position,
                    'radius': bowl.radius,
                    'color': bowl.color
                } for name, bowl in config.bowls.items()
            },
            'performance': {
                'mode': config.performance.mode,
                'display_fps': config.performance.display_fps,
                'detection_cache_frames': config.performance.detection_cache_frames,
                'stats_update_frequency': config.performance.stats_update_frequency,
                'heatmap_update_frequency': config.performance.heatmap_update_frequency,
                'frame_skip_ratio': config.performance.frame_skip_ratio
            },
            'confidence_threshold': config.confidence_threshold,
            'alert_cooldown': config.alert_cooldown,
            'email_config': config.email_config,
            'model_path': config.model_path,
            'version': '1.0',
            'created_at': datetime.datetime.now().isoformat()
        }
    
    def _dict_to_config(self, config_dict: Dict) -> AppConfig:
        """Convert dictionary to AppConfig."""
        # Load zones
        zones = []
        for zone_data in config_dict.get('zones', []):
            zone = Zone(
                name=zone_data['name'],
                coords=tuple(zone_data['coords']),
                zone_type=zone_data['zone_type'],
                color=tuple(zone_data['color'])
            )
            zones.append(zone)
        
        # Load bowls
        bowls = {}
        for name, bowl_data in config_dict.get('bowls', {}).items():
            bowl = BowlLocation(
                name=bowl_data['name'],
                position=tuple(bowl_data['position']),
                radius=bowl_data.get('radius', 30),
                color=tuple(bowl_data.get('color', (255, 0, 0)))
            )
            bowls[name] = bowl
        
        # Load performance settings
        perf_data = config_dict.get('performance', {})
        performance = PerformanceSettings(
            mode=perf_data.get('mode', 'balanced'),
            display_fps=perf_data.get('display_fps', 30.0),
            detection_cache_frames=perf_data.get('detection_cache_frames', 3),
            stats_update_frequency=perf_data.get('stats_update_frequency', 10),
            heatmap_update_frequency=perf_data.get('heatmap_update_frequency', 10),
            frame_skip_ratio=perf_data.get('frame_skip_ratio', 1)
        )
        
        return AppConfig(
            zones=zones,
            bowls=bowls,
            performance=performance,
            confidence_threshold=config_dict.get('confidence_threshold', 0.5),
            alert_cooldown=config_dict.get('alert_cooldown', 60),
            email_config=config_dict.get('email_config'),
            model_path=config_dict.get('model_path', 'models/yolo12n.pt')
        )
    
    def create_default_config(self) -> AppConfig:
        """Create a default configuration."""
        return AppConfig(
            zones=[],
            bowls={},
            performance=PerformanceSettings.from_mode("balanced"),
            confidence_threshold=0.5,
            alert_cooldown=60,
            email_config=None,
            model_path="models/yolo12n.pt"
        )


class ReportGenerator:
    """Generates various types of reports from activity data."""
    
    def __init__(self, statistics: ActivityStatistics):
        self.statistics = statistics
    
    def generate_text_report(self, file_path: str) -> bool:
        """Generate a text-based activity report."""
        try:
            report_data = self.statistics.get_summary_report()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            with open(file_path, 'w') as f:
                f.write("Pet Activity Tracker - Comprehensive Report\n")
                f.write("=" * 50 + "\n")
                f.write(f"Generated: {timestamp}\n\n")
                
                # Summary statistics
                f.write("SUMMARY STATISTICS\n")
                f.write("-" * 20 + "\n")
                summary = report_data['summary']
                for key, value in summary.items():
                    f.write(f"{key.replace('_', ' ').title()}: {value}\n")
                
                f.write("\nZONE STATISTICS\n")
                f.write("-" * 15 + "\n")
                for zone_stat in report_data['zone_statistics']:
                    f.write(f"Zone: {zone_stat['name']}\n")
                    f.write(f"  Visits: {zone_stat['visits']}\n")
                    f.write(f"  Duration: {zone_stat['duration']}\n\n")
                
                f.write("ACTIVITY TIMELINE (by hour)\n")
                f.write("-" * 25 + "\n")
                timeline = report_data['activity_timeline']
                for hour in range(24):
                    count = timeline.get(hour, 0)
                    if count > 0:
                        f.write(f"{hour:02d}:00 - {count} activities\n")
                
                f.write("\nRECENT ACTIVITIES\n")
                f.write("-" * 17 + "\n")
                for activity in report_data['recent_activities']:
                    f.write(f"{activity}\n")
            
            return True
            
        except Exception as e:
            print(f"Failed to generate text report: {e}")
            return False
    
    def generate_json_report(self, file_path: str) -> bool:
        """Generate a JSON report with all data."""
        try:
            report_data = self.statistics.export_to_dict()
            report_data['metadata'] = {
                'generated_at': datetime.datetime.now().isoformat(),
                'report_type': 'comprehensive_json',
                'version': '1.0'
            }
            
            with open(file_path, 'w') as f:
                json.dump(report_data, f, indent=4, default=str)
            
            return True
            
        except Exception as e:
            print(f"Failed to generate JSON report: {e}")
            return False
    
    def generate_csv_report(self, file_path: str) -> bool:
        """Generate CSV report with statistics."""
        # Add this check at the very beginning
        if not PANDAS_AVAILABLE:
            print("Pandas not available. Cannot generate CSV report.")
            return False
        
        try:
            # Import pandas only if available
            import pandas as pd
            
            report_data = self.statistics.get_summary_report()
            
            # Create DataFrame with various statistics
            data = []
            
            # Add summary stats
            summary = report_data['summary']
            for key, value in summary.items():
                data.append({
                    'Category': 'Summary',
                    'Metric': key.replace('_', ' ').title(),
                    'Value': value,
                    'Unit': 'count' if 'count' in key or key.endswith('s') else 'other'
                })
            
            # Add zone statistics
            for zone_stat in report_data['zone_statistics']:
                data.append({
                    'Category': 'Zone',
                    'Metric': f"{zone_stat['name']} - Visits",
                    'Value': zone_stat['visits'],
                    'Unit': 'count'
                })
                data.append({
                    'Category': 'Zone',
                    'Metric': f"{zone_stat['name']} - Duration",
                    'Value': zone_stat['total_seconds'],
                    'Unit': 'seconds'
                })
            
            # Add timeline data
            timeline = report_data['activity_timeline']
            for hour, count in timeline.items():
                if count > 0:
                    data.append({
                        'Category': 'Timeline',
                        'Metric': f"Hour {hour:02d}",
                        'Value': count,
                        'Unit': 'activities'
                    })
            
            # Create and save DataFrame
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            
            return True
            
        except Exception as e:
            print(f"Failed to generate CSV report: {e}")
            return False
        
    def generate_html_report(self, file_path: str) -> bool:
        """Generate an HTML report with styling."""
        try:
            report_data = self.statistics.get_summary_report()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Pet Activity Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                    h1, h2 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
                    .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }}
                    .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #4CAF50; }}
                    .stat-value {{ font-size: 2em; font-weight: bold; color: #2196F3; }}
                    .stat-label {{ color: #666; margin-top: 5px; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                    th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                    th {{ background-color: #4CAF50; color: white; }}
                    tr:nth-child(even) {{ background-color: #f2f2f2; }}
                    .alert {{ color: #d32f2f; font-weight: bold; }}
                    .timeline {{ margin: 20px 0; }}
                    .activity-log {{ background: #f8f9fa; padding: 15px; border-radius: 8px; max-height: 300px; overflow-y: auto; }}
                    .activity-item {{ margin: 5px 0; padding: 5px; border-left: 3px solid #2196F3; padding-left: 10px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>🐾 Pet Activity Report</h1>
                    <p><strong>Generated:</strong> {timestamp}</p>
                    
                    <h2>Summary Statistics</h2>
                    <div class="summary">
            """
            
            # Add summary cards
            summary = report_data['summary']
            for key, value in summary.items():
                if value is not None:
                    label = key.replace('_', ' ').title()
                    alert_class = ' alert' if 'violation' in key else ''
                    html_content += f"""
                        <div class="stat-card">
                            <div class="stat-value{alert_class}">{value}</div>
                            <div class="stat-label">{label}</div>
                        </div>
                    """
            
            html_content += """
                    </div>
                    
                    <h2>Zone Activity</h2>
                    <table>
                        <tr><th>Zone Name</th><th>Visits</th><th>Total Duration</th></tr>
            """
            
            # Add zone statistics
            for zone_stat in report_data['zone_statistics']:
                html_content += f"""
                    <tr>
                        <td>{zone_stat['name']}</td>
                        <td>{zone_stat['visits']}</td>
                        <td>{zone_stat['duration']}</td>
                    </tr>
                """
            
            html_content += """
                    </table>
                    
                    <h2>Activity Timeline</h2>
                    <div class="timeline">
            """
            
            # Add timeline
            timeline = report_data['activity_timeline']
            if timeline:
                for hour in range(24):
                    count = timeline.get(hour, 0)
                    if count > 0:
                        width = min(100, (count / max(timeline.values())) * 100)
                        html_content += f"""
                            <div style="margin: 5px 0;">
                                <span style="display: inline-block; width: 60px;">{hour:02d}:00</span>
                                <div style="display: inline-block; width: 200px; background: #e0e0e0; border-radius: 3px;">
                                    <div style="width: {width}%; background: #4CAF50; height: 20px; border-radius: 3px; display: flex; align-items: center; padding-left: 5px; color: white; font-size: 12px;">
                                        {count}
                                    </div>
                                </div>
                            </div>
                        """
            else:
                html_content += "<p>No activity data available</p>"
            
            html_content += """
                    </div>
                    
                    <h2>Recent Activities</h2>
                    <div class="activity-log">
            """
            
            # Add recent activities
            for activity in report_data['recent_activities'][-20:]:  # Last 20
                alert_class = 'style="border-left-color: #d32f2f; background: #ffebee;"' if 'ALERT' in activity else ''
                html_content += f'<div class="activity-item" {alert_class}>{activity}</div>'
            
            html_content += """
                    </div>
                </div>
            </body>
            </html>
            """
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"Failed to generate HTML report: {e}")
            return False


class DataExporter:
    """Exports various types of data for external analysis."""
    
    @staticmethod
    def export_statistics_csv(statistics, file_path: str) -> bool:
        """Export statistics to CSV format."""
        if not PANDAS_AVAILABLE:
            print("Pandas not available. Cannot export to CSV format.")
            return False
        
        try:
            import pandas as pd
            
            # Convert statistics to DataFrame
            stats_data = []
            for key, value in statistics.stats.items():
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        stats_data.append({
                            'category': key,
                            'metric': sub_key,
                            'value': sub_value
                        })
                else:
                    stats_data.append({
                        'category': 'general',
                        'metric': key,
                        'value': value
                    })
            
            df = pd.DataFrame(stats_data)
            df.to_csv(file_path, index=False)
            return True
            
        except Exception as e:
            print(f"Failed to export statistics: {e}")
            return False
        
    @staticmethod
    def export_activity_log_csv(statistics: ActivityStatistics, file_path: str) -> bool:
        """Export activity log to CSV."""
        try:
            activities = list(statistics.activity_log)
            
            # Parse timestamp and message from each log entry
            data = []
            for activity in activities:
                if ': ' in activity:
                    timestamp_str, message = activity.split(': ', 1)
                    data.append({
                        'timestamp': timestamp_str,
                        'message': message,
                        'is_alert': 'ALERT' in message
                    })
                else:
                    data.append({
                        'timestamp': '',
                        'message': activity,
                        'is_alert': False
                    })
            
            df = pd.DataFrame(data)
            df.to_csv(file_path, index=False)
            return True
            
        except Exception as e:
            print(f"Failed to export activity log: {e}")
            return False
    
    @staticmethod
    def backup_application_data(config: AppConfig, statistics: ActivityStatistics, 
                               backup_dir: str) -> bool:
        """Create a complete backup of application data."""
        try:
            # Create backup directory
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(backup_dir, f"pet_tracker_backup_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # Save configuration
            config_manager = ConfigurationManager()
            config_manager.save_config(config, os.path.join(backup_path, "config.json"))
            
            # Save statistics
            report_generator = ReportGenerator(statistics)
            report_generator.generate_json_report(os.path.join(backup_path, "statistics.json"))
            
            # Export CSV data
            DataExporter.export_statistics_csv(statistics, os.path.join(backup_path, "stats.csv"))
            DataExporter.export_activity_log_csv(statistics, os.path.join(backup_path, "activities.csv"))
            
            # Create backup info file
            backup_info = {
                'created_at': datetime.datetime.now().isoformat(),
                'version': '1.0',
                'files': ['config.json', 'statistics.json', 'stats.csv', 'activities.csv']
            }
            
            with open(os.path.join(backup_path, "backup_info.json"), 'w') as f:
                json.dump(backup_info, f, indent=4)
            
            print(f"✓ Backup created at: {backup_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to create backup: {e}")
            return False