"""
Простое Python-приложение для демонстрации работы с Docker Images.
"""
import os
import platform
import sys

APP_VERSION = os.environ.get("APP_VERSION", "v1")

def main():
    print("=" * 50)
    print("  Docker Images Practice — Python App")
    print("=" * 50)
    print(f"App version:    {APP_VERSION}")
    print(f"Python:        {sys.version.split()[0]}")
    print(f"Platform:      {platform.system()} {platform.machine()}")
    print(f"Hostname:      {platform.node()}")
    print("=" * 50)
    print("Hello from Docker container!")
    print("This image was built and tagged as part of the practice.")
    print("=" * 50)

if __name__ == "__main__":
    main()
