"""
backend/services/sound_service.py
Sound alert service for pet activity notifications.
"""
import time
import platform
import threading
import numpy as np
from typing import Optional


class SoundAlertService:
    """Handles sound notifications for pet activity alerts."""
    
    def __init__(self):
        self.initialized = False
        self.sound_available = False
        self.pygame = None
        self.enabled = True
        self.last_alert_time = 0
        self.alert_cooldown = 2.0  # seconds
        
    def initialize(self) -> bool:
        """Initialize the sound system."""
        if self.initialized:
            return self.sound_available
        
        try:
            # Import pygame
            import pygame
            self.pygame = pygame
            
            # Hide pygame support prompt
            import os
            os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
            
            # Platform-specific initialization
            if platform.system() == "Darwin":  # macOS
                os.environ['SDL_VIDEODRIVER'] = 'dummy'
            
            # Initialize mixer
            self.pygame.mixer.pre_init(
                frequency=44100, 
                size=-16, 
                channels=2, 
                buffer=512
            )
            self.pygame.mixer.init()
            
            self.initialized = True
            self.sound_available = True
            print("✓ Sound system initialized successfully")
            
        except Exception as e:
            print(f"⚠ Sound system initialization failed: {e}")
            self.initialized = True
            self.sound_available = False
        
        return self.sound_available
    
    def play_alert(self, duration: float = 2.0, frequency: int = 440) -> bool:
        """
        Play an alert sound.
        
        Args:
            duration: Duration of the alert in seconds
            frequency: Frequency of the tone in Hz
            
        Returns:
            True if sound was played successfully
        """
        if not self.enabled:
            return False
        
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_alert_time < self.alert_cooldown:
            return False
        
        self.last_alert_time = current_time
        
        # Initialize if not already done
        if not self.initialized:
            self.initialize()
        
        if not self.sound_available:
            # Fallback to system bell
            self._system_bell()
            return False
        
        # Play sound in background thread
        thread = threading.Thread(
            target=self._play_tone,
            args=(duration, frequency),
            daemon=True
        )
        thread.start()
        
        return True
    
    def _play_tone(self, duration: float, frequency: int):
        """Play a tone using pygame."""
        try:
            # Generate tone
            sample_rate = 44100
            amplitude = 0.5
            
            # Create waveform
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            wave = amplitude * np.sin(frequency * 2 * np.pi * t)
            
            # Convert to 16-bit integers
            wave_normalized = np.int16(wave * 32767)
            
            # Create stereo wave
            stereo_wave = np.column_stack((wave_normalized, wave_normalized))
            
            # Play sound
            sound = self.pygame.sndarray.make_sound(stereo_wave)
            sound.play()
            
            # Wait for completion
            time.sleep(duration)
            
        except Exception as e:
            print(f"Error playing tone: {e}")
            self._system_bell()
    
    def _system_bell(self):
        """Fallback to system bell."""
        try:
            print('\a')  # ASCII bell character
            print("🔔 Alert: Pet activity detected!")
        except Exception:
            print("Alert: Pet activity detected!")
    
    def play_restricted_zone_alert(self) -> bool:
        """Play alert for restricted zone entry."""
        return self.play_alert(duration=3.0, frequency=880)  # Higher pitch, longer
    
    def play_feeding_alert(self) -> bool:
        """Play alert for feeding activities."""
        return self.play_alert(duration=1.0, frequency=440)  # Standard tone
    
    def play_general_alert(self) -> bool:
        """Play general alert sound."""
        return self.play_alert(duration=2.0, frequency=660)  # Mid-range tone
    
    def play_notification(self) -> bool:
        """Play a gentle notification sound."""
        return self.play_alert(duration=0.5, frequency=523)  # Short, gentle tone
    
    def test_sound(self) -> bool:
        """Test the sound system."""
        if not self.initialized:
            self.initialize()
        
        if self.sound_available:
            try:
                # Play a short test tone
                self._play_tone(0.5, 440)
                return True
            except Exception:
                return False
        else:
            # Test system bell
            self._system_bell()
            return False
    
    def set_enabled(self, enabled: bool):
        """Enable or disable sound alerts."""
        self.enabled = enabled
    
    def set_cooldown(self, seconds: float):
        """Set the cooldown period between alerts."""
        self.alert_cooldown = max(0.1, seconds)
    
    def get_status(self) -> dict:
        """Get sound system status."""
        return {
            'initialized': self.initialized,
            'available': self.sound_available,
            'enabled': self.enabled,
            'platform': platform.system(),
            'cooldown': self.alert_cooldown,
            'pygame_available': self.pygame is not None
        }
    
    def shutdown(self):
        """Shutdown the sound system."""
        if self.pygame and self.initialized:
            try:
                self.pygame.mixer.quit()
            except Exception:
                pass
        self.initialized = False
        self.sound_available = False
    
    def play_startup_sound(self):
        """Play startup notification."""
        if self.initialize():
            # Play ascending tones
            def startup_sequence():
                frequencies = [440, 523, 659, 784]  # A, C, E, G
                for freq in frequencies:
                    self._play_tone(0.2, freq)
                    time.sleep(0.1)
            
            thread = threading.Thread(target=startup_sequence, daemon=True)
            thread.start()
    
    def play_shutdown_sound(self):
        """Play shutdown notification."""
        if self.sound_available:
            # Play descending tones
            def shutdown_sequence():
                frequencies = [784, 659, 523, 440]  # G, E, C, A
                for freq in frequencies:
                    self._play_tone(0.2, freq)
                    time.sleep(0.1)
            
            thread = threading.Thread(target=shutdown_sequence, daemon=True)
            thread.start()
            time.sleep(1)  # Wait for completion before shutdown