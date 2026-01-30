# CribbageSim

Source code: [GitHub](https://github.com/KevinRGeurts/CribbageSim)
---
CribbageSim is a Python implementation of the Cribbage card game. It allows interactive play with one human player against one computer player.
It also includes a simulation mode where both players are played by the computer. Simulation mode can be used
to analyze different player strategies and to generate game-play statistics. In simulation mode, as deployed, the players use
a play strategy based on that described by Hoyle's Rules of Games, supplemented with experience of the developer.

## Credit where credit is due

- The Strategy design pattern is used to implement both playing strategies and scoring card combinations, and follows the concepts, UML diagrams, and examples provided in
  "Design Patterns: Elements of Reusable Object-Oriented Software," by Eric Gamma, Richard Helm, Ralph Johnson,
  and John Vlissides, published by Addison-Wesley, 1995.
- The ```HoyleishCribbagePlayStrategy``` class implements a player strategy that is similar to the one described in "Hoyle's Rules of Games," by A.H. Morehead and G. Mott-Smith, second revised edition, published by Signet, 1983. However, significant additions have been made based on the experience of the developer.

## Requirements
- UserResponseCollector>=1.0.4: [GitHub](https://github.com/KevinRGeurts/UserResponseCollector), [PyPi](https://pypi.org/project/UserResponseCollector/)
- HandsDecksCards>=1.0.0: [GitHub](https://github.com/KevinRGeurts/HandsDecksCards), [PyPi](https://pypi.org/project/HandsDecksCards/)

## Usage
To play the game interactively or to run various simulations:
```
python -m CribbageSim.main
```
A menu of options for play and simulation will be presented.

## Unittests
Unit tests for CribbageSim have filenames starting with test_. To run the unit tests,
type ```python -m unittest discover -s .\..\tests -v``` in a terminal window in the project directory.

## License
MIT License. See the LICENSE file for details