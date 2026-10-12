"""CPU scoring: burst grouping + keeper selection."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import timedelta

from ..ingest import Frame
from ..vision import FaceResult


@dataclass
class ScoredFrame:
    frame: Frame
    faces: list[FaceResult] = field(default_factory=list)
    focus_score: float = 0.0
    black_clip: float = 0.0
    white_clip: float = 0.0
    blink: bool = False
    keeper_score: float = 0.0
    star_rating: int = 0
    burst_id: int = -1
    is_burst_best: bool = False


BURST_WINDOW = timedelta(seconds=3)


def group_bursts(scored: list[ScoredFrame]) -> list[list[ScoredFrame]]:
    ordered = sorted(scored, key=lambda s: (s.frame.captured_at is None, s.frame.captured_at))
    bursts: list[list[ScoredFrame]] = []
    current: list[ScoredFrame] = []
    for s in ordered:
        if (current and s.frame.captured_at and current[-1].frame.captured_at
                and (s.frame.captured_at - current[-1].frame.captured_at) <= BURST_WINDOW
                and s.frame.camera_serial == current[-1].frame.camera_serial):
            current.append(s)
        else:
            if current:
                bursts.append(current)
            current = [s]
    if current:
        bursts.append(current)
    for i, burst in enumerate(bursts):
        for s in burst:
            s.burst_id = i
    return bursts


def score_keeper(s: ScoredFrame) -> float:
    score = 0.5
    focus_norm = min(1.0, max(0.0, (math.log10(s.focus_score + 1) - 1.0) / 2.3))
    score += 0.30 * focus_norm
    if s.blink:
        score -= 0.35
    score -= 0.20 * min(1.0, s.white_clip * 8)
    score -= 0.10 * min(1.0, s.black_clip * 8)
    if s.faces:
        score += 0.05
    return max(0.0, min(1.0, score))


def rate_burst_best(bursts: list[list[ScoredFrame]]) -> None:
    for burst in bursts:
        if not burst:
            continue
        for s in burst:
            s.keeper_score = score_keeper(s)
        best = max(burst, key=lambda s: s.keeper_score)
        best.is_burst_best = True
        for s in burst:
            stars = 1 + int(round(s.keeper_score * 4))
            if s is best:
                stars = max(3, stars)
            if s.blink:
                stars = min(2, stars)
            s.star_rating = max(1, min(5, stars))
