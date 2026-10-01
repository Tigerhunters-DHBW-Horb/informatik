"""Roboter-Telemetrie-Parser (mod_cyclic_inputs).

Empfaengt die Rueckmeldungen der eigenen Roboter (z. B. ueber Funk) und wandelt
sie in RobotTelemetry-Objekte. Dazu gehoeren u. a. der Kicker-Lichtschranken-
Status (has_ball), der Batteriestand und das Encoder-Feedback (v_x, v_y, omega).
"""