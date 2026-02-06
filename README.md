# Application Pygame - Affichage de l'heure

Une application d'horloge numérique optimisée pour un écran de 4.3 pouces (800x480 pixels) avec monitoring système.

## Caractéristiques

- ✅ Affichage de l'heure en temps réel (format HH:MM:SS)
- ✅ Affichage de la date (format JJ/MM/AAAA)
- ✅ Affichage du jour de la semaine en français
- ✅ **Monitoring système en temps réel :**
  - 🌡️ Température du CPU (Raspberry Pi)
  - 💻 Utilisation du CPU (%)
  - 🧠 Utilisation de la RAM (GB et %)
- ✅ **Indicateurs colorés selon les seuils :**
  - 🟢 Vert : Normal
  - 🟡 Jaune : Attention
  - 🟠 Orange : Alerte
  - 🔴 Rouge : Critique
- ✅ Interface moderne avec un design épuré
- ✅ **Mode plein écran sans bordure** (optimisé pour Raspberry Pi)
- ✅ **Bouton de fermeture graphique moderne** avec effet hover
- ✅ Cadre décoratif avec coins arrondis
- ✅ Optimisé pour écran tactile 4.3 pouces (800x480)

## Prérequis

- Python 3.7 ou supérieur
- Pygame 2.5.0 ou supérieur
- psutil 5.9.0 ou supérieur (pour les informations système)

## Installation

1. Clonez ou téléchargez le projet
2. Créez un environnement virtuel (optionnel mais recommandé) :
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Linux/Mac
   .venv\Scripts\activate     # Windows
   ```
3. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

## Utilisation

Lancez l'application avec :
```bash
python main.py
```

### Commandes

- **ESC** ou **Q** : Quitter l'application
- **Clic sur le bouton rouge** (coin supérieur droit) : Fermer l'application
- **Fermer la fenêtre** : Quitter l'application

## Configuration

Vous pouvez modifier les paramètres dans le fichier `main.py` :

- `SCREEN_WIDTH` et `SCREEN_HEIGHT` : Résolution de l'écran (par défaut 800x480)
- `FPS` : Taux de rafraîchissement (par défaut 30 fps)
- Les couleurs peuvent être personnalisées en modifiant les constantes `BLACK`, `WHITE`, `BLUE`, `DARK_BLUE`, `GRAY`

## Pour un écran Raspberry Pi

Cette application est spécialement optimisée pour Raspberry Pi avec écran tactile 4.3 pouces.

### Mode plein écran
Le mode plein écran est activé par défaut avec les flags :
- `pygame.FULLSCREEN` : Mode plein écran
- `pygame.NOFRAME` : Suppression de la barre de titre et des bordures

Cela garantit qu'aucune barre de contrôle n'apparaît en haut de l'écran.

### Installation sur Raspberry Pi

1. Installez les dépendances système :
   ```bash
   sudo apt-get update
   sudo apt-get install python3-pygame python3-pip
   ```

2. Installez l'application :
   ```bash
   cd /home/pi
   git clone [votre-repo]
   cd MiniOS
   pip3 install -r requirements.txt
   ```

3. Pour lancer l'application au démarrage :
   
   **Méthode 1 : Avec autostart (recommandé pour interface graphique)**
   ```bash
   mkdir -p ~/.config/autostart
   nano ~/.config/autostart/horloge.desktop
   ```
   
   Ajoutez :
   ```ini
   [Desktop Entry]
   Type=Application
   Name=Horloge
   Exec=python3 /home/pi/PythonProject/main.py
   Terminal=false
   ```

   **Méthode 2 : Avec crontab**
   ```bash
   crontab -e
   ```
   
   Ajoutez :
   ```
   @reboot DISPLAY=:0 python3 /home/pi/PythonProject/main.py
   ```

## Bouton de fermeture

Un bouton rouge circulaire avec un "X" est affiché dans le coin supérieur droit de l'écran :
- **Couleur normale** : Rouge foncé (#C0392B)
- **Couleur au survol** : Rouge vif (#E74C3C)
- **Position** : 80 pixels du bord droit, 20 pixels du haut
- **Taille** : Cercle de 60 pixels de diamètre

Le bouton change de couleur quand la souris passe dessus et ferme l'application au clic.

## Palette de couleurs

- **Fond** : Noir (0, 0, 0)
- **Heure** : Blanc (255, 255, 255)
- **Date** : Gris clair (189, 195, 199)
- **Jour** : Bleu clair (52, 152, 219)
- **Cadre** : Bleu clair (52, 152, 219)
- **Bouton fermeture** : Rouge (#C0392B / #E74C3C)

## Structure du code

- `draw_close_button(mouse_pos)` : Dessine le bouton de fermeture avec effet de survol
- `draw_clock()` : Fonction qui dessine l'horloge avec l'heure actuelle
- `main()` : Boucle principale de l'application qui gère les événements et l'affichage

