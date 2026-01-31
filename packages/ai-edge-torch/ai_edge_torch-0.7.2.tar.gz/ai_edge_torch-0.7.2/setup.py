import sys
from setuptools import find_packages, setup
from setuptools.command.install import install

# Custom warning message
DEPRECATION_WARNING = """
=====================================================================
WARNING: ai-edge-torch is now DEPRECATED.
It has been renamed to 'litert-torch'.

Please update your requirements:
  pip install litert-torch

Future updates will ONLY be released under the 'litert-torch' name.
=====================================================================
"""


class PostInstallWarning(install):

  def run(self):
    # Run the standard installation first
    install.run(self)
    # Print the warning to stderr so it shows up in most terminals
    sys.stderr.write(DEPRECATION_WARNING)


setup(
    name="ai-edge-torch",
    version="0.7.2",
    description="DEPRECATED: renamed to litert-torch",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "litert-torch",  # Redirects the user to the new package automatically
    ],
    cmdclass={
        "install": PostInstallWarning,
    },
    classifiers=[
        "Development Status :: 7 - Inactive",
    ],
)
