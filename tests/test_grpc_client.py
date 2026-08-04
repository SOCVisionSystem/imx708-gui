# SPDX-License-Identifier: GPL-2.0-only
"""
Tests for the GrpcClient module.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from typing import Dict, Optional

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from imx708_gui.grpc_client import GrpcClient


class MockStub:
    """Mock gRPC stub that returns canned responses."""

    def __init__(self):
        self.GetStatus = MagicMock(return_value=MagicMock(
            temperature=32, frame_count=42, pll_locked=True,
            streaming=True, error=False, gain=480, digital_gain=256,
            exposure=1600, width=4608, height=2592, fps=14))
        self.GetModes = MagicMock(return_value=MagicMock(modes=[
            MagicMock(index=0, width=4608, height=2592, code=0x2eb,
                      fps=14, hblank=15648, vblank=58, bit_depth=10,
                      pixel_rate=595200000),
            MagicMock(index=1, width=2304, height=1296, code=0x2eb,
                      fps=56, hblank=7824, vblank=40, bit_depth=10,
                      pixel_rate=585600000),
        ]))
        self.StartStream = MagicMock(return_value=MagicMock(success=True))
        self.StopStream = MagicMock(return_value=MagicMock(success=True))
        self.SoftReset = MagicMock(return_value=MagicMock(success=True))
        self.SetGain = MagicMock(return_value=MagicMock(success=True))
        self.SetExposure = MagicMock(return_value=MagicMock(success=True))
        self.SetHdr = MagicMock(return_value=MagicMock(success=True))
        self.SetTestPattern = MagicMock(return_value=MagicMock(success=True))
        self.CaptureFrame = MagicMock(return_value=MagicMock(
            width=4608, height=2592, stride=9216, format=0,
            timestamp_ns=123456789, frame_number=1, gain=480,
            exposure=1600, data=b'\x00' * (4608 * 2592 * 2)))
        self.ReadRegister = MagicMock(return_value=MagicMock(val=0x0708))
        self.WriteRegister = MagicMock(return_value=MagicMock(success=True))
        self.GetImageProcessing = MagicMock(return_value=MagicMock(
            brightness=0, contrast=128, saturation=128, hue=0,
            sharpness=0, gamma=128, auto_wb=True, wb_temperature=5000,
            hflip=False, vflip=False))
        self.SetImageProcessing = MagicMock(return_value=MagicMock(success=True))
        self.StreamStatus = MagicMock(return_value=iter([
            MagicMock(status_update=MagicMock(
                temperature=32, frame_count=43, pll_locked=True,
                streaming=True, error=False, gain=480, digital_gain=256,
                exposure=1600, width=4608, height=2592, fps=14))
        ]))


class TestGrpcClient(unittest.TestCase):
    """Test suite for GrpcClient."""

    def setUp(self):
        # Mock the proto module so GrpcClient methods can create message objects
        self.proto_module = MagicMock()
        self.proto_module.Empty = MagicMock
        self.proto_module.GainConfig = MagicMock
        self.proto_module.ExposureConfig = MagicMock
        self.proto_module.HdrConfig = MagicMock
        self.proto_module.TestPatternConfig = MagicMock
        self.proto_module.CaptureParams = MagicMock
        self.proto_module.RegisterAccess = MagicMock
        self.proto_module.ImageProcessingConfig = MagicMock

        self.proto_grpc_module = MagicMock()
        self.proto_grpc_module.Imx708ServiceStub = MagicMock(return_value=MagicMock())

        self.patches = [
            patch('imx708_gui.grpc_client.HAVE_GRPC', True),
            patch('imx708_gui.grpc_client.HAVE_PROTO', True),
            patch('imx708_gui.grpc_client.imx708_pb2', self.proto_module, create=True),
            patch('imx708_gui.grpc_client.imx708_pb2_grpc', self.proto_grpc_module, create=True),
        ]
        for p in self.patches:
            p.start()

        self.client = GrpcClient("localhost:50051")
        self.mock_stub = MockStub()
        self.client._stub = self.mock_stub
        self.client._connected = True
        self.logs: list = []
        self.client.log_message.connect(self.logs.append)

    def tearDown(self):
        for p in self.patches:
            p.stop()

    # ── Connection ──────────────────────────────────────────────────────

    @patch('imx708_gui.grpc_client.HAVE_GRPC', True)
    @patch('imx708_gui.grpc_client.HAVE_PROTO', True)
    @patch('imx708_gui.grpc_client.insecure_channel')
    def test_connect_success(self, mock_channel):
        mock_channel.return_value = MagicMock()
        client = GrpcClient("test:50051")
        with patch.object(client, '_stub', create=True) as mock_stub:
            mock_stub.GetStatus.return_value = MagicMock(temperature=25)
            result = client.connect()
            self.assertTrue(result)

    @patch('imx708_gui.grpc_client.HAVE_GRPC', True)
    @patch('imx708_gui.grpc_client.HAVE_PROTO', True)
    @patch('imx708_gui.grpc_client.insecure_channel')
    def test_connect_failure(self, mock_channel):
        mock_channel.return_value = MagicMock()
        # Make Imx708ServiceStub return a stub whose GetStatus raises
        bad_stub = MagicMock()
        bad_stub.GetStatus.side_effect = Exception("connection refused")
        with patch('imx708_gui.grpc_client.imx708_pb2_grpc') as mock_grpc:
            mock_grpc.Imx708ServiceStub.return_value = bad_stub
            client = GrpcClient("test:50051")
            result = client.connect()
            self.assertFalse(result)

    def test_disconnect(self):
        self.client._channel = MagicMock()
        self.client.disconnect()
        self.assertFalse(self.client.connected)
        self.assertIsNone(self.client._stub)

    # ── Status ─────────────────────────────────────────────────────────

    def test_get_status(self):
        status = self.client.get_status()
        self.assertIsNotNone(status)
        self.assertEqual(status['temperature'], 32)
        self.assertEqual(status['frame_count'], 42)
        self.assertTrue(status['pll_locked'])
        self.assertTrue(status['streaming'])
        self.assertEqual(status['gain'], 480)
        self.assertEqual(status['exposure'], 1600)

    def test_get_status_when_disconnected(self):
        self.client._stub = None
        status = self.client.get_status()
        self.assertIsNone(status)

    # ── Modes ──────────────────────────────────────────────────────────

    def test_get_modes(self):
        modes = self.client.get_modes()
        self.assertEqual(len(modes), 2)
        self.assertEqual(modes[0]['width'], 4608)
        self.assertEqual(modes[0]['fps'], 14)
        self.assertEqual(modes[1]['width'], 2304)
        self.assertEqual(modes[1]['fps'], 56)

    # ── Stream Control ─────────────────────────────────────────────────

    def test_start_stream(self):
        result = self.client.start_stream()
        self.assertTrue(result)

    def test_stop_stream(self):
        result = self.client.stop_stream()
        self.assertTrue(result)

    def test_soft_reset(self):
        result = self.client.soft_reset()
        self.assertTrue(result)

    # ── Gain / Exposure ────────────────────────────────────────────────

    def test_set_gain(self):
        result = self.client.set_gain(480, 256)
        self.assertTrue(result)
        self.mock_stub.SetGain.assert_called_once()

    def test_set_exposure(self):
        result = self.client.set_exposure(1600)
        self.assertTrue(result)
        self.mock_stub.SetExposure.assert_called_once()

    # ── HDR ────────────────────────────────────────────────────────────

    def test_set_hdr(self):
        result = self.client.set_hdr(1)
        self.assertTrue(result)
        self.mock_stub.SetHdr.assert_called_once()

    # ── Test Pattern ────────────────────────────────────────────────────

    def test_set_test_pattern(self):
        result = self.client.set_test_pattern(1)
        self.assertTrue(result)
        self.mock_stub.SetTestPattern.assert_called_once()

    # ── Capture ────────────────────────────────────────────────────────

    def test_capture_frame(self):
        frame = self.client.capture_frame()
        self.assertIsNotNone(frame)
        self.assertEqual(frame['width'], 4608)
        self.assertEqual(frame['height'], 2592)
        self.assertEqual(len(frame['data']), 4608 * 2592 * 2)

    def test_capture_frame_custom_size(self):
        self.mock_stub.CaptureFrame.return_value = MagicMock(
            width=1920, height=1080, stride=3840, format=0,
            timestamp_ns=987654321, frame_number=2, gain=240,
            exposure=800, data=b'\x00' * (1920 * 1080 * 2))
        frame = self.client.capture_frame(width=1920, height=1080)
        self.assertEqual(frame['width'], 1920)
        self.assertEqual(frame['height'], 1080)

    # ── Registers ──────────────────────────────────────────────────────

    def test_read_register(self):
        val = self.client.read_register(0x0016)
        self.assertEqual(val, 0x0708)

    def test_write_register(self):
        result = self.client.write_register(0x0204, 0x80)
        self.assertTrue(result)
        self.mock_stub.WriteRegister.assert_called_once()

    # ── Image Processing ──────────────────────────────────────────────

    def test_get_image_processing(self):
        cfg = self.client.get_image_processing()
        self.assertIsNotNone(cfg)
        self.assertEqual(cfg['brightness'], 0)
        self.assertEqual(cfg['contrast'], 128)
        self.assertTrue(cfg['auto_wb'])

    def test_set_image_processing(self):
        result = self.client.set_image_processing(brightness=50, contrast=200)
        self.assertTrue(result)

    # ── Edge Cases ─────────────────────────────────────────────────────

    def test_get_status_returns_none_on_error(self):
        self.mock_stub.GetStatus.side_effect = Exception("timeout")
        status = self.client.get_status()
        self.assertIsNone(status)

    def test_capture_frame_returns_none_on_error(self):
        self.mock_stub.CaptureFrame.side_effect = Exception("capture failed")
        frame = self.client.capture_frame()
        self.assertIsNone(frame)

    def test_all_operations_fail_when_disconnected(self):
        self.client._stub = None
        self.assertIsNone(self.client.get_status())
        self.assertEqual(self.client.get_modes(), [])
        self.assertFalse(self.client.start_stream())
        self.assertFalse(self.client.stop_stream())
        self.assertFalse(self.client.soft_reset())
        self.assertFalse(self.client.set_gain(0, 0))
        self.assertFalse(self.client.set_exposure(0))
        self.assertFalse(self.client.set_hdr(0))
        self.assertFalse(self.client.set_test_pattern(0))
        self.assertIsNone(self.client.capture_frame())
        self.assertIsNone(self.client.read_register(0))
        self.assertFalse(self.client.write_register(0, 0))
        self.assertIsNone(self.client.get_image_processing())
        self.assertFalse(self.client.set_image_processing())

    # ── Logging ─────────────────────────────────────────────────────────

    def test_log_message_on_error(self):
        self.mock_stub.GetStatus.side_effect = Exception("test error")
        self.client.get_status()
        self.assertTrue(any("test error" in log for log in self.logs))


if __name__ == '__main__':
    unittest.main()
