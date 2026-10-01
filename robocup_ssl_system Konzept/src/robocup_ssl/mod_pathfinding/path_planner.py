"""Modul Bahnplanung (mod_pathfinding).

Ueberfuehrt einen RobotIntent in kollisionsfreie Geschwindigkeitsvektoren.
Der resultierende Vektor wird in das Roboter-Koordinatensystem transformiert (v_t, v_o, omega).

    Inputs : RobotIntent, WorldState
    Outputs: HardwareCommand

Ausfuehrung: pro Roboter ein eigener Prozess (5x parallel), gestartet aus main.py.
"""