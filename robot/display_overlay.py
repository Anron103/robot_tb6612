import pygame
import os
import sys
import signal
import threading
import time
from pathlib import Path
from config import UPDATE_LOOP_FPS
#handles the overlay window rendering and management
class DisplayOverlay:
    def __init__(self, screen_size=(848, 480), position=(0, 0)): # 848, 450 for top panel to show itself | 848, 480 for full screen
        # initialize variables
        self.screen_size = screen_size
        self.position = position
        self.current_image = None
        self.running = True
        self.image_path = Path(__file__).parent
        self.last_image_name = None
        # configure sdl for minimal window interference
        os.environ['SDL_VIDEO_WINDOW_POS'] = f'{position[0]},{position[1]}'
        os.environ['SDL_VIDEO_ALLOW_SCREENSAVER'] = '1'
        os.environ['SDL_HINT_VIDEO_X11_NET_WM_BYPASS_COMPOSITOR'] = '0'
        pygame.init()
        pygame.display.set_caption("robot eyes overlay")
        # create borderless transparent window
        self.screen = pygame.display.set_mode(
            self.screen_size,
            pygame.NOFRAME | pygame.SRCALPHA
        )
        # configure x11 for true overlay behavior
        self._configure_x11_overlay()
        # start with transparent background
        self.screen.fill((0, 0, 0, 1))
        pygame.display.update()
        # start rendering thread
        self.update_thread = threading.Thread(target=self._update_loop, daemon=True)
        self.update_thread.start()

    def _configure_x11_overlay(self):
        try:
            import Xlib.display
            import Xlib.X
            import Xlib.Xatom
            import Xlib.ext.shape
            # get x11 window id from pygame
            wm_info = pygame.display.get_wm_info()
            window_id = wm_info['window']
            # connect to x server
            display = Xlib.display.Display()
            xwindow = display.create_resource_object('window', window_id)
            # set window to stay on top and sticky
            xwindow.change_property(
                display.intern_atom('_NET_WM_STATE'),
                Xlib.Xatom.ATOM,
                32,
                [
                    display.intern_atom('_NET_WM_STATE_ABOVE'),
                    display.intern_atom('_NET_WM_STATE_STICKY')
                ]
            )
            # set window type to dock for proper layering
            xwindow.change_property(
                display.intern_atom('_NET_WM_WINDOW_TYPE'),
                Xlib.Xatom.ATOM,
                32,
                [display.intern_atom('_NET_WM_WINDOW_TYPE_DOCK')]
            )
            region = xwindow.create_region()
            xwindow.shape_mask(Xlib.ext.shape.SO.Set, Xlib.ext.shape.SK.Input, 0, 0, region)
            display.sync()
        except ImportError:
            pass
        except Exception:
            pass

    def _load_image(self, img_name):
        # try to load actual image file
        for ext in ['.png', '.jpg', '.jpeg', '.bmp']:
            path = self.image_path / f"{img_name}{ext}"
            if path.exists():
                try:
                    img = pygame.image.load(str(path)).convert_alpha()
                    return pygame.transform.scale(img, self.screen_size)
                except Exception:
                    continue
        # fallback: colored rectangle with text label
        colors = {
            'closed': (50, 50, 50, 230),
            'common': (70, 130, 180, 230),
            'crazy': (255, 0, 0, 230),
            'cry': (100, 100, 255, 230),
            'error': (255, 50, 50, 230),
            'evil': (128, 0, 128, 230),
            'flinch': (255, 165, 0, 230),
            'happy': (46, 139, 87, 230),
            'irritate': (255, 215, 0, 230),
            'pop': (255, 105, 180, 230),
            'rolled': (138, 43, 226, 230),
            'sad': (70, 130, 180, 230),
        }
        color = colors.get(img_name, (80, 80, 80, 230))
        surface = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        surface.fill(color)
        try:
            font = pygame.font.SysFont('DejaVu Sans', 36, bold=True)
        except:
            font = pygame.font.SysFont('Arial', 36, bold=True)
        text = font.render(img_name.upper(), True, (255, 255, 255))
        text_rect = text.get_rect(center=(self.screen_size[0]//2, self.screen_size[1]//2))
        surface.blit(text, text_rect)
        return surface
#change displayed image without blocking
    def show_image(self, img_name):
        if not self.running or img_name == self.last_image_name:
            return
        try:
            self.current_image = self._load_image(img_name)
            self.last_image_name = img_name
        except Exception:
            pass
    def hide(self):
        self.current_image = pygame.Surface(self.screen_size, pygame.SRCALPHA)
        self.current_image.fill((0, 0, 0, 1))
        self.last_image_name = None
#background thread for rendering images
    def _update_loop(self):
        clock = pygame.time.Clock()
        while self.running:
            # handle minimal events to keep window alive
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            # render current image
            if self.current_image:
                self.screen.fill((0, 0, 0, 1))
                self.screen.blit(self.current_image, (0, 0))
                pygame.display.update()
            clock.tick(UPDATE_LOOP_FPS)

    def stop(self):
        self.running = False
        if hasattr(self, 'update_thread'):
            self.update_thread.join(timeout=1.0)
        pygame.quit()

# global overlay instance
_overlay = None

def init_overlay(screen_size=(848, 480), position=(0, 0)):
    global _overlay
    if _overlay is None:
        _overlay = DisplayOverlay(screen_size, position)
        _overlay.show_image('closed')
    return _overlay

def show_image(img_name):
    """
    show specific image on overlay
    args:
        img_name: name of image file without extension
    """
    if _overlay:
        _overlay.show_image(img_name)

def hide_overlay():
    if _overlay:
        _overlay.hide()

def shutdown_overlay():
    global _overlay
    if _overlay:
        _overlay.stop()
        _overlay = None

# signal handler for clean shutdown
def _signal_handler(sig, frame):
    shutdown_overlay()
    sys.exit(0)

signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)

if __name__ == "__main__":
    # test mode
    overlay = init_overlay()
    print("test mode: showing eye images in sequence...")
    for img in ['closed', 'common', 'happy', 'irritate', 'pop', 'rolled', 'sad', 'cry', 'evil', 'error']:
        show_image(img)
        time.sleep(1.0)
    print("test complete, shutting down...")
    shutdown_overlay()