with open("datalogger/version.py") as f:
    exec(f.read())

from setuptools import setup

setup(
    name="datalogger-tf",
    description="datalogger-tf is a GUI interfaced software to log multiple instruments via ethernet, usb or serial connection.",
    version=__version__,
    packages=["datalogger", "datalogger.instruments"],
    scripts=["bin/datalogger-gui"],
    install_requires=["PyQt6", "numpy", "telnetlib3", "pyserial", "labjack-ljm"],
    author="Baptiste Marechal",
    maintainer="Benoit Dubois",
    maintainer_email="benoit.dubois@femto-engineering.fr",
    url="https://gitlab.com/pythonbase1/datalogger",
    license = "GPL-3.0-or-later",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Operating System :: POSIX",
        "Programming Language :: Python",
        "Topic :: Scientific/Engineering",
    ],
)
