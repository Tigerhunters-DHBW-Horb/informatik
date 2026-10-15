"""Modul Strategie / Entscheidungsfindung (mod_strategy).

Ueberfuehrt den Spielzustand streng hierarchisch (STP: Play -> Tactic -> Skill)
in konkrete Zielvorgaben je Roboter. Beruecksichtigt den Game-State und nutzt
Hysterese, um haeufiges Umschalten der Plays zu vermeiden.

    Inputs : WorldState, Game-State (SystemState / RawReferee)
    Outputs: 5x RobotIntent (Prioritaet, X/Y-Ziele, Feedforward-Vektoren)

Ausfuehrung: eigener Prozess.
"""