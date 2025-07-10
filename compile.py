import subprocess
import shutil
import os
import requests

# venv requirements: 
# pip install pyinstaller
# pip install requests
# pip install regex

# Path to cell-ACDC icon
icon_path = r"path\to\icon.ico"


# source code for the Cell-ACDC installer
install_py = r"install_CellACDC.py"
# source code for the Cell-ACDC launcher
launch_py = r"CellACDC.py"
# python miniforge folder
mini_source = r"path\to\miniforge3"
# path to portable git source code, used for the installer
git_source = r"path\to\PortableGit"
# Path to Cell-ACDC source code
cell_ACDC_source = r"path\to\cellacdc-1.6.2-py3-none-any.whl"
# Python version to install in the miniforge environment
py_ver_install = "3.12.10"
# Path to the Inno Setup script file
iss_file = "CellACDC.iss" 
# Version of Cell-ACDC to build the installer for, this is 
# used to give the exe a name. Should match cell_ACDC_source version, but 
# any version can be used to install up to date github or OLDER pypi versions
acdc_version = "1.6.2"
acdc_version_no_points = acdc_version.replace(".", "_")

build_output = os.path.join(acdc_version, "dist")

def get_pypi_versions(package_name):
    url = f"https://pypi.org/pypi/{package_name}/json"
    resp = requests.get(url)
    if resp.status_code == 200:
        data = resp.json()
        versions = sorted(data["releases"].keys(), reverse=True)
    # filter for versions that are lower than 1.6.1
        idx = versions.index("1.6.1")
        # Get all versions before 1.6.1
        versions = versions[:idx]
        return versions
    else:
        raise ValueError(f"Package {package_name} not found on PyPI")

def run_pyinstaller(python_script, exe_name, admin=False):
    # if ps1_name is None:
    #     ps1_name = os.path.basename(python_script).replace(".py", ".ps1")

    # if not isinstance(ps1_name, list):
    #     ps1_name = [ps1_name]
    
    cmd = [
        "pyinstaller",
        "--onefile",
        "--console",
        "--noconfirm",  # Don't ask for confirmation
        f"--name={exe_name}",
        f"--icon={icon_path}",
        python_script
    ]
    
    # Add UAC admin flag for installer executable
    if admin:
        cmd.append("--uac-admin")

    # for ps1 in ps1_name:
    #     ps1 = os.path.join(os.path.dirname(python_script), ps1)
    #     cmd.append(f"--add-data={ps1};.")

    print(f"📦 Compiling: {python_script}")
    subprocess.run(cmd, check=True)

    exe_path = os.path.join("dist", exe_name + ".exe")
    target_path = os.path.join(build_output, exe_name + ".exe")
    shutil.move(exe_path, target_path)
    filename = os.path.basename(exe_path)
    target_path = os.path.join(os.path.dirname(os.path.dirname(target_path)), filename.replace(".exe", ".spec"))
    shutil.move(filename.replace(".exe", ".spec"), target_path)
    # clean up the build artifacts
    print(f"✅ Copied to: {target_path}\n")

def move_build_folder(acdc_version):
    print(f"📦 Moving build folder to: {acdc_version}"
          )
    try:
        shutil.move("build", acdc_version)
    except shutil.Error as e:
        print(f"❌ Error moving build folder: {e}")
        try:
            shutil.rmtree("build")
        except Exception as e:
            import time
            time.sleep(3)
            shutil.rmtree("build")
        return False
    return True

# def copy_python(py_path, py_target_path):
#     print(f"🔧 Copying python: {py_path} -> {py_target_path}")
#     if os.path.exists(py_target_path):
#         try:
#             if os.path.isdir(py_target_path):
#                 shutil.rmtree(py_target_path)  # Remove directory
#             else:
#                 os.remove(py_target_path)      # Remove file
#         except PermissionError as e:
#             print(f"❌ Permission error while trying to remove {py_target_path}: {e}")
#             return False
    
#     # Check if source is a directory or file
#     if os.path.isdir(py_path):
#         shutil.copytree(py_path, py_target_path)  # Copy entire directory tree
#     else:
#         shutil.copy2(py_path, py_target_path)     # Copy single file

#     print(f"✅ Copied python")
#     return True

def update_iss_file(iss_path, acdc_version, available_versions, 
                    py_source):
    print(f"🔧 Updating ISS file: {iss_path}")
    iss_path_new = os.path.join(acdc_version, "CellACDC.iss")

    shutil.copy2(iss_path, iss_path_new)
    
    # Read the file first
    with open(iss_path_new, 'r') as file:
        content = file.read()
    
    # Replace the version placeholder
    content = content.replace("ACDC_VERSION", acdc_version)
    
    # Generate version dropdown lines
    version_lines = []
    for version in available_versions:  # Limit to top 10 versions
        version_lines.append(f"    VersionCombo.Items.Add('{version}');")
    
    version_code = "\n".join(version_lines)
    
    # Replace the available versions placeholder
    content = content.replace("ACDC_AVAILABLE_VERSIONS", version_code)

    content = content.replace("PYTHON_SOURCE", py_source)

    content = content.replace("PLACEHOLDER_PY_VER", py_ver_install)

    content = content.replace("VERSION_NO_POINTS", acdc_version_no_points)

    content = content.replace("MINIFORGE_SOURCE", py_source)  # Ensure this is set correctly

    content = content.replace("CELLACDC_SOURCE", cell_ACDC_source)  # Ensure this is set correctly

    content = content.replace("CELLACDC_FILE_NAME", os.path.basename(cell_ACDC_source))  # Select the correct file name for Cell-ACDC source code programmatically

    content = content.replace("GIT_SOURCE", git_source)  # Ensure this is set correctly

    # Write the updated content back
    with open(iss_path_new, 'w') as file:
        file.write(content)

def check_package_installs():
    print("🔍 Checking package installations..."
          )
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
        print("✅ Required packages are installed.")

    except Exception:
        print("❌ PyInstaller is not installed. Please install it using 'pip install pyinstaller'.")
        raise SystemExit("Exiting due to missing PyInstaller.")


    try:
        import regex
        print("✅ Regex is installed.")
    except ImportError:
        print("❌ Regex is not installed. Please install it using 'pip install regex'.")
        raise SystemExit("Exiting due to missing Regex.")
    
    try:
        import requests
        print("✅ Requests is installed.")
    except ImportError:
        print("❌ Requests is not installed. Please install it using 'pip install requests'.")
        raise SystemExit("Exiting due to missing Requests.")

# # build
if __name__ == "__main__":
    check_package_installs()
    shutil.rmtree(acdc_version, ignore_errors=True)  # Clean up previous builds
    os.makedirs(build_output, exist_ok=True)
    run_pyinstaller(install_py, "Cell-ACDC-installer", admin=True)
    run_pyinstaller(launch_py, "Cell-ACDC")
    # copy_python_success = copy_python(mini_source, os.path.join(acdc_version, "dist", "miniforge"))
    versions = get_pypi_versions("cellacdc")
    print(f"📋 Found {len(versions)} available versions: {versions}...")
    update_iss_file(iss_file, acdc_version, versions, mini_source)
    move_build_folder_success = move_build_folder(acdc_version)
    print("🎉 Compilation completed successfully!")

    try:
        os.rmdir("dist")
    except:
        import time
        time.sleep(3)  # Wait a bit to ensure the dist folder is not in use
        os.rmdir("dist")

# if not copy_python_success:
#     print("❌ Failed to copy Python files. If python was not changed, this can be ignored.")

# if not move_build_folder_success:
#     print("❌ Failed to move build folder, deleted build folder. (Not used in the installer)")
