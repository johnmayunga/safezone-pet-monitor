# SafeZone Pet Monitor: Intelligent Access Control System for Enhanced Home Safety

An intelligent computer vision-based pet monitoring system that provides real-time pet detection, customizable zone-based access control, and comprehensive activity analysis for enhanced home safety.

![Python](https://img.shields.io/badge/python-v3.11+-blue.svg)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green.svg)
![YOLO](https://img.shields.io/badge/YOLO-v12-red.svg)
![License](https://img.shields.io/badge/license-GNU-blue.svg)

## 🐾 Features

### Core Functionality
- **Real-time Pet Detection**: Uses YOLO12 deep learning model for accurate cat and dog detection
- **Customizable Zone Management**: Define restricted, normal, and feeding areas with intuitive drawing interface
- **Multi-channel Alerts**: Audio and email notifications for zone violations
- **Activity Analytics**: Track eating, drinking, zone visits, and movement patterns
- **Performance Optimization**: Four performance modes from high-quality to ultra-performance for various hardware

### Advanced Features
- **Movement Heatmaps**: Visualize pet activity patterns over time
- **Behavioral Analysis**: Monitor feeding habits, zone preferences, and activity timelines
- **Multi-threaded Architecture**: Responsive UI with background processing
- **Comprehensive Reporting**: Export data in JSON, HTML, CSV, and Excel formats
- **Configuration Management**: Save and load custom setups

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Webcam or video files for processing
- Minimum 4GB RAM (8GB recommended for optimal performance)

### Folder structure
pet_activity_tracker/
├── 📄 main.py                           # Application entry point
├── 📄 requirements.txt                  # Python dependencies
├── 📄 README.md                         # Project documentation
├── 📄 .gitignore                        # Git ignore rules
├── 📄 LICENSE                           # Project license
│
├── 📁 config/                           # Configuration files
│   ├── 📄 __init__.py
│   ├── 📄 default_config.json          # Default application settings
│
├── 📁 models/                           # YOLO model files
│   ├── 📄 __init__.py
│   ├── 📄 yolo12n.pt                   # Main YOLO model
│
├── 📁 backend/                          # Core backend logic
│   ├── 📄 __init__.py
│   │
│   ├── 📁 core/                         # Core detection and tracking
│   │   ├── 📄 __init__.py
│   │   ├── 📄 detector.py               # YOLO pet detection
│   │    └── 📄 tracker.py                # Activity tracking and zone monitoring
│   │
│   ├── 📁 data/                         # Data models and statistics
│   │   ├── 📄 __init__.py
│   │   ├── 📄 models.py                 # Data classes (Zone, Bowl, Detection, etc.)
│   │   └── 📄 statistics.py             # Activity statistics management
│   │
│   ├── 📁 services/                     # External services
│   │   ├── 📄 __init__.py
│   │   ├── 📄 email_service.py          # Email notification service
│   │   └── 📄 sound_service.py          # Sound alert service
│   │
│   └── 📁 utils/                        # Utility functions
│       ├── 📄 __init__.py
│       ├── 📄 io_utils.py               # File I/O and configuration management
│       └── 📄 video_utils.py            # Video processing utilities
│
├── 📁 frontend/                         # GUI and user interface
│   ├── 📄 __init__.py
│   ├── 📄 app.py                        # Main application coordinator
│   │
│   ├── 📁 components/                   # Reusable UI components
│   │   ├── 📄 __init__.py
│   │   ├── 📄 video_display.py          # Video display panel
│   │   ├── 📄 control_panel.py          # Control buttons and settings
│   │   └── 📄 statistics_panel.py       # Statistics and metrics display
│   │
│   ├── 📁 utils/                        # Utility functions
│   │   ├── 📄 __init__.py
│   │   └── 📄 styling.py
│   │
│   └── 📁 dialogs/                      # Configuration dialogs
│       ├── 📄 __init__.py
│       ├── 📄 zone_dialog.py            # Zone configuration dialog
│       ├── 📄 bowl_dialog.py            # Bowl placement dialog
│       ├── 📄 email_dialog.py           # Email settings dialog
│       └── 📄 alert_dialog.py           # Alert configuration dialog
│
├── 📁 tests/                            # Unit tests and testing
│   ├── 📁 fixtures/
│   │   ├── 📄 sample_detections.json    # Test files to posit testing objects
│   │   └── 📄 test_config.json          # Auto generated file for test saving config if works
│   │
│   ├── 📁 mocks/
│   │   ├── 📄 __init__.py
│   │   ├── 📄 mock_detector.py          # Mock Detector
│   │   └── 📄 mock_video_capture.py     # Mock Video capture
│   │
│   ├── 📄 __init__.py
│   ├── 📄 test_detector.py              # Test pet detection
│   ├── 📄 test_tracker.py               # Test activity tracking
│   ├── 📄 test_statistics.py            # Test statistics functionality
│   └── 📄 test_email_service.py         # Test email notifications
│
└── 📁 test_videos/                      # Sample videos for testing
   ├── 📄 TestingVideo1.MOV
   └── 📄 TestingVideo2.MOV

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/johnmayunga/safezone-pet-monitor.git
cd safezone-pet-monitor
```

2. **Install required dependencies:**
```bash
pip install -r requirements.txt
```

**Or install manually:**
```bash
pip install opencv-python ultralytics matplotlib pillow numpy pygame tkinter pandas
```

3. **Download YOLO model** (automatic on first run):
```bash
python main.py
```

### Run test
**This will excecute all test functions and provide you with test results in console
```bash
python tests/__init__.py
```

### Basic Usage

1. **Launch the application:**
```bash
python main.py
```

2. **Load video source:**
   - Use **File → Open Video** for video files
   - Use **File → Use Camera** for live webcam feed

3. **Configure zones** (optional):
   - Go to **Settings → Configure Zones**
   - Click "Draw Zone" and click points on video to create areas
   - Right-click or press "Finish Zone" to complete

4. **Set bowl locations** (optional):
   - Go to **Settings → Set Bowl Locations**
   - Click "Add Food Bowl" or "Add Water Bowl"
   - Click on video where bowls are located
   - You can also drag the bowl to reposit

5. **Start tracking:**
   - Click the **Start** button
   - Monitor real-time detection and alerts

## Performance Modes

Choose the optimal performance mode for your hardware:

| Mode            | Detection Accuracy | Processing Speed | Resource Usage | Best For                 |
|-----------------|--------------------|------------------|----------------|--------------------------|
| **Quality**     | 94.8%              | 16 FPS           | High           | High-end systems         |
| **Balanced**    | 92.3%              | 30 FPS           | Medium         | Most computers           |
| **Performance** | 87.5%              | 45 FPS           | Low            | Older hardware           |
| **Ultra**       | 80.2%              | 60+ FPS          | Very Low       | Resource-limited devices |

## Zone Types

- **Restricted Zones**: Areas where pets shouldn't enter (triggers alerts)
- **Normal Zones**: Regular living areas (kitchen, bedroom, living room)
- **Feeding Areas**: Designated locations for food and water

## Configuration

### Email Notifications
1. Go to **Settings → Email Notifications**
2. Enter Gmail credentials (use App Passwords for security)
3. Set recipient email address
4. Test configuration
5. Save

### Alert Settings
- Adjust alert cooldown periods
- Set Alert Duration
- Enable/disable specific alert types
- Test audio alerts

### Zone Drawing
1. Select zone type (restricted, kitchen, etc.)
2. Click "Draw Zone" 
3. Click points on video to create polygon
4. Right-click or "Finish Zone" to complete
5. Zones can be deleted or modified later

## Analytics & Reporting

### Real-time Statistics
- Total pet detections
- Eating and drinking events
- Zone violation counts
- Activity timelines

### Visual Analytics
- **Heatmaps**: See where pets spend most time
- **Timeline Charts**: Activity patterns by hour
- **Zone Statistics**: Visit frequency and duration

### Export Options
- **JSON**: Raw data for further analysis
- **HTML**: Formatted reports with charts
- **CSV/Excel**: Spreadsheet-compatible data
- **Activity Logs**: Timestamped event history

## Technical Details

### Architecture
- **Multi-threaded Design**: Separate threads for capture, processing, and display
- **Optimized Detection**: Adaptive frame processing and result caching
- **Memory Management**: Bounded queues and garbage collection
- **Cross-platform**: Supports Windows, macOS, and Linux

### Optimization Techniques
- **Detection Caching**: Reuse YOLO results across frames
- **Frame Skipping**: Process subset of frames based on performance mode
- **Adaptive Scaling**: Dynamic resolution adjustment
- **Pre-computed Overlays**: Efficient zone and UI rendering

### Supported Formats
- **Video Input**: MP4, AVI, MOV, MKV
- **Live Sources**: USB webcams
- **Export Formats**: JSON, HTML, CSV, Excel, PDF

## Troubleshooting

### Common Issues

**1. "Could not open video source"**
- Check camera permissions
- Verify video file format
- Try different video source

**2. "Audio system initialization failed"**
- Audio alerts will be disabled
- Visual alerts still work
- Install pygame: `pip install pygame`

**3. Low detection accuracy**
- Ensure good lighting
- Check confidence threshold (default: 0.5)
- Try higher performance mode

**4. High CPU usage**
- Switch to "Performance" or "Ultra" mode
- Reduce video resolution
- Close other applications

### Performance Tips
- Use "Balanced" mode for most applications
- Enable GPU acceleration if available
- Ensure adequate lighting for better detection
- Position camera for clear pet visibility

## System Requirements

### Recommended Requirements
- Python 3.11+
- 8GB RAM
- GPU with CUDA support (optional)
- 1GB disk space
- HD webcam (720p+)

### Supported Platforms
- Windows 10/11
- macOS 10.15+
- Ubuntu 18.04+
- Raspberry Pi 4 (with optimizations)

## Configuration Files

### Auto-saved Configuration
The application automatically saves configuration to:
```
config/default_config.json
```

### Manual Configuration
Save/load custom configurations via:
- **File → Save Configuration**
- **File → Load Configuration**

### Configuration Contents
- Zone definitions and coordinates
- Bowl locations and types
- Performance settings
- Alert preferences
- Detection thresholds

## License

This project is licensed under the GNU GENERAL PUBLIC LICENSE - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **Ultralytics YOLO**: State-of-the-art object detection
- **OpenCV**: Computer vision library
- **Python Community**: Amazing ecosystem

## Bug Reports

Found a bug? Please create an issue with:
- System information (OS, Python version)
- Steps to reproduce
- Expected vs actual behavior
- Screenshots or logs if helpful
---

**Happy Pet Monitoring! 🐕🐱**