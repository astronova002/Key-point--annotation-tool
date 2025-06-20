import subprocess
import sys
import os

def main():
    print("Starting both servers in separate terminals...")
    
    # Get the absolute path to the Python executable
    python_exe = sys.executable.replace('\\', '/')
    
    # Get the absolute path to the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__)).replace('\\', '/')
    
    # Create commands for both servers with proper path formatting
    django_script = os.path.join(current_dir, "run_django.py").replace('\\', '/')
    react_script = os.path.join(current_dir, "run_react.py").replace('\\', '/')
    
    # Print paths for debugging
    print(f"Python executable: {python_exe}")
    print(f"Django script: {django_script}")
    print(f"React script: {react_script}")
    
    try:
        # Use PowerShell instead of cmd for better path handling
        django_cmd = f'powershell -Command "Start-Process powershell -ArgumentList \'-NoExit\', \'-Command\', \'cd {current_dir}; {python_exe} {django_script}\'"'
        react_cmd = f'powershell -Command "Start-Process powershell -ArgumentList \'-NoExit\', \'-Command\', \'cd {current_dir}; {python_exe} {react_script}\'"'
        
        # Run both commands
        subprocess.run(django_cmd, shell=True, check=True)
        subprocess.run(react_cmd, shell=True, check=True)
        
        print("\nBoth servers have been started in separate terminals.")
        print("You can close the servers by closing their respective terminal windows.")
    except subprocess.CalledProcessError as e:
        print(f"\nError starting servers: {e}")
        print("Please make sure all paths are correct and you have necessary permissions.")
    except Exception as e:
        print(f"\nUnexpected error: {e}")

if __name__ == "__main__":
    main()
