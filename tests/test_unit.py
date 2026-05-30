"""
Regression tests for issue #621 — run without a live stack.

Verifies:
  1. _cleanup_stale_test_data calls the ORM delete with all three known usernames.
  2. A cleanup failure prints a warning instead of aborting setUpClass.
  3. tearDownClass quits both drivers even when _delete_object raises any exception.
  4. tearDownClass raises RuntimeError when _delete_object fails, so CI exits non-zero.
"""
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.dirname(__file__))


class TestCleanupStaleData(unittest.TestCase):
    def setUp(self):
        from runtests import TestServices

        self.cls = TestServices

    def test_targets_all_three_known_usernames(self):
        """Command sent to docker must reference all three stale usernames."""
        with patch.object(self.cls, "_execute_docker_compose_command") as mock_exec:
            self.cls._cleanup_stale_test_data()
            mock_exec.assert_called_once()
            shell_cmd = " ".join(str(a) for a in mock_exec.call_args[0][0])
            for username in ("signup-user", "test_superuser", "test_superuser2"):
                self.assertIn(username, shell_cmd, f"Missing username: {username}")

    def test_failure_does_not_raise(self):
        """A docker exec failure must print a warning and not abort the test suite."""
        with patch.object(
            self.cls,
            "_execute_docker_compose_command",
            side_effect=RuntimeError("docker exec failed"),
        ):
            try:
                self.cls._cleanup_stale_test_data()
            except Exception as exc:
                self.fail(f"_cleanup_stale_test_data raised unexpectedly: {exc}")


class TestTeardownResilience(unittest.TestCase):
    def test_quits_drivers_even_when_delete_object_raises(self):
        """Both drivers must be quit even if _delete_object raises any exception."""
        from runtests import TestServices

        mock_driver = MagicMock()
        saved_objects = list(TestServices.objects_to_delete)
        saved_failed = getattr(TestServices, "failed_test", False)
        had_base = hasattr(TestServices, "base_driver")
        had_second = hasattr(TestServices, "second_driver")

        try:
            TestServices.objects_to_delete = ["http://fake/resource/change/"]
            TestServices.failed_test = False
            TestServices.base_driver = mock_driver
            TestServices.second_driver = mock_driver

            with patch.object(
                TestServices,
                "_delete_object",
                side_effect=Exception("ReadTimeoutError: read timeout=120"),
            ):
                with self.assertRaises(RuntimeError):
                    TestServices.tearDownClass()

            self.assertEqual(mock_driver.quit.call_count, 2)
        finally:
            TestServices.objects_to_delete = saved_objects
            TestServices.failed_test = saved_failed
            if not had_base and "base_driver" in TestServices.__dict__:
                delattr(TestServices, "base_driver")
            if not had_second and "second_driver" in TestServices.__dict__:
                delattr(TestServices, "second_driver")


class TestTeardownSurfacesErrors(unittest.TestCase):
    def test_teardown_raises_when_delete_object_fails(self):
        """tearDownClass must raise so unittest records a failure and CI exits non-zero."""
        from runtests import TestServices

        mock_driver = MagicMock()
        saved_objects = list(TestServices.objects_to_delete)
        saved_failed = getattr(TestServices, "failed_test", False)
        had_base = hasattr(TestServices, "base_driver")
        had_second = hasattr(TestServices, "second_driver")

        try:
            TestServices.objects_to_delete = ["http://fake/resource/change/"]
            TestServices.failed_test = False
            TestServices.base_driver = mock_driver
            TestServices.second_driver = mock_driver

            with patch.object(
                TestServices,
                "_delete_object",
                side_effect=Exception("NoSuchElementException: no such element"),
            ):
                with self.assertRaises(RuntimeError):
                    TestServices.tearDownClass()
        finally:
            TestServices.objects_to_delete = saved_objects
            TestServices.failed_test = saved_failed
            if not had_base and "base_driver" in TestServices.__dict__:
                delattr(TestServices, "base_driver")
            if not had_second and "second_driver" in TestServices.__dict__:
                delattr(TestServices, "second_driver")


if __name__ == "__main__":
    unittest.main(verbosity=2)
