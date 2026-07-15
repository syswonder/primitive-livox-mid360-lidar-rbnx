from __future__ import annotations

import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest import mock


class _Primitive:
    def __init__(self, **_kwargs):
        self.declared_topics: list[tuple[tuple, dict]] = []

    @staticmethod
    def on_init(func):
        return func

    @staticmethod
    def on_shutdown(func):
        return func

    def declare_ros2_topic(self, *args, **kwargs):
        self.declared_topics.append((args, kwargs))

    @staticmethod
    def run():
        return None


def _load_driver():
    api = types.ModuleType("robonix_api")
    api.Primitive = _Primitive
    api.Ok = lambda value=None: ("ok", value)
    api.Err = lambda value=None: ("err", value)

    module_path = Path(__file__).parents[1] / "mid360_driver" / "main.py"
    spec = importlib.util.spec_from_file_location("mid360_driver_main_test", module_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)

    with mock.patch.dict(sys.modules, {"robonix_api": api}):
        spec.loader.exec_module(module)
    return module


class InitLifecycleTests(unittest.TestCase):
    def test_init_starts_one_static_transform_publisher(self):
        driver = _load_driver()

        with (
            mock.patch.object(driver, "_spawn_livox"),
            mock.patch.object(driver, "_wait_for_pointcloud", return_value=True),
            mock.patch.object(driver, "_spawn_stp") as spawn_stp,
        ):
            result = driver.init({"extrinsics": {"x": 0.1}})

        self.assertEqual(result[0], "ok")
        spawn_stp.assert_called_once_with({"extrinsics": {"x": 0.1}})
        self.assertEqual(len(driver.cap.declared_topics), 1)


if __name__ == "__main__":
    unittest.main()
