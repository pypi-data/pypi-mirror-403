# Velmu Python SDK

Une bibliothèque Python moderne, robuste et asynchrone pour interagir avec l'API Velmu et créer des bots puissants.

## Fonctionnalités Principales

- **100% Asynchrone** : Construit sur `asyncio` et `aiohttp` pour des performances élevées.
- **Temps Réel** : Connexion WebSocket persistante avec gestion automatique des reconnexions.
- **Système de Commandes** : Extension `commands` puissante (inspirée de discord.py) pour créer des bots facilement.
- **Gestion des Permissions** : Système fin de permissions (Bitwise flags) compatible avec l'architecture backend.
- **Historique et Pagination** : Itérateurs asynchrones performants pour parcourir l'historique des messages.
- **Typage Fort** : Modèles objets complets (`Member`, `Role`, `Guild`, `Channel`) pour une excellente expérience développeur (DX).

## Installation

Vous pouvez installer la bibliothèque directement depuis les sources :

```bash
pip install .
```

## Démarrage Rapide

Voici un bot minimal utilisant l'extension `commands` :

```python
import velmu
from velmu.ext import commands
import os

# Configuration
intents = velmu.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'Prêt ! Connecté en tant que {bot.user}')

@bot.command()
async def ping(ctx):
    await ctx.reply('Pong ! 🏓')

bot.run("VOTRE_TOKEN")
```

## Exemples

Des exemples complets sont disponibles dans le dossier `examples/` :

- **[basic_bot.py](examples/basic_bot.py)** : Bot basique avec commandes simples.
- **[moderation.py](examples/moderation.py)** : Démonstration du système de permissions (Kick, Ban, Checks).
- **[history.py](examples/history.py)** : Utilisation de `ctx.channel.history()` pour lire les anciens messages.

## Structure du Projet

- `velmu/` : Code source de la bibliothèque.
  - `client.py` : Client WebSocket et gestion des événements.
  - `api.py` : Client HTTP REST.
  - `ext/commands/` : Framework de commandes.
  - `models/` : Modèles de données (User, Guild, Channel...).
- `examples/` : Scripts d'exemple.

## Licence

Distribué sous la licence MIT.
