import subprocess
import sys
import os

def main():
    print("Starting React server...")
    os.chdir('Frontend-ts')
    if sys.platform == 'win32':
        subprocess.run(['npm', 'run', 'dev'], shell=True, check=True)
    else:
        subprocess.run(['npm', 'run', 'dev'], check=True)

if __name__ == "__main__":
    main() 