"""Whisper hallucinates confidently over instrumental gaps in an isolated vocal
stem. These segments used to be written straight to the database."""

from types import SimpleNamespace

import pytest

from app.services.stt_service import STTService, VAD_PARAMETERS


def segment(text=" a line ", avg_logprob=-0.3, no_speech_prob=0.1):
    return SimpleNamespace(
        text=text, avg_logprob=avg_logprob, no_speech_prob=no_speech_prob
    )


def test_keeps_a_confident_segment():
    assert STTService._is_plausible(segment()) is True


@pytest.mark.parametrize("text", ["", "   ", "\n"])
def test_drops_blank_text(text):
    assert STTService._is_plausible(segment(text=text)) is False


def test_drops_low_confidence_segment():
    assert STTService._is_plausible(segment(avg_logprob=-1.5)) is False


def test_drops_segment_over_silence():
    assert STTService._is_plausible(segment(no_speech_prob=0.9)) is False


def test_thresholds_are_inclusive_at_the_boundary():
    # Exactly at the configured limits still counts as plausible.
    assert STTService._is_plausible(segment(avg_logprob=-1.0)) is True
    assert STTService._is_plausible(segment(no_speech_prob=0.6)) is True


def test_vad_is_tuned_for_singing_not_speech():
    # Silero's defaults (0.5 / 2000ms) clip breathy phrase tails and merge a
    # verse into the chorus that follows it.
    assert VAD_PARAMETERS.threshold < 0.5
    assert VAD_PARAMETERS.min_silence_duration_ms < 2000
