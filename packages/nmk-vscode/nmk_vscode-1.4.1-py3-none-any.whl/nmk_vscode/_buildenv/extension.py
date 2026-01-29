import logging
import shutil
import subprocess
from pathlib import Path

from buildenv2._utils import LOGGER_NAME
from buildenv2.extension import BuildEnvExtension, BuildEnvRenderer
from jinja2 import Environment, PackageLoader

# Logger instance
_logger = logging.getLogger(LOGGER_NAME)


class NmkVsCodeBuildEnvExtension(BuildEnvExtension):
    def init(self, force: bool):
        # Nothing to do in init for buildenv >= 2
        pass

    def generate_activation_scripts(self, renderer: BuildEnvRenderer):
        """
        When called, this method:

        * looks for **vscode** shell init script path
        * adds an activation script to call it
        """

        # Check for code command
        code_cmd = shutil.which("code")
        if code_cmd is not None:
            # Ask for init script
            cp = subprocess.run(
                [code_cmd, "--locate-shell-integration-path", "bash"],
                capture_output=True,
                check=False,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            if cp.returncode == 0:
                # Check for returned script path
                output_lines = cp.stdout.splitlines()
                script_path = cp.stdout.splitlines()[0].strip() if output_lines else None
                if script_path and Path(script_path).is_file():
                    # Add activation script
                    renderer.render(Environment(loader=PackageLoader("nmk_vscode", "_templates")), "vscode.sh.jinja", keywords={"vscodeScript": script_path})
                else:
                    _logger.warning(f"nmk-vscode: bash init script not found: {script_path}")
            else:
                _logger.warning("nmk-vscode: 'code --locate-shell-integration-path bash' command failed!")
        else:
            _logger.warning("nmk-vscode: 'code' command not found!")
