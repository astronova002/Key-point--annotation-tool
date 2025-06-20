import subprocess
import sys
import os

def main():
    print("Starting Django server...")
    os.chdir('backend')
    subprocess.run([sys.executable, 'manage.py', 'runserver'], check=True)

if __name__ == "__main__":
    main() 