"""Referee-Parser (mod_cyclic_inputs).

Empfaengt die Pakete des SSL Game Controllers (Referee-Box) und wandelt sie in
eine RawReferee-Dataclass. Liefert Spielkommandos (HALT, STOP, NORMAL_START,
DIRECT_FREE_*, ...), Spielstand und ggf. die designierte Ballposition.

"""
