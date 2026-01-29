.. Gonzo Card Games documentation master file, created by
   sphinx-quickstart on Sun Jan 18 16:39:53 2026.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Gonzo Card Games Documentation
====================================
Library to create virtualizations of card games with a standard deck 52 card deck(s).

Background
====================================
The creation of this library was done as a learning exercise and as such is in an alpha state. The modules currently avaiable are intended to 
be the core modules needed to expand this library to include many different card games. The CardDeck module has all functionality required to 
manipulate/create individual playing cards and full card decks. The RatScrew module is an example of what virtualization of a card game can look like.
Lastly, the Templates module was added to give a starting a point of adding new modules for other card games, where each card game module would have the 
same API calls for getting a games rules, controls, and for initiating play.  

Installation
====================================
python -m pip install gonzo-card-games

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   gonzo_card_games

