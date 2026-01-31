# Modification du pipeline

## Pré-requis

- Python >= 3.9
- make
- [Poetry](https://python-poetry.org) 
  - installation au 3 juillet 2024: `curl -sSL https://install.python-poetry.org | python3 -`

## Aide sur les commandes

Un Makefile regroupe les commandes courantes utiles pour le développement.
Les commandes du Makefile peuvent être listées ainsi:

    make help

Soit les commandes suivantes disponibles (via `make <commande>`):

    install      Installation des dépendances
    format       Formatage des sources avec Black
    test         Lancer les tests
    build        Construire le paquet
    publish      Publier le paquet sur pypi.org
    deploy       Déployer le paquet sur metopes.unicaen.fr
    help         Voir l'aide
