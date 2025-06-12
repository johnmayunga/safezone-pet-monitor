"""
frontend/dialogs/email_dialog.py
Email configuration dialog.
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Dict, Callable, Optional
import threading


class EmailConfigDialog:
    """Dialog for configuring email notifications."""
    
    def __init__(self, parent, current_config: Optional[Dict] = None,
                 save_callback: Optional[Callable] = None,
                 test_callback: Optional[Callable] = None):
        self.parent = parent
        self.current_config = current_config or {}
        self.save_callback = save_callback
        self.test_callback = test_callback
        
        # Create dialog
        self._create_dialog()
        
        # Load current configuration
        self._load_current_config()
    
    def _create_dialog(self):
        """Create the email configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Email Notification Settings")
        self.dialog.geometry("500x750")
        self.dialog.resizable(False, False)
        
        # Center the dialog
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        # Create sections
        self._create_email_settings(main_frame)
        self._create_notification_settings(main_frame)
        self._create_test_section(main_frame)
        self._create_action_buttons(main_frame)
        
        # Bind events
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_email_settings(self, parent):
        """Create email account settings section."""
        email_frame = ttk.LabelFrame(parent, text="Email Account Settings", padding=10)
        email_frame.pack(fill="x", pady=5)
        
        # Sender email
        ttk.Label(email_frame, text="Sender Email:").grid(row=0, column=0, sticky="w", pady=5)
        self.sender_email_var = tk.StringVar()
        sender_entry = ttk.Entry(email_frame, textvariable=self.sender_email_var, width=40)
        sender_entry.grid(row=0, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Password/App password
        ttk.Label(email_frame, text="App Password:").grid(row=1, column=0, sticky="w", pady=5)
        self.password_var = tk.StringVar()
        password_entry = ttk.Entry(email_frame, textvariable=self.password_var, show="*", width=40)
        password_entry.grid(row=1, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # Show/hide password
        self.show_password_var = tk.BooleanVar()
        show_check = ttk.Checkbutton(email_frame, text="Show password", 
                                    variable=self.show_password_var,
                                    command=lambda: password_entry.config(
                                        show="" if self.show_password_var.get() else "*"
                                    ))
        show_check.grid(row=2, column=1, sticky="w", padx=5)
        
        # Recipient email
        ttk.Label(email_frame, text="Recipient Email:").grid(row=3, column=0, sticky="w", pady=5)
        self.recipient_email_var = tk.StringVar()
        recipient_entry = ttk.Entry(email_frame, textvariable=self.recipient_email_var, width=40)
        recipient_entry.grid(row=3, column=1, columnspan=2, sticky="ew", padx=5, pady=5)
        
        # SMTP settings
        ttk.Label(email_frame, text="SMTP Server:").grid(row=4, column=0, sticky="w", pady=5)
        self.smtp_server_var = tk.StringVar(value="smtp.gmail.com")
        smtp_combo = ttk.Combobox(email_frame, textvariable=self.smtp_server_var, width=25,
                                 values=["smtp.gmail.com", "smtp.outlook.com", "smtp.yahoo.com", "smtp.mail.me.com", "smtp.163.com"])
        smtp_combo.grid(row=4, column=1, sticky="w", padx=5, pady=5)
        
        ttk.Label(email_frame, text="Port:").grid(row=4, column=2, sticky="w", padx=10)
        self.smtp_port_var = tk.IntVar(value=587)
        port_entry = ttk.Entry(email_frame, textvariable=self.smtp_port_var, width=8)
        port_entry.grid(row=4, column=3, sticky="w", pady=5)
        
        # Configure grid weights
        email_frame.grid_columnconfigure(1, weight=1)
        
        # Help text
        help_text = (
            "Note: For Gmail, use an App Password instead of your regular password.\n"
            "Generate one at: Google Account > Security > 2-Step Verification > App passwords"
        )
        help_label = ttk.Label(email_frame, text=help_text, font=("Arial", 8), foreground="gray")
        help_label.grid(row=5, column=0, columnspan=4, sticky="w", pady=5)
    
    def _create_notification_settings(self, parent):
        """Create notification settings section."""
        notif_frame = ttk.LabelFrame(parent, text="Notification Settings", padding=10)
        notif_frame.pack(fill="x", pady=5)
        
        # Enable/disable notifications
        self.notifications_enabled_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(notif_frame, text="Enable email notifications", 
                       variable=self.notifications_enabled_var).grid(row=0, column=0, columnspan=2, sticky="w")
        
        # Notification types
        ttk.Label(notif_frame, text="Send notifications for:").grid(row=1, column=0, sticky="nw", pady=(10, 5))
        
        self.notif_types = {
            "restricted_zone": tk.BooleanVar(value=True),
            "feeding": tk.BooleanVar(value=False),
            "long_absence": tk.BooleanVar(value=True),
            "unusual_activity": tk.BooleanVar(value=False)
        }
        
        notif_descriptions = {
            "restricted_zone": "🚫 Restricted zone entries",
            "feeding": "🍽️ Feeding activities", 
            "long_absence": "⏰ Long absence periods",
            "unusual_activity": "❓ Unusual activity patterns"
        }
        
        for i, (key, var) in enumerate(self.notif_types.items()):
            ttk.Checkbutton(notif_frame, text=notif_descriptions[key], 
                           variable=var).grid(row=i+2, column=0, columnspan=2, sticky="w", padx=20)
        
        # Cooldown period
        ttk.Label(notif_frame, text="Cooldown period (minutes):").grid(row=6, column=0, sticky="w", pady=(10, 5))
        self.cooldown_var = tk.IntVar(value=5)
        cooldown_scale = ttk.Scale(notif_frame, from_=1, to=60, variable=self.cooldown_var, 
                                  orient="horizontal", length=200)
        cooldown_scale.grid(row=6, column=1, sticky="w", padx=5)
        
        self.cooldown_label = ttk.Label(notif_frame, text="5 min")
        self.cooldown_label.grid(row=6, column=2, sticky="w", padx=5)
        
        # Update cooldown label
        def update_cooldown_label(value=None):
            self.cooldown_label.config(text=f"{int(self.cooldown_var.get())} min")
        
        cooldown_scale.config(command=update_cooldown_label)
    
    def _create_test_section(self, parent):
        """Create test email section."""
        test_frame = ttk.LabelFrame(parent, text="Test Configuration", padding=10)
        test_frame.pack(fill="x", pady=5)
        
        # Test button and status
        test_button_frame = ttk.Frame(test_frame)
        test_button_frame.pack(fill="x")
        
        self.test_button = ttk.Button(test_button_frame, text="🧪 Send Test Email", 
                                     command=self._send_test_email)
        self.test_button.pack(side="left")
        
        self.test_status_label = ttk.Label(test_button_frame, text="")
        self.test_status_label.pack(side="left", padx=10)
        
        # Test progress
        self.test_progress = ttk.Progressbar(test_frame, mode='indeterminate')
        self.test_progress.pack(fill="x", pady=5)
        
        # Test results
        test_result_frame = ttk.Frame(test_frame)
        test_result_frame.pack(fill="x", pady=5)
        
        self.test_result_text = tk.Text(test_result_frame, height=4, width=50, 
                                       font=("Courier", 9), state="disabled")
        test_scrollbar = ttk.Scrollbar(test_result_frame, orient="vertical", 
                                      command=self.test_result_text.yview)
        self.test_result_text.configure(yscrollcommand=test_scrollbar.set)
        
        self.test_result_text.pack(side="left", fill="both", expand=True)
        test_scrollbar.pack(side="right", fill="y")
    
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
        
        ttk.Button(button_frame, text="Save Configuration", 
                  command=self._save_configuration,
                  style="Success.TButton").pack(side="right", padx=5)
    
    def _load_current_config(self):
        """Load current configuration into form fields."""
        if not self.current_config:
            return
        
        # Email settings
        self.sender_email_var.set(self.current_config.get("sender_email", ""))
        self.password_var.set(self.current_config.get("sender_password", ""))
        self.recipient_email_var.set(self.current_config.get("recipient_email", ""))
        self.smtp_server_var.set(self.current_config.get("smtp_server", "smtp.gmail.com"))
        self.smtp_port_var.set(self.current_config.get("smtp_port", 587))
        
        # Notification settings
        self.notifications_enabled_var.set(self.current_config.get("enabled", True))
        
        # Notification types
        notif_types = self.current_config.get("notification_types", {})
        for key, var in self.notif_types.items():
            var.set(notif_types.get(key, True))
        
        # Cooldown
        cooldown_minutes = self.current_config.get("cooldown_period", 300) // 60
        self.cooldown_var.set(cooldown_minutes)
        self.cooldown_label.config(text=f"{cooldown_minutes} min")
    
    def _send_test_email(self):
        """Send a test email."""
        # Validate required fields
        if not self._validate_email_settings():
            return
        
        # Get current configuration
        config = self._get_email_config()
        
        # Update UI
        self.test_button.config(state="disabled")
        self.test_status_label.config(text="Sending test email...", foreground="blue")
        self.test_progress.start()
        self._clear_test_results()
        
        # Send test email in background thread
        def test_email_thread():
            try:
                if self.test_callback:
                    success = self.test_callback(config)
                    # If we get here, the test was successful
                    self.dialog.after(0, lambda: self._on_test_complete(True))
                else:
                    self.dialog.after(0, lambda: self._on_test_complete(False, "No test callback configured"))
                    
            except Exception as e:
                # Capture the actual error message from the email service
                error_msg = str(e)
                self.dialog.after(0, lambda msg=error_msg: self._on_test_complete(False, msg))
        
        threading.Thread(target=test_email_thread, daemon=True).start()
    
    def _on_test_complete(self, success: bool, error_message: str = ""):
        """Handle test email completion."""
        # Stop progress bar
        self.test_progress.stop()
        
        # Update UI
        self.test_button.config(state="normal")
        
        if success:
            self.test_status_label.config(text="✅ Test email sent successfully!", foreground="green")
            self._add_test_result("✅ Test email sent successfully!")
            self._add_test_result("Check your inbox to confirm delivery.")
        else:
            self.test_status_label.config(text="❌ Test email failed", foreground="red")
            self._add_test_result("❌ Test email failed:")
            if error_message:
                self._add_test_result(f"Error: {error_message}")
            self._add_test_result("\nTroubleshooting:")
            self._add_test_result("• Check email and password")
            self._add_test_result("• Verify SMTP settings")
            self._add_test_result("• Ensure App Password for Gmail")
    
    def _clear_test_results(self):
        """Clear test results display."""
        self.test_result_text.config(state="normal")
        self.test_result_text.delete(1.0, tk.END)
        self.test_result_text.config(state="disabled")
    
    def _add_test_result(self, message: str):
        """Add message to test results."""
        self.test_result_text.config(state="normal")
        self.test_result_text.insert(tk.END, message + "\n")
        self.test_result_text.see(tk.END)
        self.test_result_text.config(state="disabled")
    
    def _validate_email_settings(self) -> bool:
        """Validate email settings."""
        if not self.sender_email_var.get().strip():
            messagebox.showerror("Validation Error", "Sender email is required")
            return False
        
        if not self.password_var.get().strip():
            messagebox.showerror("Validation Error", "Password is required")
            return False
        
        if not self.recipient_email_var.get().strip():
            messagebox.showerror("Validation Error", "Recipient email is required")
            return False
        
        # Basic email validation
        sender = self.sender_email_var.get().strip()
        recipient = self.recipient_email_var.get().strip()
        
        if "@" not in sender or "." not in sender:
            messagebox.showerror("Validation Error", "Invalid sender email format")
            return False
        
        if "@" not in recipient or "." not in recipient:
            messagebox.showerror("Validation Error", "Invalid recipient email format")
            return False
        
        return True
    
    def _get_email_config(self) -> Dict:
        """Get current email configuration from form."""
        return {
            "sender_email": self.sender_email_var.get().strip(),
            "sender_password": self.password_var.get(),
            "recipient_email": self.recipient_email_var.get().strip(),
            "smtp_server": self.smtp_server_var.get(),
            "smtp_port": self.smtp_port_var.get(),
            "enabled": self.notifications_enabled_var.get(),
            "notification_types": {
                key: var.get() for key, var in self.notif_types.items()
            },
            "cooldown_period": self.cooldown_var.get() * 60  # Convert to seconds
        }
    
    def _save_configuration(self):
        """Save email configuration."""
        if not self._validate_email_settings():
            return
        
        config = self._get_email_config()
        
        # Call save callback
        if self.save_callback:
            self.save_callback(config)
        
        messagebox.showinfo("Success", "Email configuration saved successfully!")
        self._on_close()
    
    def _reset_to_defaults(self):
        """Reset all settings to defaults."""
        if messagebox.askyesno("Confirm Reset", "Reset all settings to defaults?"):
            # Clear all fields
            self.sender_email_var.set("")
            self.password_var.set("")
            self.recipient_email_var.set("")
            self.smtp_server_var.set("smtp.gmail.com")
            self.smtp_port_var.set(587)
            
            # Reset notification settings
            self.notifications_enabled_var.set(True)
            for var in self.notif_types.values():
                var.set(True)
            self.cooldown_var.set(5)
            self.cooldown_label.config(text="5 min")
            
            # Clear test results
            self._clear_test_results()
            self.test_status_label.config(text="")
    
    def _on_close(self):
        """Handle dialog closing."""
        self.dialog.destroy()