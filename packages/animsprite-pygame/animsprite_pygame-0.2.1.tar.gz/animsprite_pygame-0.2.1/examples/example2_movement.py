"""
Exemple 2: Animation avec mouvement et contrôle du personnage
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
pygame.display.set_caption("Pygame Spritesheet - Exemple 2: Mouvement et Contrôle")
clock = pygame.time.Clock()

# Créer des groupes de sprites
all_sprites = pygame.sprite.Group()

# Classe personnalisée pour un personnage contrôlable
class ControllableCharacter(AnimatedSprite):
    def __init__(self, frames, x, y, animation_speed=0.1):
        super().__init__(frames, x, y, animation_speed, loop=True)
        self.velocity_x = 0
        self.velocity_y = 0
        self.speed = 5
    
    def handle_input(self, keys):
        """Gère les entrées clavier"""
        self.velocity_x = 0
        self.velocity_y = 0
        
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.velocity_y = -self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.velocity_y = self.speed
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.velocity_x = -self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.velocity_x = self.speed
    
    def update(self, delta_time=1/60):
        """Met à jour la position et l'animation"""
        # Mettre à jour l'animation
        super().update(delta_time)
        
        # Mettre à jour la position
        self.rect.x += self.velocity_x
        self.rect.y += self.velocity_y
        
        # Limiter le mouvement dans l'écran
        self.rect.x = max(0, min(SCREEN_WIDTH - self.rect.width, self.rect.x))
        self.rect.y = max(0, min(SCREEN_HEIGHT - self.rect.height, self.rect.y))

try:
    # Charger le spritesheet
    sheet = Spritesheet("../assets/spritesheet_example2.png")
    
    # Extraire les frames
    frames = sheet.get_sprites_from_grid(
        sprite_width=512,
        sprite_height=512,
        cols=1,
        rows=8
    )
    
    # Créer le personnage
    character = ControllableCharacter(
        frames=frames,
        x=40,
        y=40,
        animation_speed=0.15
    )
    all_sprites.add(character)
    
    # Boucle principale
    running = True
    while running:
        delta_time = clock.tick(FPS) / 1000
        
        # Gestion des événements
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
        
        # Récupérer les touches enfoncées
        keys = pygame.key.get_pressed()
        character.handle_input(keys)
        
        # Mettre à jour les sprites
        all_sprites.update(delta_time)
        
        # Affichage
        screen.fill((30, 30, 50))
        all_sprites.draw(screen)
        
        # Afficher les infos
        font = pygame.font.Font(None, 24)
        
        pos_text = font.render(
            f"Position: ({character.rect.x:.0f}, {character.rect.y:.0f})",
            True,
            (255, 255, 255)
        )
        screen.blit(pos_text, (10, 10))
        
        frame_text = font.render(
            f"Frame: {character.get_current_frame_index() + 1}/{character.get_total_frames()}",
            True,
            (255, 255, 255)
        )
        screen.blit(frame_text, (10, 35))
        
        controls_text = font.render(
            "Contrôles: ZQSD ou Flèches | ESC: Quitter",
            True,
            (200, 200, 200)
        )
        screen.blit(controls_text, (10, 60))
        
        pygame.display.flip()

except FileNotFoundError:
    print("Erreur: Le fichier 'assets/spritesheet_example2.png' n'a pas été trouvé.")
    print("Veuillez créer ou télécharger un spritesheet et le placer dans le dossier 'assets'.")

pygame.quit()
sys.exit()
