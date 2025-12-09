import subprocess
import sys
import os
import platform


def check_python():
    """Check Python version"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 yoki yuqori versiya kerak")
        sys.exit(1)
    print("✅ Python versiyasi: OK")


def install_pip_packages():
    """Install required Python packages"""
    print("\n📦 Python kutubxonalari tekshirilmoqda...")

    required_packages = ['flet', 'yt-dlp', 'ffmpeg-python']

    try:
        import flet
        import yt_dlp
        import ffmpeg
        print("✅ Barcha Python kutubxonalari o'rnatilgan")
        return True
    except ImportError:
        print("⚙️  Python kutubxonalari o'rnatilmoqda...")
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', '--quiet',
                'flet>=0.23.0', 'yt-dlp>=2024.0.0', 'ffmpeg-python>=0.2.0'
            ])
            print("✅ Python kutubxonalari muvaffaqiyatli o'rnatildi")
            return True
        except subprocess.CalledProcessError:
            print("❌ Python kutubxonalarini o'rnatishda xatolik")
            return False


def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("\n🎬 FFmpeg tekshirilmoqda...")

    try:
        result = subprocess.run(['ffmpeg', '-version'],
                              capture_output=True,
                              text=True,
                              timeout=5)
        if result.returncode == 0:
            print("✅ FFmpeg o'rnatilgan")
            return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        pass

    print("⚠️  FFmpeg topilmadi. O'rnatilmoqda...")
    return install_ffmpeg()


def install_ffmpeg():
    """Install FFmpeg based on OS"""
    system = platform.system()

    try:
        if system == "Darwin":  # macOS
            print("   Homebrew orqali FFmpeg o'rnatilmoqda...")

            # Check if Homebrew is installed
            try:
                subprocess.run(['brew', '--version'],
                             capture_output=True,
                             check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("❌ Homebrew o'rnatilmagan.")
                print("   Iltimos, quyidagi komandani terminal'da ishga tushiring:")
                print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
                print("\n   Yoki FFmpeg'ni qo'lda o'rnating: https://ffmpeg.org/download.html")
                return False

            subprocess.check_call(['brew', 'install', 'ffmpeg'],
                                stdout=subprocess.DEVNULL)
            print("✅ FFmpeg muvaffaqiyatli o'rnatildi")
            return True

        elif system == "Linux":
            print("   apt orqali FFmpeg o'rnatilmoqda...")
            subprocess.check_call(['sudo', 'apt-get', 'update', '-qq'])
            subprocess.check_call(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'],
                                stdout=subprocess.DEVNULL)
            print("✅ FFmpeg muvaffaqiyatli o'rnatildi")
            return True

        else:  # Windows
            print("❌ Windows uchun avtomatik o'rnatish qo'llab-quvvatlanmaydi")
            print("   Iltimos, FFmpeg'ni qo'lda o'rnating:")
            print("   1. https://ffmpeg.org/download.html dan yuklab oling")
            print("   2. FFmpeg'ni PATH ga qo'shing")
            return False

    except subprocess.CalledProcessError:
        print("❌ FFmpeg'ni o'rnatishda xatolik")
        print("   Iltimos, qo'lda o'rnating: https://ffmpeg.org/download.html")
        return False


def main():
    print("=" * 60)
    print("🚀 YouTube Downloader - Setup")
    print("=" * 60)

    check_python()

    if not install_pip_packages():
        print("\n❌ O'rnatish muvaffaqiyatsiz tugadi")
        sys.exit(1)

    ffmpeg_ok = check_ffmpeg()

    print("\n" + "=" * 60)
    if ffmpeg_ok:
        print("✅ Barcha komponentlar tayyor!")
    else:
        print("⚠️  Setup yakunlandi, lekin FFmpeg o'rnatilmadi")
        print("   Video QuickTime'da ishlamasligi mumkin")
    print("=" * 60)
    print("\n📖 Ilovani ishga tushirish uchun:")
    print("   python3 run.py")
    print()


if __name__ == "__main__":
    main()
