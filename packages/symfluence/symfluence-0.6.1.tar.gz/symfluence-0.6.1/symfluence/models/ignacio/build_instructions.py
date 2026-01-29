"""
IGNACIO build instructions for SYMFLUENCE.

This module defines how to install IGNACIO (Fire-Engine-Framework) from source.
IGNACIO is a Python package implementing the Canadian FBP System for fire
spread simulation with Richards' elliptical wave propagation.

Unlike compiled tools, IGNACIO is installed via pip as an editable package.
"""

from symfluence.cli.services import BuildInstructionsRegistry


@BuildInstructionsRegistry.register('ignacio')
def get_ignacio_build_instructions():
    """
    Get IGNACIO build instructions.

    IGNACIO is a Python package that implements the Canadian Forest Fire
    Behavior Prediction (FBP) System. It is installed via pip from the
    cloned repository.

    Returns:
        Dictionary with complete build configuration for IGNACIO.
    """
    return {
        'description': 'IGNACIO - Canadian FBP System fire spread model',
        'config_path_key': 'IGNACIO_INSTALL_PATH',
        'config_exe_key': 'IGNACIO_CLI',
        'default_path_suffix': 'installs/ignacio',
        'default_exe': 'ignacio',  # CLI entry point after pip install
        'repository': 'https://github.com/KatherineHopeReece/Fire-Engine-Framework.git',
        'branch': None,
        'install_dir': 'ignacio',
        'build_commands': [
            r'''
set -e
echo "Installing IGNACIO (Fire-Engine-Framework)..."

# Verify we're in the ignacio directory with pyproject.toml
if [ ! -f "pyproject.toml" ]; then
    echo "ERROR: pyproject.toml not found. Are we in the ignacio directory?"
    exit 1
fi

# Check if ignacio is already installed
if python -c "import ignacio" 2>/dev/null; then
    echo "IGNACIO already installed, checking if update needed..."
    # Reinstall in editable mode to pick up any changes
fi

# Install in editable mode with pip
echo "Installing IGNACIO in editable mode..."
pip install -e . --quiet

# Verify installation
echo "Verifying installation..."
if python -c "import ignacio; print(f'IGNACIO version: {ignacio.__version__ if hasattr(ignacio, \"__version__\") else \"unknown\"}')" 2>/dev/null; then
    echo "IGNACIO Python package installed successfully"
else
    echo "ERROR: IGNACIO Python package installation failed"
    exit 1
fi

# Verify CLI is available
if command -v ignacio >/dev/null 2>&1; then
    echo "IGNACIO CLI available: $(which ignacio)"
else
    echo "WARNING: IGNACIO CLI not found in PATH"
    echo "You may need to activate your environment or add the bin directory to PATH"
fi

echo "IGNACIO installation complete"
            '''.strip()
        ],
        'dependencies': [],
        'test_command': '--help',  # Test CLI with --help
        'verify_install': {
            'python_import': 'ignacio',
            'check_type': 'python_import'
        },
        'order': 15  # Install after other fire models
    }
