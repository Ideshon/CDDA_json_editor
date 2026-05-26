import subprocess
import sys
import unittest
import os
from pathlib import Path


class TestWindowsTaskHelpers(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "win32", "Windows task helpers are only executable on Windows")
    def test_tasks_cmd_check_uses_working_local_poetry(self):
        project_root = Path(__file__).resolve().parents[1]

        result = subprocess.run(
            [str(project_root / "tasks.cmd"), "check"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60,
        )

        output = (result.stdout + result.stderr).strip()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("All set!", output)

    @unittest.skipUnless(sys.platform == "win32", "Windows task helpers are only executable on Windows")
    def test_tasks_cmd_test_can_run_fast_smoke_target(self):
        result = self._run_task(
            "test",
            {"CDDA_TASKS_TEST_ARGS": "tests.test_package_entrypoint -v"},
        )

        output = (result.stdout + result.stderr).strip()
        self.assertEqual(result.returncode, 0, output)
        self.assertIn("Ran 1 test", output)

    @unittest.skipUnless(sys.platform == "win32", "Windows task helpers are only executable on Windows")
    def test_tasks_cmd_build_can_run_fast_smoke_target(self):
        result = self._run_task(
            "build",
            {"CDDA_TASKS_BUILD_ARGS": "--version"},
        )

        output = (result.stdout + result.stderr).strip()
        self.assertEqual(result.returncode, 0, output)
        self.assertRegex(output, r"\d+\.\d+")

    def _run_task(
        self,
        task: str,
        extra_env: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        project_root = Path(__file__).resolve().parents[1]
        env = os.environ.copy()
        if extra_env:
            env.update(extra_env)

        return subprocess.run(
            [str(project_root / "tasks.cmd"), task],
            cwd=project_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=60,
        )


if __name__ == "__main__":
    unittest.main()
