"""Face-covering graphical overlays must be flagged, not called creative PASS."""
import importlib.util
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

HAS_DEPS = (importlib.util.find_spec("cv2") is not None
            and importlib.util.find_spec("numpy") is not None
            and bool(shutil.which("ffmpeg")))


@unittest.skipUnless(HAS_DEPS, "Requires OpenCV, NumPy and FFmpeg")
class BeforeAfterFaceWarnings(unittest.TestCase):
    def make_video(self, folder):
        source=folder/"source.mp4"
        overlay=folder/"overlay.mp4"
        subprocess.run([
            "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-f","lavfi","-i","testsrc2=size=360x640:rate=8:duration=2",
            "-c:v","libx264","-pix_fmt","yuv420p",str(source)
        ],check=True,timeout=30)
        subprocess.run([
            "ffmpeg","-hide_banner","-loglevel","error","-nostdin","-y",
            "-i",str(source),
            "-vf","drawbox=x=120:y=210:w=100:h=110:color=white:t=fill",
            "-c:v","libx264","-pix_fmt","yuv420p",str(overlay)
        ],check=True,timeout=30)
        return source,overlay

    def fake_detector(self):
        import numpy as np
        class Face:
            def detect(self,frame):
                # YuNet face bbox plus 10 landmark values and confidence.
                data=np.zeros((1,15),dtype=np.float32)
                data[0,:4]=[120,210,100,110]
                data[0,14]=0.99
                return 1,data
        return SimpleNamespace(create=lambda *args:Face())

    def test_obvious_face_cover_is_detected(self):
        import cv2
        from tools.face_motion_qc import inspect_face_change
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            source,overlay=self.make_video(folder)
            model=folder/"dummy.onnx"
            model.write_bytes(b"test-model-stub")
            with patch.object(cv2,"FaceDetectorYN",self.fake_detector()):
                report=inspect_face_change(source,overlay,model)
            self.assertEqual("POSSIBLE_FACE_OVERLAY_REVIEW_REQUIRED",report["status"])
            self.assertEqual(3,report["face_detections"])
            self.assertGreater(report["possible_overlays"],0)
            self.assertTrue(all("face_found" in p for p in report["samples"]))

    def test_unaltered_face_remains_without_major_change(self):
        import cv2
        from tools.face_motion_qc import inspect_face_change
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp)
            source,_=self.make_video(folder)
            model=folder/"dummy.onnx"
            model.write_bytes(b"test-model-stub")
            with patch.object(cv2,"FaceDetectorYN",self.fake_detector()):
                report=inspect_face_change(source,source,model)
            self.assertEqual("NO_MAJOR_FACE_CHANGE_IN_SAMPLED_FRAMES",report["status"])
            self.assertEqual(0,report["possible_overlays"])


if __name__=="__main__":
    unittest.main()
