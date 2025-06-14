"""
frontend/components/statistics_panel.py
Statistics display panel component.
"""
import tkinter as tk
import tkinter.ttk as ttk
from typing import Dict, List
from backend.data.statistics import ActivityStatistics


class StatisticsPanel:
    """Panel for displaying real-time activity statistics."""
    
    def __init__(self, parent, row: int, column: int, statistics: ActivityStatistics):
        self.parent = parent
        self.statistics = statistics
        
        # Create the statistics panel
        self._create_panel(row, column)
        
        # Update interval (milliseconds)
        self.update_interval = 2000
        self._schedule_update()
    
    def _create_panel(self, row: int, column: int):
        """Create the statistics display panel."""
        # Main frame
        self.frame = ttk.LabelFrame(self.parent, text="Statistics", padding=10)
        self.frame.grid(row=row, column=column, padx=10, pady=5, sticky="nsew")
        
        # Configure frame to prevent expansion
        self.frame.config(width=300)
        self.frame.grid_propagate(False)
        
        # Create notebook for multiple tabs
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.pack(fill="both", expand=True)
        
        # Create tabs
        self._create_main_stats_tab()
        self._create_zone_stats_tab()
        self._create_timeline_tab()
    
    def _create_main_stats_tab(self):
        """Create the main statistics tab."""
        self.main_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.main_frame, text="Main Stats")
        
        # Statistics labels dictionary
        self.stats_labels = {}
        
        # Define main statistics to display
        main_stats = [
            ("total_detections", "Total Detections", "🔍"),
            ("eating_events", "Eating Events", "🍽️"),
            ("drinking_events", "Drinking Events", "💧"),
            ("restricted_zone_violations", "Zone Violations", "⚠️")
        ]
        
        for i, (key, label, icon) in enumerate(main_stats):
            # Create stat card frame
            card_frame = ttk.Frame(self.main_frame, relief="solid", borderwidth=1)
            card_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=2)
            card_frame.grid_columnconfigure(1, weight=1)
            
            # Icon and label
            ttk.Label(card_frame, text=icon, font=("Arial", 12)).grid(row=0, column=0, padx=5)
            ttk.Label(card_frame, text=label, font=("Arial", 9)).grid(row=0, column=1, sticky="w")
            
            # Value label
            value_label = ttk.Label(card_frame, text="0", font=("Arial", 12, "bold"))
            value_label.grid(row=0, column=2, padx=5)
            
            self.stats_labels[key] = value_label
        
        # Configure grid weights
        self.main_frame.grid_columnconfigure(0, weight=1)
    
    def _create_zone_stats_tab(self):
        """Create the zone statistics tab."""
        self.zone_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.zone_frame, text="Zones")
        
        # Create treeview for zone statistics
        columns = ("Zone", "Visits", "Duration")
        self.zone_tree = ttk.Treeview(self.zone_frame, columns=columns, show="headings", height=8)
        
        # Configure columns
        self.zone_tree.heading("Zone", text="Zone")
        self.zone_tree.heading("Visits", text="Visits")
        self.zone_tree.heading("Duration", text="Duration")
        
        self.zone_tree.column("Zone", width=80, minwidth=60)
        self.zone_tree.column("Visits", width=50, minwidth=40)
        self.zone_tree.column("Duration", width=80, minwidth=60)
        
        # Add scrollbar
        zone_scrollbar = ttk.Scrollbar(self.zone_frame, orient="vertical", command=self.zone_tree.yview)
        self.zone_tree.configure(yscrollcommand=zone_scrollbar.set)
        
        # Pack widgets
        self.zone_tree.pack(side="left", fill="both", expand=True)
        zone_scrollbar.pack(side="right", fill="y")
    
    def _create_timeline_tab(self):
        """Create the activity timeline tab."""
        self.timeline_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.timeline_frame, text="Timeline")
        
        # Create canvas for timeline visualization
        self.timeline_canvas = tk.Canvas(self.timeline_frame, height=200, bg="white")
        self.timeline_canvas.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Timeline info
        info_frame = ttk.Frame(self.timeline_frame)
        info_frame.pack(fill="x", padx=5, pady=2)
        
        self.peak_hour_label = ttk.Label(info_frame, text="Peak Hour: --", font=("Arial", 8))
        self.peak_hour_label.pack(side="left")
        
        self.total_activity_label = ttk.Label(info_frame, text="Total: 0", font=("Arial", 8))
        self.total_activity_label.pack(side="right")
    
    def update_display(self):
        """Update all statistics displays."""
        self._update_main_stats()
        self._update_zone_stats()
        self._update_timeline()
    
    def _update_main_stats(self):
        """Update main statistics display."""
        stats = self.statistics.stats
        
        for stat_key, label in self.stats_labels.items():
            value = stats.get(stat_key, 0)
            label.config(text=str(value))
            
            # Color code violations
            if stat_key == "restricted_zone_violations" and value > 0:
                label.config(foreground="red")
            else:
                label.config(foreground="black")
    
    def _update_zone_stats(self):
        """Update zone statistics display."""
        # Clear existing items
        for item in self.zone_tree.get_children():
            self.zone_tree.delete(item)
        
        # Get zone statistics
        zone_stats = self.statistics.get_zone_statistics()
        
        # Add items to treeview
        for stat in zone_stats:
            self.zone_tree.insert("", "end", values=(
                stat['name'],
                stat['visits'],
                stat['duration']
            ))
    
    def _update_timeline(self):
        """Update activity timeline visualization."""
        self.timeline_canvas.delete("all")
        
        # Get timeline data
        timeline = self.statistics.get_activity_timeline()
        if not timeline:
            self.timeline_canvas.create_text(
                150, 100, text="No activity data", 
                fill="gray", font=("Arial", 10)
            )
            return
        
        # Canvas dimensions
        canvas_width = self.timeline_canvas.winfo_width()
        canvas_height = self.timeline_canvas.winfo_height()
        
        if canvas_width <= 1:
            canvas_width = 280
        if canvas_height <= 1:
            canvas_height = 200
        
        # Calculate bar dimensions
        margin = 20
        bar_width = (canvas_width - 2 * margin) / 24
        max_height = canvas_height - 2 * margin
        
        # Find maximum value for scaling
        max_value = max(timeline.values()) if timeline else 1
        if max_value == 0:
            max_value = 1
        
        # Draw timeline bars
        peak_hour = -1
        peak_value = 0
        total_activity = 0
        
        for hour in range(24):
            count = timeline.get(hour, 0)
            total_activity += count
            
            if count > peak_value:
                peak_value = count
                peak_hour = hour
            
            # Calculate bar height
            bar_height = (count / max_value) * max_height * 0.8
            
            # Calculate bar position
            x1 = margin + hour * bar_width
            y1 = canvas_height - margin
            x2 = x1 + bar_width - 2
            y2 = y1 - bar_height
            
            # Choose color based on activity level
            if count == 0:
                color = "#e0e0e0"
            elif count == peak_value and peak_value > 0:
                color = "#ff6b6b"  # Peak hour in red
            elif count > max_value * 0.5:
                color = "#4ecdc4"  # High activity in teal
            else:
                color = "#95e1d3"  # Normal activity in light teal
            
            # Draw bar
            self.timeline_canvas.create_rectangle(
                x1, y1, x2, y2, fill=color, outline="#333", width=1
            )
            
            # Add hour label for every 4th hour
            if hour % 4 == 0:
                self.timeline_canvas.create_text(
                    x1 + bar_width/2, y1 + 10, 
                    text=f"{hour:02d}", font=("Arial", 6), fill="gray"
                )
            
            # Add count label on top of bar if significant
            if count > 0 and bar_height > 15:
                self.timeline_canvas.create_text(
                    x1 + bar_width/2, y2 - 5,
                    text=str(count), font=("Arial", 6), fill="white"
                )
        
        # Update info labels
        if peak_hour >= 0:
            self.peak_hour_label.config(text=f"Peak Hour: {peak_hour:02d}:00 ({peak_value})")
        else:
            self.peak_hour_label.config(text="Peak Hour: --")
        
        self.total_activity_label.config(text=f"Total: {total_activity}")
    
    def _schedule_update(self):
        """Schedule the next update."""
        self.parent.after(self.update_interval, self._update_and_schedule)
    
    def _update_and_schedule(self):
        """Update display and schedule next update."""
        try:
            self.update_display()
        except Exception as e:
            print(f"Statistics update error: {e}")
        finally:
            self._schedule_update()
    
    def get_current_stats(self) -> Dict:
        """Get current statistics summary."""
        return {
            'main_stats': dict(self.statistics.stats),
            'zone_stats': self.statistics.get_zone_statistics(),
            'timeline': self.statistics.get_activity_timeline()
        }
    
    def reset_stats(self):
        """Reset all statistics."""
        self.statistics.reset_statistics()
        self.update_display()
    
    def set_update_interval(self, interval_ms: int):
        """Set the update interval in milliseconds."""
        self.update_interval = max(500, interval_ms)  # Minimum 500ms