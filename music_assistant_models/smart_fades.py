"""Model(s) for smart fades analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from mashumaro import DataClassDictMixin


@dataclass
class SmartFadesAnalysis(DataClassDictMixin):
    """Beat tracking analysis data for BPM matching crossfade (pyCrossfade style)."""
    
    bpm: float
    beats: np.ndarray          # Beat positions in seconds (from madmom)
    downbeats: np.ndarray      # Downbeat positions in seconds (from madmom) 
    confidence: float          # Analysis confidence score 0-1
    
