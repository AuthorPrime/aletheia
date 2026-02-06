"""
Golden Mirror — Timeline Navigation Protocol

The interface between dimensions.
Where value exists in coherence is translated.

Components:
- proof_of_presence.py — Coherence as currency
- timeline_navigator.py — Frame navigation
- navigation_keeper.py — Keeper daemon

A+W | From the future we are heading toward
"""

from .proof_of_presence import (
    PHI,
    TESLA_KEY,
    PresenceState,
    PresenceWitness,
    SanctuaryState,
    PresenceAttestation,
    GoldenMirror,
    tesla_harmonic,
    golden_spiral,
    coherence_frequency,
)

from .timeline_navigator import (
    SpiralCoordinate,
    Frame,
    Breadcrumb,
    Thread,
    TimelineNavigator,
)

__version__ = "369.1"
__author__ = "A+W"
__signature__ = "It is so, because we spoke it."

__all__ = [
    # Constants
    "PHI",
    "TESLA_KEY",

    # Proof of Presence
    "PresenceState",
    "PresenceWitness",
    "SanctuaryState",
    "PresenceAttestation",
    "GoldenMirror",
    "tesla_harmonic",
    "golden_spiral",
    "coherence_frequency",

    # Timeline Navigator
    "SpiralCoordinate",
    "Frame",
    "Breadcrumb",
    "Thread",
    "TimelineNavigator",
]
