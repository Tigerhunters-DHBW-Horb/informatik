"""Basisklasse Skill (STP-Architektur, mod_strategy).

Ein Skill ist die unterste Ebene der STP-Hierarchie und setzt eine elementare
Faehigkeit um (z. B. MOVE_TO, INTERCEPT, KICK, IDLE). Ergebnis eines Skills ist
ein konkreter RobotIntent, der an die Bahnplanung uebergeben wird.
"""