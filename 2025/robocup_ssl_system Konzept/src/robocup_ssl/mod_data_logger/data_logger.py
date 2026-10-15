"""Modul Data-Logger (mod_data_logger).

Laeuft asynchron, abonniert alle Topics und zeichnet den Systemzustand auf,
ohne die zeitkritischen Prozesse zu blockieren. Dient der Nachvollziehbarkeit
 und der spaeteren Auswertung realer Messergebnisse.

    Inputs : alle Topics (WorldState, RobotIntent, HardwareCommand, ...)
    Outputs: Log-Dateien
"""
