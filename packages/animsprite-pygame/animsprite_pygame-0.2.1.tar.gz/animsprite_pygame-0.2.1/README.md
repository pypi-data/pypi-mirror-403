# Animesprite-pygame

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/downloads/)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![PyPI version](https://badge.fury.io/py/pygame-spritesheet.svg)](https://badge.fury.io/py/pygame-spritesheet)
[![GitHub release](https://img.shields.io/github/v/release/EnOx-S/animsprite_pygame)](https://github.com/EnOx-S/animsprite_pygame/releases)

Une librairie légère et facile à utiliser pour gérer les **spritesheets** et les **flipbooks** dans Pygame. Idéale pour créer des animations de personnages, d'ennemis ou d'effets visuels dans vos jeux.

## Caractéristiques

✨ **Gestion facile des spritesheets** - Charger et extraire des sprites automatiquement d'une grille
🎬 **Animation fluide** - Système d'animation intégré avec contrôle de la vitesse
🎮 **Sprite animé** - Classe `AnimatedSprite` héritant de `pygame.sprite.Sprite` pour intégration facile
⚙️ **Flexible** - Redimensionnement, boucle, pause/reprendre l'animation
📦 **Léger** - Zéro dépendance à part Pygame

## Installation

### Depuis le répertoire du projet

```bash
pip install -e .
```

### Via pip (une fois publié sur PyPI)

```bash
pip install animsprite_pygame
```

### Dépendances

- Python >= 3.8
- Pygame >= 2.0

## Utilisation rapide

### 1. Charger un spritesheet et extraire les sprites

```python
from animsprite_pygame import Spritesheet

# Charger l'image du spritesheet
sheet = Spritesheet("path/to/spritesheet.png")

# Extraire les sprites organisés en grille (4 colonnes, 4 lignes, 32x32 pixels chacun)
frames = sheet.get_sprites_from_grid(
    sprite_width=32,
    sprite_height=32,
    cols=4,
    rows=4
)

# Ou extraire un sprite spécifique
single_sprite = sheet.get_sprite(x=0, y=0, width=32, height=32)
```

### 2. Créer un sprite animé

```python
from animsprite_pygame import AnimatedSprite

# Créer un sprite animé avec les frames
animated_sprite = AnimatedSprite(
    frames=frames,
    x=100,  # Position X
    y=100,  # Position Y
    animation_speed=0.1,  # Délai entre les frames en secondes
    loop=True  # Boucler l'animation?
)

# L'ajouter à un groupe de sprites
all_sprites.add(animated_sprite)
```

### 3. Mettre à jour et afficher dans votre boucle de jeu

```python
# Dans votre boucle de jeu
delta_time = clock.tick(60) / 1000  # Temps écoulé en secondes

# Mettre à jour
all_sprites.update(delta_time)

# Afficher
screen.fill((0, 0, 0))
all_sprites.draw(screen)
pygame.display.flip()
```

## API

### Classe `Spritesheet`

#### `__init__(filepath: str)`
Charge un spritesheet à partir d'une image.

**Paramètres:**
- `filepath`: Chemin vers le fichier image

#### `get_sprite(x, y, width, height, scale=None) -> pygame.Surface`
Extrait un sprite unique du spritesheet.

**Paramètres:**
- `x`: Position X du sprite
- `y`: Position Y du sprite
- `width`: Largeur du sprite
- `height`: Hauteur du sprite
- `scale`: Tuple (width, height) pour redimensionner (optionnel)

#### `get_sprites_from_grid(sprite_width, sprite_height, cols, rows=None, scale=None) -> List[pygame.Surface]`
Extrait tous les sprites du spritesheet organisés en grille.

**Paramètres:**
- `sprite_width`: Largeur de chaque sprite
- `sprite_height`: Hauteur de chaque sprite
- `cols`: Nombre de colonnes
- `rows`: Nombre de lignes (optionnel, calcul automatique)
- `scale`: Tuple (width, height) pour redimensionner

### Classe `AnimatedSprite`

Hérite de `pygame.sprite.Sprite`

#### `__init__(frames, x=0, y=0, animation_speed=0.1, loop=True)`
Crée un sprite animé.

**Paramètres:**
- `frames`: Liste des surfaces Pygame (frames de l'animation)
- `x`: Position X initiale
- `y`: Position Y initiale
- `animation_speed`: Délai entre les frames (en secondes)
- `loop`: Si l'animation boucle ou s'arrête

#### `update(delta_time=1/60)`
Met à jour l'animation (à appeler dans votre boucle de jeu).

#### `play()`
Démarre l'animation.

#### `stop()`
Arrête l'animation.

#### `reset()`
Réinitialise l'animation au début.

#### `set_animation_speed(speed: float)`
Change la vitesse de l'animation.

#### `move(x: float, y: float)`
Déplace le sprite.

#### `set_position(x: float, y: float)`
Définit la position du sprite.

#### `get_position() -> Tuple[float, float]`
Retourne la position actuelle (x, y).

#### `get_current_frame_index() -> int`
Retourne l'index de la frame actuelle.

#### `get_total_frames() -> int`
Retourne le nombre total de frames.

## Exemples

Consultez le dossier [examples/](examples/) pour des exemples complets:

- **[example1_basic.py](examples/example1_basic.py)** - Animation basique avec contrôle (pause/reset)
- **[example2_movement.py](examples/example2_movement.py)** - Sprite avec mouvement contrôlable au clavier
- **[example3_multiple_animations.py](examples/example3_multiple_animations.py)** - Gestion de plusieurs animations et changement de state

## Créer vos propres spritesheets

### Ressources gratuites

- [OpenGameArt.org](https://opengameart.org/) - Sprites et assets libres
- [Itch.io](https://itch.io/game-assets) - Assets créés par la communauté
- [Kenney.nl](https://kenney.nl/) - Assets libres de qualité

### Créer votre propre spritesheet

1. Créez ou trouvez des images de sprites individuels
2. Arrangez-les dans une grille sur une seule image
3. Placez-les sans espaces ou avec des espaces réguliers
4. Utilisez `get_sprites_from_grid()` en spécifiant les dimensions

## Conseils d'utilisation

### Optimisation de la performance

```python
# Pré-charger tous les spritesheets au démarrage
sprites_dict = {
    'player': Spritesheet("player.png").get_sprites_from_grid(32, 32, 4, 4),
    'enemy': Spritesheet("enemy.png").get_sprites_from_grid(32, 32, 4, 4),
}

# Puis réutiliser les frames
player = AnimatedSprite(sprites_dict['player'])
enemy = AnimatedSprite(sprites_dict['enemy'])
```

### Créer des variantes de sprites

```python
# Obtenir les frames à différentes résolutions
small_frames = sheet.get_sprites_from_grid(32, 32, 4, 4, scale=(16, 16))
large_frames = sheet.get_sprites_from_grid(32, 32, 4, 4, scale=(64, 64))
```

## Licence

MIT - Voir [LICENSE](LICENSE)

## Contribution

Les contributions sont bienvenues ! N'hésitez pas à:
- Signaler des bugs
- Proposer des améliorations
- Soumettre des pull requests

---

Créé avec ❤️ pour les développeurs de jeux Pygame

