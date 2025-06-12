"""
frontend/dialogs/__init__.py
Alert settings configuration dialog.
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Callable, Optional
import platform


class AlertConfigDialog:
    """Dialog for configuring alert settings."""
    
    def __init__(self, parent, sound_service, email_service, 
                 current_cooldown: int = 60,
                 save_callback: Optional[Callable] = None):
        self.parent = parent
        self.sound_service = sound_service
        self.email_service = email_service
        self.current_cooldown = current_cooldown
        self.save_callback = save_callback
        
        # Create dialog
        self._create_dialog()
        
        # Load current settings
        self._load_current_settings()
    
    def _create_dialog(self):
        """Create the alert configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Alert Settings")
        self.dialog.geometry("500x700")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Create sections
        self._create_sound_settings(main_frame)
        self._create_alert_types_settings(main_frame)
        self._create_timing_settings(main_frame)
        self._create_system_info(main_frame)
        self._create_test_section(main_frame)
        self._create_action_buttons(main_frame)
        
        # Bind events
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_sound_settings(self, parent):
        """Create sound alert settings section."""
        sound_frame = ttk.LabelFrame(parent, text="Sound Alerts", padding=10)
        sound_frame.pack(fill="x", pady=5)
        
        # Enable sound alerts
        self.sound_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sound_frame, text="Enable sound alerts", 
                       variable=self.sound_enabled_var,
                       command=self._on_sound_enabled_changed).pack(anchor="w")
        
        # Sound system status
        status_frame = ttk.Frame(sound_frame)
        status_frame.pack(fill="x", pady=5)
        
        ttk.Label(status_frame, text="Sound System Status:").pack(side="left")
        self.sound_status_label = ttk.Label(status_frame, text="Checking...", foreground="blue")
        self.sound_status_label.pack(side="left", padx=10)
        
        # Test sound button
        test_frame = ttk.Frame(sound_frame)
        test_frame.pack(fill="x", pady=5)
        
        self.test_sound_button = ttk.Button(test_frame, text="🔊 Test Sound", 
                                          command=self._test_sound)
        self.test_sound_button.pack(side="left")
        
        self.test_sound_status = ttk.Label(test_frame, text="")
        self.test_sound_status.pack(side="left", padx=10)
        
        # Sound volume (placeholder - pygame doesn't have easy volume control)
        volume_frame = ttk.Frame(sound_frame)
        volume_frame.pack(fill="x", pady=5)
        
        ttk.Label(volume_frame, text="Alert Duration:").pack(side="left")
        self.sound_duration_var = tk.DoubleVar(value=2.0)
        duration_scale = ttk.Scale(volume_frame, from_=0.5, to=5.0, 
                                  variable=self.sound_duration_var, 
                                  orient="horizontal", length=150)
        duration_scale.pack(side="left", padx=5)
        
        self.duration_label = ttk.Label(volume_frame, text="2.0s")
        self.duration_label.pack(side="left", padx=5)
        
        # Update duration label
        def update_duration_label(value=None):
            self.duration_label.config(text=f"{self.sound_duration_var.get():.1f}s")
        
        duration_scale.config(command=update_duration_label)
    
    def _create_alert_types_settings(self, parent):
        """Create alert types settings section."""
        types_frame = ttk.LabelFrame(parent, text="Alert Types", padding=10)
        types_frame.pack(fill="x", pady=5)
        
        # Alert type configurations
        self.alert_types = {
            "restricted_zone": {
                "var": tk.BooleanVar(value=True),
                "sound_var": tk.BooleanVar(value=True),
                "email_var": tk.BooleanVar(value=True),
                "label": "🚫 Restricted Zone Entry",
                "description": "Pet enters a restricted area"
            },
            "feeding": {
                "var": tk.BooleanVar(value=False),
                "sound_var": tk.BooleanVar(value=False),
                "email_var": tk.BooleanVar(value=False),
                "label": "🍽️ Feeding Activity",
                "description": "Pet eating or drinking detected"
            },
            "long_absence": {
                "var": tk.BooleanVar(value=True),
                "sound_var": tk.BooleanVar(value=False),
                "email_var": tk.BooleanVar(value=True),
                "label": "⏰ Long Absence",
                "description": "No pet activity for extended period"
            },
            "unusual_activity": {
                "var": tk.BooleanVar(value=False),
                "sound_var": tk.BooleanVar(value=False),
                "email_var": tk.BooleanVar(value=False),
                "label": "❓ Unusual Activity",
                "description": "Abnormal behavior patterns detected"
            }
        }
        
        # Header row
        header_frame = ttk.Frame(types_frame)
        header_frame.pack(fill="x", pady=2)
        
        ttk.Label(header_frame, text="Alert Type", font=("Arial", 9, "bold")).grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(header_frame, text="Enable", font=("Arial", 9, "bold")).grid(row=0, column=1, padx=5)
        ttk.Label(header_frame, text="Sound", font=("Arial", 9, "bold")).grid(row=0, column=2, padx=5)
        ttk.Label(header_frame, text="Email", font=("Arial", 9, "bold")).grid(row=0, column=3, padx=5)
        
        # Alert type rows
        for i, (alert_type, config) in enumerate(self.alert_types.items()):
            row_frame = ttk.Frame(types_frame)
            row_frame.pack(fill="x", pady=2)
            
            # Alert type label
            type_label = ttk.Label(row_frame, text=config["label"])
            type_label.grid(row=0, column=0, sticky="w", padx=5)
            
            # Add tooltip
            self._add_tooltip(type_label, config["description"])
            
            # Enable checkbox
            enable_check = ttk.Checkbutton(row_frame, variable=config["var"])
            enable_check.grid(row=0, column=1, padx=20)
            
            # Sound checkbox
            sound_check = ttk.Checkbutton(row_frame, variable=config["sound_var"])
            sound_check.grid(row=0, column=2, padx=20)
            
            # Email checkbox
            email_check = ttk.Checkbutton(row_frame, variable=config["email_var"])
            email_check.grid(row=0, column=3, padx=20)
    
    def _create_timing_settings(self, parent):
        """Create timing settings section."""
        timing_frame = ttk.LabelFrame(parent, text="Timing Settings", padding=10)
        timing_frame.pack(fill="x", pady=5)
        
        # Alert cooldown
        cooldown_frame = ttk.Frame(timing_frame)
        cooldown_frame.pack(fill="x", pady=5)
        
        ttk.Label(cooldown_frame, text="Alert Cooldown Period:").pack(side="left")
        
        self.cooldown_var = tk.IntVar(value=self.current_cooldown)
        cooldown_scale = ttk.Scale(cooldown_frame, from_=10, to=300, 
                                  variable=self.cooldown_var, 
                                  orient="horizontal", length=200)
        cooldown_scale.pack(side="left", padx=10)
        
        self.cooldown_label = ttk.Label(cooldown_frame, text=f"{self.current_cooldown}s")
        self.cooldown_label.pack(side="left", padx=5)
        
        # Update cooldown label
        def update_cooldown_label(value=None):
            seconds = int(self.cooldown_var.get())
            if seconds >= 60:
                minutes = seconds // 60
                remaining_seconds = seconds % 60
                if remaining_seconds == 0:
                    self.cooldown_label.config(text=f"{minutes}m")
                else:
                    self.cooldown_label.config(text=f"{minutes}m {remaining_seconds}s")
            else:
                self.cooldown_label.config(text=f"{seconds}s")
        
        cooldown_scale.config(command=update_cooldown_label)
        
        # Cooldown description
        cooldown_desc = ttk.Label(timing_frame, 
                                 text="Minimum time between similar alerts to prevent spam",
                                 font=("Arial", 8), foreground="gray")
        cooldown_desc.pack(anchor="w", padx=5)
        
        # Long absence threshold
        absence_frame = ttk.Frame(timing_frame)
        absence_frame.pack(fill="x", pady=5)
        
        ttk.Label(absence_frame, text="Long Absence Threshold:").pack(side="left")
        
        self.absence_threshold_var = tk.IntVar(value=120)  # 2 hours default
        absence_scale = ttk.Scale(absence_frame, from_=30, to=480,  # 30 min to 8 hours
                                 variable=self.absence_threshold_var,
                                 orient="horizontal", length=200)
        absence_scale.pack(side="left", padx=10)
        
        self.absence_label = ttk.Label(absence_frame, text="2h")
        self.absence_label.pack(side="left", padx=5)
        
        # Update absence label
        def update_absence_label(value=None):
            minutes = int(self.absence_threshold_var.get())
            hours = minutes // 60
            remaining_minutes = minutes % 60
            if hours == 0:
                self.absence_label.config(text=f"{minutes}m")
            elif remaining_minutes == 0:
                self.absence_label.config(text=f"{hours}h")
            else:
                self.absence_label.config(text=f"{hours}h {remaining_minutes}m")
        
        absence_scale.config(command=update_absence_label)
    
    def _create_system_info(self, parent):
        """Create system information section."""
        info_frame = ttk.LabelFrame(parent, text="System Information", padding=10)
        info_frame.pack(fill="x", pady=5)
        
        # Platform info
        platform_info = f"Platform: {platform.system()} {platform.release()}"
        ttk.Label(info_frame, text=platform_info, font=("Arial", 8)).pack(anchor="w")
        
        # Email service status
        email_status_frame = ttk.Frame(info_frame)
        email_status_frame.pack(fill="x", pady=2)
        
        ttk.Label(email_status_frame, text="Email Service:").pack(side="left")
        email_status = "Configured" if self.email_service.enabled else "Not Configured"
        email_color = "green" if self.email_service.enabled else "red"
        ttk.Label(email_status_frame, text=email_status, foreground=email_color).pack(side="left", padx=10)
        
        # Sound service status will be updated in _update_sound_status
        self._update_sound_status()
    
    def _create_test_section(self, parent):
        """Create test section."""
        test_frame = ttk.LabelFrame(parent, text="Test Alerts", padding=10)
        test_frame.pack(fill="x", pady=5)
        
        # Test buttons
        button_frame = ttk.Frame(test_frame)
        button_frame.pack(fill="x")
        
        ttk.Button(button_frame, text="🔊 Test Sound", 
                  command=self._test_sound).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="📧 Test Email", 
                  command=self._test_email).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="🚨 Test All Alerts", 
                  command=self._test_all_alerts).pack(side="left", padx=5)
        
        # Test status
        self.test_status_label = ttk.Label(test_frame, text="")
        self.test_status_label.pack(pady=5)
    
    def _create_action_buttons(self, parent):
        """Create main action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=20)
        
        # Left side - reset button
        ttk.Button(button_frame, text="Reset to Defaults", 
                  command=self._reset_to_defaults).pack(side="left")
        
        # Right side - main buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self._on_close).pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="Save Settings", 
                  command=self._save_settings,
                  style="Success.TButton").pack(side="right", padx=5)
    
    def _add_tooltip(self, widget, text):
        """Add tooltip to widget."""
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
            
            tooltip.after(3000, tooltip.destroy)
        
        widget.bind("<Enter>", show_tooltip)
    
    def _load_current_settings(self):
        """Load current settings into the dialog."""
        # Update cooldown
        self.cooldown_var.set(self.current_cooldown)
        
        # Update sound status
        self._update_sound_status()
    
    def _update_sound_status(self):
        """Update sound system status display."""
        status = self.sound_service.get_status()
        
        if status['available']:
            self.sound_status_label.config(text="✅ Available", foreground="green")
            self.test_sound_button.config(state="normal")
        else:
            self.sound_status_label.config(text="❌ Not Available", foreground="red")
            self.test_sound_button.config(state="disabled")
    
    def _on_sound_enabled_changed(self):
        """Handle sound enabled checkbox change."""
        enabled = self.sound_enabled_var.get()
        self.sound_service.set_enabled(enabled)
    
    def _test_sound(self):
        """Test sound alert."""
        duration = self.sound_duration_var.get()
        
        if self.sound_service.test_sound():
            self.test_sound_status.config(text="✅ Sound played", foreground="green")
        else:
            self.test_sound_status.config(text="❌ Sound failed", foreground="red")
        
        # Clear status after 3 seconds
        self.dialog.after(3000, lambda: self.test_sound_status.config(text=""))
    
    def _test_email(self):
        """Test email alert."""
        if not self.email_service.enabled:
            self.test_status_label.config(text="❌ Email not configured", foreground="red")
            return
        
        # Send test email
        success = self.email_service.send_test_email()
        
        if success:
            self.test_status_label.config(text="✅ Test email sent", foreground="green")
        else:
            self.test_status_label.config(text="❌ Email test failed", foreground="red")
        
        # Clear status after 5 seconds
        self.dialog.after(5000, lambda: self.test_status_label.config(text=""))
    
    def _test_all_alerts(self):
        """Test all alert systems."""
        results = []
        
        # Test sound
        if self.sound_enabled_var.get():
            if self.sound_service.test_sound():
                results.append("Sound: ✅")
            else:
                results.append("Sound: ❌")
        
        # Test email
        if self.email_service.enabled:
            if self.email_service.send_test_email():
                results.append("Email: ✅")
            else:
                results.append("Email: ❌")
        else:
            results.append("Email: Not configured")
        
        # Display results
        result_text = " | ".join(results)
        self.test_status_label.config(text=result_text, foreground="blue")
        
        # Clear status after 5 seconds
        self.dialog.after(5000, lambda: self.test_status_label.config(text=""))
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Confirm Reset", "Reset all alert settings to defaults?"):
            # Reset sound settings
            self.sound_enabled_var.set(True)
            self.sound_duration_var.set(2.0)
            
            # Reset alert types
            defaults = {
                "restricted_zone": {"enable": True, "sound": True, "email": True},
                "feeding": {"enable": False, "sound": False, "email": False},
                "long_absence": {"enable": True, "sound": False, "email": True},
                "unusual_activity": {"enable": False, "sound": False, "email": False}
            }
            
            for alert_type, settings in defaults.items():
                if alert_type in self.alert_types:
                    self.alert_types[alert_type]["var"].set(settings["enable"])
                    self.alert_types[alert_type]["sound_var"].set(settings["sound"])
                    self.alert_types[alert_type]["email_var"].set(settings["email"])
            
            # Reset timing
            self.cooldown_var.set(60)
            self.absence_threshold_var.set(120)
            
            # Update labels
            self.cooldown_label.config(text="1m")
            self.absence_label.config(text="2h")
            self.duration_label.config(text="2.0s")
    
    def _save_settings(self):
        """Save alert settings."""
        # Get settings
        settings = {
            "sound_enabled": self.sound_enabled_var.get(),
            "sound_duration": self.sound_duration_var.get(),
            "cooldown_period": self.cooldown_var.get(),
            "absence_threshold": self.absence_threshold_var.get(),
            "alert_types": {}
        }
        
        # Get alert type settings
        for alert_type, config in self.alert_types.items():
            settings["alert_types"][alert_type] = {
                "enabled": config["var"].get(),
                "sound": config["sound_var"].get(),
                "email": config["email_var"].get()
            }
        
        # Apply settings to services
        self.sound_service.set_enabled(settings["sound_enabled"])
        self.sound_service.set_cooldown(2.0)  # Fixed cooldown for sound
        self.email_service.set_cooldown_period(settings["cooldown_period"])
        
        # Call save callback
        if self.save_callback:
            self.save_callback(settings["cooldown_period"])
        
        messagebox.showinfo("Success", "Alert settings saved successfully!")
        self._on_close()
    
    def _on_close(self):
        """Handle dialog closing."""
        self.dialog.destroy()