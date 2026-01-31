"""Setup script to run code generation during installation."""

import subprocess
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install


def run_code_generation():
    """Run the code generation script after installation."""
    try:
        # Get the project root directory
        project_root = Path(__file__).parent

        # Run the code generation
        subprocess.check_call(
            [
                sys.executable,
                "-m",
                "qualpipe_webapp.backend.codegen.generate_data_models",
                "--module",
                "qualpipe.core.criterion",
                "--out-generated",
                str(project_root / "src" / "qualpipe_webapp" / "backend" / "generated"),
                "--out-schemas",
                str(project_root / "src" / "qualpipe_webapp" / "frontend" / "static"),
            ]
        )
        print("✅ Code generation completed successfully")
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Code generation failed: {e}")
        print("You can run it manually with: qualpipe-generate-models")
    except Exception as e:
        print(f"⚠️  Could not run code generation: {e}")
        print("You can run it manually with: qualpipe-generate-models")


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self):  # noqa: D102
        develop.run(self)
        self.execute(run_code_generation, (), msg="Running code generation")


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self):  # noqa: D102
        install.run(self)
        self.execute(run_code_generation, (), msg="Running code generation")


if __name__ == "__main__":
    setup(
        cmdclass={
            "develop": PostDevelopCommand,
            "install": PostInstallCommand,
        },
    )
