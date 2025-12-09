# YouTube Video Downloader

YouTube videolarini yuklash uchun desktop ilova. Python va Flet yordamida yaratilgan.

## 🚀 Tez Ishga Tushirish

Faqat bitta komanda kerak:

```bash
python3 run.py
```

Bu komanda grafik oyna ochadi va quyidagilarni ko'rsatadi:
- ✅ Barcha kerakli komponentlarni tekshiradi (check mark bilan)
- ✅ Agar biror narsa yo'q bo'lsa, "Install qilish" tugmasi paydo bo'ladi
- ✅ Hamma narsa tayyor bo'lganda "Boshlash" tugmasi ko'rsatiladi
- ✅ "Boshlash" bosganda versiya tanlash oynasi ochiladi
- ✅ MVP yoki Advanced versiyani tanlaysiz va ilova ishga tushadi

## Foydalanish

### MVP versiya (oddiy yuklash)

**Funksiyalar:**
- YouTube URL kiriting
- "Start Download" tugmasini bosing
- Video avtomatik eng yaxshi sifatda yuklanadi
- Progress foizi ko'rsatiladi
- Fayllar `~/Downloads` papkasiga saqlanadi
- "Show File" tugmasi bilan faylni Finder'da ochish

### Advanced versiya (sifat tanlash)

**Funksiyalar:**
- YouTube URL kiriting
- "Formatlarni ko'rish" tugmasini bosing
- Video haqida ma'lumot ko'ring (nom, davomiylik)
- Kerakli sifatni tanlang (masalan: 1080p - 34.5MB)
- "Start Download" tugmasini bosing
- Progress foizi ko'rsatiladi
- "Show File" tugmasi bilan faylni Finder'da ochish

## Xususiyatlar

✅ **Avtomatik o'rnatish** - Barcha kerakli komponentlar avtomatik o'rnatiladi
✅ **Sodda interfeys** - Foydalanish oson va tushunarli
✅ **Progress monitoring** - Yuklanish foizi va hajmi ko'rsatiladi
✅ **Sifat tanlash** - Turli sifatlarni tanlash (720p, 1080p, va h.k.)
✅ **Fayl hajmi** - Har bir sifat uchun fayl hajmi ko'rsatiladi
✅ **QuickTime moslik** - Video QuickTime'da ishlaydi
✅ **Finder integratsiya** - "Show File" tugmasi bilan faylni topish
✅ **Uzbek tili** - To'liq uzbek tilida interfeys

## Texnologiyalar

- **Python 3.7+**
- **Flet** - Desktop UI framework
- **yt-dlp** - YouTube video yuklash kutubxonasi
- **FFmpeg** - Video qayta ishlash

## Qo'lda O'rnatish (Agar avtomatik ishlamasa)

### Python kutubxonalari:
```bash
pip install -r requirements.txt
```

### FFmpeg (agar avtomatik o'rnatilmagan bo'lsa):

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**Windows:**
1. https://ffmpeg.org/download.html dan yuklab oling
2. FFmpeg'ni PATH ga qo'shing

## Boshqa Ishga Tushirish Usullari

### GUI Launcher (Tavsiya etiladi):
```bash
python3 launcher.py
```

### To'g'ridan-to'g'ri versiyani ishga tushirish:
```bash
# MVP versiya
python3 youtube_downloader_mvp.py

# Advanced versiya
python3 youtube_downloader_advanced.py
```

### Console setup:
```bash
python3 setup.py
```

## Muammolar

Agar muammolar yuzaga kelsa:
1. FFmpeg o'rnatilganligini tekshiring: `ffmpeg -version`
2. Python 3.7+ o'rnatilganligini tekshiring: `python3 --version`
3. Internet aloqasi barqaror ekanligini tekshiring
4. `python3 setup.py` komandasi bilan qayta o'rnatib ko'ring
