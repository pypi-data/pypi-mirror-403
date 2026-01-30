"""
Tests unitaires pour la librairie animsprite_pygame
"""

import pytest
import pygame
import os
from pathlib import Path
from animsprite_pygame import Spritesheet, AnimatedSprite


# Créer une image de test simple
def create_test_image(width, height, filename):
    """Crée une image de test simple"""
    pygame.init()
    surface = pygame.Surface((width, height))
    surface.fill((255, 0, 0))
    pygame.image.save(surface, filename)


@pytest.fixture(scope="module")
def test_image():
    """Fixture pour créer une image de test"""
    test_dir = Path(__file__).parent
    img_path = test_dir / "test_spritesheet.png"
    
    if not img_path.exists():
        create_test_image(128, 128, str(img_path))
    
    yield img_path
    
    # Nettoyage
    if img_path.exists():
        img_path.unlink()


class TestSpritesheet:
    """Tests pour la classe Spritesheet"""
    
    def test_init(self, test_image):
        """Test l'initialisation d'un spritesheet"""
        sheet = Spritesheet(str(test_image))
        assert sheet.image is not None
        assert sheet.filepath == str(test_image)
    
    def test_get_sprite(self, test_image):
        """Test l'extraction d'un sprite unique"""
        sheet = Spritesheet(str(test_image))
        sprite = sheet.get_sprite(0, 0, 32, 32)
        
        assert sprite is not None
        assert sprite.get_width() == 32
        assert sprite.get_height() == 32
    
    def test_get_sprite_with_scale(self, test_image):
        """Test l'extraction d'un sprite avec redimensionnement"""
        sheet = Spritesheet(str(test_image))
        sprite = sheet.get_sprite(0, 0, 32, 32, scale=(16, 16))
        
        assert sprite.get_width() == 16
        assert sprite.get_height() == 16
    
    def test_get_sprites_from_grid(self, test_image):
        """Test l'extraction des sprites en grille"""
        sheet = Spritesheet(str(test_image))
        sprites = sheet.get_sprites_from_grid(
            sprite_width=32,
            sprite_height=32,
            cols=2,
            rows=2
        )
        
        assert len(sprites) == 4
        assert all(s.get_width() == 32 for s in sprites)
        assert all(s.get_height() == 32 for s in sprites)


class TestAnimatedSprite:
    """Tests pour la classe AnimatedSprite"""
    
    def test_init(self, test_image):
        """Test l'initialisation d'un sprite animé"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        
        sprite = AnimatedSprite(frames=frames, x=100, y=100)
        
        assert sprite.rect.x == 100
        assert sprite.rect.y == 100
        assert sprite.get_total_frames() == 4
        assert sprite.is_playing
    
    def test_play_pause(self, test_image):
        """Test play et pause"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        sprite = AnimatedSprite(frames=frames)
        
        sprite.stop()
        assert not sprite.is_playing
        
        sprite.play()
        assert sprite.is_playing
    
    def test_reset(self, test_image):
        """Test la réinitialisation"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        sprite = AnimatedSprite(frames=frames)
        
        sprite.current_frame = 2
        sprite.reset()
        
        assert sprite.current_frame == 0
        assert sprite.elapsed_time == 0
    
    def test_set_animation_speed(self, test_image):
        """Test le changement de vitesse d'animation"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        sprite = AnimatedSprite(frames=frames, animation_speed=0.1)
        
        sprite.set_animation_speed(0.2)
        assert sprite.animation_speed == 0.2
        
        # Test que la vitesse minimum est respectée
        sprite.set_animation_speed(0.001)
        assert sprite.animation_speed >= 0.01
    
    def test_position(self, test_image):
        """Test la gestion de la position"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        sprite = AnimatedSprite(frames=frames, x=50, y=50)
        
        assert sprite.get_position() == (50, 50)
        
        sprite.set_position(100, 100)
        assert sprite.get_position() == (100, 100)
        
        sprite.move(10, 10)
        assert sprite.get_position() == (110, 110)
    
    def test_animation_loop(self, test_image):
        """Test la boucle d'animation"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        sprite = AnimatedSprite(frames=frames, animation_speed=0.01, loop=True)
        
        # Simuler plusieurs updates pour passer à travers toutes les frames
        for _ in range(100):
            sprite.update(0.02)
        
        # Avec loop=True, on devrait être revenu au début
        assert sprite.current_frame >= 0
        assert not sprite.is_finished
    
    def test_animation_no_loop(self, test_image):
        """Test quand l'animation ne boucle pas"""
        sheet = Spritesheet(str(test_image))
        frames = sheet.get_sprites_from_grid(32, 32, 2, 2)
        sprite = AnimatedSprite(frames=frames, animation_speed=0.01, loop=False)
        
        # Simuler plusieurs updates
        for _ in range(100):
            sprite.update(0.02)
        
        # Avec loop=False, l'animation doit être terminée
        assert sprite.is_finished
        assert sprite.current_frame == len(frames) - 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
