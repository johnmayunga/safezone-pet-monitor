"""
frontend/app.py
Main frontend application class that coordinates all GUI components.
"""
import tkinter as tk
from tkinter import messagebox, filedialog
import threading
import time
import queue
import gc
import pandas as pd
import os

# Backend imports
from backend.core.detector import PetDetector
from backend.core.tracker import PetActivityTracker
from backend.data.statistics import ActivityStatistics
from backend.data.models import AppConfig, PerformanceSettings
from backend.services.email_service import EmailNotificationService, EmailConfig
from backend.services.sound_service import SoundAlertService
from backend.utils.io_utils import ConfigurationManager, ReportGenerator
from backend.utils.video_utils import VideoCapture

# Frontend components
from .components.video_display import VideoDisplayPanel
from .components.control_panel import ControlPanel
from .components.statistics_panel import StatisticsPanel
from .dialogs.zone_dialog import ZoneConfigDialog
from .dialogs.bowl_dialog import BowlConfigDialog
from .dialogs.email_dialog import EmailConfigDialog
from .dialogs.alert_dialog import AlertConfigDialog

# Import modern styling
try:
    from .utils.styling import apply_modern_styling, modern_style
    STYLING_AVAILABLE = True
except ImportError:
    STYLING_AVAILABLE = False
    print("Warning: Modern styling not available")

class PetTrackerApplication:
    """Main application class that orchestrates all components."""
    
    def __init__(self):
        # Initialize backend services
        self.statistics = ActivityStatistics()
        self.tracker = PetActivityTracker(self.statistics)
        self.detector = PetDetector()
        self.email_service = EmailNotificationService()
        self.sound_service = SoundAlertService()
        self.config_manager = ConfigurationManager()
        
        # Application state
        self.config = self.config_manager.create_default_config()
        self.running = False
        self.video_capture = None
        self.processing_thread = None
        self.shutdown_event = threading.Event()
        
        # Frame processing queues
        self.frame_queue = queue.Queue(maxsize=30)
        self.processed_frame_queue = queue.Queue(maxsize=10)
        
        # Performance tracking
        self.fps_counter = 0
        self.last_fps_time = time.time()
        
        # GUI components
        self.root = None
        self.video_display = None
        self.control_panel = None
        self.statistics_panel = None
        
        # Load default configuration if available
        self._load_default_config()
        
        # Initialize GUI
        self._setup_gui()
    
    def _load_default_config(self):
        """Load default configuration if it exists."""
        config = self.config_manager.load_config()
        if config:
            self.config = config
            self._apply_config_to_services()
    
    def _apply_config_to_services(self):
        """Apply configuration to backend services."""
        # Update detector settings
        self.detector.update_confidence_threshold(self.config.confidence_threshold)
        self.detector.update_performance_settings(self.config.performance)
        
        # Update tracker with zones and bowls
        self.tracker.update_zones(self.config.zones)
        self.tracker.update_bowls(self.config.bowls)
        
        # Configure email service if config exists
        if self.config.email_config:
            try:
                email_config_obj = self.config.get_email_config_object()
                if email_config_obj:
                    self.email_service.configure(email_config_obj)
            except Exception as e:
                print(f"Warning: Failed to configure email service: {e}")
                # Continue without email service rather than crash
    
    def _setup_gui(self):
        """Initialize the main GUI."""
        self.root = tk.Tk()
        self.root.title("Pet Activity Tracker")
        self.root.minsize(1200, 800)
        self.root.geometry("1400x900")

        # Apply modern styling
        if STYLING_AVAILABLE:
            print(f"Platform detected: {modern_style.platform}")
            print(f"Fonts available: {modern_style.fonts}")

            self.style = apply_modern_styling(self.root)
            modern_style.apply_window_styling(self.root)

            # Configure window background for Windows
            if modern_style.is_windows:
                self.root.configure(bg=modern_style.get_color('bg_secondary'))

            # Test if styling actually worked
            if modern_style.styling_applied:
                print("✅ Modern styling successfully applied!")
                
                # Configure window background for all platforms
                self.root.configure(bg=modern_style.get_color('bg_secondary'))
            else:
                print("⚠️ Modern styling partially failed, using fallbacks")
        else:
            print("❌ Modern styling not available - using default theme")
            
        # Configure grid weights
        self.root.grid_rowconfigure(1, weight=3)
        self.root.grid_rowconfigure(2, weight=1)
        self.root.grid_columnconfigure(0, weight=6)
        self.root.grid_columnconfigure(1, weight=1)
        
        # Create menu bar
        self._create_menu_bar()
        
        # Initialize GUI components
        self._create_gui_components()

        # Status bar with modern styling
        if STYLING_AVAILABLE:
            self.status_bar = tk.Label(
                self.root, 
                text="Ready", 
                relief=tk.FLAT, 
                anchor=tk.W,
                font=modern_style.get_font('small'),
                bg=modern_style.get_color('bg_tertiary'),
                fg=modern_style.get_color('text_secondary'),
                pady=5, padx=10
            )
        else:
            self.status_bar = tk.Label(self.root, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        
        # Status bar
        self.status_bar.grid(row=3, column=0, columnspan=2, sticky="ew")
        
        # Bind window close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        
        # Initialize sound system after GUI is ready
        self.root.after(1000, self.sound_service.initialize)
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open Video", command=self._open_video)
        file_menu.add_command(label="Use Camera", command=self._use_camera)
        file_menu.add_separator()
        file_menu.add_command(label="Save Report", command=self._save_report)
        file_menu.add_command(label="Export Statistics", command=self._export_statistics)
        file_menu.add_separator()
        file_menu.add_command(label="Save Configuration", command=self._save_configuration)
        file_menu.add_command(label="Load Configuration", command=self._load_configuration)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self._on_closing)
        
        # Settings menu
        settings_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Settings", menu=settings_menu)
        settings_menu.add_command(label="Configure Zones", command=self._configure_zones)
        settings_menu.add_command(label="Set Bowl Locations", command=self._configure_bowls)
        settings_menu.add_command(label="Email Notifications", command=self._configure_email)
        settings_menu.add_command(label="Alert Settings", command=self._configure_alerts)
        
        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Heatmap", command=self._show_heatmap)
        view_menu.add_command(label="Activity Timeline", command=self._show_timeline)
        view_menu.add_command(label="Zone Statistics", command=self._show_zone_stats)
    
    def _create_gui_components(self):
        """Create all GUI components."""
        # Control panel
        self.control_panel = ControlPanel(
            self.root, 
            row=0, 
            column=0, 
            columnspan=2,
            start_callback=self._start_tracking,
            pause_callback=self._pause_tracking,
            stop_callback=self._stop_tracking,
            performance_callback=self._update_performance_mode,
            confidence_callback=self._update_confidence_threshold
        )
        
        # Video display panel
        self.video_display = VideoDisplayPanel(
            self.root,
            row=1,
            column=0,
            click_callback=self._on_video_click,
            motion_callback=self._on_video_motion,
            drag_callback=self._on_video_drag,
            release_callback=self._on_video_release
        )
        
        # Statistics panel
        self.statistics_panel = StatisticsPanel(
            self.root,
            row=1,
            column=1,
            statistics=self.statistics
        )
        
        # Activity log
        self._create_activity_log()
    
    def _create_activity_log(self):
        """Create the activity log panel."""
        import tkinter.ttk as ttk
        
        log_frame = ttk.LabelFrame(self.root, text="Activity Log", padding=10)
        log_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=5, sticky="nsew")
        
        log_frame.grid_rowconfigure(0, weight=1)
        log_frame.grid_columnconfigure(0, weight=1)
        
        # Create text widget with scrollbar
        self.log_text = tk.Text(log_frame, height=8, width=80)
        scrollbar = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=scrollbar.set)
        
        self.log_text.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        
        # Log controls
        log_controls = ttk.Frame(log_frame)
        log_controls.grid(row=1, column=0, columnspan=2, pady=5)
        
        ttk.Button(log_controls, text="Clear Log", command=self._clear_log).pack(side="left", padx=5)
        ttk.Button(log_controls, text="Export Log", command=self._export_log).pack(side="left", padx=5)
    
    def _start_tracking(self):
        """Start pet tracking."""
        if not self.video_capture:
            messagebox.showwarning("Warning", "Please load a video source first")
            return
        
        # Clear processing queues
        while not self.frame_queue.empty():
            try:
                self.frame_queue.get_nowait()
            except queue.Empty:
                break
        
        while not self.processed_frame_queue.empty():
            try:
                self.processed_frame_queue.get_nowait()
            except queue.Empty:
                break
        
        # Reset detector cache
        self.detector.clear_cache()
        
        # Start processing
        self.running = True
        self.shutdown_event.clear()
        
        # Start processing thread
        self.processing_thread = threading.Thread(target=self._processing_loop, daemon=True)
        self.processing_thread.start()
        
        # Update GUI
        self.control_panel.set_tracking_state(True)
        self.status_bar.config(text="Tracking started")
    
    def _pause_tracking(self):
        """Pause pet tracking."""
        self.running = False
        self.control_panel.set_tracking_state(False, paused=True)
        self.status_bar.config(text="Tracking paused")
    
    def _stop_tracking(self):
        """Stop pet tracking."""
        self.running = False
        self.shutdown_event.set()
        
        # Wait for processing thread to finish
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=2.0)
        
        # Release video capture
        if self.video_capture:
            self.video_capture.release()
            self.video_capture = None
        
        # Update GUI
        self.control_panel.set_tracking_state(False)
        self.status_bar.config(text="Tracking stopped")
        
        # Force garbage collection
        gc.collect()
    
    def _processing_loop(self):
        """Main processing loop running in background thread."""
        frame_number = 0
        last_fps_update = time.time()
        
        while self.running and not self.shutdown_event.is_set():
            try:
                # Read frame from video capture
                ret, frame = self.video_capture.read()
                if not ret:
                    # End of video or error
                    if self.video_capture.get_properties()['is_camera']:
                        continue  # Keep trying for camera
                    else:
                        # Video file ended
                        self.root.after(0, lambda: self._stop_tracking())
                        break
                
                # Set frame shape for tracker
                self.tracker.set_frame_shape(frame.shape[:2])
                
                # Detect pets
                detections = self.detector.detect_pets(frame, frame_number)
                
                # Process detections with tracker
                activity_results = self.tracker.process_detections(detections)
                
                # Handle alerts
                self._handle_activity_alerts(activity_results)
                
                # Draw overlays
                processed_frame = self._draw_all_overlays(frame, detections)
                
                # Add to processed frame queue
                if not self.processed_frame_queue.full():
                    self.processed_frame_queue.put(processed_frame)
                
                # Update display
                self.root.after_idle(self._update_display)
                
                # Update FPS counter
                self.fps_counter += 1
                current_time = time.time()
                if current_time - last_fps_update >= 1.0:
                    fps = self.fps_counter / (current_time - last_fps_update)
                    self.root.after(0, lambda f=fps: self.control_panel.update_fps(f))
                    self.fps_counter = 0
                    last_fps_update = current_time
                
                frame_number += 1
                
                # Small delay to prevent CPU overload
                time.sleep(0.001)
                
            except Exception as e:
                print(f"Processing error: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(0.1)
    
    def _draw_all_overlays(self, frame, detections):
        """Draw all overlays on the frame."""
        # Draw detections
        if detections:
            frame = self.detector.draw_detections(frame, detections)
        
        # Draw zones
        frame = self.tracker.draw_zones(frame)
        
        # Draw bowls
        frame = self.tracker.draw_bowls(frame)
        
        return frame
    
    def _update_display(self):
        """Update video display with latest processed frame."""
        if not self.processed_frame_queue.empty():
            try:
                frame = self.processed_frame_queue.get_nowait()
                self.video_display.update_frame(frame)
                
                # Update statistics panel periodically
                if self.fps_counter % 30 == 0:  # Every 30 frames
                    self.statistics_panel.update_display()
                
            except queue.Empty:
                pass
    
    def _handle_activity_alerts(self, activity_results):
        """Handle alerts from activity detection."""
        for zone_activity in activity_results.get('zone_activities', []):
            if zone_activity.get('alert'):
                # Restricted zone alert
                self._send_alert(
                    "restricted_zone",
                    f"Restricted Zone Alert",
                    f"{zone_activity['pet_type']} entered {zone_activity['zone']}"
                )
        
        # Add activity to log
        for activity in activity_results.get('zone_activities', []) + activity_results.get('bowl_activities', []):
            message = self._format_activity_message(activity)
            if message:
                self._add_to_activity_log(message)
    
    def _format_activity_message(self, activity):
        """Format activity for logging."""
        action = activity.get('action', '')
        pet_type = activity.get('pet_type', 'pet')
        
        if 'zone' in activity:
            zone_name = activity['zone']
            if action == 'entry':
                return f"{pet_type} entered zone: {zone_name}"
            elif action == 'exit':
                return f"{pet_type} left zone: {zone_name}"
        
        elif 'bowl' in activity:
            bowl_name = activity['bowl']
            if action == 'eating':
                return f"{pet_type} started eating at {bowl_name} bowl"
            elif action == 'drinking':
                return f"{pet_type} started drinking at {bowl_name} bowl"
            elif action == 'finished':
                return f"{pet_type} finished activity at {bowl_name} bowl"
        
        return None
    
    def _add_to_activity_log(self, message):
        """Add message to activity log."""
        timestamp = time.strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        
        self.log_text.insert(tk.END, log_entry + "\n")
        self.log_text.see(tk.END)
    
    def _send_alert(self, alert_type, subject, message):
        """Send alert via configured services."""
        # Play sound alert
        if alert_type == "restricted_zone":
            self.sound_service.play_restricted_zone_alert()
        else:
            self.sound_service.play_general_alert()
        
        # Send email alert
        self.email_service.send_alert(alert_type, subject, message)
        
        # Log alert
        self._add_to_activity_log(f"ALERT: {message}")
    
    def _update_performance_mode(self, mode):
        """Update performance mode."""
        self.config.performance = PerformanceSettings.from_mode(mode)
        self.detector.update_performance_settings(self.config.performance)
    
    def _update_confidence_threshold(self, threshold):
        """Update detection confidence threshold."""
        self.config.confidence_threshold = threshold
        self.detector.update_confidence_threshold(threshold)
    
    # Video source methods
    def _open_video(self):
        """Open video file."""
        file_path = filedialog.askopenfilename(
            title="Select Video File",
            filetypes=[("Video files", "*.mp4 *.avi *.mov *.mkv *.wmv")]
        )
        
        if file_path:
            self._load_video_source(file_path)
    
    def _use_camera(self):
        """Use camera as video source."""
        self._load_video_source(0)
    
    def _load_video_source(self, source):
        """Load video source."""
        if self.running:
            self._stop_tracking()
        
        # Release existing capture
        if self.video_capture:
            self.video_capture.release()
        
        # Create new capture
        self.video_capture = VideoCapture(source)
        
        if not self.video_capture.open():
            messagebox.showerror("Error", "Could not open video source")
            return
        
        # Update displays
        self._update_video_draggable_items()
        
        # Get first frame for display
        ret, frame = self.video_capture.read()
        if ret:
            # Draw initial overlays
            frame_with_overlays = self._draw_all_overlays(frame, [])
            self.video_display.update_frame(frame_with_overlays)
            
            # Reset video position for file sources
            if source != 0:  # Not camera
                self.video_capture.set_position(0)
        
        # Update status
        source_name = "Camera" if source == 0 else os.path.basename(str(source))
        self.status_bar.config(text=f"Loaded: {source_name}")
    
    def _update_video_overlays(self):
        """Update video overlays with current zones and bowls."""
        if hasattr(self, 'video_display') and self.video_display:
            # This will trigger a redraw of overlays on the next frame
            pass
    
    # Event handlers
    def _on_video_click(self, event, canvas_coords, video_coords):
        """Handle video canvas click."""
        # Pass click to appropriate dialog if open
        if hasattr(self, '_zone_dialog') and self._zone_dialog.winfo_exists():
            self._zone_dialog.handle_canvas_click(video_coords)
        elif hasattr(self, '_bowl_dialog') and self._bowl_dialog.winfo_exists():
            self._bowl_dialog.handle_canvas_click(video_coords)
    
    def _on_video_motion(self, event, canvas_coords, video_coords):
        """Handle video canvas motion."""
        # Update cursor position display
        self.status_bar.config(text=f"Position: ({int(video_coords[0])}, {int(video_coords[1])})")
    
    def _on_video_drag(self, event, canvas_coords, video_coords, drag_info=None):
        """Handle video canvas drag."""
        if drag_info and 'item' in drag_info:
            # Bowl or other item is being dragged
            item = drag_info['item']
            new_position = drag_info['new_position']
            
            if item['type'] == 'bowl':
                # Update bowl position in real-time
                bowl_name = item['id']
                if bowl_name in self.config.bowls:
                    # Temporarily update position for visual feedback
                    self.config.bowls[bowl_name].position = (int(new_position[0]), int(new_position[1]))
                    
                    # Update the draggable items for the video display
                    self._update_video_draggable_items()
        
        # Update cursor position display
        self.status_bar.config(text=f"Dragging to: ({int(video_coords[0])}, {int(video_coords[1])})")
    
    def _on_video_release(self, event, dragging_item, final_position):
        """Handle video canvas mouse release after dragging."""
        if dragging_item and dragging_item['type'] == 'bowl':
            bowl_name = dragging_item['id']
            
            if bowl_name in self.config.bowls:
                # Finalize the bowl position
                old_position = dragging_item['original_position']
                new_position = (int(final_position[0]), int(final_position[1]))
                
                # Update the bowl's actual position
                self.config.bowls[bowl_name].position = new_position
                
                # Update the tracker with new bowl positions
                self.tracker.update_bowls(self.config.bowls)
                
                # Log the change
                self._add_to_activity_log(
                    f"Bowl '{bowl_name}' moved from {old_position} to {new_position}"
                )
                
                # Update status
                self.status_bar.config(
                    text=f"Bowl '{bowl_name}' repositioned to ({new_position[0]}, {new_position[1]})"
                )
                
                # Update video display
                self._update_video_draggable_items()
        
        # Clear dragging cursor
        try:
            self.video_display.canvas.configure(cursor="")
        except:
            pass
    
    def _update_video_draggable_items(self):
        """Update the video display with current draggable items (bowls)."""
        draggable_items = {}
        
        # Add bowls as draggable items
        for bowl_name, bowl in self.config.bowls.items():
            draggable_items[bowl_name] = {
                'type': 'bowl',
                'position': bowl.position,
                'radius': bowl.radius,
                'color': bowl.color
            }
        
        # Set draggable items in video display
        self.video_display.set_draggable_items(draggable_items)
    
    # Configuration dialogs
    def _configure_zones(self):
        """Open zone configuration dialog."""
        self._zone_dialog = ZoneConfigDialog(
            self.root,
            zones=self.config.zones,
            video_display=self.video_display,
            save_callback=self._update_zones_config
        )
    
    def _configure_bowls(self):
        """Open bowl configuration dialog."""
        self._bowl_dialog = BowlConfigDialog(
            self.root,
            bowls=self.config.bowls,
            video_display=self.video_display,
            save_callback=self._update_bowls_config
        )
    
    def _configure_email(self):
        """Open email configuration dialog."""
        email_dialog = EmailConfigDialog(
            self.root,
            current_config=self.config.email_config,
            save_callback=self._update_email_config,
            test_callback=self._test_email_config
        )
    
    def _configure_alerts(self):
        """Open alert configuration dialog."""
        alert_dialog = AlertConfigDialog(
            self.root,
            sound_service=self.sound_service,
            email_service=self.email_service,
            current_cooldown=self.config.alert_cooldown,
            save_callback=self._update_alert_config
        )
    
    # Configuration update callbacks
    def _update_zones_config(self, zones):
        """Update zones configuration."""
        self.config.zones = zones
        self.tracker.update_zones(zones)
        self.tracker.invalidate_cache()
    
    def _update_bowls_config(self, bowls):
        """Update bowls configuration."""
        self.config.bowls = bowls
        self.tracker.update_bowls(bowls)
        
        # Update draggable items in video display
        self._update_video_draggable_items()
    
    def _update_email_config(self, email_config):
        """Update email configuration."""
        self.config.email_config = email_config
        if email_config:
            # Create EmailConfig object with all required fields
            config_obj = EmailConfig(
                sender_email=email_config["sender_email"],
                sender_password=email_config["sender_password"],
                recipient_email=email_config["recipient_email"],
                smtp_server=email_config.get("smtp_server", "smtp.gmail.com"),
                smtp_port=email_config.get("smtp_port", 587),
                enabled=email_config.get("enabled", True),
                notification_types=email_config.get("notification_types", {}),
                cooldown_period=email_config.get("cooldown_period", 300)
            )
            self.email_service.configure(config_obj)
    
    def _test_email_config(self, email_config):
        """Test email configuration."""
        # Create EmailConfig object for testing
        config_obj = EmailConfig(
            sender_email=email_config["sender_email"],
            sender_password=email_config["sender_password"],
            recipient_email=email_config["recipient_email"],
            smtp_server=email_config.get("smtp_server", "smtp.gmail.com"),
            smtp_port=email_config.get("smtp_port", 587),
            enabled=email_config.get("enabled", True),
            notification_types=email_config.get("notification_types", {}),
            cooldown_period=email_config.get("cooldown_period", 300)
        )
        
        # Configure the email service
        self.email_service.configure(config_obj)
        
        # Use the new send_test_email method that returns success status and error message
        success, error_message = self.email_service.send_test_email()
        
        if not success:
            # Return the error for the dialog to display
            raise Exception(error_message)
        
        return success
    
    def _update_alert_config(self, cooldown):
        """Update alert configuration."""
        self.config.alert_cooldown = cooldown
        self.email_service.set_cooldown_period(cooldown)
    
    # Data export methods
    def _save_report(self):
        """Save comprehensive report."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".html",
            filetypes=[
                ("HTML files", "*.html"),
                ("JSON files", "*.json"), 
                ("Text files", "*.txt")
            ]
        )
        
        if file_path:
            report_generator = ReportGenerator(self.statistics)
            
            if file_path.endswith('.html'):
                success = report_generator.generate_html_report(file_path)
            elif file_path.endswith('.json'):
                success = report_generator.generate_json_report(file_path)
            else:
                success = report_generator.generate_text_report(file_path)
            
            if success:
                messagebox.showinfo("Success", "Report saved successfully")
            else:
                messagebox.showerror("Error", "Failed to save report")
    
    def _export_statistics(self):
        """Export statistics data."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx")]
        )
        
        if file_path:
            from backend.utils.io_utils import DataExporter
            
            if file_path.endswith('.csv'):
                success = DataExporter.export_statistics_csv(self.statistics, file_path)
            else:
                success = DataExporter.export_activity_log_csv(self.statistics, file_path)
            
            if success:
                messagebox.showinfo("Success", "Statistics exported successfully")
            else:
                messagebox.showerror("Error", "Failed to export statistics")
    
    def _save_configuration(self):
        """Save current configuration."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            if self.config_manager.save_config(self.config, file_path):
                messagebox.showinfo("Success", "Configuration saved successfully")
            else:
                messagebox.showerror("Error", "Failed to save configuration")
    
    def _load_configuration(self):
        """Load configuration from file."""
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON files", "*.json")]
        )
        
        if file_path:
            config = self.config_manager.load_config(file_path)
            if config:
                self.config = config
                self._apply_config_to_services()
                messagebox.showinfo("Success", "Configuration loaded successfully")
            else:
                messagebox.showerror("Error", "Failed to load configuration")
    
    # Visualization methods
    def _show_heatmap(self):
        """Show movement heatmap."""
        if self.statistics.heatmap is None:
            messagebox.showwarning("Warning", "No heatmap data available")
            return
        
        import matplotlib.pyplot as plt
        
        plt.figure(figsize=(10, 8))
        plt.imshow(self.statistics.heatmap, cmap='hot', interpolation='nearest')
        plt.colorbar(label='Activity Intensity')
        plt.title('Pet Movement Heatmap')
        plt.xlabel('X Position')
        plt.ylabel('Y Position')
        
        # Mark zones on heatmap
        for zone in self.config.zones:
            x1, y1, x2, y2 = zone.coords
            rect = plt.Rectangle((x1, y1), x2-x1, y2-y1, 
                               fill=False, edgecolor='white', linewidth=2)
            plt.gca().add_patch(rect)
            plt.text(x1, y1, zone.name, color='white', fontsize=8)
        
        plt.tight_layout()
        plt.show()
    
    def _show_timeline(self):
        """Show activity timeline."""
        timeline = self.statistics.get_activity_timeline()
        if not timeline:
            messagebox.showwarning("Warning", "No timeline data available")
            return
        
        import matplotlib.pyplot as plt
        
        hours = list(range(24))
        counts = [timeline.get(hour, 0) for hour in hours]
        
        plt.figure(figsize=(12, 6))
        bars = plt.bar(hours, counts, color='skyblue', edgecolor='navy')
        
        # Highlight peak activity hours
        max_count = max(counts) if counts else 0
        for i, bar in enumerate(bars):
            if counts[i] == max_count and max_count > 0:
                bar.set_color('orange')
        
        plt.xlabel('Hour of Day')
        plt.ylabel('Activity Count')
        plt.title('Pet Activity Timeline')
        plt.xticks(hours)
        plt.grid(axis='y', alpha=0.3)
        
        plt.tight_layout()
        plt.show()
    
    def _show_zone_stats(self):
        """Show zone statistics."""
        zone_stats = self.statistics.get_zone_statistics()
        if not zone_stats:
            messagebox.showwarning("Warning", "No zone statistics available")
            return
        
        import matplotlib.pyplot as plt
        
        zones = [stat['name'] for stat in zone_stats]
        visits = [stat['visits'] for stat in zone_stats]
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Bar chart
        bars = ax1.bar(zones, visits, color='lightgreen', edgecolor='darkgreen')
        ax1.set_xlabel('Zones')
        ax1.set_ylabel('Visit Count')
        ax1.set_title('Zone Visit Frequency')
        ax1.tick_params(axis='x', rotation=45)
        
        # Pie chart
        ax2.pie(visits, labels=zones, autopct='%1.1f%%', startangle=90)
        ax2.set_title('Zone Visit Distribution')
        
        plt.tight_layout()
        plt.show()
    
    # Utility methods
    def _clear_log(self):
        """Clear activity log."""
        self.log_text.delete(1.0, tk.END)
    
    def _export_log(self):
        """Export activity log."""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        
        if file_path:
            try:
                log_content = self.log_text.get(1.0, tk.END)
                with open(file_path, 'w') as f:
                    f.write(log_content)
                messagebox.showinfo("Success", "Log exported successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export log: {e}")
    
    def _on_closing(self):
        """Handle application closing."""
        if self.running:
            self._stop_tracking()
        
        # Save default configuration
        self.config_manager.save_config(self.config)
        
        # Shutdown services
        self.sound_service.shutdown()
        
        # Close GUI
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the application."""
        # Play startup sound
        self.sound_service.play_startup_sound()
        
        # Start GUI main loop
        self.root.mainloop()