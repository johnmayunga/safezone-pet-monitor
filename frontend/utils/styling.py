"""
frontend/utils/styling.py
Cross-platform GUI styling utilities for better appearance on Windows.
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
        
        # Fonts
        self.fonts = self._get_platform_fonts()
        
    def _get_platform_fonts(self):
        """Get appropriate fonts for each platform."""
        if self.is_windows:
            return {
                'default': ('Segoe UI', 9),
                'heading': ('Segoe UI', 12, 'bold'),
                'subheading': ('Segoe UI', 10, 'bold'),
                'small': ('Segoe UI', 8),
                'monospace': ('Consolas', 9),
                'large': ('Segoe UI', 14, 'bold')
            }
        elif self.is_macos:
            return {
                'default': ('SF Pro Display', 13),
                'heading': ('SF Pro Display', 16, 'bold'),
                'subheading': ('SF Pro Display', 14, 'bold'),
                'small': ('SF Pro Display', 11),
                'monospace': ('SF Mono', 12),
                'large': ('SF Pro Display', 18, 'bold')
            }
        else:  # Linux
            return {
                'default': ('Ubuntu', 10),
                'heading': ('Ubuntu', 14, 'bold'),
                'subheading': ('Ubuntu', 12, 'bold'),
                'small': ('Ubuntu', 9),
                'monospace': ('Ubuntu Mono', 10),
                'large': ('Ubuntu', 16, 'bold')
            }
    
    def configure_ttk_styles(self, root):
        """Configure ttk styles for modern appearance."""
        style = ttk.Style(root)
        
        # Try to use a modern theme
        if self.is_windows:
            # Try different themes in order of preference
            available_themes = style.theme_names()
            preferred_themes = ['vista', 'winnative', 'xpnative', 'default']
            
            for theme in preferred_themes:
                if theme in available_themes:
                    style.theme_use(theme)
                    break
        
        # Configure button styles
        style.configure('Modern.TButton',
                       font=self.fonts['default'],
                       padding=(12, 8),
                       relief='flat',
                       borderwidth=0,
                       focuscolor='none')
        
        style.map('Modern.TButton',
                 background=[('active', self.colors['primary']),
                            ('pressed', self.colors['primary']),
                            ('!active', self.colors['bg_secondary'])],
                 foreground=[('active', self.colors['text_light']),
                            ('pressed', self.colors['text_light']),
                            ('!active', self.colors['text_primary'])])
        
        # Success button style
        style.configure('Success.TButton',
                       font=self.fonts['default'],
                       padding=(12, 8),
                       relief='flat',
                       borderwidth=0,
                       focuscolor='none',
                       background=self.colors['success'],
                       foreground=self.colors['text_light'])
        
        style.map('Success.TButton',
                 background=[('active', '#45a049'),
                            ('pressed', '#3d8b40')])
        
        # Danger button style
        style.configure('Danger.TButton',
                       font=self.fonts['default'],
                       padding=(12, 8),
                       relief='flat',
                       borderwidth=0,
                       focuscolor='none',
                       background=self.colors['danger'],
                       foreground=self.colors['text_light'])
        
        # Configure label styles
        style.configure('Heading.TLabel',
                       font=self.fonts['heading'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Subheading.TLabel',
                       font=self.fonts['subheading'],
                       foreground=self.colors['text_primary'])
        
        style.configure('Small.TLabel',
                       font=self.fonts['small'],
                       foreground=self.colors['text_secondary'])
        
        # Configure frame styles
        style.configure('Card.TFrame',
                       relief='flat',
                       borderwidth=1,
                       background=self.colors['bg_primary'])
        
        # Configure entry styles
        style.configure('Modern.TEntry',
                       font=self.fonts['default'],
                       padding=(8, 6),
                       relief='flat',
                       borderwidth=1,
                       focuscolor=self.colors['primary'])
        
        # Configure notebook styles
        style.configure('Modern.TNotebook',
                       background=self.colors['bg_secondary'],
                       borderwidth=0)
        
        style.configure('Modern.TNotebook.Tab',
                       font=self.fonts['default'],
                       padding=[20, 8],
                       borderwidth=0)
        
        # Configure treeview styles
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
        
        # Configure scale styles
        style.configure('Modern.TScale',
                       background=self.colors['bg_secondary'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        # Configure progressbar styles
        style.configure('Modern.TProgressbar',
                       background=self.colors['primary'],
                       troughcolor=self.colors['bg_tertiary'],
                       borderwidth=0,
                       lightcolor=self.colors['primary'],
                       darkcolor=self.colors['primary'])
        
        return style
    
    def create_card_frame(self, parent, **kwargs):
        """Create a modern card-style frame."""
        default_options = {
            'style': 'Card.TFrame',
            'padding': 15,
            'relief': 'flat',
            'borderwidth': 1
        }
        default_options.update(kwargs)
        
        frame = ttk.Frame(parent, **default_options)
        
        # Add subtle shadow effect on Windows
        if self.is_windows:
            # Create shadow frame
            shadow = tk.Frame(parent, bg='#E0E0E0', height=2)
            return frame, shadow
        
        return frame
    
    def create_modern_button(self, parent, text, command=None, style='Modern.TButton', **kwargs):
        """Create a modern styled button."""
        default_options = {
            'style': style,
            'command': command
        }
        default_options.update(kwargs)
        
        button = ttk.Button(parent, text=text, **default_options)
        
        # Add hover effects for Windows
        if self.is_windows:
            def on_enter(e):
                button.state(['active'])
            
            def on_leave(e):
                button.state(['!active'])
            
            button.bind('<Enter>', on_enter)
            button.bind('<Leave>', on_leave)
        
        return button
    
    def create_modern_entry(self, parent, **kwargs):
        """Create a modern styled entry widget."""
        default_options = {
            'style': 'Modern.TEntry',
            'font': self.fonts['default']
        }
        default_options.update(kwargs)
        
        entry = ttk.Entry(parent, **default_options)
        
        # Add focus effects for Windows
        if self.is_windows:
            def on_focus_in(e):
                entry.configure(style='ModernFocus.TEntry')
            
            def on_focus_out(e):
                entry.configure(style='Modern.TEntry')
            
            entry.bind('<FocusIn>', on_focus_in)
            entry.bind('<FocusOut>', on_focus_out)
        
        return entry
    
    def apply_window_styling(self, window):
        """Apply modern styling to a window."""
        if self.is_windows:
            # Set window background
            window.configure(bg=self.colors['bg_secondary'])
            
            # Try to remove window border for modern look (Windows 10+)
            try:
                window.wm_attributes('-transparentcolor', window['bg'])
            except:
                pass
        
        # Set window icon and properties
        window.resizable(True, True)
        
        # Center window on screen
        self.center_window(window)
    
    def center_window(self, window):
        """Center window on screen."""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_color(self, color_name):
        """Get color value by name."""
        return self.colors.get(color_name, '#000000')
    
    def get_font(self, font_name):
        """Get font by name."""
        return self.fonts.get(font_name, self.fonts['default'])


# Global style instance
modern_style = ModernStyle()


def apply_modern_styling(root):
    """Apply modern styling to the entire application."""
    return modern_style.configure_ttk_styles(root)