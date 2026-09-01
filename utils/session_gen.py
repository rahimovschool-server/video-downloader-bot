"""
Bu skript STRING_SESSION yaratish uchun.
Faqat BIR MARTA ishga tushuriladi, keyin .env ga qo'yiladi.

Ishlatish:
    python utils/session_gen.py

Kerak bo'lgan narsalar:
    - API_ID va API_HASH (https://my.telegram.org dan)
    - Telegram hisobingizning telefon raqami
"""
import asyncio
from hydrogram import Client


async def main():
    print("=" * 50)
    print("  📱 STRING_SESSION yaratish")
    print("=" * 50)
    print()
    print("🔗 https://my.telegram.org saytiga kiring:")
    print("   1. Telefon raqamingiz bilan kiring")
    print("   2. 'API Development Tools' ga o'ting")
    print("   3. App yarating (nom va platform ahamiyatsiz)")
    print("   4. api_id va api_hash ni nusxalab oling")
    print()

    api_id  = int(input("API_ID → ").strip())
    api_hash = input("API_HASH → ").strip()

    print()
    print("📲 Telegram hisobingizga ulanilmoqda...")
    print("   (SMS yoki Telegram app orqali kod keladi)")
    print()

    async with Client(
        name="session_generator",
        api_id=api_id,
        api_hash=api_hash,
        in_memory=True,
    ) as app:
        session_string = await app.export_session_string()
        me = await app.get_me()

    print()
    print("=" * 50)
    print(f"✅ Muvaffaqiyatli! Hisob: {me.first_name} ({me.phone_number})")
    print()
    print("📋 STRING_SESSION (quyidagini .env ga qo'ying):")
    print()
    print(f"STRING_SESSION={session_string}")
    print()
    print("=" * 50)
    print()
    print("⚠️  MUHIM:")
    print("   - Bu sessiyani hech kimga bermang!")
    print("   - .gitignore ga .env qo'shilgan — xavfsiz")
    print("   - Railway'da Variables bo'limiga qo'ying")


if __name__ == "__main__":
    asyncio.run(main())
