=======
History
=======

0.3.2 (2020-02-19)
------------------

* Added friendly fire.
* Added a probability to miss a shot.
* Fixed agent stop when there are pending messages to be sent.
* Fixed max length bug in text render.
* Moved ontology constants to a new file.


0.3.1 (2020-02-17)
------------------

* Fixed adding new actions in inherited classes.
* Improved logger.
* Added verbosity parameter.
* Improved jps and a* algorithms by avoiding being near walls.


0.3.0 (2020-02-10)
------------------

* Migrated msg format to msgpack.
* Black sttyle applied to code.
* Major refactoring of code in renders.

0.2.3 (2019-07-10)
------------------

* Upgrade default ASLs.
* Agent name in JSON file is no longer required.

0.2.2 (2019-07-10)
------------------

* Change all coordinate actions and beliefs to tuple of coordinates.
* Update spade-bdi.

0.2.1 (2019-07-08)
------------------

* Change the .create_control_points from action to function.
* Change all coordinate actions and beliefs to tuple of coordinates.

0.2.0 (2019-07-05)
------------------

* Added game replay support.
* Added action to register generic services.
* Added turn action for the troop agents.
* Added a new map (map_08)
* Minor bug fixes.

0.1.0 (2019-06-13)
------------------

* First release on PyPI.
