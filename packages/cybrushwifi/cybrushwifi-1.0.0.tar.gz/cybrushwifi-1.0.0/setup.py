from setuptools import setup, find_packages
from pathlib import Path

# Read README safely
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding="utf-8")

setup(
    name="cybrushwifi",
    version="1.0.0",
    author="Cybrush Security",
    author_email="contact@cybrushsecurity.com",
    description="Professional Wi-Fi security scanning and monitoring tool",
    long_description=long_description,
    long_description_content_type="text/markdown",

    packages=find_packages(),
    include_package_data=True,   # 👈 REQUIRED to include web/index.html

    install_requires=[
        "pywebview",
        "requests",
        "reportlab"
    ],

    entry_points={
        "console_scripts": [
            "cybrushwifi=cybrushwifi.gui:launch"
        ]
    },

    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Information Technology",
        "Topic :: Security",
        "Topic :: System :: Networking",
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent"
    ],

    python_requires=">=3.8",
)
