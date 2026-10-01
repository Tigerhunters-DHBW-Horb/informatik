"""System-Manager / Game-Controller & Safety.

Verwaltet den systemweiten Betriebszustand (SystemState) und den Spielzustand.
Wertet die Referee-Kommandos aus und leitet einen HALT-Befehl mit hoechster
Prioritaet ueber den Sicherheitspfad direkt an den Dispatcher weiter, unter
Umgehung der regulaeren Entscheidungs- und Planungsschritte.

Zustaende (SystemState.mode): AUTONOMOUS, MANUAL_JOYPAD, EMERGENCY_STOP.
Ueberwacht zudem die Lebendigkeit von Vision und Referee (Timeouts).

    Inputs : RawReferee, Health-Signale (vision_alive, referee_alive)
    Outputs: SystemState, HALT (Sicherheitspfad)
"""
