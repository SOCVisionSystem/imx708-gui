# SPDX-License-Identifier: GPL-2.0-only
"""
gRPC client for the IMX708 camera sensor.

Copyright (C) 2026 SoC Centric
Author: Sandesh <sandesh@soccentric.com>
"""

import sys
import os
import threading
from typing import Optional, List, Dict

from PySide6.QtCore import QObject, Signal

# Try to import gRPC
try:
    import grpc
    from grpc import insecure_channel
    HAVE_GRPC = True
except ImportError:
    HAVE_GRPC = False

# Try to import proto modules
try:
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))

    sys.path.insert(0, os.path.join(base_path, '..', 'imx708_proto'))
    sys.path.insert(0, os.path.join(base_path, '..', 'build'))
    sys.path.insert(0, base_path)

    import imx708_pb2
    import imx708_pb2_grpc
    HAVE_PROTO = True
except ImportError as e:
    HAVE_PROTO = False


class GrpcClient(QObject):
    """gRPC client running in a background thread."""

    status_updated = Signal(dict)
    frame_received = Signal(dict)
    connection_changed = Signal(bool)
    log_message = Signal(str)

    MAX_MESSAGE_BYTES = 100 * 1024 * 1024

    CHANNEL_OPTIONS = [
        ("grpc.max_receive_message_length", MAX_MESSAGE_BYTES),
        ("grpc.max_send_message_length", MAX_MESSAGE_BYTES),
    ]

    def __init__(self, server_addr: str = "localhost:50051"):
        super().__init__()
        self.server_addr = server_addr
        self._channel = None
        self._stub = None
        self._connected = False
        self._running = False
        self._status_thread = None
        self._frame_thread = None
        self._status_call = None

    @property
    def connected(self) -> bool:
        return self._connected

    def connect(self) -> bool:
        if not HAVE_GRPC or not HAVE_PROTO:
            self.log_message.emit("gRPC or proto modules not available")
            return False
        try:
            self._channel = insecure_channel(
                self.server_addr, options=self.CHANNEL_OPTIONS)
            self._stub = imx708_pb2_grpc.Imx708ServiceStub(self._channel)
            resp = self._stub.GetStatus(imx708_pb2.Empty(), timeout=2)
            self._connected = True
            self.connection_changed.emit(True)
            self.log_message.emit(f"Connected to {self.server_addr}")
            return True
        except Exception as e:
            self._connected = False
            self.connection_changed.emit(False)
            self.log_message.emit(f"Connection failed: {e}")
            return False

    def disconnect(self):
        self.stop_status_stream()
        if self._channel:
            self._channel.close()
            self._channel = None
        self._stub = None
        self._connected = False
        self.connection_changed.emit(False)

    # ── Unary RPCs ──────────────────────────────────────────────────────

    def get_status(self) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            resp = self._stub.GetStatus(imx708_pb2.Empty(), timeout=5)
            return {
                'temperature': resp.temperature,
                'frame_count': resp.frame_count,
                'pll_locked': resp.pll_locked,
                'streaming': resp.streaming,
                'error': resp.error,
                'gain': resp.gain,
                'digital_gain': resp.digital_gain,
                'exposure': resp.exposure,
                'width': resp.width,
                'height': resp.height,
                'fps': resp.fps,
            }
        except Exception as e:
            self.log_message.emit(f"get_status error: {e}")
            return None

    def get_modes(self) -> List[Dict]:
        if not self._stub:
            return []
        try:
            resp = self._stub.GetModes(imx708_pb2.Empty(), timeout=5)
            return [
                {
                    'index': m.index, 'width': m.width, 'height': m.height,
                    'code': m.code, 'fps': m.fps, 'hblank': m.hblank,
                    'vblank': m.vblank, 'bit_depth': m.bit_depth,
                    'pixel_rate': m.pixel_rate
                }
                for m in resp.modes
            ]
        except Exception as e:
            self.log_message.emit(f"get_modes error: {e}")
            return []

    def start_stream(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.StartStream(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"start_stream error: {e}")
            return False

    def stop_stream(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.StopStream(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"stop_stream error: {e}")
            return False

    def soft_reset(self) -> bool:
        if not self._stub:
            return False
        try:
            resp = self._stub.SoftReset(imx708_pb2.Empty(), timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"soft_reset error: {e}")
            return False

    def set_gain(self, analog: int, digital: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.GainConfig(analog_gain=analog, digital_gain=digital)
            resp = self._stub.SetGain(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_gain error: {e}")
            return False

    def set_exposure(self, exposure: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.ExposureConfig(exposure=exposure)
            resp = self._stub.SetExposure(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_exposure error: {e}")
            return False

    def set_hdr(self, mode: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.HdrConfig(mode=mode)
            resp = self._stub.SetHdr(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_hdr error: {e}")
            return False

    def set_test_pattern(self, pattern: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.TestPatternConfig(pattern=pattern)
            resp = self._stub.SetTestPattern(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_test_pattern error: {e}")
            return False

    def capture_frame(self, width: int = 0, height: int = 0) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            req = imx708_pb2.CaptureParams(
                width=width or 4608, height=height or 2592,
                format=0, num_frames=1)
            resp = self._stub.CaptureFrame(req, timeout=30)
            return {
                'width': resp.width, 'height': resp.height,
                'stride': resp.stride, 'format': resp.format,
                'timestamp_ns': resp.timestamp_ns,
                'frame_number': resp.frame_number,
                'gain': resp.gain, 'exposure': resp.exposure,
                'data': resp.data,
            }
        except Exception as e:
            self.log_message.emit(f"capture_frame error: {e}")
            return None

    def read_register(self, addr: int) -> Optional[int]:
        if not self._stub:
            return None
        try:
            req = imx708_pb2.RegisterAccess(reg=addr)
            resp = self._stub.ReadRegister(req, timeout=5)
            return resp.val
        except Exception as e:
            self.log_message.emit(f"read_register error: {e}")
            return None

    def write_register(self, addr: int, val: int) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.RegisterAccess(reg=addr, val=val)
            resp = self._stub.WriteRegister(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"write_register error: {e}")
            return False

    def get_image_processing(self) -> Optional[Dict]:
        if not self._stub:
            return None
        try:
            resp = self._stub.GetImageProcessing(imx708_pb2.Empty(), timeout=5)
            return {
                'brightness': resp.brightness, 'contrast': resp.contrast,
                'saturation': resp.saturation, 'hue': resp.hue,
                'sharpness': resp.sharpness, 'gamma': resp.gamma,
                'auto_wb': resp.auto_wb, 'wb_temperature': resp.wb_temperature,
                'hflip': resp.hflip, 'vflip': resp.vflip,
            }
        except Exception as e:
            self.log_message.emit(f"get_image_processing error: {e}")
            return None

    def set_image_processing(self, **kwargs) -> bool:
        if not self._stub:
            return False
        try:
            req = imx708_pb2.ImageProcessingConfig(**kwargs)
            resp = self._stub.SetImageProcessing(req, timeout=5)
            return resp.success
        except Exception as e:
            self.log_message.emit(f"set_image_processing error: {e}")
            return False

    # ── Streaming RPCs ──────────────────────────────────────────────────

    def start_status_stream(self):
        if not self._stub or self._running:
            return
        self._running = True
        self._status_thread = threading.Thread(target=self._status_loop, daemon=True)
        self._status_thread.start()

    def stop_status_stream(self):
        self._running = False
        if self._status_call:
            self._status_call.cancel()
        if self._status_thread and self._status_thread.is_alive():
            self._status_thread.join(timeout=2)

    def _status_loop(self):
        try:
            self._status_call = self._stub.StreamStatus(
                imx708_pb2.Empty(), timeout=86400)
            for event in self._status_call:
                if not self._running:
                    break
                if event.HasField('status_update'):
                    s = event.status_update
                    self.status_updated.emit({
                        'temperature': s.temperature,
                        'frame_count': s.frame_count,
                        'pll_locked': s.pll_locked,
                        'streaming': s.streaming,
                        'error': s.error,
                        'gain': s.gain,
                        'digital_gain': s.digital_gain,
                        'exposure': s.exposure,
                        'width': s.width,
                        'height': s.height,
                        'fps': s.fps,
                    })
        except Exception as e:
            if self._running:
                self.log_message.emit(f"Status stream ended: {e}")
                # Auto-reconnect on stream drop
                self.connection_changed.emit(False)
        finally:
            self._status_call = None
            self._running = False
