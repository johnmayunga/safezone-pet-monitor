"""
frontend/components/control_panel.py
Control panel component for tracking controls and settings.
"""
import tkinter as tk
import tkinter.ttk as ttk
from typing import Callable, Optional

# Import modern styling if available
try:
    from ..utils.styling import modern_style
    STYLING_AVAILABLE = True
except ImportError:
    STYLING_AVAILABLE = False

class ControlPanel:
    """Control panel for pet tracking operations."""
    
    def __init__(self, parent, row: int, column: int, columnspan: int = 1,
                 start_callback: Optional[Callable] = None,
                 pause_callback: Optional[Callable] = None,
                 stop_callback: Optional[Callable] = None,
                 performance_callback: Optional[Callable] = None,
                 confidence_callback: Optional[Callable] = None):
        
        self.parent = parent
        self.start_callback = start_callback
        self.pause_callback = pause_callback
        self.stop_callback = stop_callback
        self.performance_callback = performance_callback
        self.confidence_callback = confidence_callback
        
        # Control variables
        self.performance_mode = tk.StringVar(value="balanced")
        self.confidence_threshold = tk.DoubleVar(value=0.5)
        self.alerts_enabled = tk.BooleanVar(value=True)
        
        # Create the control panel
        self._create_panel(row, column, columnspan)
        
        # Tracking state
        self.is_tracking = False
        self.is_paused = False
    
    def _create_panel(self, row: int, column: int, columnspan: int):
        """Create the control panel."""
        # Main frame with modern styling
        if STYLING_AVAILABLE:
            self.frame = ttk.LabelFrame(self.parent, text="Controls", padding=15, style='Card.TFrame')
        else:
            self.frame = ttk.LabelFrame(self.parent, text="Controls", padding=10)
        
        self.frame.grid(row=row, column=column, columnspan=columnspan, 
                       padx=10, pady=5, sticky="ew")
        
        # Configure grid weights
        self.frame.grid_columnconfigure(4, weight=1)
        
        # Tracking controls
        self._create_tracking_controls()
        
        # Performance settings
        self._create_performance_controls()
        
        # Detection settings
        self._create_detection_controls()
        
        # Status indicators
        self._create_status_indicators()
    
    def _create_tracking_controls(self):
        """Create start/pause/stop buttons."""
        # Button frame
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=0, column=0, padx=5, sticky="w")
        
        # Start button with modern styling
        if STYLING_AVAILABLE:
            self.start_button = modern_style.create_modern_button(
                button_frame, "▶ Start", 
                command=self._on_start,
                style="Success.TButton"
            )
        else:
            self.start_button = ttk.Button(
                button_frame, text="▶ Start", 
                command=self._on_start
            )
        self.start_button.pack(side="left", padx=2)

        # Pause button
        if STYLING_AVAILABLE:
            self.pause_button = modern_style.create_modern_button(
                button_frame, "⏸ Pause", 
                command=self._on_pause,
                style="Modern.TButton"
            )
        else:
            self.pause_button = ttk.Button(
                button_frame, text="⏸ Pause", 
                command=self._on_pause
            )
        self.pause_button.config(state="disabled")
        self.pause_button.pack(side="left", padx=2)
        
        # Stop button
        if STYLING_AVAILABLE:
            self.stop_button = modern_style.create_modern_button(
                button_frame, "⏹ Stop", 
                command=self._on_stop,
                style="Danger.TButton"
            )
        else:
            self.stop_button = ttk.Button(
                button_frame, text="⏹ Stop", 
                command=self._on_stop
            )
        self.stop_button.config(state="disabled")
        self.stop_button.pack(side="left", padx=2)
    
    def _create_performance_controls(self):
        """Create performance mode selection."""
        perf_frame = ttk.LabelFrame(self.frame, text="Performance Mode", padding=5)
        perf_frame.grid(row=0, column=1, padx=10, sticky="ew")
        
        # Performance radio buttons
        modes = [
            ("Quality", "quality", "Best detection accuracy"),
            ("Balanced", "balanced", "Good balance of speed/accuracy"),
            ("Performance", "performance", "Faster processing"),
            ("Ultra", "ultra", "Maximum speed")
        ]
        
        for i, (text, value, tooltip) in enumerate(modes):
            radio = ttk.Radiobutton(
                perf_frame, text=text, 
                variable=self.performance_mode, 
                value=value,
                command=self._on_performance_change
            )
            radio.grid(row=i//2, column=i%2, sticky="w", padx=2)
            
            # Add tooltip (simple implementation)
            self._add_tooltip(radio, tooltip)
    
    def _create_detection_controls(self):
        """Create detection threshold and alert controls."""
        detection_frame = ttk.LabelFrame(self.frame, text="Detection", padding=5)
        detection_frame.grid(row=0, column=2, padx=10, sticky="ew")
        
        # Confidence threshold
        ttk.Label(detection_frame, text="Confidence:").grid(row=0, column=0, sticky="w")
        
        self.confidence_scale = ttk.Scale(
            detection_frame, from_=0.1, to=0.9, 
            variable=self.confidence_threshold,
            orient="horizontal", length=100,
            command=self._on_confidence_change
        )
        self.confidence_scale.grid(row=0, column=1, padx=5)
        
        self.confidence_label = ttk.Label(detection_frame, text="0.5")
        self.confidence_label.grid(row=0, column=2)
        
        # Alert toggle
        self.alert_check = ttk.Checkbutton(
            detection_frame, text="Enable Alerts", 
            variable=self.alerts_enabled
        )
        self.alert_check.grid(row=1, column=0, columnspan=3, sticky="w", pady=2)
    
    def _create_status_indicators(self):
        """Create status indicators."""
        status_frame = ttk.Frame(self.frame)
        status_frame.grid(row=0, column=3, padx=10, sticky="e")
        
        # FPS display
        ttk.Label(status_frame, text="FPS:").grid(row=0, column=0, sticky="w")
        self.fps_label = ttk.Label(status_frame, text="0", foreground="blue")
        self.fps_label.grid(row=0, column=1, padx=5)
        
        # Status indicator
        ttk.Label(status_frame, text="Status:").grid(row=1, column=0, sticky="w")
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=1, column=1, padx=5)
        
        # Recording indicator (if applicable)
        self.recording_indicator = ttk.Label(
            status_frame, text="●", foreground="red", font=("Arial", 12)
        )
        # Initially hidden
    
    def _add_tooltip(self, widget, text):
        """Add a simple tooltip to a widget."""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(
                tooltip, text=text, 
                background="lightyellow", 
                relief="solid", borderwidth=1,
                font=("Arial", 8)
            )
            label.pack()
            
            # Schedule tooltip destruction
            tooltip.after(3000, tooltip.destroy)
        
        widget.bind("<Enter>", show_tooltip)
    
    def _on_start(self):
        """Handle start button click."""
        if self.start_callback:
            self.start_callback()
    
    def _on_pause(self):
        """Handle pause button click."""
        if self.pause_callback:
            self.pause_callback()
    
    def _on_stop(self):
        """Handle stop button click."""
        if self.stop_callback:
            self.stop_callback()
    
    def _on_performance_change(self):
        """Handle performance mode change."""
        if self.performance_callback:
            self.performance_callback(self.performance_mode.get())
    
    def _on_confidence_change(self, value=None):
        """Handle confidence threshold change."""
        confidence = self.confidence_threshold.get()
        self.confidence_label.config(text=f"{confidence:.2f}")
        
        if self.confidence_callback:
            self.confidence_callback(confidence)
    
    def set_tracking_state(self, tracking: bool, paused: bool = False):
        """Update button states based on tracking status."""
        self.is_tracking = tracking
        self.is_paused = paused
        
        if tracking and not paused:
            # Currently tracking
            self.start_button.config(state="disabled", text="▶ Start")
            self.pause_button.config(state="normal")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Tracking", foreground="green")
            
            # Show recording indicator
            self.recording_indicator.grid(row=0, column=2, padx=2)
            
        elif paused:
            # Paused
            self.start_button.config(state="normal", text="▶ Resume")
            self.pause_button.config(state="disabled")
            self.stop_button.config(state="normal")
            self.status_label.config(text="Paused", foreground="orange")
            
            # Hide recording indicator
            self.recording_indicator.grid_remove()
            
        else:
            # Not tracking
            self.start_button.config(state="normal", text="▶ Start")
            self.pause_button.config(state="disabled")
            self.stop_button.config(state="disabled")
            self.status_label.config(text="Ready", foreground="blue")
            
            # Hide recording indicator
            self.recording_indicator.grid_remove()
    
    def update_fps(self, fps: float):
        """Update FPS display."""
        self.fps_label.config(text=f"{fps:.1f}")
        
        # Color code FPS for performance indication
        if fps >= 25:
            color = "green"
        elif fps >= 15:
            color = "orange"
        else:
            color = "red"
        
        self.fps_label.config(foreground=color)
    
    def get_settings(self) -> dict:
        """Get current control panel settings."""
        return {
            'performance_mode': self.performance_mode.get(),
            'confidence_threshold': self.confidence_threshold.get(),
            'alerts_enabled': self.alerts_enabled.get()
        }
    
    def set_settings(self, settings: dict):
        """Apply settings to control panel."""
        if 'performance_mode' in settings:
            self.performance_mode.set(settings['performance_mode'])
        
        if 'confidence_threshold' in settings:
            self.confidence_threshold.set(settings['confidence_threshold'])
            self._on_confidence_change()
        
        if 'alerts_enabled' in settings:
            self.alerts_enabled.set(settings['alerts_enabled'])
    
    def enable_controls(self, enabled: bool):
        """Enable or disable control inputs."""
        state = "normal" if enabled else "disabled"
        
        # Performance radio buttons
        for child in self.frame.winfo_children():
            if isinstance(child, ttk.LabelFrame) and "Performance" in child['text']:
                for radio in child.winfo_children():
                    if isinstance(radio, ttk.Radiobutton):
                        radio.config(state=state)
        
        # Detection controls
        self.confidence_scale.config(state=state)
        self.alert_check.config(state=state)
    
    def set_status_message(self, message: str, color: str = "black"):
        """Set a custom status message."""
        self.status_label.config(text=message, foreground=color)
    
    def show_error(self, message: str):
        """Show an error status."""
        self.set_status_message(f"Error: {message}", "red")
    
    def show_warning(self, message: str):
        """Show a warning status."""
        self.set_status_message(f"Warning: {message}", "orange")
    
    def show_info(self, message: str):
        """Show an info status."""
        self.set_status_message(message, "blue")