========
  weii
========

-----------------------------------------
Measure weight using a Wii Balance Board.
-----------------------------------------

:Author: Petter Reinholdtsen <pere@hungry.com>
:Date:   2024-09-09
:Copyright: public domain
:Version: 0.1
:Manual section: 1
:Manual group: General Commands Manual

SYNOPSIS
========

weii [-h] [-a ADJUST] [-c COMMAND] [-d ADDRESS] [-w]

DESCRIPTION
===========

Weii (pronounced "weigh") is a small script that connects to a Wii
Balance Board, reads a weight measurement, and disconnects.

OPTIONS
=======

-h, --help              show this help message and exit
-a ADJUST, --adjust ADJUST
                        adjust the final weight by some value (e.g. to
                        match some other scale, or to account for
                        clothing)
-l MINLIMIT, --minlimit MINLIMIT
                        adjust the minimum weight limit
-c COMMAND, --command COMMAND
                        the command to run when done (use `{weight}`
                        to pass the weight to the command
-d ADDRESS, --disconnect-when-done ADDRESS
                        disconnect the board when done, so it turns
                        off.  The address value can be found using
                        "hcitool dev" when the board is connected.
-w, --weight-only       only print the final weight


SEE ALSO
========

hcitool(1),
lswm(1),
wmgui(1),
xwiimote(7).
