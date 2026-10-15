"""Joypad-Reader (mod_cyclic_inputs).

Liest ein angeschlossenes Gamepad aus und erzeugt daraus manuelle Fahrbefehle.
Dient dem Modus MANUAL_JOYPAD (vgl. SystemState.mode) zur direkten Steuerung
eines einzelnen Roboters, z. B. fuer Tests und Inbetriebnahme.

Der aktive Roboter wird ueber SystemState.active_joypad_robot bestimmt.
"""
