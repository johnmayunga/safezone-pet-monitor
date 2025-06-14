"""
frontend/utils/styling.py
Cross-platform GUI styling utilities with proper error handling and fallbacks.
"""
import tkinter as tk
import tkinter.ttk as ttk
import platform
import sys


class ModernStyle:
    """Modern styling for cross-platform GUI applications."""
    
    def __init__(self):
        self.platform = platform.system()
        self.is_windows = self.platform == "Windows"
        self.is_macos = self.platform == "Darwin"
        self.is_linux = self.platform == "Linux"
        
        # Color scheme
        self.colors = {
            'primary': '#2196F3',
            'secondary': '#4CAF50', 
            'accent': '#FF9800',
            'danger': '#F44336',
            'warning': '#FF5722',
            'success': '#4CAF50',
            'info': '#2196F3',
            
            # Background colors
            'bg_primary': '#FFFFFF',
            'bg_secondary': '#F5F5F5',
            'bg_tertiary': '#E0E0E0',
            'bg_dark': '#212121',
            
            # Text colors
            'text_primary': '#212121',
            'text_secondary': '#757575',
            'text_light': '#FFFFFF',
            
            # Border colors
            'border_light': '#E0E0E0',
            'border_medium': '#BDBDBD',
            'border_dark': '#757575',
        }
        
        # Fonts with fallbacks
        self.fonts = self._get_platform_fonts()
        
        # Track if styling has been applied
        self.styling_applied = False
        
    def _get_platform_fonts(self):
        """Get appropriate fonts for each platform with fallbacks."""
        if self.is_windows:
            return {
                'default': ('Segoe UI', 9, 'normal'),
                'heading': ('Segoe UI', 12, 'bold'),
                'subheading': ('Segoe UI', 10, 'bold'),
                'small': ('Segoe UI', 8, 'normal'),
                'monospace': ('Consolas', 9, 'normal'),
                'large': ('Segoe UI', 14, 'bold')
            }
        elif self.is_macos:
            # Use system fonts that actually exist on macOS
            return {
                'default': ('Helvetica Neue', 13, 'normal'),
                'heading': ('Helvetica Neue', 16, 'bold'),
                'subheading': ('Helvetica Neue', 14, 'bold'),
                'small': ('Helvetica Neue', 11, 'normal'),
                'monospace': ('Monaco', 12, 'normal'),
                'large': ('Helvetica Neue', 18, 'bold')
            }
        else:  # Linux
            return {
                'default': ('DejaVu Sans', 10, 'normal'),
                'heading': ('DejaVu Sans', 14, 'bold'),
                'subheading': ('DejaVu Sans', 12, 'bold'),
                'small': ('DejaVu Sans', 9, 'normal'),
                'monospace': ('DejaVu Sans Mono', 10, 'normal'),
                'large': ('DejaVu Sans', 16, 'bold')
            }
    
    def configure_ttk_styles(self, root):
        """Configure ttk styles for modern appearance with error handling."""
        try:
            style = ttk.Style(root)
            
            # Print available themes for debugging
            print(f"Available themes: {style.theme_names()}")
            print(f"Current theme: {style.theme_use()}")
            
            # Try to use a modern theme
            self._set_theme(style)
            
            # Configure all styles with error handling
            self._configure_button_styles(style)
            self._configure_label_styles(style)
            self._configure_frame_styles(style)
            self._configure_entry_styles(style)
            self._configure_other_styles(style)
            
            self.styling_applied = True
            print("✅ Modern styling applied successfully")
            return style
            
        except Exception as e:
            print(f"❌ Error applying modern styling: {e}")
            # Return basic style as fallback
            return ttk.Style(root)
    
    def _set_theme(self, style):
        """Set appropriate theme for platform."""
        try:
            available_themes = style.theme_names()
            
            if self.is_windows:
                # Windows theme preferences
                preferred_themes = ['vista', 'winnative', 'xpnative', 'default']
            elif self.is_macos:
                # macOS theme preferences
                preferred_themes = ['aqua', 'default']
            else:
                # Linux theme preferences
                preferred_themes = ['clam', 'alt', 'default']
            
            for theme in preferred_themes:
                if theme in available_themes:
                    style.theme_use(theme)
                    print(f"✅ Using theme: {theme}")
                    break
        except Exception as e:
            print(f"❌ Error setting theme: {e}")
    
    def _configure_button_styles(self, style):
        """Configure button styles with error handling."""
        try:
            # Modern button style
            style.configure('Modern.TButton',
                           font=self.fonts['default'],
                           padding=(12, 8),
                           relief='flat',
                           borderwidth=1,
                           focuscolor='none')
            
            # Success button style
            style.configure('Success.TButton',
                           font=self.fonts['default'],
                           padding=(12, 8),
                           relief='flat',
                           borderwidth=1,
                           focuscolor='none')
            
            # Danger button style
            style.configure('Danger.TButton',
                           font=self.fonts['default'],
                           padding=(12, 8),
                           relief='flat',
                           borderwidth=1,
                           focuscolor='none')
            
            # Apply color mappings
            style.map('Modern.TButton',
                     background=[('active', self.colors['primary']),
                                ('pressed', self.colors['primary']),
                                ('!active', self.colors['bg_secondary'])])
            
            style.map('Success.TButton',
                     background=[('active', '#45a049'),
                                ('pressed', '#3d8b40'),
                                ('!active', self.colors['success'])])
            
            style.map('Danger.TButton',
                     background=[('active', '#d32f2f'),
                                ('pressed', '#b71c1c'),
                                ('!active', self.colors['danger'])])
            
        except Exception as e:
            print(f"❌ Error configuring button styles: {e}")
    
    def _configure_label_styles(self, style):
        """Configure label styles with error handling."""
        try:
            style.configure('Heading.TLabel',
                           font=self.fonts['heading'],
                           foreground=self.colors['text_primary'])
            
            style.configure('Subheading.TLabel',
                           font=self.fonts['subheading'],
                           foreground=self.colors['text_primary'])
            
            style.configure('Small.TLabel',
                           font=self.fonts['small'],
                           foreground=self.colors['text_secondary'])
            
        except Exception as e:
            print(f"❌ Error configuring label styles: {e}")
    
    def _configure_frame_styles(self, style):
        """Configure frame styles with error handling."""
        try:
            style.configure('Card.TFrame',
                           relief='flat',
                           borderwidth=1,
                           background=self.colors['bg_primary'])
            
        except Exception as e:
            print(f"❌ Error configuring frame styles: {e}")
    
    def _configure_entry_styles(self, style):
        """Configure entry styles with error handling."""
        try:
            style.configure('Modern.TEntry',
                           font=self.fonts['default'],
                           padding=(8, 6),
                           relief='flat',
                           borderwidth=1)
            
            # Focus style
            style.configure('ModernFocus.TEntry',
                           font=self.fonts['default'],
                           padding=(8, 6),
                           relief='flat',
                           borderwidth=2)
            
        except Exception as e:
            print(f"❌ Error configuring entry styles: {e}")
    
    def _configure_other_styles(self, style):
        """Configure other widget styles with error handling."""
        try:
            # Notebook styles
            style.configure('Modern.TNotebook',
                           background=self.colors['bg_secondary'],
                           borderwidth=0)
            
            style.configure('Modern.TNotebook.Tab',
                           font=self.fonts['default'],
                           padding=[20, 8],
                           borderwidth=0)
            
            # Treeview styles
            style.configure('Modern.Treeview',
                           font=self.fonts['default'],
                           background=self.colors['bg_primary'],
                           foreground=self.colors['text_primary'],
                           fieldbackground=self.colors['bg_primary'],
                           borderwidth=0,
                           relief='flat')
            
            style.configure('Modern.Treeview.Heading',
                           font=self.fonts['subheading'],
                           background=self.colors['bg_secondary'],
                           foreground=self.colors['text_primary'],
                           borderwidth=1,
                           relief='flat')
            
        except Exception as e:
            print(f"❌ Error configuring other styles: {e}")
    
    def create_modern_button(self, parent, text, command=None, style='Modern.TButton', **kwargs):
        """Create a modern styled button with fallback."""
        try:
            # Use styled button if styling was applied
            if self.styling_applied:
                default_options = {
                    'style': style,
                    'command': command
                }
                default_options.update(kwargs)
                
                button = ttk.Button(parent, text=text, **default_options)
                
                # Add hover effects
                self._add_button_hover_effects(button)
                
                return button
            else:
                # Fallback to regular button
                return tk.Button(parent, text=text, command=command, **kwargs)
                
        except Exception as e:
            print(f"❌ Error creating modern button: {e}")
            # Fallback to regular button
            return tk.Button(parent, text=text, command=command)
    
    def _add_button_hover_effects(self, button):
        """Add hover effects to button."""
        try:
            def on_enter(e):
                button.state(['active'])
            
            def on_leave(e):
                button.state(['!active'])
            
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)
        except Exception as e:
            print(f"❌ Error adding hover effects: {e}")
    
    def apply_window_styling(self, window):
        """Apply modern styling to a window with error handling."""
        try:
            # Set window background
            window.configure(bg=self.colors['bg_secondary'])
            
            # Set minimum size
            window.minsize(800, 600)
            
            # Center window
            self.center_window(window)
            
            print("✅ Window styling applied")
            
        except Exception as e:
            print(f"❌ Error applying window styling: {e}")
    
    def center_window(self, window):
        """Center window on screen with error handling."""
        try:
            window.update_idletasks()
            width = window.winfo_reqwidth()
            height = window.winfo_reqheight()
            
            # Get screen dimensions
            screen_width = window.winfo_screenwidth()
            screen_height = window.winfo_screenheight()
            
            # Calculate position
            x = (screen_width // 2) - (width // 2)
            y = (screen_height // 2) - (height // 2)
            
            # Ensure window is not off-screen
            x = max(0, x)
            y = max(0, y)
            
            window.geometry(f'{width}x{height}+{x}+{y}')
            
        except Exception as e:
            print(f"❌ Error centering window: {e}")
    
    def get_color(self, color_name):
        """Get color value by name with fallback."""
        return self.colors.get(color_name, '#000000')
    
    def get_font(self, font_name):
        """Get font by name with fallback."""
        return self.fonts.get(font_name, self.fonts['default'])


# Global style instance
modern_style = ModernStyle()


def apply_modern_styling(root):
    """Apply modern styling to the entire application with error handling."""
    try:
        print("🎨 Applying modern styling...")
        return modern_style.configure_ttk_styles(root)
    except Exception as e:
        print(f"❌ Failed to apply modern styling: {e}")
        return ttk.Style(root)  # Return basic style as fallback


# Debug function to test styling
def test_styling():
    """Test function to verify styling works."""
    root = tk.Tk()
    root.title("Style Test")
    
    # Apply styling
    style = apply_modern_styling(root)
    modern_style.apply_window_styling(root)
    
    # Create test widgets
    frame = ttk.Frame(root, style='Card.TFrame', padding=20)
    frame.pack(padx=20, pady=20, fill='both', expand=True)
    
    ttk.Label(frame, text="Heading", style='Heading.TLabel').pack(pady=5)
    ttk.Label(frame, text="Subheading", style='Subheading.TLabel').pack(pady=5)
    ttk.Label(frame, text="Small text", style='Small.TLabel').pack(pady=5)
    
    modern_style.create_modern_button(frame, "Modern Button").pack(pady=5)
    modern_style.create_modern_button(frame, "Success Button", style='Success.TButton').pack(pady=5)
    modern_style.create_modern_button(frame, "Danger Button", style='Danger.TButton').pack(pady=5)
    
    ttk.Entry(frame, style='Modern.TEntry').pack(pady=5, fill='x')
    
    root.mainloop()


if __name__ == "__main__":
    test_styling()