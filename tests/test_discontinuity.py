"""Unit tests for non-linear step discontinuity detection, PSLR confidence, PAL pitch restoration, and container offsets."""

import unittest
import numpy as np

from src.core.correlator import (
    compute_pslr_confidence,
    detect_temporal_discontinuities,
    calculate_offset_from_signals
)
from src.core.models import ContainerTimeOffsets, DiscontinuityReport
from src.core.transformer import build_pitch_restoration_filter


class TestDiscontinuityAndResilience(unittest.TestCase):

    def test_pslr_computation_high_peak(self):
        # Create a synthetic correlation curve with sharp peak at index 500
        length = 1000
        curve = np.random.normal(loc=0.0, scale=0.05, size=length).astype(np.float32)
        curve[500] = 0.95  # Distinct peak

        pslr, z_conf = compute_pslr_confidence(curve, 500)
        self.assertGreater(pslr, 5.0)
        self.assertGreater(z_conf, 0.6)

    def test_pslr_computation_flat_noise(self):
        # Flat noise curve without distinct peak
        length = 1000
        curve = np.random.normal(loc=0.2, scale=0.1, size=length).astype(np.float32)
        peak_idx = int(np.argmax(curve))

        pslr, z_conf = compute_pslr_confidence(curve, peak_idx)
        # Sidelobes / noise floor ratio should be low
        self.assertLess(pslr, 3.8)

    def test_detect_temporal_discontinuity_step_cut(self):
        # Case: T1 approx T2 << T3 (e.g. cut/opening omitted at second half)
        # Window 1 (100s): +120ms
        # Window 2 (1000s): +130ms (flat)
        # Window 3 (2000s): +850ms (jump of +720ms)
        window_offsets = [
            (100.0, 120.0, 0.85),
            (1000.0, 130.0, 0.88),
            (2000.0, 850.0, 0.80)
        ]
        report = detect_temporal_discontinuities(window_offsets, duration_sec=2200.0)
        self.assertTrue(report.has_cuts)
        self.assertGreater(abs(report.step_delta_ms), 500.0)
        self.assertIsNotNone(report.estimated_split_timestamp_sec)
        self.assertIn("degrau", report.diagnosis.lower())

    def test_detect_temporal_discontinuity_linear_drift(self):
        # Case: continuous linear framerate drift (23.976 -> 24.000)
        # constant slope of approx 1.001 ms / s
        window_offsets = [
            (100.0, 100.0, 0.9),
            (1000.0, 1001.0, 0.9),
            (2000.0, 2002.0, 0.9)
        ]
        report = detect_temporal_discontinuities(window_offsets, duration_sec=2200.0)
        self.assertFalse(report.has_cuts)
        self.assertEqual(report.step_delta_ms, 0.0)

    def test_container_time_offsets_net_calculation(self):
        # Container offsets logic
        offsets = ContainerTimeOffsets(
            format_start_time_ms=50.0,
            stream_start_time_ms=80.0,
            edit_list_offset_ms=20.0,
            net_adjustment_ms=100.0
        )
        self.assertEqual(offsets.total_pts_start_ms, 100.0)

    def test_pal_pitch_restoration_filter(self):
        # Test filter string generation for 25.0 fps -> 24.0 fps
        filter_str = build_pitch_restoration_filter(input_fps=25.0, output_fps=24.0, target_sr=48000)
        # 48000 * 24 / 25 = 46080
        self.assertIn("asetrate=r=46080", filter_str)
        self.assertIn("aresample=resampler=soxr:osr=48000", filter_str)


if __name__ == "__main__":
    unittest.main()
