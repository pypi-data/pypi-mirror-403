"""
Exemple 1: Utilisation basique avec une animation simple
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
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Créer l'écran
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Spritesheet - Exemple 1: Animation Simple")
clock = pygame.time.Clock()

# Créer un groupe de sprites
sprites_group = pygame.sprite.Group()

# Note: Pour cet exemple, vous devez créer ou télécharger un spritesheet
# Vous pouvez utiliser un spritesheet de personnage/monstre disponible en ligne
# Ou créer votre propre image avec des frames

try:
    # Charger le spritesheet
    sheet = Spritesheet("../assets/spritesheet_example1.png")
    
    # Extraire les frames (exemple: grille 4x4 avec sprites de 32x32 pixels)
    frames = sheet.get_sprites_from_grid(
        sprite_width=512,
        sprite_height=512,
        cols=1,
        rows=8
    )
    
    # Créer un sprite animé
    animated_sprite = AnimatedSprite(
        frames=frames,
        x=40,
        y=40,
        animation_speed=0.1,  # Délai de 0.1 secondes entre les frames
        loop=True
    )
    sprites_group.add(animated_sprite)
    
    # Boucle principale
    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000  # Temps écoulé en secondes
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Espace: pause/reprendre l'animation
                    if animated_sprite.is_playing:
                        animated_sprite.stop()
                    else:
                        animated_sprite.play()
                elif event.key == pygame.K_r:
                    # R: réinitialiser l'animation
                    animated_sprite.reset()
        
        # Mettre à jour les sprites
        sprites_group.update(delta_time)
        
        # Afficher
        screen.fill((50, 50, 50))
        sprites_group.draw(screen)
        
        # Afficher les infos
        font = pygame.font.Font(None, 36)
        text = font.render(
            f"Frame: {animated_sprite.get_current_frame_index() + 1}/{animated_sprite.get_total_frames()}",
            True,
            (255, 255, 255)
        )
        screen.blit(text, (10, 10))
        
        info_text = font.render(
            "SPACE: Pause | R: Reset",
            True,
            (200, 200, 200)
        )
        screen.blit(info_text, (10, 50))
        
        pygame.display.flip()

except FileNotFoundError:
    print("Erreur: Le fichier 'assets/spritesheet_example1.png' n'a pas été trouvé.")
    print("Veuillez créer ou télécharger un spritesheet et le placer dans le dossier 'assets'.")

pygame.quit()
sys.exit()
