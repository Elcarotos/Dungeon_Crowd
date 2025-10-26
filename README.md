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
* ``Dungeon_crowd.py`` est le corps principale du projet, c'est lui qui gère l'affichage avec pygame (menus, boutons, effets visuels, etc). Il s'occupe aussi du son et de sa gestion avec la fonction ``create_dummy_sound``, qui génére des sons en 16-bit. Il s'occupe aussi de la gestion du joueur en entier.
* ``Monster_Gestion.py`` est, comme son nom l'indique, le programme qui s'occupe de la gestion des monstres. C'est à dire: leur couleur, leur fonctionnement ainsi que leurs projectiles, explosions et particules.
* ``player_profiles.json`` et ``settings.json`` sont deux fichiers de sauvgardes crées automatiquement lors du lancement du jeu, il ne faut les supprimer sous aucun prétexte, cela entraine un reset des informations relative aux utilisateurs et des régalges.
