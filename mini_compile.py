from compile import run_pyinstaller
import os
install_py = "install_CellACDC.py"
run_pyinstaller(install_py, "Cell-ACDC-installer", admin=True)
