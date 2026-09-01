# 🤖 Media Downloader Bot

YouTube va Instagram'dan video, audio va rasmlarni yuklovchi Telegram bot.  
**Limit yo'q** (2GB gacha), **to'liq playlist**, **kesh** tizimi.

---

## ⚡ Imkoniyatlar

| | YouTube | Instagram |
|--|---------|-----------|
| 🎬 Video | ✅ 4K/1080p/720p/480p/360p | ✅ |
| 🎵 Audio MP3 | ✅ 320/192/128 kbps | ✅ |
| 🖼️ Rasm | ❌ | ✅ Carousel ham |
| 📋 Playlist | ✅ **Cheksiz** | ❌ |
| 📦 Fayl limiti | ✅ **2 GB gacha** | ✅ |
| ⚡ Kesh | ✅ Qayta so'rov = darhol | ✅ |

---

## 🔧 O'rnatish (Lokal)

### 1. FFmpeg o'rnatish

**Windows:**  
[ffmpeg.org](https://ffmpeg.org/download.html) dan yuklab, `C:\ffmpeg\bin` ga joylang va PATH ga qo'shing.

**Linux/Mac:**
```bash
sudo apt install ffmpeg    # Ubuntu
brew install ffmpeg        # Mac
```

### 2. Python kutubxonalari

```bash
pip install -r requirements.txt
```

### 3. Telegram API kalitlarini olish

1. [my.telegram.org](https://my.telegram.org) ga kiring
2. **API Development Tools** → yangi app yarating
3. `api_id` va `api_hash` ni nusxalab oling

### 4. STRING_SESSION yaratish

```bash
python utils/session_gen.py
```

Telefon raqamingiz bilan kiring → sessiya satri chiqadi → `.env` ga qo'ying.

### 5. Yopiq kanal yaratish

1. Telegram'da yangi **private kanal** yarating
2. Botni **admin** qiling (fayl yuklash huquqi)
3. Kanal ID sini oling:
   - @username_to_id_bot ga kanaldan xabar forward qiling
   - Yoki kanalga `@RawDataBot` qo'shing
4. ID ni `.env` → `STORAGE_CHANNEL_ID` ga qo'ying (masalan: `-1001234567890`)

### 6. .env fayl

```bash
copy .env.example .env   # Windows
cp .env.example .env     # Linux/Mac
```

`.env` ni to'ldiring:
```env
BOT_TOKEN=1234567890:ABCdef...
API_ID=12345678
API_HASH=abcdef1234567890...
STRING_SESSION=BQA...uzun_matn...
STORAGE_CHANNEL_ID=-1001234567890
PLAYLIST_MAX_ITEMS=0
```

### 7. Botni ishga tushirish

```bash
python bot.py
```

---

## 🚂 Railway'ga Deploy

### 1. GitHub'ga push

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/USERNAME/media-bot.git
git push -u origin main
```

### 2. Railway sozlash

1. [railway.app](https://railway.app) → **New Project** → **GitHub repo**
2. Repozitoriyangizni tanlang
3. **Variables** bo'limiga quyidagilarni qo'ying:

| Variable | Qiymat |
|----------|--------|
| `BOT_TOKEN` | BotFather tokeni |
| `API_ID` | my.telegram.org |
| `API_HASH` | my.telegram.org |
| `STRING_SESSION` | session_gen.py dan |
| `STORAGE_CHANNEL_ID` | `-100...` |
| `WEBHOOK_SECRET` | `my-secret-token-12345` |
| `PLAYLIST_MAX_ITEMS` | `0` (cheksiz) |

> ✅ `RAILWAY_PUBLIC_DOMAIN` ni o'zingiz kiritmang — Railway o'zi beradi!

### 3. Deploy!

Railway avtomatik `nixpacks.toml` dan **FFmpeg** ni o'rnatadi va botni ishga tushiradi.

**Logs'da ko'rsangiz:**
```
🟢 Pyrogram ulandi: Ism (@username)
✅ SQLite kesh bazasi tayyor
🤖 Bot ishga tushdi (WEBHOOK): @YourBot
```
Bot tayyor! ✅

---

## 🏗️ Arxitektura

```
Foydalanuvchi URL yuboradi
         ↓
[aiogram] URL aniqlaydi (YT/IG)
         ↓
📋 SQLite kesh tekshiriladi
   ├── ✅ file_id bor → darhol yuboradi ⚡
   └── ❌ yo'q → yt-dlp yuklab oladi
                     ↓
             [Pyrogram] → Kanalga upload (2GB)
                     ↓
             file_id → SQLite ga saqlanadi
                     ↓
             Bot file_id orqali yuboradi
                     ↓
             Local fayl o'chiriladi 🗑️
```

---

## 📁 Loyiha tuzilmasi

```
MediaBot/
├── bot.py                  # Asosiy (Polling ↔ Webhook)
├── config.py               # Barcha sozlamalar
├── railway.json            # Railway konfiguratsiyasi
├── nixpacks.toml           # FFmpeg o'rnatish
├── .env.example            # Namuna sozlamalar
├── .gitignore
├── requirements.txt
├── handlers/
│   ├── start.py            # /start, /help
│   └── downloader.py       # URL + callback + playlist
├── services/
│   ├── detector.py         # URL turi aniqlash
│   ├── yt_service.py       # YouTube + Playlist
│   ├── ig_service.py       # Instagram
│   ├── uploader.py         # Pyrogram → kanal (2GB)
│   └── cache.py            # SQLite kesh
├── keyboards/
│   └── inline.py           # Sifat tanlash tugmalari
├── middlewares/
│   └── throttle.py         # Anti-spam
└── utils/
    ├── cleaner.py          # Temp fayllarni tozalash
    └── session_gen.py      # STRING_SESSION yaratish
```

---

## ❓ Tez-tez so'raladigan savollar

**Q: 50MB limitni qanday yengdik?**  
A: Pyrogram (user account) orqali fayllar private kanalga yuklanadi (2GB). Aiogram bot esa kanaldan `file_id` orqali foydalanuvchiga yuboradi.

**Q: Kesh nima uchun?**  
A: Bir marta yuklangan fayl SQLite'da `file_id` bilan saqlanadi. Keyingi so'rovda qayta yuklanmaydi — darhol yuboriladi.

**Q: Baza kerakmi?**  
A: Faqat SQLite (fayl ko'rinishida, server shart emas). Railway'da ham ishlaydi.

**Q: Playlist nechta video yuboradi?**  
A: `.env` da `PLAYLIST_MAX_ITEMS=0` bo'lsa — **cheksiz**. `10` qo'ysangiz — faqat birinchi 10 ta.
