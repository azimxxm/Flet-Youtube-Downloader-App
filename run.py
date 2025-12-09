#!/usr/bin/env python3
"""
YouTube Downloader Launcher
Simple launcher that starts the GUI setup window
"""
import subprocess
import sys


def main():
    """Launch the GUI launcher"""
    try:
        subprocess.run([sys.executable, 'launcher.py'])
    except KeyboardInterrupt:
        print("\n\n👋 Dastur to'xtatildi")
    except FileNotFoundError:
        print("❌ launcher.py topilmadi")
        print("   Iltimos, dastur papkasida ekanligingizni tekshiring")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Xatolik: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
