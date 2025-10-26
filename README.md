# Dungeon_Crowd

## Description
Dungeon_crowd est un mini-jeu développé en python avec le module pygame.  

## Design/Gameplay
Le joueur incarne un petit chevalier cubique se battant contre des hordes incessantes de monstres (eux aussi cubique). Le but est simple : Survivre, accumuler de l'expérience et devenir le plus puissant possible grâce au système de leveling intégré.

## Librairies 
* Python 3.13.1
* Pygame 2.6
* Json
* Array

## Fonctionnement
* ``Dungeon_crowd.py`` est le corps principale du projet, c'est lui qui gère l'affichage avec pygame (menus, boutons, effets visuels, etc). Il s'occupe aussi du son et de sa gestion avec la fonction ``create_dummy_sound``, qui génére des sons en 16-bit. Il s'occupe aussi de la gestion du joueur en entier.
* ``Monster_Gestion.py`` est, comme son nom l'indique, le programme qui s'occupe de la gestion des monstres. C'est à dire: leur couleur, leur fonctionnement ainsi que leurs projectiles, explosions et particules.
* ``player_profiles.json`` et ``settings.json`` sont deux fichiers de sauvgardes crées automatiquement lors du lancement du jeu, il ne faut les supprimer sous aucun prétexte, cela entraine un reset des informations relative aux utilisateurs et des régalges.
