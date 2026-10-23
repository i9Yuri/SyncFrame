"""Unit tests for FFT acoustic cross-correlation and framerate drift diagnostics."""

import math
import unittest
import numpy as np

from src.core.correlator import (
    calculate_offset_from_signals,
    calculate_signed_offset,
    map_offset_to_player_delay,
    diagnose_drift_and_framerate,
    _cross_correlate_fft
)


class TestCorrelator(unittest.TestCase):

    def test_fft_cross_correlation_synthetic(self):
        sample_rate = 16000
        duration_sec = 2.0
        n_samples = int(duration_sec * sample_rate)

        # Generate a synthetic signal: harmonic sum of sine waves + noise burst
        t = np.linspace(0, duration_sec, n_samples, endpoint=False, dtype=np.float32)
        ref_signal = (
            np.sin(2 * np.pi * 440 * t) +
            0.5 * np.sin(2 * np.pi * 880 * t) +
            0.3 * np.sin(2 * np.pi * 1760 * t)
        )
        # Add transient pulse
        pulse_idx = int(0.5 * sample_rate)
        ref_signal[pulse_idx:pulse_idx + 200] += 2.0

        # Create target signal delayed by exactly 350 ms
        delay_ms = 350.0
        delay_samples = int((delay_ms / 1000.0) * sample_rate)

        target_signal = np.zeros_like(ref_signal)
        target_signal[delay_samples:] = ref_signal[:len(ref_signal) - delay_samples]

        # Add mild independent noise to simulate separate dub mix
        np.random.seed(42)
        target_signal += 0.05 * np.random.randn(len(target_signal)).astype(np.float32)

        # Calculate offset
        detected_offset_ms, confidence, curve, pslr = calculate_offset_from_signals(
            ref_signal, target_signal, sample_rate, max_lag_sec=2.0
        )

        # Should match 350ms within ±1 sample (1/16000 sec = 0.0625ms tolerance)
        self.assertAlmostEqual(detected_offset_ms, delay_ms, delta=1.0)
        self.assertGreater(confidence, 0.70)
        self.assertGreater(pslr, 3.0)
        self.assertTrue(len(curve) > 0)

    def test_framerate_diagnose_ntsc_telecine(self):
        # Discrepancy between 23.976 and 24.000:
        # drift_ratio = 1001/1000 = 1.001001
        # slope = (1.001 - 1.0) * 1000 = 1.001 ms drift per second
        t1, t2, t3 = 100.0, 1000.0, 3000.0
        # offset(t) = 500ms + 1.001 * t
        offsets = [
            (t1, 500.0 + (1.001 * t1), 0.9),
            (t2, 500.0 + (1.001 * t2), 0.9),
            (t3, 500.0 + (1.001 * t3), 0.9),
        ]
        drift, mismatch, diag, stretch = diagnose_drift_and_framerate(offsets)
        self.assertTrue(mismatch)
        self.assertAlmostEqual(drift, 1.001, places=3)
        self.assertIn("23.976 fps -> 24.000 fps", diag)

    def test_framerate_diagnose_congruous(self):
        # Constant offset (no drift)
        offsets = [
            (100.0, 250.0, 0.95),
            (1000.0, 250.1, 0.92),
            (3000.0, 249.9, 0.94),
        ]
        drift, mismatch, diag, stretch = diagnose_drift_and_framerate(offsets)
        self.assertFalse(mismatch)
        self.assertAlmostEqual(drift, 1.0, places=4)
        self.assertEqual(stretch, 1.0)
        self.assertIn("congruentes", diag.lower())

    def test_calculate_signed_offset_delayed(self):
        """When target audio is delayed (+500ms after ref), calculate_signed_offset returns +500ms."""
        sample_rate = 16000
        duration_sec = 3.0
        n_samples = int(duration_sec * sample_rate)
        t = np.linspace(0, duration_sec, n_samples, endpoint=False, dtype=np.float32)

        # Distinct pulse pattern at t=1.0s
        ref = np.zeros(n_samples, dtype=np.float32)
        ref[int(1.0 * sample_rate):int(1.1 * sample_rate)] = 1.0

        # Target has the same pulse delayed by 500ms (at t=1.5s)
        target = np.zeros(n_samples, dtype=np.float32)
        target[int(1.5 * sample_rate):int(1.6 * sample_rate)] = 1.0

        offset_ms = calculate_signed_offset(ref, target, sample_rate, max_lag_sec=2.0)
        self.assertAlmostEqual(offset_ms, 500.0, delta=1.0)

    def test_calculate_signed_offset_advanced(self):
        """When target audio is advanced (-500ms before ref), calculate_signed_offset returns -500ms."""
        sample_rate = 16000
        duration_sec = 3.0
        n_samples = int(duration_sec * sample_rate)

        # Distinct pulse pattern at t=1.5s in reference
        ref = np.zeros(n_samples, dtype=np.float32)
        ref[int(1.5 * sample_rate):int(1.6 * sample_rate)] = 1.0

        # Target has the same pulse early by 500ms (at t=1.0s)
        target = np.zeros(n_samples, dtype=np.float32)
        target[int(1.0 * sample_rate):int(1.1 * sample_rate)] = 1.0

        offset_ms = calculate_signed_offset(ref, target, sample_rate, max_lag_sec=2.0)
        self.assertAlmostEqual(offset_ms, -500.0, delta=1.0)

    def test_map_offset_to_player_delay(self):
        """Verifies mathematical inversion contract across mkvmerge, mpv, and ffplay."""
        # 1. Delayed target audio (+500ms) -> container delay must be -500ms, player delay -0.5s
        self.assertEqual(map_offset_to_player_delay(500.0, "mkvmerge"), -500.0)
        self.assertEqual(map_offset_to_player_delay(500.0, "mpv"), -0.5)
        self.assertEqual(map_offset_to_player_delay(500.0, "ffplay"), -0.5)

        # 2. Advanced target audio (-500ms) -> container delay must be +500ms, player delay +0.5s
        self.assertEqual(map_offset_to_player_delay(-500.0, "mkvmerge"), 500.0)
        self.assertEqual(map_offset_to_player_delay(-500.0, "mpv"), 0.5)
        self.assertEqual(map_offset_to_player_delay(-500.0, "ffplay"), 0.5)

        # 3. Zero offset -> zero delay
        self.assertEqual(map_offset_to_player_delay(0.0, "mkvmerge"), 0.0)
        self.assertEqual(map_offset_to_player_delay(0.0, "mpv"), 0.0)


if __name__ == "__main__":
    unittest.main()
