"""Vision-Parser (mod_cyclic_inputs).

Empfaengt die UDP-Multicast-Pakete von SSL-Vision bzw. grSim, dekodiert das
Protobuf-Format und erzeugt eine RawVisionFrame. Der Zeitstempel der
Bildaufnahme (t_capture) wird uebernommen und ist fuer die Latenzkompensation
im Weltmodell entscheidend.
"""
