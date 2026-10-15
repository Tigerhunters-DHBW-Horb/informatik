"""Modul Weltmodell (mod_world_model).

Erzeugt aus den verrauschten Rohdaten ein konsistentes Abbild des Spielfeldes.
Filtert die Positionsdaten (Kalman), kompensiert die ueber den Zeitstempel
bestimmbare Latenz (Praediktion auf den aktuellen Zeitpunkt), spiegelt bei
Bedarf die Feldseite und behandelt Sonderfaelle des Balls.

    Inputs : RawVisionFrame, RobotTelemetry
    Outputs: WorldState (gefiltert, zukunfts-praediziert)

Ausfuehrung: eigener Prozess. Das Weltmodell ist die einzige verlaessliche
Datenquelle fuer alle uebergeordneten Entscheidungen.
"""