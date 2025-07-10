try:
    import os
    import subprocess
    import argparse
    import json
    import datetime
    import sys
    import traceback
    import platform

    import re
    import time
    import pathlib

except ImportError as e:
    print(f"❌ Import error: {e}")
    input("Press Enter to close...")
    sys.exit(1)

def run_subprocess_with_logging(cmd):
    """Run subprocess and capture all output to log file with real-time streaming"""
    if isinstance(cmd, str):
        cmd = [cmd]

    print("-" * 40)
    print(f"🔧 Running command: {' '.join(cmd)}")
    print(f"   Working Directory: {os.getcwd()}")
    print(f"   Timestamp: {datetime.datetime.now().strftime('%H:%M:%S')}")
    print("📤 Command output (streaming):")
    
    max_tries = 3
    tries_remaining = max_tries
    
    while tries_remaining > 0:
        try:
            if tries_remaining < max_tries:
                print(f"🔄 Retrying command (attempt {max_tries - tries_remaining + 1} of {max_tries})...")
            
            start_time = datetime.datetime.now()
            
            # Start the process with pipes for real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr into stdout for unified output
                text=True,
                encoding='utf-8',
                errors='replace',
                bufsize=1,
                universal_newlines=True
            )
            
            # Stream output in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    # Print to console (and thus to log via Tee)
                    print(output.rstrip())
                    output_lines.append(output)
            
            # Wait for process to complete and get return code
            return_code = process.poll()
            
            end_time = datetime.datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            if return_code == 0:
                print(f"   ✅ Command completed successfully in {duration:.2f} seconds")
                print("-" * 40)
                return  # Success, exit the retry loop
            else:
                print(f"❌ Command failed with return code {return_code} after {duration:.2f} seconds")
                tries_remaining -= 1
                
                if tries_remaining > 0:
                    print(f"⏳ {tries_remaining} tries remaining. Waiting 5 seconds before retry...")
                    time.sleep(5)
                else:
                    print(f"❌ All {max_tries} attempts failed")
                    raise subprocess.CalledProcessError(return_code, cmd, output=''.join(output_lines))
            
        except subprocess.CalledProcessError as e:
            if tries_remaining <= 1:
                print(f"❌ Command failed with return code {e.returncode} after all retries")
                print("-" * 40)
                raise e
            else:
                tries_remaining -= 1
                print(f"❌ Command failed with return code {e.returncode}")
                print(f"⏳ {tries_remaining} tries remaining. Waiting 5 seconds before retry...")
                time.sleep(5)
                
        except Exception as e:
            if tries_remaining <= 1:
                print(f"❌ Error running subprocess: {e}")
                print("-" * 40)
                raise e
            else:
                tries_remaining -= 1
                print(f"❌ Error running subprocess: {e}")
                print(f"⏳ {tries_remaining} tries remaining. Waiting 5 seconds before retry...")
                time.sleep(5)

class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            try:
                if isinstance(obj, bytes):
                    obj = obj.decode('utf-8', errors='replace')
                f.write(obj)
                f.flush()
            except (UnicodeEncodeError, ValueError):
                if f != sys.__stdout__ and f != sys.__stderr__:
                    try:
                        sys.__stdout__.write(obj)
                        sys.__stdout__.flush()
                    except:
                        pass
    def flush(self):
        for f in self.files:
            try:
                f.flush()
            except (ValueError, AttributeError):
                pass
        
def get_install_params(executable_dir):
    command_file = os.path.join(executable_dir, "installation_command.txt")
    print(f"📝 Loading values from command file: {command_file}")
    
    try:
        with open(command_file, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Extract the command line from the file content
        # Look for the line that contains the actual command with flags
        command_line = ""
        for line in content.split('\n'):
            if '--target' in line and 'Cell-ACDC-installer.exe' in line:
                command_line = line.strip()
                break
        
        if command_line:
            print(f"📋 Found command: {command_line}")
            
            # Extract all parameters using a single regex with multiple capture groups
            pattern = (r'--target\s+"([^"]+)".*?'
                    r'--use_github\s+"([^"]+)".*?'
                    r'--version\s+"([^"]+)".*?'
                    r'--python_path\s+"([^"]+)".*?'
                    r'--embeddedpyflag\s+"([^"]+)".*?'
                    r'--pyversion\s+(\S+).*?'
                    r'--custom_CellACDC_path\s+"([^"]+)"')

            match = re.search(pattern, command_line)
            if match:
                target_dir = match.group(1)
                use_github = match.group(2).lower() == 'true'
                cellacdc_version = match.group(3)
                python_path = match.group(4)
                is_embedded_python = match.group(5).lower() == 'true'
                pyversion = match.group(6)
                custom_CellACDC_path = match.group(7)
                
                print(f"   Target: {target_dir}")
                print(f"   Use GitHub: {use_github}")
                print(f"   Version: {cellacdc_version}")
                print(f"   Python Path: {python_path}")
                print(f"   Embedded Python: {is_embedded_python}")
                print(f"   Python Version: {pyversion}")
                print(f"   Custom CellACDC Path: {custom_CellACDC_path}")
            else:
                print("⚠️ Unable to parse all required parameters from the command line in installation_command.txt.")
                print("   Please ensure the file contains all required flags:")
                print("   --target, --use_github, --version, --python_path, --embeddedpyflag, --pyversion, --custom_CellACDC_path")
                raise ValueError("Failed to extract installation parameters from command. Please check installation_command.txt for completeness and correct formatting.")
            
            print("✅ Successfully loaded installation parameters from command file")
        else:
            print("⚠️ Could not find a valid command line in installation_command.txt.")
            print("   Please ensure the file contains a line with all required flags:")
            print("   --target, --use_github, --version, --python_path, --embeddedpyflag, --pyversion, --custom_CellACDC_path")
            raise ValueError(
                "Could not load installation parameters from command file. Please check installation_command.txt."
            )                
    except FileNotFoundError as e:
        print(f"⚠️ installation_command.txt not found at: {command_file}")
        print("   Please run the installer with all required flags or ensure installation_command.txt exists in the executable directory.")
        raise e

    except Exception as e:
        print(f"⚠️ Error reading installation_command.txt: {e}")
        print("   Please check the file for correct formatting and required flags.")
        raise e
    
    return target_dir, use_github, cellacdc_version, python_path, is_embedded_python, pyversion, custom_CellACDC_path

def setup_logging():
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}_cellacdc_install.log"
    user_home_path = str(pathlib.Path.home())
    user_profile_path = os.path.join(user_home_path, 'acdc-appdata')
    log_path = os.path.join(user_profile_path, ".acdc-logs", log_filename)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    # Open log file with UTF-8 encoding
    log_file = open(log_path, 'w', encoding='utf-8', errors='replace')
    
    # Store original stdout/stderr
    original_stdout = sys.stdout
    original_stderr = sys.stderr
    
    # Redirect stdout and stderr to both console and log file
    sys.stdout = Tee(original_stdout, log_file)
    sys.stderr = Tee(original_stderr, log_file)

    # Log session header with system information
    print("=" * 80)
    print(f"Cell-ACDC Installation Session - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"System Information:")
    print(f"  Platform: {platform.platform()}")
    print(f"  Python Version: {sys.version}")
    print(f"  Working Directory: {os.getcwd()}")
    print(f"  Log File: {log_path}")
    print("=" * 80)
    print()

    print(f"📄 Installation log will be saved to: {log_path}")
    return log_file, original_stdout, original_stderr, log_path

def print_closing_logging(log_path):
    """Print closing message for logging"""
    print()
    print("=" * 80)
    print("Logging session ended.")
    print(f"📄 Installation log can be found at: {log_path}")
    print("=" * 80)

    print("INSTALLATION SUMMARY")
    print("=" * 80)
    print(f"Target Directory: {target_dir}")
    print(f"Python Path: {python_path}")
    print(f"Virtual Environment: {venv_path if not is_conda else conda_venv_path}")
    print(f"Using Conda: {is_conda}")
    print(f"Installation Source: {'GitHub' if use_github else 'PyPI'}")
    if not use_github:
        print(f"Version: {cellacdc_version}")
    print(f"Session End: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    print("✅ Installation completed successfully!")

if __name__ == "__main__":
    try:
        # Set up logging at the beginning of your script
        log_file, original_stdout, original_stderr, log_path = setup_logging()

        repo_url = "https://github.com/SchmollerLab/Cell_ACDC"
        clone_path = "Cell_ACDC"
        git_path = "portable_git" # only for windows where git is not installed
        git_path = os.path.join(git_path, "cmd", "git.exe")

        parser = argparse.ArgumentParser()
        parser.add_argument('--target', help='Target install path')
        parser.add_argument('--use_github', help='Use GitHub clone (true/false)')
        parser.add_argument('--version', help='CellACDC version to install from PyPI')
        parser.add_argument('--python_path', help='Path to already installed Python')
        parser.add_argument('--embeddedpyflag', help='Path to Python installer executable (if applicable)')
        parser.add_argument('--pyversion',  help='Python version to use for conda environment')
        parser.add_argument('--custom_CellACDC_path', help='Custom path to CellACDC repository clone (if applicable)')

        args = parser.parse_args()
        target_dir = args.target if args.target else None
        use_github = args.use_github.lower() == 'true' if args.use_github else None
        cellacdc_version = args.version if args.version else None
        is_embedded_python = args.embeddedpyflag if args.embeddedpyflag else None
        python_path = args.python_path if args.python_path else None
        pyversion = args.pyversion if args.pyversion else None
        custom_CellACDC_path = args.custom_CellACDC_path if args.custom_CellACDC_path else None

        # Check if any main install flags are provided
        install_flags = [
            ('target', target_dir),
            ('use_github', use_github),
            ('version', cellacdc_version),
            ('python_path', python_path),
            ('pyversion', pyversion),
            ('embeddedpyflag', is_embedded_python),
            ('custom_CellACDC_path', custom_CellACDC_path)
        ]
        
        # Get list of provided and missing flags
        provided_flags = [name for name, value in install_flags if value is not None]
        missing_flags = [name for name, value in install_flags if value is None]
        
        # If any main install flags are provided, all must be provided
        if provided_flags and missing_flags:
            error_msg = (
                f"❌ Invalid argument combination: If any main install flags are provided, "
                f"all must be provided.\n"
                f"   Provided flags: {', '.join(['--' + flag for flag in provided_flags])}\n"
                f"   Missing flags: {', '.join(['--' + flag for flag in missing_flags])}\n"
                f"   Either provide all flags for automated installation, or provide none for interactive mode."
            )
            print(error_msg)
            raise ValueError(error_msg)
        
        # Determine and announce the installation mode
        flag_mode = all(value is not None for _, value in install_flags)

        # Get the executable path for PyInstaller
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            executable_path = sys.executable
            executable_dir = os.path.dirname(sys.executable)
            print(f"📦 Running from PyInstaller executable: {executable_path}")
        else:
            # Running as Python script
            executable_path = os.path.abspath(__file__)
            executable_dir = os.path.dirname(executable_path)
            print(f"🐍 Running as Python script: {executable_path}")
        
        if not flag_mode:
            target_dir, use_github, cellacdc_version, python_path, is_embedded_python, pyversion, custom_CellACDC_path = get_install_params(executable_dir)

        if python_path:
            python_path = os.path.abspath(python_path) # Ensure absolute path, and format correctly for Windows

        if custom_CellACDC_path.lower() == "default":
            custom_CellACDC_path = None
        
        if isinstance(custom_CellACDC_path, str):
            custom_CellACDC_path = custom_CellACDC_path.strip('"').strip("'").strip()  # Clean up quotes if present
        
        use_whl = False
        use_custom_CellACDC = False
        if custom_CellACDC_path:
            use_whl = custom_CellACDC_path.endswith('.whl')
            custom_CellACDC_path = os.path.abspath(custom_CellACDC_path)  # Ensure absolute path for custom path
            use_custom_CellACDC = True if not use_whl else False
            
        operating_system = platform.system().lower()
        is_windows = operating_system == "windows"

        clone_path = os.path.join(target_dir, clone_path)

        # Log all command line arguments for debugging
        if flag_mode:
            print("Command Line Arguments:")
            for arg, value in vars(args).items():
                print(f"  --{arg}: {value}")
            print()

        if use_github:
            if os.path.exists(clone_path):
                print(f"⚠️ CellACDC repository already exists at {clone_path}. Skipping clone.")
            else:
                print(f"📥 Cloning CellACDC repository from {repo_url} to {clone_path} (This may take a while)...")
                print(f"   Target directory: {clone_path}")
                try:
                    # Use porcelain.clone with explicit configuration to avoid interactive prompts
                    if is_windows:
                        git_prefix = os.path.abspath(os.path.join(target_dir, git_path))
                    else:
                        git_prefix = "git"
                    
                    cmd = [git_prefix, "clone", repo_url, clone_path]
                    run_subprocess_with_logging(cmd)
                    cmd = ["git", "config", "--global", "--add", 
                           "safe.directory", clone_path]
                    run_subprocess_with_logging(cmd)
                    
                    # Add a small delay to ensure file system operations are complete
                    print("   Waiting for file system operations to complete...")
                    time.sleep(2)
                    
                except Exception as e:
                    print(f"❌ Git clone failed: {e}")
                    raise
        
        if use_custom_CellACDC or use_github:
            clone_path = custom_CellACDC_path if custom_CellACDC_path else clone_path
            print(f"📂 Using CellACDC at: {clone_path}")
                    
            # Verify the clone path contains a valid Python package with retry logic
            print(f"🔍 Verifying package structure at: {clone_path}")
            max_retries = 5
            retry_count = 0
            
            while retry_count < max_retries:
                if os.path.exists(clone_path):
                    print(f"   Directory exists: {clone_path}")
                    try:
                        files_in_dir = os.listdir(clone_path)
                        print(f"   Contents: {files_in_dir}")
                        
                        # Check for setup.py or pyproject.toml
                        setup_py = os.path.join(clone_path, "setup.py")
                        pyproject_toml = os.path.join(clone_path, "pyproject.toml")
                        
                        if os.path.exists(pyproject_toml):
                            print(f"   ✅ Found pyproject.toml")
                            break
                        else:
                            print(f"   ⚠️ No pyproject.toml found on attempt {retry_count + 1}")
                            if retry_count < max_retries - 1:
                                print(f"   Waiting 2 seconds before retry...")
                                time.sleep(2)
                                retry_count += 1
                                continue
                            else:
                                print(f"   Available files: {[f for f in files_in_dir if f.endswith(('.py', '.toml', '.cfg'))]}")
                                break
                    except Exception as e:
                        print(f"   ⚠️ Error accessing directory on attempt {retry_count + 1}: {e}")
                        if retry_count < max_retries - 1:
                            print(f"   Waiting 2 seconds before retry...")
                            time.sleep(2)
                            retry_count += 1
                            continue
                        else:
                            raise
                else:
                    print(f"   ❌ Clone path does not exist on attempt {retry_count + 1}: {clone_path}")
                    if retry_count < max_retries - 1:
                        print(f"   Waiting 2 seconds before retry...")
                        time.sleep(2)
                        retry_count += 1
                        continue
                    else:
                        raise FileNotFoundError(f"Clone path not found after {max_retries} attempts: {clone_path}")

        elif use_whl:
            clone_path = os.path.abspath(custom_CellACDC_path)  # Ensure absolute path for pip install

        if isinstance(is_embedded_python, str):
            if is_embedded_python.lower() == 'true':
                is_embedded_python = True
        if is_embedded_python is True:
            # Cross-platform Python executable path
            python_exe = "python.exe" if is_windows else "python"
            python_path = os.path.join(target_dir, "miniforge", python_exe)

        is_conda = python_path.lower().find("miniforge") != -1 or python_path.lower().find("conda") != -1
        if is_conda:
            folder = os.path.dirname(python_path)
            # Cross-platform conda executable path
            if is_windows:
                conda_path = os.path.join(folder, "Scripts", "conda.exe")
            else:
                conda_path = os.path.join(folder, "bin", "conda")
            conda_path = os.path.abspath(conda_path)  # Ensure absolute path for conda
        #     conda_path = f'"{conda_path}"'  # Ensure proper quoting for Windows paths
        # python_path = f'"{python_path}"'  # Ensure proper quoting for Windows paths'
        
        if not is_conda:
            venv_path = os.path.join(target_dir, "venv")
            venv_path = os.path.abspath(venv_path)  # Ensure absolute path for venv
            print(f"🌱 Creating venv at: {venv_path}")
            print(f"Using Python at: {python_path}")
            run_subprocess_with_logging([python_path, "-m", "venv", venv_path])
            print("✅ venv created.")

            # Cross-platform pip executable path
            if is_windows:
                pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
            else:
                pip_path = os.path.join(venv_path, "bin", "pip")
            
            if use_github or custom_CellACDC_path:
                print("🛠️ Installing CellACDC and dependencies...")
                print(f"   Using Cell-ACDC path: {clone_path}")
                clone_path = os.path.abspath(clone_path)  # Ensure absolute path for pip install
                print(f"   Absolute path: {clone_path}")
                
                # Install in editable mode from local clone
                cmd = [pip_path, "install", clone_path]
                if not use_whl:
                    cmd.insert(-1, "-e")
                run_subprocess_with_logging(cmd)
            else:
                print(f"🛠️ Downloading and installing CellACDC v{cellacdc_version} and dependencies...")
                
                # Install specific version from PyPI
                run_subprocess_with_logging([
                    pip_path, "install", f"cellacdc=={cellacdc_version}"
                ])
            
            print("✅ Pip installation completed.")
        
        elif is_conda:
            conda_venv_path = os.path.join(target_dir, "conda_venv")
            conda_venv_path = os.path.abspath(conda_venv_path)  # Ensure absolute path for conda venv
            print(f"🌱 Creating conda venv: {conda_venv_path}")
            print(f"Using conda/miniforge Python at: {python_path}")

            # Create conda environment with Python
            run_subprocess_with_logging([
                conda_path,
                "create", "-y",
                "-p", conda_venv_path,
                f"python={pyversion}"
            ])
            
            print("✅ Conda environment created.")

            if use_github or custom_CellACDC_path:
                print("🛠️ Installing CellACDC and dependencies...")
                print(f"   Using Cell-ACDC path: {clone_path}")
                clone_path = os.path.abspath(clone_path)  # Ensure absolute path for pip install
                print(f"   Absolute path: {clone_path}")
                
                # Install in editable mode from local clone
                cmd = [
                    conda_path,
                    "run", "-p", conda_venv_path,
                    "pip", "install", clone_path
                ]
                if not use_whl:
                    cmd.insert(-1, "-e")

                run_subprocess_with_logging(cmd)
            else:
                print(f"🛠️ Downloading and installing CellACDC v{cellacdc_version} and dependencies...")
                
                # Install specific version from PyPI
                run_subprocess_with_logging([
                    conda_path,
                    "run", "-p", conda_venv_path,
                    "pip", "install", f"cellacdc=={cellacdc_version}"
                ])
            
            print("✅ Conda pip installation completed.")

        print("🛠️ Launching CellACDC for internal setup...")

        # Cross-platform ACDC executable paths
        if not is_conda:
            if is_windows:
                acdc_exec_path = os.path.join(venv_path, "Scripts", "acdc.exe")
            else:
                acdc_exec_path = os.path.join(venv_path, "bin", "acdc")
            subprocess.run([acdc_exec_path, "-y",
                                        "--install_details", 
                                        os.path.join(target_dir, 
                                        "install_details.json")])

        else:
            if is_windows:
                acdc_exec_path = os.path.join(conda_venv_path, "Scripts", "acdc.exe")
            else:
                acdc_exec_path = os.path.join(conda_venv_path, "bin", "acdc")
            subprocess.run([acdc_exec_path, "-y",
                                        "--install_details", 
                                        os.path.join(target_dir, 
                                        "install_details.json")])

        print("✅ CellACDC internal setup completed.")

        print("📦 Saving installation details...")
        install_details = {
            "target_dir": target_dir,
            "venv_path": venv_path if not is_conda else conda_venv_path,
            "conda": is_conda,
            "clone_path": clone_path if use_github else "",
            "use_github": use_github,
            "version": cellacdc_version,
            "conda_path": conda_path if is_conda else "",
        }
        with open(os.path.join(target_dir, "install_details.json"), "w") as f:
            json.dump(install_details, f, indent=4)

        print("✅ Installation details saved to install_details.json.")

        # Log final session summary

        print_closing_logging(log_path)
    except Exception as e:
        # Restore original stdout/stderr for error handling
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        print()
        print("=" * 80)
        print("INSTALLATION ERROR")
        print("=" * 80)
        print("❌ An error occurred during installation.")
        print(f"Error: {str(e)}")
        print(f"Error Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        traceback.print_exc()
        
        # Save error to log file
        try:
            with open(log_path, 'a', encoding='utf-8', errors='replace') as f:
                f.write(f"\n\n{'='*80}\n")
                f.write(f"INSTALLATION ERROR - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n")
                f.write(f"❌ ERROR: {str(e)}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
                f.write(f"{'='*80}\n")
            print(f"📄 Full installation log saved to: {log_path}")
            print("=" * 80)
        except:
            print("⚠️ Could not save error log.")
        
        print("Log files are saved in the following directory:")
        print(f"📂 {os.path.dirname(log_path)}")
        print("Please copy the two newest log files, and report this issue to the CellACDC team at:")
        print(repo_url)
        input("❌!!!CELL-ACDC SETUP IS IN ERROR STATE!!!❌ Press Enter to close this window...")
        
    finally:
        # Safely close log file and restore stdout/stderr
        try:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            if 'log_file' in locals() and not log_file.closed:
                log_file.close()
        except:
            pass