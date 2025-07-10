try:    
    import pathlib
    import os
    import subprocess
    import argparse
    import json
    import datetime
    import sys
    import traceback
    import platform
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Please ensure all required modules are installed.")
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
    
    try:
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
        else:
            print(f"❌ Command failed with return code {return_code} after {duration:.2f} seconds")
            raise subprocess.CalledProcessError(return_code, cmd, output=''.join(output_lines))
        
        print("-" * 40)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with return code {e.returncode}")
        print("-" * 40)
        raise e
    except Exception as e:
        print(f"❌ Error running subprocess: {e}")
        print("-" * 40)
        raise e

class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            try:
                # Ensure we're writing strings and handle encoding
                if isinstance(obj, bytes):
                    obj = obj.decode('utf-8', errors='replace')
                f.write(obj)
                f.flush()
            except (UnicodeEncodeError, ValueError):
                # Fallback for encoding issues - write to console only
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

def setup_logging():
    # Set up logging at the beginning of your script
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"{timestamp}_cellacdc_launch.log"
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
    print(f"Cell-ACDC Session - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print(f"System Information:")
    print(f"  Platform: {platform.platform()}")
    print(f"  Python Version: {sys.version}")
    print(f"  Working Directory: {os.getcwd()}")
    print(f"  Log File: {log_path}")
    print("=" * 80)
    print()

    print(f"📄 Launch log will be saved to: {log_path}")

    return log_file, original_stdout, original_stderr, log_path

def print_closing_logging(target_dir, install_configs):
        print()
        print("=" * 80)
        print("RUN SUMMARY")
        print("=" * 80)
        print(f"Target Directory: {target_dir}")
        print(f"Using install details from: {install_configs}")
        print(f"Session End: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

        print("✅ Run completed successfully!")

if __name__ == "__main__":
    try:
        # Set up logging at the beginning of your script
        log_file, original_stdout, original_stderr, log_path = setup_logging()
        start_time = datetime.datetime.now()

        parser = argparse.ArgumentParser()
        parser.add_argument('--target', help='Target install path')


        args = parser.parse_args()
        target_dir = args.target if args.target else os.getcwd()

        install_configs = os.path.join(target_dir, "install_details.json")
        if not os.path.exists(install_configs):
            raise FileNotFoundError(f"""Install details file not found: {install_configs},
                                    please either use the --target argument to specify the correct path,
                                    or ensure that the file exists in the current working directory.""")
        repo_url = "https://github.com/SchmollerLab/Cell_ACDC"

        with open(install_configs, 'r', encoding='utf-8', errors='replace') as f:
            install_details = json.load(f)
        venv_path = install_details.get("venv_path", "")
        venv_path =venv_path.strip('"')
        is_conda = install_details.get("conda", False)
        conda_path = install_details.get("conda_path", "")
        conda_path = conda_path.strip('"')
        
        print("🚀 Launching CellACDC...")

        is_windows = platform.system().lower() == "windows"

        # Open PowerShell in the same terminal
        if not is_conda:
            if is_windows:
                acdc_exec_path = os.path.join(venv_path, "Scripts", "acdc.exe")
            else:
                acdc_exec_path = os.path.join(venv_path, "bin", "acdc")
            subprocess.run([acdc_exec_path,
                                        "--install_details", os.path.join(target_dir, "install_details.json")])

        else:
            if is_windows:
                acdc_exec_path = os.path.join(venv_path, "Scripts", "acdc.exe")
            else:
                acdc_exec_path = os.path.join(venv_path, "bin", "acdc")
            subprocess.run([acdc_exec_path,
                                        "--install_details", os.path.join(target_dir, "install_details.json")])

        elapsed_time = datetime.datetime.now() - start_time
        print(f"Thanks for using CellACDC, you spend {elapsed_time.total_seconds():.2f} seconds on this session!")

        # Log final session summary
        print_closing_logging(target_dir, install_configs)

    except Exception as e:
        # Restore original stdout/stderr for error handling
        sys.stdout = original_stdout
        sys.stderr = original_stderr
        
        print()
        print("=" * 80)
        print("ERROR")
        print("=" * 80)
        print("❌ An error occurred.")
        print(f"Error: {str(e)}")
        print(f"Error Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        traceback.print_exc()
        
        # Save error to log file
        try:
            with open(log_path, 'a', encoding='utf-8', errors='replace') as f:
                f.write(f"\n\n{'='*80}\n")
                f.write(f"ERROR - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"{'='*80}\n")
                f.write(f"❌ ERROR: {str(e)}\n")
                f.write(f"Traceback:\n{traceback.format_exc()}\n")
                f.write(f"{'='*80}\n")
            print(f"📄 Full log saved to: {log_path}")
            print("=" * 80)
        except:
            print("⚠️ Could not save error log.")
        
        print("Log files are saved in the following directory:")
        print(os.path.dirname(log_path))
        print("Please copy the two newest log files, and report this issue to the CellACDC team at:")
        print(repo_url)
        input("❌!!!CELL-ACDC IS IN ERROR STATE!!!❌ Press Enter to close this window...")
        
    finally:
        # Safely close log file and restore stdout/stderr
        try:
            sys.stdout = original_stdout
            sys.stderr = original_stderr
            if 'log_file' in locals() and not log_file.closed:
                log_file.close()
        except:
            pass