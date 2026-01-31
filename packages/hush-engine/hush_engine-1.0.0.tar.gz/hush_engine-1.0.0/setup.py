"""
py2app setup script for Hush Python backend

NOTE: This file is deprecated and retained for reference only.
The app now uses Swift Package Manager for the Swift frontend and PythonKit
for runtime Python integration. Python dependencies are managed via pip/venv.

Legacy usage (if needed):
    python setup.py py2app --semi-standalone

The output would be in dist/Hush.app which contains the Python.framework
and all dependencies. However, the main app is now built via:
    cd Hush.swiftpm && swift build
"""

from setuptools import setup
import sys
import os

# Get the directory containing this script
HERE = os.path.dirname(os.path.abspath(__file__))

# Python modules to include
PACKAGES = [
    'src',
    'src.ocr',
    'src.detectors',
    'src.anonymizers',
    'src.ui',
]

# Data files to include
DATA_FILES = [
    ('icons', ['icons/hush-1024.png']),
]

# Dependencies that must be bundled
INCLUDES = [
    'PIL',
    'PIL._imaging',
    'pandas',
    'numpy',
    'spacy',
    'presidio_analyzer',
    'presidio_anonymizer',
    'faker',
    'openpyxl',
    'pyobjc',
    'Vision',
    'Quartz',
    'Foundation',
]

# Frameworks to include
FRAMEWORKS = []

# py2app options
OPTIONS = {
    'argv_emulation': False,
    'iconfile': 'icons/hush-1024.png',
    'plist': {
        'CFBundleName': 'Hush',
        'CFBundleDisplayName': 'Hush',
        'CFBundleIdentifier': 'com.hush.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'LSMinimumSystemVersion': '14.0',
        'NSHighResolutionCapable': True,
        'LSUIElement': True,  # Menu bar app, no dock icon by default
    },
    'packages': PACKAGES,
    'includes': INCLUDES,
    'frameworks': FRAMEWORKS,
    'resources': [
        'src',
    ],
    # Semi-standalone uses system Python framework but bundles site-packages
    # This reduces bundle size significantly
    'semi_standalone': True,
    # Optimize bytecode
    'optimize': 2,
    # Strip debug symbols
    'strip': True,
}

setup(
    name='Hush',
    version='1.0.0',
    description='Local PII scrubbing tool',
    author='Hush',
    # NOTE: src/main.py has been deleted. This entry point is obsolete.
    # The Swift app (Hush.swiftpm) is now the main entry point.
    app=[],  # Empty - Swift app is the entry point
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
