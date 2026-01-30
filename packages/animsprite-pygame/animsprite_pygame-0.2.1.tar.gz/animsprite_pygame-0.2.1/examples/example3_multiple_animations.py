"""
Exemple 3: Animations multiples et changement de state
"""

import pygame
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer la librairie locale
sys.path.insert(0, str(Path(__file__).parent.parent))

from animsprite_pygame import Spritesheet, AnimatedSprite

# Initialiser Pygame
pygame.init()

# Paramètres de l'écran
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 768
FPS = 60

# Créer l'écran
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Spritesheet - Exemple 3: Animations Multiples")
clock = pygame.time.Clock()

# Classe pour gérer plusieurs animations
class Character(AnimatedSprite):
    def __init__(self, animations_dict, x, y):
        """
        animations_dict: Dictionnaire avec les animations
        {
            'idle': [frames],
            'walk': [frames],
            'attack': [frames]
        }
        """
        self.animations_dict = animations_dict
        self.current_animation = 'idle'
        
        # Initialiser avec l'animation idle
        super().__init__(
            frames=animations_dict['idle'],
            x=x,
            y=y,
            animation_speed=0.1,
            loop=True
        )
    
    def set_animation(self, animation_name):
        """Change l'animation actuelle"""
        if animation_name in self.animations_dict and animation_name != self.current_animation:
            self.current_animation = animation_name
            self.frames = self.animations_dict[animation_name]
            self.reset()
            self.play()  # Relancer l'animation
            
            # Déterminer si l'animation boucle
            if animation_name == 'attack':
                self.loop = False
            else:
                self.loop = True
    
    def get_current_animation(self):
        """Retourne l'animation actuelle"""
        return self.current_animation

try:
    # Charger les spritesheets (vous auriez besoin de plusieurs fichiers ou d'un seul avec différentes animations)
    sheet = Spritesheet("../assets/spritesheet_example3.png")
    
    # Extraire différentes animations du spritesheet
    # Note: Ceci est un exemple simplifié. En réalité, vous auriez probablement
    # des spritesheets séparés pour chaque animation
    
    all_frames = sheet.get_sprites_from_grid(
        sprite_width=512,
        sprite_height=512,
        cols=1,
        rows=22
    )
    
    # Diviser les frames en animations (exemple basique)
    animations = {
        'idle': all_frames[0:8],      # Premières 8 frames
        'walk': all_frames[8:16],      # 8 frames suivantes
        'attack': all_frames[16:22]    # Les 6 dernières
    }
    
    # Créer le personnage
    character = Character(animations, 40, 40)
    
    all_sprites = pygame.sprite.Group(character)
    
    # Variables de contrôle
    current_state = 'idle'
    
    # Boucle principale
    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000
        
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    character.set_animation('idle')
                    current_state = 'idle'
                elif event.key == pygame.K_2:
                    character.set_animation('walk')
                    current_state = 'walk'
                elif event.key == pygame.K_3:
                    character.set_animation('attack')
                    current_state = 'attack'
                elif event.key == pygame.K_ESCAPE:
                    running = False
        
        # Mettre à jour
        all_sprites.update(delta_time)
        
        # Si l'animation attack est terminée, revenir à idle
        if current_state == 'attack' and character.is_finished:
            character.set_animation('idle')
            current_state = 'idle'
        
        # Affichage
        screen.fill((40, 40, 60))
        all_sprites.draw(screen)
        
        # Afficher les infos
        font_large = pygame.font.Font(None, 32)
        font_small = pygame.font.Font(None, 24)
        
        animation_text = font_large.render(
            f"Animation: {character.get_current_animation().upper()}",
            True,
            (255, 200, 100)
        )
        screen.blit(animation_text, (SCREEN_WIDTH // 2 - 150, 50))
        
        frame_text = font_small.render(
            f"Frame: {character.get_current_frame_index() + 1}/{character.get_total_frames()}",
            True,
            (255, 255, 255)
        )
        screen.blit(frame_text, (10, 10))
        
        controls = [
            "Touches:",
            "1: Idle",
            "2: Walk",
            "3: Attack",
            "ESC: Quitter"
        ]
        
        for i, text in enumerate(controls):
            control_text = font_small.render(text, True, (200, 200, 200))
            screen.blit(control_text, (10, 50 + i * 30))
        
        pygame.display.flip()

except FileNotFoundError:
    print("Erreur: Le fichier 'assets/spritesheet_example3.png' n'a pas été trouvé.")
    print("Veuillez créer ou télécharger un spritesheet et le placer dans le dossier 'assets'.")

pygame.quit()
sys.exit()
