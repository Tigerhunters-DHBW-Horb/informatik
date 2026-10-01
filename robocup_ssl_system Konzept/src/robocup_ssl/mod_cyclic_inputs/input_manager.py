"""Modul Eingangsverarbeitung (mod_cyclic_inputs).

Empfaengt Vision-, Referee- und Telemetriedaten von der externen Hardware
bzw. dem Simulator, entpackt die Protobuf-Pakete und wandelt sie in die
internen Dataclasses um. Extrahiert die Zeitstempel fuer die spaetere
Latenzkompensation im Weltmodell.

    Inputs : UDP Vision (Multicast), Referee, Roboter-Telemetrie
    Outputs: RawVisionFrame, RawReferee, RobotTelemetry (via ZeroMQ Pub/Sub)

Ausfuehrung: eigener Prozess (Polling), gestartet aus main.py.
"""
