"""
Module principal pour la gestion des spritesheets et flipbooks dans Pygame
"""

import pygame
from typing import List, Tuple, Optional


class Spritesheet:
    """
    Classe pour charger et gérer un spritesheet (image contenant plusieurs sprites)
    """

    def __init__(self, filepath: str):
        """
        Initialise un spritesheet à partir d'une image.
        
        Args:
            filepath: Chemin vers l'image du spritesheet
        """
        self.image = pygame.image.load(filepath)
        self.filepath = filepath

    def get_sprite(
        self, 
        x: int, 
        y: int, 
        width: int, 
        height: int,
        scale: Optional[Tuple[int, int]] = None
    ) -> pygame.Surface:
        """
        Extrait un sprite unique du spritesheet.
        
        Args:
            x: Position X du sprite dans le spritesheet
            y: Position Y du sprite dans le spritesheet
            width: Largeur du sprite
            height: Hauteur du sprite
            scale: Tuple (width, height) pour redimensionner le sprite (optionnel)
        
        Returns:
            Une surface Pygame contenant le sprite extrait
        """
        sprite = pygame.Surface((width, height), pygame.SRCALPHA)
        sprite.blit(self.image, (0, 0), pygame.Rect(x, y, width, height))
        
        if scale:
            sprite = pygame.transform.scale(sprite, scale)
        
        return sprite

    def get_sprites_from_grid(
        self,
        sprite_width: int,
        sprite_height: int,
        cols: int,
        rows: Optional[int] = None,
        scale: Optional[Tuple[int, int]] = None,
        padding: int = 0,
        margin: int = 0
    ) -> List[pygame.Surface]:
        """
        Extrait tous les sprites du spritesheet organisés en grille.
        
        Args:
            sprite_width: Largeur de chaque sprite
            sprite_height: Hauteur de chaque sprite
            cols: Nombre de colonnes dans la grille
            rows: Nombre de lignes dans la grille (optionnel, extraire toutes les lignes)
            scale: Tuple (width, height) pour redimensionner les sprites (optionnel)
            padding: Espacement entre les sprites (en pixels)
            margin: Marge avant le premier sprite (en pixels)
        
        Returns:
            Liste des surfaces Pygame contenant les sprites extraits
        
        Exemple:
            # Spritesheet sans espacement
            frames = sheet.get_sprites_from_grid(32, 32, cols=4, rows=4)
            
            # Spritesheet avec 2 pixels entre les sprites
            frames = sheet.get_sprites_from_grid(32, 32, cols=4, rows=4, padding=2)
            
            # Spritesheet avec 1 pixel de marge et 2 pixels d'espacement
            frames = sheet.get_sprites_from_grid(32, 32, cols=4, rows=4, margin=1, padding=2)
        """
        sprites = []
        
        # Calculer le nombre de lignes si non spécifié
        if rows is None:
            total_height = self.image.get_height()
            # Hauteur totale = margin + (rows * (sprite_height + padding)) - padding
            rows = (total_height - margin + padding) // (sprite_height + padding)
        
        for row in range(rows):
            for col in range(cols):
                # Calculer la position en tenant compte de la marge et du padding
                x = margin + col * (sprite_width + padding)
                y = margin + row * (sprite_height + padding)
                
                # Vérifier que le sprite est dans les limites de l'image
                if x + sprite_width <= self.image.get_width() and \
                   y + sprite_height <= self.image.get_height():
                    sprite = self.get_sprite(x, y, sprite_width, sprite_height, scale)
                    sprites.append(sprite)
        
        return sprites


class AnimatedSprite(pygame.sprite.Sprite):
    """
    Classe pour animer des sprites extraits d'un spritesheet
    """

    def __init__(
        self,
        frames: List[pygame.Surface],
        x: float = 0,
        y: float = 0,
        animation_speed: float = 0.1,
        loop: bool = True
    ):
        """
        Initialise un sprite animé.
        
        Args:
            frames: Liste des surfaces Pygame représentant les frames de l'animation
            x: Position X initiale du sprite
            y: Position Y initiale du sprite
            animation_speed: Délai en secondes entre chaque frame
            loop: Si True, l'animation boucle; si False, elle s'arrête à la dernière frame
        """
        super().__init__()
        
        self.frames = frames
        self.current_frame = 0
        self.animation_speed = animation_speed
        self.loop = loop
        self.elapsed_time = 0
        self.is_playing = True
        self.is_finished = False
        
        self.image = frames[0] if frames else pygame.Surface((0, 0))
        self.rect = self.image.get_rect(topleft=(x, y))

    def update(self, delta_time: float = 1/60) -> None:
        """
        Mets à jour l'animation.
        
        Args:
            delta_time: Temps écoulé depuis la dernière frame (en secondes)
        """
        if not self.is_playing or not self.frames:
            return
        
        self.elapsed_time += delta_time
        
        if self.elapsed_time >= self.animation_speed:
            self.elapsed_time = 0
            self.current_frame += 1
            
            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.current_frame = len(self.frames) - 1
                    self.is_playing = False
                    self.is_finished = True
            
            self.image = self.frames[self.current_frame]

    def play(self) -> None:
        """Démarre l'animation"""
        self.is_playing = True
        self.is_finished = False

    def stop(self) -> None:
        """Arrête l'animation"""
        self.is_playing = False

    def reset(self) -> None:
        """Réinitialise l'animation au début"""
        self.current_frame = 0
        self.elapsed_time = 0
        self.is_finished = False
        self.image = self.frames[0] if self.frames else pygame.Surface((0, 0))

    def set_animation_speed(self, speed: float) -> None:
        """Change la vitesse de l'animation"""
        self.animation_speed = max(0.01, speed)

    def move(self, x: float, y: float) -> None:
        """Déplace le sprite"""
        self.rect.x = x
        self.rect.y = y

    def set_position(self, x: float, y: float) -> None:
        """Définit la position du sprite"""
        self.rect.topleft = (x, y)

    def get_position(self) -> Tuple[float, float]:
        """Retourne la position actuelle du sprite"""
        return (self.rect.x, self.rect.y)

    def get_current_frame_index(self) -> int:
        """Retourne l'index de la frame actuelle"""
        return self.current_frame

    def get_total_frames(self) -> int:
        """Retourne le nombre total de frames"""
        return len(self.frames)
