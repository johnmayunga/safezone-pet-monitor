"""
frontend/dialogs/bowl_dialog.py
Bowl location configuration dialog.
"""
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Dict, Callable, Optional, Tuple
from backend.data.models import BowlLocation


class BowlConfigDialog:
    """Dialog for configuring pet bowl locations."""
    
    def __init__(self, parent, bowls: Dict[str, BowlLocation], video_display,
                 save_callback: Optional[Callable] = None):
        self.parent = parent
        self.bowls = bowls.copy()  # Work with a copy
        self.video_display = video_display
        self.save_callback = save_callback
        
        # Placement state
        self.placing_bowl = False
        self.bowl_type_to_place = None
        self.dragging_bowl = None
        self.drag_start = None
        
        # Bowl types and colors
        self.bowl_types = {
            "food": {"color": (255, 0, 0), "icon": "🍽️", "description": "Food bowl location"},
            "water": {"color": (0, 0, 255), "icon": "💧", "description": "Water bowl location"},
            "treats": {"color": (255, 165, 0), "icon": "🍪", "description": "Treat dispensing area"},
            "toys": {"color": (0, 255, 0), "icon": "🎾", "description": "Toy storage area"}
        }
        
        # Create dialog
        self._create_dialog()
        
        # Update bowl list
        self._update_bowl_list()
        self._update_video_overlays()
    
    def _create_dialog(self):
        """Create the bowl configuration dialog."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Configure Bowl Locations")
        self.dialog.geometry("720x600")
        self.dialog.resizable(True, True)
        
        # Make dialog stay on top
        self.dialog.attributes('-topmost', True)
        
        # Main frame
        main_frame = ttk.Frame(self.dialog, padding=10)
        main_frame.pack(fill="both", expand=True)
        
        # Instructions
        self._create_instructions(main_frame)
        
        # Bowl placement controls
        self._create_placement_controls(main_frame)
        
        # Bowl list
        self._create_bowl_list(main_frame)
        
        # Action buttons
        self._create_action_buttons(main_frame)
        
        # Bind events
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _create_instructions(self, parent):
        """Create instruction text."""
        instruction_text = (
            "• Select bowl type and click 'Place Bowl'\n"
            "• Click on video to place the bowl\n"
            "• Drag existing bowls to move them\n"
            "• Right-click bowls for options\n"
            "• Adjust size with slider below"
        )
        
        instruction_frame = ttk.LabelFrame(parent, text="Instructions", padding=5)
        instruction_frame.pack(fill="x", pady=5)
        
        ttk.Label(instruction_frame, text=instruction_text, justify="left").pack()
    
    def _create_placement_controls(self, parent):
        """Create bowl placement controls."""
        placement_frame = ttk.LabelFrame(parent, text="Add New Bowl", padding=5)
        placement_frame.pack(fill="x", pady=5)
        
        # Bowl type selection
        ttk.Label(placement_frame, text="Bowl Type:").grid(row=0, column=0, sticky="w", padx=5)
        
        self.bowl_type_var = tk.StringVar(value="food")
        type_frame = ttk.Frame(placement_frame)
        type_frame.grid(row=0, column=1, columnspan=3, sticky="w", padx=5)
        
        for bowl_type, info in self.bowl_types.items():
            radio = ttk.Radiobutton(
                type_frame, text=f"{info['icon']} {bowl_type.title()}", 
                variable=self.bowl_type_var, value=bowl_type
            )
            radio.pack(side="left", padx=5)
        
        # Bowl size
        ttk.Label(placement_frame, text="Size:").grid(row=1, column=0, sticky="w", padx=5)
        
        self.bowl_size_var = tk.IntVar(value=30)
        size_scale = ttk.Scale(
            placement_frame, from_=15, to=60, 
            variable=self.bowl_size_var, orient="horizontal", length=150
        )
        size_scale.grid(row=1, column=1, padx=5)
        
        self.size_label = ttk.Label(placement_frame, text="30px")
        self.size_label.grid(row=1, column=2, padx=5)
        
        # Update size label
        def update_size_label(value=None):
            self.size_label.config(text=f"{int(self.bowl_size_var.get())}px")
        
        size_scale.config(command=update_size_label)
        
        # Place button
        self.place_button = ttk.Button(
            placement_frame, text="Place Bowl", 
            command=self._start_placement,
            style="Success.TButton"
        )
        self.place_button.grid(row=1, column=3, padx=10)
        
        # Status label
        self.placement_status = ttk.Label(placement_frame, text="Ready")
        self.placement_status.grid(row=2, column=0, columnspan=4, pady=5)
    
    def _create_bowl_list(self, parent):
        """Create bowl list display."""
        list_frame = ttk.LabelFrame(parent, text="Current Bowls", padding=5)
        list_frame.pack(fill="both", expand=True, pady=5)
        
        # Create main container with two sections
        container = ttk.Frame(list_frame)
        container.pack(fill="both", expand=True)
        
        # Left side - Treeview with scrollbar
        tree_frame = ttk.Frame(container)
        tree_frame.pack(side="left", fill="both", expand=True)
        
        # Treeview for bowls
        columns = ("Type", "Position", "Size")
        self.bowl_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=6)
        
        # Configure columns
        self.bowl_tree.heading("Type", text="Type")
        self.bowl_tree.heading("Position", text="Position")
        self.bowl_tree.heading("Size", text="Size")
        
        self.bowl_tree.column("Type", width=100, minwidth=80)
        self.bowl_tree.column("Position", width=150, minwidth=120)
        self.bowl_tree.column("Size", width=80, minwidth=60)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(tree_frame, orient="vertical", command=self.bowl_tree.yview)
        self.bowl_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack treeview and scrollbar
        self.bowl_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Right side - Control buttons (vertical layout)
        button_frame = ttk.Frame(container)
        button_frame.pack(side="right", fill="y", padx=(10, 0))
        
        # Create buttons with uniform width
        button_width = 15  # Adjust this value as needed
        
        ttk.Button(button_frame, text="Edit Selected", 
                command=self._edit_selected_bowl,
                width=button_width).pack(pady=5, fill="x")
        
        ttk.Button(button_frame, text="Delete Selected", 
                command=self._delete_selected_bowl,
                width=button_width).pack(pady=5, fill="x")
        
        ttk.Button(button_frame, text="Clear All", 
                command=self._clear_all_bowls,
                width=button_width).pack(pady=5, fill="x")
        
        # Context menu setup
        self._create_bowl_context_menu()
        
    def _create_bowl_context_menu(self):
        """Create context menu for bowl list."""
        self.context_menu = tk.Menu(self.dialog, tearoff=0)
        self.context_menu.add_command(label="Edit Bowl", command=self._edit_selected_bowl)
        self.context_menu.add_command(label="Delete Bowl", command=self._delete_selected_bowl)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Highlight Bowl", command=self._highlight_selected_bowl)
        self.context_menu.add_command(label="Center on Bowl", command=self._center_on_selected_bowl)
        
        self.bowl_tree.bind("<Button-3>", self._show_context_menu)
        self.bowl_tree.bind("<Double-1>", self._edit_selected_bowl)
    
    def _create_action_buttons(self, parent):
        """Create main action buttons."""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill="x", pady=10)
        
        # Left side - utility buttons
        ttk.Button(button_frame, text="Load Preset", 
                  command=self._load_preset_bowls).pack(side="left", padx=5)
        
        # Right side - main buttons
        ttk.Button(button_frame, text="Cancel", 
                  command=self._on_close).pack(side="right", padx=5)
        
        ttk.Button(button_frame, text="Save Bowls", 
                  command=self._save_bowls,
                  style="Success.TButton").pack(side="right", padx=5)
    
    def _start_placement(self):
        """Start bowl placement mode."""
        self.placing_bowl = True
        self.bowl_type_to_place = self.bowl_type_var.get()
        
        # Update UI
        self.place_button.config(state="disabled")
        self.placement_status.config(text=f"Click on video to place {self.bowl_type_to_place} bowl")
        
        # Change cursor if possible
        try:
            self.video_display.canvas.configure(cursor="target")
        except:
            pass
    
    def handle_canvas_click(self, video_coords):
        """Handle click on video canvas during placement."""
        if not self.placing_bowl:
            return
        
        x, y = video_coords
        bowl_type = self.bowl_type_to_place
        
        # Check if bowl type already exists
        if bowl_type in self.bowls:
            if not messagebox.askyesno("Replace Bowl", 
                                     f"A {bowl_type} bowl already exists. Replace it?"):
                self._cancel_placement()
                return
        
        # Create new bowl
        bowl_info = self.bowl_types[bowl_type]
        bowl = BowlLocation(
            name=bowl_type,
            position=(int(x), int(y)),
            radius=self.bowl_size_var.get(),
            color=bowl_info["color"]
        )
        
        self.bowls[bowl_type] = bowl
        
        # Reset placement state
        self._cancel_placement()
        
        # Update displays immediately
        self._update_bowl_list()
        self._update_video_overlays()
        
        self.placement_status.config(text=f"{bowl_type.title()} bowl placed at ({int(x)}, {int(y)})")
        
        print(f"✓ Bowl placed: {bowl_type} at ({int(x)}, {int(y)})")  # Debug output
    
    def _cancel_placement(self):
        """Cancel bowl placement mode."""
        self.placing_bowl = False
        self.bowl_type_to_place = None
        
        # Update UI
        self.place_button.config(state="normal")
        self.placement_status.config(text="Ready")
        
        # Reset cursor
        try:
            self.video_display.canvas.configure(cursor="")
        except:
            pass
    
    def _update_bowl_list(self):
        """Update the bowl list display."""
        # Clear existing items
        for item in self.bowl_tree.get_children():
            self.bowl_tree.delete(item)
        
        # Add bowls
        for bowl_name, bowl in self.bowls.items():
            icon = self.bowl_types.get(bowl_name, {}).get("icon", "🥣")
            type_display = f"{icon} {bowl_name.title()}"
            position_str = f"({bowl.position[0]}, {bowl.position[1]})"
            size_str = f"{bowl.radius}px"
            
            self.bowl_tree.insert("", "end", values=(
                type_display,
                position_str,
                size_str
            ))
    
    def _update_video_overlays(self):
        """Update bowl overlays on video display."""
        # Clear existing bowl overlays
        self.video_display.clear_overlays("bowl_overlay")
        
        # Draw all bowls
        for bowl_name, bowl in self.bowls.items():
            color_hex = f"#{bowl.color[0]:02x}{bowl.color[1]:02x}{bowl.color[2]:02x}"
            
            # Draw bowl circle
            self.video_display.draw_overlay_circle(
                bowl.position, bowl.radius, color=color_hex, tags="bowl_overlay"
            )
            
            # Add bowl label
            icon = self.bowl_types.get(bowl_name, {}).get("icon", "🥣")
            label = f"{icon} {bowl_name.title()}"
            label_x = bowl.position[0]
            label_y = bowl.position[1] - bowl.radius - 15
            
            self.video_display.draw_overlay_text(
                (label_x, label_y), label, color=color_hex, tags="bowl_overlay"
            )
    
    def _show_context_menu(self, event):
        """Show context menu for bowl list."""
        selection = self.bowl_tree.selection()
        if selection:
            self.context_menu.post(event.x_root, event.y_root)
    
    def _edit_selected_bowl(self, event=None):
        """Edit the selected bowl."""
        selection = self.bowl_tree.selection()
        if not selection:
            return
        
        # Get bowl name from the selection
        item = self.bowl_tree.item(selection[0])
        bowl_display = item['values'][0]
        
        # Extract bowl name (remove icon)
        bowl_name = None
        for name in self.bowls.keys():
            if name.title() in bowl_display:
                bowl_name = name
                break
        
        if bowl_name and bowl_name in self.bowls:
            self._edit_bowl_dialog(bowl_name, self.bowls[bowl_name])
    
    def _edit_bowl_dialog(self, bowl_name: str, bowl: BowlLocation):
        """Show edit dialog for a bowl."""
        edit_dialog = tk.Toplevel(self.dialog)
        edit_dialog.title(f"Edit {bowl_name.title()} Bowl")
        edit_dialog.geometry("350x250")
        edit_dialog.resizable(False, False)
        
        # Bowl type (read-only)
        ttk.Label(edit_dialog, text="Bowl Type:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        ttk.Label(edit_dialog, text=bowl_name.title(), font=("Arial", 10, "bold")).grid(row=0, column=1, sticky="w", padx=5, pady=5)
        
        # Position
        ttk.Label(edit_dialog, text="Position (X, Y):").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        
        pos_frame = ttk.Frame(edit_dialog)
        pos_frame.grid(row=1, column=1, sticky="w", padx=5, pady=5)
        
        x_var = tk.IntVar(value=bowl.position[0])
        y_var = tk.IntVar(value=bowl.position[1])
        
        ttk.Entry(pos_frame, textvariable=x_var, width=8).pack(side="left")
        ttk.Label(pos_frame, text=",").pack(side="left", padx=2)
        ttk.Entry(pos_frame, textvariable=y_var, width=8).pack(side="left")
        
        # Size
        ttk.Label(edit_dialog, text="Size (radius):").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        
        size_var = tk.IntVar(value=bowl.radius)
        size_frame = ttk.Frame(edit_dialog)
        size_frame.grid(row=2, column=1, sticky="w", padx=5, pady=5)
        
        size_scale = ttk.Scale(size_frame, from_=10, to=80, variable=size_var, orient="horizontal", length=120)
        size_scale.pack(side="left")
        
        size_label = ttk.Label(size_frame, text=f"{bowl.radius}px")
        size_label.pack(side="left", padx=5)
        
        def update_size_label(value=None):
            size_label.config(text=f"{int(size_var.get())}px")
        
        size_scale.config(command=update_size_label)
        
        # Color preview
        ttk.Label(edit_dialog, text="Color:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        
        color_frame = ttk.Frame(edit_dialog, relief="solid", borderwidth=1)
        color_frame.grid(row=3, column=1, sticky="w", padx=5, pady=5)
        
        color_hex = f"#{bowl.color[0]:02x}{bowl.color[1]:02x}{bowl.color[2]:02x}"
        color_label = tk.Label(color_frame, text="   ", bg=color_hex, width=10)
        color_label.pack(padx=2, pady=2)
        
        # Buttons
        button_frame = ttk.Frame(edit_dialog)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        def save_changes():
            bowl.position = (x_var.get(), y_var.get())
            bowl.radius = size_var.get()
            self._update_bowl_list()
            self._update_video_overlays()
            edit_dialog.destroy()
        
        def reset_position():
            # Allow user to click on video to set new position
            edit_dialog.withdraw()
            self.placing_bowl = True
            self.bowl_type_to_place = bowl_name
            self.placement_status.config(text=f"Click on video to reposition {bowl_name} bowl")
            
            # When placement is done, restore dialog
            def check_placement():
                if not self.placing_bowl:
                    edit_dialog.deiconify()
                    # Update position vars
                    if bowl_name in self.bowls:
                        new_bowl = self.bowls[bowl_name]
                        x_var.set(new_bowl.position[0])
                        y_var.set(new_bowl.position[1])
                else:
                    edit_dialog.after(100, check_placement)
            
            check_placement()
        
        ttk.Button(button_frame, text="Save", command=save_changes).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Reposition", command=reset_position).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=edit_dialog.destroy).pack(side="left", padx=5)
    
    def _delete_selected_bowl(self):
        """Delete the selected bowl."""
        selection = self.bowl_tree.selection()
        if not selection:
            return
        
        item = self.bowl_tree.item(selection[0])
        bowl_display = item['values'][0]
        
        # Extract bowl name
        bowl_name = None
        for name in self.bowls.keys():
            if name.title() in bowl_display:
                bowl_name = name
                break
        
        if bowl_name and messagebox.askyesno("Confirm Delete", f"Delete {bowl_name} bowl?"):
            del self.bowls[bowl_name]
            self._update_bowl_list()
            self._update_video_overlays()
    
    def _highlight_selected_bowl(self):
        """Highlight the selected bowl on video."""
        selection = self.bowl_tree.selection()
        if not selection:
            return
        
        item = self.bowl_tree.item(selection[0])
        bowl_display = item['values'][0]
        
        # Find bowl
        bowl_name = None
        for name in self.bowls.keys():
            if name.title() in bowl_display:
                bowl_name = name
                break
        
        if bowl_name and bowl_name in self.bowls:
            bowl = self.bowls[bowl_name]
            
            # Highlight the bowl
            self.video_display.draw_overlay_circle(
                bowl.position, bowl.radius + 10, color="yellow", width=4, tags="highlight"
            )
            
            # Remove highlight after 2 seconds
            self.dialog.after(2000, lambda: self.video_display.clear_overlays("highlight"))
    
    def _center_on_selected_bowl(self):
        """Center video display on selected bowl."""
        # This would require implementing pan functionality in video display
        messagebox.showinfo("Info", "Center on bowl feature not yet implemented")
    
    def _clear_all_bowls(self):
        """Clear all bowls."""
        if messagebox.askyesno("Confirm Clear", "Delete all bowls?"):
            self.bowls.clear()
            self._update_bowl_list()
            self._update_video_overlays()
    
    def _load_preset_bowls(self):
        """Load preset bowl configurations."""
        preset_dialog = tk.Toplevel(self.dialog)
        preset_dialog.title("Load Preset Bowls")
        preset_dialog.geometry("400x250")
        
        ttk.Label(preset_dialog, text="Select a preset configuration:").pack(pady=10)
        
        # Sample presets
        presets = {
            "Basic Setup": {
                "food": BowlLocation("food", (100, 300), 25, (255, 0, 0)),
                "water": BowlLocation("water", (200, 300), 25, (0, 0, 255))
            },
            "Full Setup": {
                "food": BowlLocation("food", (80, 350), 30, (255, 0, 0)),
                "water": BowlLocation("water", (180, 350), 25, (0, 0, 255)),
                "treats": BowlLocation("treats", (280, 350), 20, (255, 165, 0))
            },
            "Multiple Pets": {
                "food": BowlLocation("food", (50, 300), 35, (255, 0, 0)),
                "water": BowlLocation("water", (150, 300), 30, (0, 0, 255)),
                "treats": BowlLocation("treats", (250, 300), 25, (255, 165, 0)),
                "toys": BowlLocation("toys", (350, 300), 40, (0, 255, 0))
            }
        }
        
        preset_var = tk.StringVar()
        for preset_name, bowls in presets.items():
            frame = ttk.Frame(preset_dialog)
            frame.pack(anchor="w", padx=20, pady=2)
            
            ttk.Radiobutton(frame, text=preset_name, 
                           variable=preset_var, value=preset_name).pack(side="left")
            
            # Show bowl types in preset
            bowl_types = ", ".join([f"{info['icon']} {name}" 
                                   for name, bowl in bowls.items() 
                                   for bowl_type, info in self.bowl_types.items() 
                                   if bowl_type == name])
            ttk.Label(frame, text=f"({bowl_types})", font=("Arial", 8)).pack(side="left", padx=10)
        
        def load_preset():
            selected = preset_var.get()
            if selected and selected in presets:
                if messagebox.askyesno("Confirm Load", "Replace current bowls with preset?"):
                    self.bowls = presets[selected].copy()
                    self._update_bowl_list()
                    self._update_video_overlays()
                    preset_dialog.destroy()
        
        button_frame = ttk.Frame(preset_dialog)
        button_frame.pack(pady=20)
        
        ttk.Button(button_frame, text="Load", command=load_preset).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Cancel", command=preset_dialog.destroy).pack(side="left", padx=5)
    
    def _save_bowls(self):
        """Save bowls and close dialog."""
        if self.save_callback:
            self.save_callback(self.bowls)
        
        # Also trigger immediate video overlay update
        if hasattr(self, 'video_display'):
            self._update_video_overlays()
        
        messagebox.showinfo("Success", f"Saved {len(self.bowls)} bowl locations successfully!")
        self._on_close()
    
    def _on_close(self):
        """Handle dialog closing."""
        # Cancel any active placement
        self._cancel_placement()
        
        # Clear video overlays
        self.video_display.clear_overlays("bowl_overlay")
        self.video_display.clear_overlays("highlight")
        
        # Close dialog
        self.dialog.destroy()
    
    def winfo_exists(self):
        """Check if dialog still exists."""
        try:
            return self.dialog.winfo_exists()
        except:
            return False