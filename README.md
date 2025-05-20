# GitHub Profile Checker Bot

Bot Telegram untuk cek status akun GitHub (aktif, suspend, badge PRO, dll) secara satuan atau bulk.  
Mendukung fitur admin untuk upgrade user ke premium.

## Fitur
- `/check <username>` — Cek satu akun GitHub
- `/bulkcheck` — Cek banyak username sekaligus (kirim daftar username, lalu `/done`)
- `/mystats` — Lihat statistik penggunaan
- `/addpremium <user_id>` — (Admin) Upgrade user ke premium
- Proxy support untuk request ke GitHub

---

## Upload Project ke VPS

### **A. Upload via SCP (Jika Belum di GitHub)**
Kamu bisa upload file ke VPS menggunakan `scp` dari terminal lokal:
```bash
scp -r * username@ip_vps:/home/username/GHSBOT
```
Ganti `username` dan `ip_vps` sesuai VPS kamu.  
Pastikan di VPS sudah ada folder tujuan (`GHSBOT`), atau buat dulu dengan `mkdir GHSBOT`.

### **B. Upload ke GitHub (Jika Belum)**
Jika Anda belum mengupload project ke GitHub, lakukan langkah berikut di folder project Anda:
```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/username/repo-anda.git
git push -u origin main
```
Ganti `https://github.com/username/repo-anda.git` dengan URL repository GitHub Anda.

---

## Instalasi di VPS Ubuntu

1. **Clone repo dari GitHub (jika sudah di GitHub)**
    ```bash
    git clone https://github.com/ronaldarman/notbadn.git
    cd notbadn
    ```

2. **Install dependencies**
    ```bash
    pip3 install -r requirements.txt
    ```

3. **Siapkan file konfigurasi**
    - Jika **belum punya** file `admin.json`, buat baru:
      ```bash
      nano admin.json
      ```
      Isi seperti berikut:
      ```json
      {
        "bot_token": "TOKEN_BOT_ANDA",
        "admin_ids": [123456789],
        "limits": {
          "regular_daily_limit": 10,
          "premium_daily_limit": 100
        },
        "check_cooldown": 3
      }
      ```
    - Jika **sudah punya** file `admin.json`, **jangan lupa edit dulu** agar sesuai dengan token dan admin id Anda:
      ```bash
      nano admin.json
      ```
    - (Opsional) Buat file `proxy.txt` — satu proxy per baris:
      ```bash
      nano proxy.txt
      ```
    - Pastikan file konfigurasi memiliki izin baca/tulis:
      ```bash
      chmod 600 admin.json
      ```

4. **Jalankan bot**
    ```bash
    python3 bot.py
    ```
    Atau jalankan di background:
    ```bash
    nohup python3 bot.py > bot.log 2>&1 &
    ```
    Untuk melihat log:
    ```bash
    tail -f bot.log
    ```
    Untuk menghentikan bot:
    ```bash
    pkill -f bot.py
    ```

---

## Instalasi & Menjalankan di Windows

1. **Install Python**  
   Download dan install Python 3 dari [python.org](https://www.python.org/downloads/).

2. **Clone repo atau upload file ke folder**
    - Jika dari GitHub:
      ```cmd
      git clone https://github.com/ronaldarman/notbadn.git
      cd notbadn
      ```
    - Atau upload manual semua file ke satu folder.

3. **Install dependencies**
    ```cmd
    pip install -r requirements.txt
    ```

4. **Siapkan file konfigurasi**
    - Jika belum ada, buat `admin.json` seperti contoh di atas.
    - Jika sudah ada, **jangan lupa edit dulu** dengan Notepad atau editor lain.

5. **Jalankan bot**
    ```cmd
    python bot.py
    ```

---

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
