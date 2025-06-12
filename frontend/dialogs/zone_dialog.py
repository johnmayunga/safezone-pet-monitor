"""
frontend/dialogs/zone_dialog.py
Zone configuration dialog for setting up monitoring zones.
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import List, Callable, Optional, Tuple
from backend.data.models import Zone


class ZoneConfigDialog:
    """Dialog for configuring monitoring zones."""
    
    def __init__(self, parent, zones: List[Zone], video_display, 
                 save_callback: Optional[Callable] = None):
        self.parent = parent
        self.zones = zones.copy()  # Work with a copy
        self.video_display = video_display
        self.save_callback = save_callback
        
        # Drawing state
        self.drawing_mode = False
        self.current_zone_points = []
        self.zone_type_var = tk.StringVar(value="restricted")
        
        # Zone colors
        self.zone_colors = {
            "restricted": (255, 0, 0),     # Red
            "kitchen": (255, 165, 0),      # Orange
            "bedroom": (0, 0, 255),        # Blue
            "living_room": (0, 255, 0),    # Green
            "feeding_area": (255, 255, 0)  # Yellow
        }
        
        # Create dialog
        self._create_dialog()
        
        # Update zone list
        self._update_zone_list()
    
    def _create_dialog(self):
        """Create the zone configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configure Zones")
        self.dialog.geometry("600x700")
        self.dialog.resizable(True, True)
        
        # Make dialog stay on top
        self.dialog.attributes('-topmost', True)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Instructions
        self._create_instructions(main_frame)
        
        # Zone type selection
        self._create_zone_type_selection(main_frame)
        
        # Zone list
        self._create_zone_list(main_frame)
        
        # Drawing controls
        self._create_drawing_controls(main_frame)
        
        # Action buttons
        self._create_action_buttons(main_frame)
        
        # Bind events
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
        self.dialog.bind("<Escape>", self._cancel_drawing)
    
    def _create_instructions(self, parent):
        """Create instruction text."""
        instruction_text = (
            "1. Select zone type below\n"
            "2. Click 'Start Drawing' to begin\n"
            "3. Click on video to place points\n"
            "4. Right-click or press Escape to finish\n"
            "5. Click 'Save Zones' when done"
        )
        
        instruction_frame = ttk.LabelFrame(parent, text="Instructions", padding=5)
        instruction_frame.pack(fill="x", pady=5)
        
        ttk.Label(instruction_frame, text=instruction_text, justify="left").pack()
    
    def _create_zone_type_selection(self, parent):
        """Create zone type selection."""
        type_frame = ttk.LabelFrame(parent, text="Zone Type", padding=5)
        type_frame.pack(fill="x", pady=5)
        
        zone_types = [
            ("Restricted", "restricted", "Areas pets should not enter"),
            ("Kitchen", "kitchen", "Kitchen/cooking area"),
            ("Bedroom", "bedroom", "Sleeping area"),
            ("Living Room", "living_room", "Main living space"),
            ("Feeding Area", "feeding_area", "Where pets eat/drink")
        ]
        
        for i, (display_name, value, description) in enumerate(zone_types):
            frame = ttk.Frame(type_frame)
            frame.grid(row=i//2, column=i%2, sticky="w", padx=5, pady=2)
            
            radio = ttk.Radiobutton(
                frame, text=display_name, 
                variable=self.zone_type_var, 
                value=value
            )
            radio.pack(side="left")
            
            # Add tooltip
            self._add_tooltip(radio, description)
    
    def _create_zone_list(self, parent):
        """Create zone list display."""
        list_frame = ttk.LabelFrame(parent, text="Configured Zones", padding=5)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # Treeview for zones
        columns = ("Name", "Type", "Coordinates")
        self.zone_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=8)
        
        # Configure columns
        self.zone_tree.heading("Name", text="Zone Name")
        self.zone_tree.heading("Type", text="Type")
        self.zone_tree.heading("Coordinates", text="Coordinates")
        
        self.zone_tree.column("Name", width=120, minwidth=80)
        self.zone_tree.column("Type", width=100, minwidth=80)
        self.zone_tree.column("Coordinates", width=200, minwidth=150)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.zone_tree.yview)
        self.zone_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        self.zone_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Context menu
        self._create_zone_context_menu()
    
    def _create_zone_context_menu(self):
        """Create context menu for zone list."""
        self.context_menu = tk.Menu(self.dialog, tearoff=0)
        self.context_menu.add_command(label="Edit Zone", command=self._edit_selected_zone)
        self.context_menu.add_command(label="Delete Zone", command=self._delete_selected_zone)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Highlight Zone", command=self._highlight_selected_zone)
        
        self.zone_tree.bind("<Button-3>", self._show_context_menu)
    
    def _create_drawing_controls(self, parent):
        """Create drawing control buttons."""
        drawing_frame = ttk.LabelFrame(parent, text="Drawing Controls", padding=5)
        drawing_frame.pack(fill="x", pady=5)
        
        # Drawing buttons
        self.start_draw_btn = ttk.Button(
            drawing_frame, text="Start Drawing", 
            command=self._start_drawing,
            style="Success.TButton"
        )
        self.start_draw_btn.pack(side="left", padx=5)
        
        self.finish_draw_btn = ttk.Button(
            drawing_frame, text="Finish Zone", 
            command=self._finish_drawing,
            state="disabled"
        )
        self.finish_draw_btn.pack(side="left", padx=5)
        
        self.cancel_draw_btn = ttk.Button(
            drawing_frame, text="Cancel Drawing", 
            command=self._cancel_drawing,
            state="disabled"
        )
        self.cancel_draw_btn.pack(side="left", padx=5)
        
        # Status label
        self.drawing_status = ttk.Label(drawing_frame, text="Ready to draw")
        self.drawing_status.pack(side="right", padx=5)
    
    def _create_action_buttons(self, parent):
        """Create main action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=10)
        
        # Left side - utility buttons
        ttk.Button(button_frame, text="Clear All Zones", 
                  command=self._clear_all_zones).pack(side="left", padx=5)
        
        ttk.Button(button_frame, text="Load Preset", 
                  command=self._load_preset_zones).pack(side="left", padx=5)
        
        # Right side - main buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self._on_close).pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="Save Zones", 
                  command=self._save_zones,
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
    
    def _start_drawing(self):
        """Start zone drawing mode."""
        self.drawing_mode = True
        self.current_zone_points = []
        
        # Update button states
        self.start_draw_btn.config(state="disabled")
        self.finish_draw_btn.config(state="disabled") 
        self.cancel_draw_btn.config(state="normal")
        
        # Update status
        self.drawing_status.config(text="Click on video to place points")
        
        # Clear any existing temporary drawings
        self.video_display.clear_overlays("zone_drawing")
        
        # Change cursor if possible
        try:
            self.video_display.canvas.configure(cursor="crosshair")
        except:
            pass
    
    def _finish_drawing(self):
        """Finish drawing current zone."""
        if not self.drawing_mode or len(self.current_zone_points) < 3:
            messagebox.showwarning("Invalid Zone", "Please place at least 3 points to create a zone.")
            return
        
        # Calculate bounding box
        xs = [p[0] for p in self.current_zone_points]
        ys = [p[1] for p in self.current_zone_points]
        x1, y1, x2, y2 = min(xs), min(ys), max(xs), max(ys)
        
        # Create zone
        zone_type = self.zone_type_var.get()
        zone_name = f"{zone_type}_{len(self.zones) + 1}"
        color = self.zone_colors.get(zone_type, (128, 128, 128))
        
        new_zone = Zone(
            name=zone_name,
            coords=(int(x1), int(y1), int(x2), int(y2)),
            zone_type=zone_type,
            color=color
        )
        
        self.zones.append(new_zone)
        
        # Reset drawing state
        self._reset_drawing_state()
        
        # Update display
        self._update_zone_list()
        self._update_video_overlays()
        
        self.drawing_status.config(text=f"Zone '{zone_name}' created")
    
    def _cancel_drawing(self, event=None):
        """Cancel current drawing."""
        self._reset_drawing_state()
        self.drawing_status.config(text="Drawing cancelled")
    
    def _reset_drawing_state(self):
        """Reset drawing state and UI."""
        self.drawing_mode = False
        self.current_zone_points = []
        
        # Update button states
        self.start_draw_btn.config(state="normal")
        self.finish_draw_btn.config(state="disabled")
        self.cancel_draw_btn.config(state="disabled")
        
        # Clear temporary drawings
        self.video_display.clear_overlays("zone_drawing")
        
        # Reset cursor
        try:
            self.video_display.canvas.configure(cursor="")
        except:
            pass
    
    def handle_canvas_click(self, video_coords):
        """Handle click on video canvas during drawing."""
        if not self.drawing_mode:
            return
        
        x, y = video_coords
        self.current_zone_points.append((x, y))
        
        # Draw point on video
        self.video_display.draw_overlay_circle(
            (int(x), int(y)), 5, color="red", tags="zone_drawing"
        )
        
        # Draw lines between points
        if len(self.current_zone_points) > 1:
            p1 = self.current_zone_points[-2]
            p2 = self.current_zone_points[-1]
            # Note: Line drawing would need to be implemented in video_display
            
        # Update status
        point_count = len(self.current_zone_points)
        self.drawing_status.config(text=f"Points placed: {point_count}")
        
        # Enable finish button when we have enough points
        if point_count >= 3:
            self.finish_draw_btn.config(state="normal")
    
    def _update_zone_list(self):
        """Update the zone list display."""
        # Clear existing items
        for item in self.zone_tree.get_children():
            self.zone_tree.delete(item)
        
        # Add zones
        for zone in self.zones:
            coords_str = f"({zone.coords[0]}, {zone.coords[1]}) - ({zone.coords[2]}, {zone.coords[3]})"
            self.zone_tree.insert("", "end", values=(
                zone.name,
                zone.zone_type.replace('_', ' ').title(),
                coords_str
            ))
    
    def _update_video_overlays(self):
        """Update zone overlays on video display."""
        # Clear existing zone overlays
        self.video_display.clear_overlays("zone_overlay")
        
        # Draw all zones
        for zone in self.zones:
            color_hex = f"#{zone.color[0]:02x}{zone.color[1]:02x}{zone.color[2]:02x}"
            self.video_display.draw_overlay_rectangle(
                zone.coords, color=color_hex, tags="zone_overlay"
            )
            
            # Add zone label
            label_x = zone.coords[0] + 5
            label_y = zone.coords[1] - 10
            self.video_display.draw_overlay_text(
                (label_x, label_y), zone.name, color=color_hex, tags="zone_overlay"
            )
    
    def _show_context_menu(self, event):
        """Show context menu for zone list."""
        selection = self.zone_tree.selection()
        if selection:
            self.context_menu.post(event.x_root, event.y_root)
    
    def _edit_selected_zone(self):
        """Edit the selected zone."""
        selection = self.zone_tree.selection()
        if not selection:
            return
        
        item = self.zone_tree.item(selection[0])
        zone_name = item['values'][0]
        
        # Find the zone
        zone = next((z for z in self.zones if z.name == zone_name), None)
        if zone:
            self._edit_zone_dialog(zone)
    
    def _edit_zone_dialog(self, zone):
        """Show edit dialog for a zone."""
        edit_dialog = tk.Toplevel(self.dialog)
        edit_dialog.title(f"Edit Zone: {zone.name}")
        edit_dialog.geometry("300x200")
        edit_dialog.resizable(False, False)
        
        # Zone name
        ttk.Label(edit_dialog, text="Zone Name:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        name_var = tk.StringVar(value=zone.name)
        name_entry = ttk.Entry(edit_dialog, textvariable=name_var, width=20)
        name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        # Zone type
        ttk.Label(edit_dialog, text="Zone Type:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        type_var = tk.StringVar(value=zone.zone_type)
        type_combo = ttk.Combobox(edit_dialog, textvariable=type_var, 
                                 values=list(self.zone_colors.keys()), state="readonly")
        type_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Coordinates (read-only for now)
        ttk.Label(edit_dialog, text="Coordinates:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        coords_text = f"{zone.coords[0]}, {zone.coords[1]}, {zone.coords[2]}, {zone.coords[3]}"
        ttk.Label(edit_dialog, text=coords_text, font=("Courier", 8)).grid(row=2, column=1, padx=5, pady=5)
        
        # Buttons
        button_frame = ttk.Frame(edit_dialog)
        button_frame.grid(row=3, column=0, columnspan=2, pady=10)
        
        def save_changes():
            zone.name = name_var.get()
            zone.zone_type = type_var.get()
            zone.color = self.zone_colors.get(zone.zone_type, (128, 128, 128))
            self._update_zone_list()
            self._update_video_overlays()
            edit_dialog.destroy()
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side="left", padx=5)
    
    def _delete_selected_zone(self):
        """Delete the selected zone."""
        selection = self.zone_tree.selection()
        if not selection:
            return
        
        item = self.zone_tree.item(selection[0])
        zone_name = item['values'][0]
        
        if messagebox.askyesno("Confirm Delete", f"Delete zone '{zone_name}'?"):
            self.zones = [z for z in self.zones if z.name != zone_name]
            self._update_zone_list()
            self._update_video_overlays()
    
    def _highlight_selected_zone(self):
        """Highlight the selected zone on video."""
        selection = self.zone_tree.selection()
        if not selection:
            return
        
        item = self.zone_tree.item(selection[0])
        zone_name = item['values'][0]
        
        zone = next((z for z in self.zones if z.name == zone_name), None)
        if zone:
            # Temporarily highlight the zone
            self.video_display.draw_overlay_rectangle(
                zone.coords, color="yellow", width=4, tags="highlight"
            )
            
            # Remove highlight after 2 seconds
            self.dialog.after(2000, lambda: self.video_display.clear_overlays("highlight"))
    
    def _clear_all_zones(self):
        """Clear all zones."""
        if messagebox.askyesno("Confirm Clear", "Delete all zones?"):
            self.zones.clear()
            self._update_zone_list()
            self._update_video_overlays()
    
    def _load_preset_zones(self):
        """Load preset zone configurations."""
        preset_dialog = tk.Toplevel(self.dialog)
        preset_dialog.title("Load Preset Zones")
        preset_dialog.geometry("400x300")
        
        ttk.Label(preset_dialog, text="Select a preset configuration:").pack(pady=10)
        
        # Sample presets
        presets = {
            "Home Layout": [
                Zone("Living Room", (50, 50, 300, 200), "living_room", (0, 255, 0)),
                Zone("Kitchen", (320, 50, 500, 180), "kitchen", (255, 165, 0)),
                Zone("Restricted Area", (520, 50, 600, 150), "restricted", (255, 0, 0))
            ],
            "Apartment": [
                Zone("Main Area", (30, 30, 400, 250), "living_room", (0, 255, 0)),
                Zone("Bedroom", (420, 30, 580, 180), "bedroom", (0, 0, 255)),
                Zone("Kitchen Counter", (50, 260, 200, 300), "restricted", (255, 0, 0))
            ]
        }
        
        preset_var = tk.StringVar()
        for preset_name in presets.keys():
            ttk.Radiobutton(preset_dialog, text=preset_name, 
                           variable=preset_var, value=preset_name).pack(anchor="w", padx=20)
        
        def load_preset():
            selected = preset_var.get()
            if selected and selected in presets:
                if messagebox.askyesno("Confirm Load", "Replace current zones with preset?"):
                    self.zones = presets[selected].copy()
                    self._update_zone_list()
                    self._update_video_overlays()
                    preset_dialog.destroy()
        
        button_frame = ttk.Frame(preset_dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Load", command=load_preset).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=preset_dialog.destroy).pack(side="left", padx=5)
    
    def _save_zones(self):
        """Save zones and close dialog."""
        if self.save_callback:
            self.save_callback(self.zones)
        
        messagebox.showinfo("Success", f"Saved {len(self.zones)} zones successfully!")
        self._on_close()
    
    def _on_close(self):
        """Handle dialog closing."""
        # Cancel any active drawing
        self._cancel_drawing()
        
        # Clear video overlays
        self.video_display.clear_overlays("zone_overlay")
        self.video_display.clear_overlays("zone_drawing")
        self.video_display.clear_overlays("highlight")
        
        # Close dialog
        self.dialog.destroy()
    
    def winfo_exists(self):
        """Check if dialog still exists."""
        try:
            return self.dialog.winfo_exists()
        except:
            return False