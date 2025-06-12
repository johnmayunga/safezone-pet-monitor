"""
frontend/components/video_display.py
Video display component for showing the video feed with overlays.
"""
import tkinter as tk
import tkinter.ttk as ttk
import cv2
import numpy as np
from PIL import Image, ImageTk
from typing import Callable, Optional, Tuple


class VideoDisplayPanel:
    """Video display panel with zoom, pan, and overlay support."""
    
    def __init__(self, parent, row: int, column: int, 
                 click_callback: Optional[Callable] = None,
                 motion_callback: Optional[Callable] = None,
                 drag_callback: Optional[Callable] = None,
                 release_callback: Optional[Callable] = None):
        
        self.parent = parent
        self.click_callback = click_callback
        self.motion_callback = motion_callback
        self.drag_callback = drag_callback
        self.release_callback = release_callback
        
        # Display properties
        self.canvas_width = 750
        self.canvas_height = 450
        self.current_frame = None
        self.current_photo = None
        
        # Coordinate transformation
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        # Video properties
        self.video_width = 0
        self.video_height = 0
        
        # Interaction state
        self.dragging = False
        self.drag_start_x = 0
        self.drag_start_y = 0
        self.dragging_item = None
        self._draggable_items = {}
        
        # Create the display panel
        self._create_panel(row, column)
    
    def _create_panel(self, row: int, column: int):
        """Create the video display panel."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Video Feed", padding=10)
        self.frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsew")
        
        # Canvas container
        canvas_container = ttk.Frame(self.frame)
        canvas_container.pack(fill="both", expand=True)
        
        # Video canvas
        self.canvas = tk.Canvas(
            canvas_container, 
            bg='black',
            width=self.canvas_width,
            height=self.canvas_height,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Bind events
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._on_right_click)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        
        # Video controls
        self._create_controls()
        
        # Initial message
        self._show_initial_message()
    
    def _create_controls(self):
        """Create video control buttons."""
        controls_frame = ttk.Frame(self.frame)
        controls_frame.pack(fill="x", pady=5)
        
        # Zoom controls
        ttk.Label(controls_frame, text="Zoom:").pack(side="left", padx=5)
        ttk.Button(controls_frame, text="Fit", command=self._fit_to_window).pack(side="left", padx=2)
        ttk.Button(controls_frame, text="100%", command=self._actual_size).pack(side="left", padx=2)
        ttk.Button(controls_frame, text="+", command=self._zoom_in, width=3).pack(side="left", padx=2)
        ttk.Button(controls_frame, text="-", command=self._zoom_out, width=3).pack(side="left", padx=2)
        
        # Info label
        self.info_label = ttk.Label(controls_frame, text="")
        self.info_label.pack(side="right", padx=5)
    
    def _show_initial_message(self):
        """Show initial message when no video is loaded."""
        self.canvas.delete("all")
        self.canvas.create_text(
            self.canvas_width / 2, self.canvas_height / 2,
            text="Load a video source to begin tracking (Click File then Open Video/Use Camera)",
            fill="white", font=("Arial", 14),
            tags="message"
        )
    
    def update_frame(self, frame: np.ndarray):
        """Update the displayed frame."""
        if frame is None:
            return
        
        self.current_frame = frame.copy()
        self.video_height, self.video_width = frame.shape[:2]
        
        # Convert to RGB
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Calculate display parameters
        self._calculate_display_parameters()
        
        # Resize frame for display
        display_width = int(self.video_width * self.scale_x)
        display_height = int(self.video_height * self.scale_y)
        
        if display_width > 0 and display_height > 0:
            frame_resized = cv2.resize(frame_rgb, (display_width, display_height))
            
            # Convert to PhotoImage
            image = Image.fromarray(frame_resized)
            self.current_photo = ImageTk.PhotoImage(image=image)
            
            # Update canvas
            self.canvas.delete("video")
            self.canvas.create_image(
                self.offset_x, self.offset_y,
                image=self.current_photo,
                anchor="nw",
                tags="video"
            )
            
            # Update info
            self._update_info_display()
    
    def _calculate_display_parameters(self):
        """Calculate scale and offset for displaying the video."""
        if self.video_width == 0 or self.video_height == 0:
            return
        
        # Get current canvas size
        self.canvas.update_idletasks()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            canvas_width = self.canvas_width
            canvas_height = self.canvas_height
        
        # Calculate scale to fit
        scale_x = canvas_width / self.video_width
        scale_y = canvas_height / self.video_height
        scale = min(scale_x, scale_y)
        
        # Apply scale
        self.scale_x = scale
        self.scale_y = scale
        
        # Calculate offsets for centering
        scaled_width = self.video_width * self.scale_x
        scaled_height = self.video_height * self.scale_y
        
        self.offset_x = (canvas_width - scaled_width) / 2
        self.offset_y = (canvas_height - scaled_height) / 2
    
    def _update_info_display(self):
        """Update the information display."""
        if self.video_width > 0 and self.video_height > 0:
            zoom_percent = int(self.scale_x * 100)
            info_text = f"{self.video_width}×{self.video_height} | {zoom_percent}%"
            self.info_label.config(text=info_text)
    
    def convert_canvas_to_video_coords(self, canvas_x: float, canvas_y: float) -> Tuple[float, float]:
        """Convert canvas coordinates to video coordinates."""
        # Adjust for offset
        adjusted_x = canvas_x - self.offset_x
        adjusted_y = canvas_y - self.offset_y
        
        # Apply inverse scaling
        if self.scale_x > 0:
            video_x = adjusted_x / self.scale_x
        else:
            video_x = adjusted_x
        
        if self.scale_y > 0:
            video_y = adjusted_y / self.scale_y
        else:
            video_y = adjusted_y
        
        return video_x, video_y
    
    def convert_video_to_canvas_coords(self, video_x: float, video_y: float) -> Tuple[float, float]:
        """Convert video coordinates to canvas coordinates."""
        # Apply scaling
        scaled_x = video_x * self.scale_x
        scaled_y = video_y * self.scale_y
        
        # Add offset
        canvas_x = scaled_x + self.offset_x
        canvas_y = scaled_y + self.offset_y
        
        return canvas_x, canvas_y
    
    def _fit_to_window(self):
        """Fit video to window size."""
        self._calculate_display_parameters()
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def _actual_size(self):
        """Show video at actual size (100%)."""
        self.scale_x = 1.0
        self.scale_y = 1.0
        self.offset_x = 0
        self.offset_y = 0
        
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def _zoom_in(self):
        """Zoom in by 25%."""
        self.scale_x *= 1.25
        self.scale_y *= 1.25
        
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def _zoom_out(self):
        """Zoom out by 25%."""
        self.scale_x *= 0.8
        self.scale_y *= 0.8
        
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def _on_click(self, event):
        """Handle mouse click."""
        # Convert coordinates
        canvas_coords = (event.x, event.y)
        video_coords = self.convert_canvas_to_video_coords(event.x, event.y)
        
        # Store drag start position
        self.drag_start_x = event.x
        self.drag_start_y = event.y
        
        # Check if clicking on a bowl for dragging
        self.dragging_item = self._find_item_at_position(video_coords)
        
        if self.dragging_item:
            # Change cursor to indicate draggable item
            try:
                self.canvas.configure(cursor="hand1")
            except:
                pass
        
        # Call callback if provided
        if self.click_callback:
            self.click_callback(event, canvas_coords, video_coords)
    
    def _find_item_at_position(self, video_coords):
        """Find if there's a draggable item at the given position."""
        x, y = video_coords
        
        # This will be set by the parent application when bowls are available
        if hasattr(self, '_draggable_items') and self._draggable_items:
            for item_id, item_data in self._draggable_items.items():
                item_x, item_y = item_data['position']
                radius = item_data.get('radius', 30)
                
                # Check if click is within the item's radius
                distance = ((x - item_x) ** 2 + (y - item_y) ** 2) ** 0.5
                if distance <= radius:
                    return {
                        'id': item_id,
                        'type': item_data['type'],
                        'original_position': (item_x, item_y),
                        'offset_x': x - item_x,
                        'offset_y': y - item_y
                    }
        
        return None
    
    def set_draggable_items(self, items):
        """Set items that can be dragged (bowls, etc.)."""
        self._draggable_items = items
    
    def _on_motion(self, event):
        """Handle mouse motion."""
        if self.video_width > 0 and self.video_height > 0:
            # Convert coordinates
            canvas_coords = (event.x, event.y)
            video_coords = self.convert_canvas_to_video_coords(event.x, event.y)
            
            # Call callback if provided
            if self.motion_callback:
                self.motion_callback(event, canvas_coords, video_coords)
    
    def _on_drag(self, event):
        """Handle mouse drag."""
        if not self.dragging:
            self.dragging = True
            # Change cursor to indicate dragging
            try:
                self.canvas.configure(cursor="hand2")
            except:
                pass
        
        # Convert coordinates
        canvas_coords = (event.x, event.y)
        video_coords = self.convert_canvas_to_video_coords(event.x, event.y)
        
        # Handle item dragging
        if hasattr(self, 'dragging_item') and self.dragging_item:
            # Calculate new position accounting for initial offset
            new_x = video_coords[0] - self.dragging_item['offset_x']
            new_y = video_coords[1] - self.dragging_item['offset_y']
            
            # Update the dragging item's position for real-time preview
            self.dragging_item['current_position'] = (new_x, new_y)
            
            # Draw preview of new position
            self._draw_drag_preview(new_x, new_y)
            
            # Call drag callback with item information
            if self.drag_callback:
                self.drag_callback(event, canvas_coords, video_coords, {
                    'item': self.dragging_item,
                    'new_position': (new_x, new_y)
                })
        else:
            # Regular drag callback
            if self.drag_callback:
                self.drag_callback(event, canvas_coords, video_coords)
    
    def _draw_drag_preview(self, x, y):
        """Draw a preview of the item being dragged."""
        if hasattr(self, 'dragging_item') and self.dragging_item:
            # Clear previous preview
            self.clear_overlays("drag_preview")
            
            # Draw preview circle/shape
            if self.dragging_item['type'] == 'bowl':
                radius = self.dragging_item.get('radius', 30)
                self.draw_overlay_circle(
                    (int(x), int(y)), radius, 
                    color="yellow", width=3, tags="drag_preview"
                )
                
                # Add preview text
                self.draw_overlay_text(
                    (int(x), int(y - radius - 15)), 
                    f"Moving {self.dragging_item['id']}", 
                    color="yellow", tags="drag_preview"
                )
    
    def _on_release(self, event):
        """Handle mouse release."""
        was_dragging_item = hasattr(self, 'dragging_item') and self.dragging_item
        
        if was_dragging_item:
            # Clear drag preview
            self.clear_overlays("drag_preview")
            
            # Finalize the drag operation
            final_coords = self.convert_canvas_to_video_coords(event.x, event.y)
            new_x = final_coords[0] - self.dragging_item['offset_x']
            new_y = final_coords[1] - self.dragging_item['offset_y']
            
            # Call release callback with final position
            if hasattr(self, 'release_callback') and self.release_callback:
                self.release_callback(event, self.dragging_item, (new_x, new_y))
            
            # Clear dragging state
            self.dragging_item = None
        
        self.dragging = False
        
        # Reset cursor
        try:
            self.canvas.configure(cursor="")
        except:
            pass
    
    def set_release_callback(self, callback):
        """Set callback for mouse release events."""
        self.release_callback = callback
    
    def _on_right_click(self, event):
        """Handle right mouse click."""
        # Could be used for context menu
        pass
    
    def _on_mousewheel(self, event):
        """Handle mouse wheel for zooming."""
        # Get mouse position for zoom center
        mouse_x = event.x
        mouse_y = event.y
        
        # Calculate zoom factor
        if event.delta > 0:
            zoom_factor = 1.1
        else:
            zoom_factor = 0.9
        
        # Apply zoom
        old_scale_x = self.scale_x
        old_scale_y = self.scale_y
        
        self.scale_x *= zoom_factor
        self.scale_y *= zoom_factor
        
        # Adjust offset to zoom towards mouse position
        scale_change_x = self.scale_x - old_scale_x
        scale_change_y = self.scale_y - old_scale_y
        
        self.offset_x -= (mouse_x - self.offset_x) * (scale_change_x / old_scale_x)
        self.offset_y -= (mouse_y - self.offset_y) * (scale_change_y / old_scale_y)
        
        # Update display
        if self.current_frame is not None:
            self.update_frame(self.current_frame)
    
    def draw_overlay_rectangle(self, coords: Tuple[int, int, int, int], 
                             color: str = "red", width: int = 2, tags: str = "overlay"):
        """Draw a rectangle overlay on the canvas."""
        x1, y1, x2, y2 = coords
        
        # Convert to canvas coordinates
        canvas_x1, canvas_y1 = self.convert_video_to_canvas_coords(x1, y1)
        canvas_x2, canvas_y2 = self.convert_video_to_canvas_coords(x2, y2)
        
        return self.canvas.create_rectangle(
            canvas_x1, canvas_y1, canvas_x2, canvas_y2,
            outline=color, width=width, tags=tags
        )
    
    def draw_overlay_circle(self, center: Tuple[int, int], radius: int,
                          color: str = "blue", width: int = 2, tags: str = "overlay"):
        """Draw a circle overlay on the canvas."""
        x, y = center
        
        # Convert to canvas coordinates
        canvas_x, canvas_y = self.convert_video_to_canvas_coords(x, y)
        canvas_radius = radius * self.scale_x  # Scale radius
        
        return self.canvas.create_oval(
            canvas_x - canvas_radius, canvas_y - canvas_radius,
            canvas_x + canvas_radius, canvas_y + canvas_radius,
            outline=color, width=width, tags=tags
        )
    
    def draw_overlay_text(self, position: Tuple[int, int], text: str,
                        color: str = "white", tags: str = "overlay"):
        """Draw text overlay on the canvas."""
        x, y = position
        
        # Convert to canvas coordinates
        canvas_x, canvas_y = self.convert_video_to_canvas_coords(x, y)
        
        return self.canvas.create_text(
            canvas_x, canvas_y, text=text, fill=color,
            font=("Arial", 10), tags=tags
        )
    
    def clear_overlays(self, tags: str = "overlay"):
        """Clear overlay elements."""
        self.canvas.delete(tags)
    
    def get_canvas_size(self) -> Tuple[int, int]:
        """Get current canvas size."""
        self.canvas.update_idletasks()
        return self.canvas.winfo_width(), self.canvas.winfo_height()
    
    def get_video_size(self) -> Tuple[int, int]:
        """Get video frame size."""
        return self.video_width, self.video_height
    
    def get_display_info(self) -> dict:
        """Get current display information."""
        return {
            'canvas_size': self.get_canvas_size(),
            'video_size': self.get_video_size(),
            'scale': (self.scale_x, self.scale_y),
            'offset': (self.offset_x, self.offset_y),
            'zoom_percent': int(self.scale_x * 100)
        }