"""Modul Ausgangsverarbeitung / Dispatcher (mod_cyclic_outputs).

Sammelt die Steuervektoren der Bahnplanungs-Prozesse, wendet abschliessende
Sicherheitspruefungen an (Clipping der Geschwindigkeiten, Not-Aus / HALT) und
uebertraegt die Befehle an den Simulator (grSim) oder das Funknetzwerk.

    Inputs : HardwareCommand (je Roboter), HALT
    Outputs: Steuerpakete an Simulator / Funk
"""

