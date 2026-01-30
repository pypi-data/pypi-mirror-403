# Guide de Contribution

Merci d'être intéressé par la contribution à **Pygame Spritesheet** ! 🎉

## Comment contribuer

### Signaler des bugs

Avant de signaler un bug, vérifiez que le problème n'a pas déjà été reporté.

Lors de la création d'un rapport de bug, incluez:
- Une description claire du problème
- Étapes pour reproduire le comportement
- Comportement observé et attendu
- Votre environnement (Python version, Pygame version, OS)

### Proposer des améliorations

Les suggestions d'amélioration sont bienvenues ! Décrivez clairement:
- Votre idée
- Pourquoi ce serait utile
- Un exemple d'utilisation si possible

### Soumettre des Pull Requests

1. **Fork** le repository
2. **Créez une branche** pour votre feature (`git checkout -b feature/AmazingFeature`)
3. **Commitez** vos changements (`git commit -m 'Add some AmazingFeature'`)
4. **Poussez** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrez une Pull Request**

## Standards de développement

### Style de code

- Suivez [PEP 8](https://www.python.org/dev/peps/pep-0008/)
- Utilisez des noms de variables explicites
- Ajoutez des docstrings aux fonctions et classes
- Maintenez une indentation cohérente (4 espaces)

### Documentation

- Documentez les nouvelles features avec des docstrings
- Mettez à jour le README si nécessaire
- Ajoutez des exemples pour les nouvelles fonctionnalités

### Tests

- Écrivez des tests pour toutes les nouvelles features
- Assurez-vous que tous les tests passent
- Maintenez une couverture de tests décente

### Commits

- Utilisez des messages de commit clairs et descriptifs
- Un commit = une change logique
- Référencez les issues concernées si possible

## Développement local

### Installation en mode développement

```bash
git clone https://github.com/EnOx-S/animsprite_pygame.git
cd animsprite_pygame
pip install -e .
pip install pytest
```

### Exécuter les tests

```bash
pytest tests/
```

### Lancer les exemples

```bash
python examples/example1_basic.py
```

## Licence

En contribuant, vous acceptez que vos contributions soient licenciées sous la même licence MIT que le projet.

---

Merci encore pour votre contribution ! 🚀
