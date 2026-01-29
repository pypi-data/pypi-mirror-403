# Gonzo Card Games

Library to create virtualizations of card games with a standard deck 52 card deck(s).

## Background

The creation of this library was done as a learning exercise and as such is in an alpha state. The modules currently avaiable are intended to
be the core modules needed to expand this library to include many different card games. The CardDeck module has all functionality required to
manipulate/create individual playing cards and full card decks. The RatScrew module is an example of what virtualization of a card game can look like.
Lastly, the Templates module was added to give a starting a point of adding new modules for other card games, where each card game module would have the
same API calls for getting a games rules, controls, and for initiating play.

## Installation

## Documentation

Documentation on how to use Gonzo Card Games library is available at [https://gonz1247.github.io/card_games/](https://gonz1247.github.io/card_games/)

## Running locally with Docker

This project can be ran locally using Docker if just interested in playing the currently available built-in card games and not creating new ones. To run locally with Docker you must have [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed.

1. Launch Docker Desktop on your machine
2. Build the Docker image for gonzo_card_games: `docker build -t gonzo_card_games .`
3. Launch the Docker container to play card games: `docker run --rm -it gonzo_card_games`
