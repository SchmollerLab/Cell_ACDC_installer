.. |acdclogo| image:: https://raw.githubusercontent.com/SchmollerLab/Cell_ACDC/6bf8442b6a33d41fa9de09a2098c6c2b9efbcff1/cellacdc/resources/logo.svg
   :width: 80

|acdclogo| Cell-ACDC Installer
================================

Overview
--------
Cell-ACDC is a scientific application for cell analysis. The main repository can be found
`here <https://github.com/SchmollerLab/Cell_ACDC>`_.
This is the official Cell-ACDC installer for x86_64 Windows systems, which simplifies the installation process and eliminates the need for command line usage. It provides a user-friendly interface to install and run Cell-ACDC with all necessary dependencies.

Download
--------
Pre-built installers (.exe) for Cell-ACDC can be downloaded from the `official release page <https://hmgubox2.helmholtz-muenchen.de/index.php/s/aBFkjEYrH6HW5bN>`_:

`📥 Download Cell-ACDC Installer <https://hmgubox2.helmholtz-muenchen.de/index.php/s/aBFkjEYrH6HW5bN>`_

The installer was created using `Inno Setup <https://jrsoftware.org/isinfo.php>`_ and contains a `Portable Git <https://git-scm.com/download/win>`_ and a `Miniforge <https://github.com/conda-forge/miniforge>`_ version.

Installation Info
-----------------

**✨ For more information, please consult our** `installation guide <https://cell-acdc.readthedocs.io/en/latest/installation.html#install-cell-acdc-on-windows-using-the-installer>`_. ✨

- The installer relies on an internet connection for downloading dependencies and updates.
- The installer supports installing Cell-ACDC with an embedded Python environment (Miniforge) or using a custom Python/Forge installation.
- You can choose to install from a bundled Cell-ACDC package, from PyPI, directly from GitHub, or your own Cell-ACDC source.
- The installer will set up all dependencies, download Cell-ACDC if needed, create an environment, and add shortcuts to your Start Menu and Desktop (optional).
- All files are installed to ``%LOCALAPPDATA%\Cell-ACDC`` by default, but you can select a custom directory during installation.

What Gets Installed
-------------------
- Cell-ACDC application files
- Python environment (Miniforge/conda) if no custom Python is selected
- All required Python packages
- A portable Git client (for GitHub installs)
- Shortcuts for easy launching

Building the Installer
----------------------
If you want to build the installer yourself:

1. Install Required Software

   Download and install Inno Setup from: \
   https://jrsoftware.org/isdl.php#stable

   Download and install Portable Git from: \
   https://git-scm.com/download/win

   Download and install Miniforge from: \
   https://conda-forge.org/download/

2. Install Python dependencies
   Open a terminal in this directory and run:

   .. code-block:: bash

      pip install pyinstaller requests regex

3. Customise the build

   - Edit ``compile.py`` to set the Python version, Cell-ACDC version, and other parameters.
   - Make sure all paths are correct and the required files are present.
   - The ``acdc_version`` should match the version of Cell-ACDC you want to build.

   Settings users should change in ``compile.py``:

   .. code-block:: python
   
         cell_ACDC_source = r"path/to/Cell-ACDC.whl"  # Path to the Cell-ACDC whl source code
         git_source = r"path/to/portablegit/source"  # Path to the Portable Git source folder
         mini_source = r"path/to/miniforge"  # Path to the Miniforge folder
         icon_path = r"path/to/CellACDCicon.ico"  # Path to the icon file for the installer
         acdc_version = "1.6.1"  # Cell-ACDC version to build

4. Build the executables
   Run the build script:

   .. code-block:: bash

      python compile.py

   This will generate the required ``.exe`` files, as well as the Inno Setup script, in a subfolder corresponding to the Cell-ACDC version (e.g., ``1.6.1/``).

5. Build the installer
   Open the generated ``.iss`` file (e.g., ``1.6.1/CellACDC.iss``) in Inno Setup and click "Compile".
   The installer executable will be created (e.g., in ``1.6.1/Output/Cell-ACDC-1_6_1-Setup.exe``).

Installing Cell-ACDC
--------------------
- Double-click the setup ``.exe`` and follow the installation instructions.
- The installer will set up Cell-ACDC and create shortcuts.

**✨ For more information, please consult our** `installation guide <https://cell-acdc.readthedocs.io/en/latest/installation.html#install-cell-acdc-on-windows-using-the-installer>`_. ✨


