# pocketlife
A Python package for manipulation of patterns in cellular automata.
## Introduction
This is my first Python package, and it contains functions for manipulating patterns in cellular automata.
It was inspired by the much faster [lifelib](https://gitlab.com/apgoucher/lifelib) by Adam P. Goucher, but unlike lifelib, this package:
* Is written entirely in Python.
* Works regardless of OS and CPU architecture.
It is very slow, however, and so it is mostly written as a test.
## Classes
Cellular automata functionality is implemented through the class ```lifetree```. A lifetree is responsible for the actual simulation, using an extremely basic algorithm and an unbounded grid. It does this as a backend to the class ```Pattern```, which stores a dictionary of live cells.
The syntax is very similar to lifelib, with patterns being advanced using ```pt[gens]```, and many functions and properties are similar as well.
## Documentation
Documentation on the ```lifetree``` and ```Pattern``` classes can be found in /doc.
