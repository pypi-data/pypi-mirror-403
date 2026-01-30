"""
animsprite_pygame - Une librairie pour gérer les spritesheets/flipbooks dans Pygame

Une librairie légère et facile à utiliser pour créer des animations fluides
de sprites extraits depuis des spritesheets dans Pygame.

Usage:
    >>> from animsprite_pygame import Spritesheet, AnimatedSprite
    >>> sheet = Spritesheet("spritesheet.png")
    >>> frames = sheet.get_sprites_from_grid(32, 32, cols=4, rows=4)
    >>> sprite = AnimatedSprite(frames, x=100, y=100)
"""

from .spritesheet import Spritesheet, AnimatedSprite
from .version import __version__, __author__, __license__, __copyright__

__all__ = [
    "Spritesheet",
    "AnimatedSprite",
    "__version__",
    "__author__",
    "__license__",
]
