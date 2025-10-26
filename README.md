# Dungeon_Crowd

## Description
Dungeon_crowd is a mini-game develop in Python with the module PyGame.  

## Design/Gameplay
The player embodies a small cubic knight fighting against endless hordes of monsters (also cubic). The goal is simple: Survive, accumulate experience and become as powerful as possible thanks to the integrated leveling system.

## Librairies 
* Python 3.13.1
* PyGame 2.6
* Json
* Array

## Fonctionnement
* ``Dungeon_crowd.py`` is the main body of the project, it manages the display with pygame (menus, buttons, visual effects, etc.). It also takes care of the sound and its management with the ``create_dummy_sound`` function, which generates 16-bit sounds. It also takes care of the management of the entire player.
* ``Monster_Gestion.py`` is, as its name suggests, the program that handles monster management. That is to say: their color, their functioning as well as their projectiles, explosions and particles.
* ``player_profiles.json`` and ``settings.json`` are two backup files that are automatically created when the game is launched. You should not delete them if you value your data because this will reset user information and settings.
