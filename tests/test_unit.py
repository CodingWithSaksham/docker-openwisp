import unittest
from unittest.mock import MagicMock, patch


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
        """tearDownClass must raise so CI exits non-zero on _delete_object failure."""
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
