# GitHub Profile Checker Bot

Bot Telegram untuk cek status akun GitHub (aktif, suspend, badge PRO, dll) secara satuan atau bulk.  
Mendukung fitur admin untuk upgrade user ke premium.

## Fitur
- `/check <username>` — Cek satu akun GitHub
- `/bulkcheck` — Cek banyak username sekaligus (kirim daftar username, lalu `/done`)
- `/mystats` — Lihat statistik penggunaan
- `/addpremium <user_id>` — (Admin) Upgrade user ke premium
- Proxy support untuk request ke GitHub

## Instalasi

1. **Clone repo & install dependencies**
    ```bash
    pip install -r requirements.txt
    ```

2. **Siapkan file konfigurasi**
    - `admin.json`  
      ```json
      {
        "bot_token": "TOKEN_BOT_ANDA",
        "admin_ids": [123456789],
        "limits": {
          "regular_daily_limit": 10,
          "premium_daily_limit": 100
        },
        "check_cooldown": 1
      }
      ```
    - (Opsional) `proxy.txt` — satu proxy per baris

3. **Jalankan bot**
    ```bash
    python bot.py
    ```

## Cara Pakai

- **Cek satu username:**  
  `/check username`

- **Bulk check:**  
  1. `/bulkcheck`
  2. Kirim daftar username (boleh banyak baris sekaligus)
  3. Ketik `/done` untuk mulai cek

- **Upgrade user ke premium (admin):**  
  `/addpremium <user_id>`

## Catatan
- User harus pernah menjalankan `/start` agar bisa di-upgrade ke premium.
- Limit harian berbeda untuk regular & premium (lihat `admin.json`).

---

**Lisensi:** MIT