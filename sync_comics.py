import os
import sys
import time
import tarfile
import re
import urllib.request
import json

try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except Exception:
    pass

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir:
    os.chdir(script_dir)

COMICS = [
    {
        'folder': '01_Huong_Dan_Sinh_Ton_Trong_Hoc_Vien',
        'title': 'Hướng Dẫn Sinh Tồn Trong Học Viện',
        'url': 'https://nettruyenar.com/truyen-tranh/huong-dan-sinh-ton-trong-hoc-vien-18036',
        'slug': 'huong-dan-sinh-ton-trong-hoc-vien'
    },
    {
        'folder': '02_Helmut_Dua_Tre_Bi_Lang_Quen',
        'title': 'Helmut - Đứa Trẻ Bị Lãng Quên',
        'url': 'https://nettruyenar.com/truyen-tranh/helmut-dua-tre-bi-ruong-bo-12894',
        'slug': 'helmut-dua-tre-bi-ruong-bo'
    },
    {
        'folder': '03_Sat_Thu_Tai_Sinh_Thanh_Kiem_Si',
        'title': 'Sát Thủ Tái Sinh Thành Một Kiếm Sĩ Thiên Tài',
        'url': 'https://nettruyenar.com/truyen-tranh/sat-thu-tai-sinh-thanh-mot-kiem-si-thien-tai-15127',
        'slug': 'sat-thu-tai-sinh-thanh-mot-kiem-si-thien-tai'
    },
    {
        'folder': '04_Phap_Su_Thien_Tai_Giau_Nghe',
        'title': 'Pháp Sư Thiên Tài Giấu Nghề',
        'url': 'https://nettruyenar.com/truyen-tranh/thien-tai-ma-phap-su-giau-nghe-12113',
        'slug': 'thien-tai-ma-phap-su-giau-nghe'
    },
    {
        'folder': '05_Chuyen_Sinh_Thanh_Con_Ngoai_Gia_Thu',
        'title': 'Chuyển Sinh Thành Con Ngoài Giá Thú Của Gia Đình Kiếm Thuật Danh Tiếng',
        'url': 'https://nettruyenar.com/truyen-tranh/chuyen-sinh-thanh-con-ngoai-gia-thu-cua-gia-dinh-kiem-thuat-danh-tieng-26170',
        'slug': 'chuyen-sinh-thanh-con-ngoai-gia-thu-cua-gia-dinh-kiem-thuat-danh-tieng'
    },
    {
        'folder': '06_Vo_Han_Phap_Su',
        'title': 'Vô Hạn Pháp Sư',
        'url': 'https://nettruyenar.com/truyen-tranh/dai-phap-su-toan-nang-13507',
        'slug': 'dai-phap-su-toan-nang'
    },
    {
        'folder': '07_Ke_Song_Sot_Vua_Kiem',
        'title': 'Kẻ Sống Sót Vua Kiếm',
        'url': 'https://nettruyenar.com/truyen-tranh/cau-chuyen-sinh-ton-cua-kiem-vuong-o-the-gioi-khac-29404',
        'slug': 'cau-chuyen-sinh-ton-cua-kiem-vuong-o-the-gioi-khac'
    }
]

DIST_DIR = 'dist'
os.makedirs(DIST_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://nettruyenar.com/'
}

def http_get(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode('utf-8', errors='ignore')

def download_file(url, dest):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        content = resp.read()
        if len(content) > 1000:
            with open(dest, 'wb') as f:
                f.write(content)
            return True
    return False

def process():
    synced_archives = []

    for c in COMICS:
        print(f"\n==========================================")
        print(f"Checking: {c['title']} ({c['url']})")

        try:
            html = http_get(c['url'])
            
            # Find all chapter links for this comic
            re_chap = re.compile(r'<a[^>]+href="((?:https://nettruyenar\.com)?/truyen-tranh/[^"]+/(?:chapter|chuong)-(\d+(?:\.\d+)?)[^"]*)"[^>]*>', re.IGNORECASE)
            chapters = []
            for m in re_chap.finditer(html):
                href = m.group(1)
                if href.startswith('/'):
                    href = 'https://nettruyenar.com' + href
                if c['slug'] in href:
                    num = float(m.group(2))
                    chapters.append({'href': href, 'num': num, 'raw_num': m.group(2)})

            if not chapters:
                print(f"Warning: No chapter links found for {c['title']}")
                continue

            # Sort descending by chapter number
            chapters.sort(key=lambda x: x['num'], reverse=True)
            
            # Deduplicate by chapter number
            unique_chapters = []
            seen_nums = set()
            for ch in chapters:
                if ch['num'] not in seen_nums:
                    seen_nums.add(ch['num'])
                    unique_chapters.append(ch)

            # Get the latest chapter
            latest = unique_chapters[0]
            chap_clean = f"Chuong_{int(latest['num']) if latest['num'].is_integer() else latest['num']}"
            print(f"Latest Chapter: {chap_clean} -> {latest['href']}")

            # Fetch chapter page
            chap_html = http_get(latest['href'])

            # Extract comic image URLs
            img_urls = re.findall(r'https?://[^"\'\s]+/nettruyen/[^"\'\s]+\.(?:jpg|jpeg|png|webp)', chap_html, re.IGNORECASE)
            
            # Deduplicate while preserving order
            seen_urls = set()
            ordered_imgs = []
            for u in img_urls:
                if u not in seen_urls:
                    seen_urls.add(u)
                    ordered_imgs.append(u)

            print(f"Found {len(ordered_imgs)} pages for {c['title']} {chap_clean}")
            if not ordered_imgs:
                print("No images found, skipping archive creation.")
                continue

            # Download images to staging
            chap_dir = os.path.join("staging", c['folder'], chap_clean)
            os.makedirs(chap_dir, exist_ok=True)

            downloaded = 0
            for idx, u in enumerate(ordered_imgs):
                dest_file = os.path.join(chap_dir, f"{idx+1:03d}.jpg")
                try:
                    if download_file(u, dest_file):
                        downloaded += 1
                except Exception as ex:
                    print(f"  Err downloading page {idx+1}: {ex}")

            print(f"Downloaded {downloaded}/{len(ordered_imgs)} pages.")

            # Create tar.gz archive
            tar_filename = f"{c['folder']}.tar.gz"
            tar_path = os.path.join(DIST_DIR, tar_filename)

            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(os.path.join("staging", c['folder']), arcname=c['folder'])

            size_mb = os.path.getsize(tar_path) / (1024 * 1024)
            print(f"Created archive: {tar_path} ({size_mb:.2f} MB)")
            synced_archives.append((c['folder'], tar_filename))

        except Exception as e:
            print(f"Error processing {c['title']}: {e}")

    # Generate xteink_cloud_sync.sh for the ASUS ZenFone 4 Max
    now_str = time.strftime('%H:%M %d/%m')
    sync_sh = f"""#!/system/bin/sh
# Auto-generated by GitHub Actions for ASUS ZenFone XTEINK at {now_str}
BOOKS_DIR="/data/media/0/Books"
[ ! -d "$BOOKS_DIR" ] && BOOKS_DIR="/sdcard/Books"
mkdir -p "$BOOKS_DIR"

BASE_URL="https://github.com/KonKuKon/xteink-comic-sync/releases/download/latest"

"""
    for folder, tar_fn in synced_archives:
        sync_sh += f"""
echo "Dang dong bo {folder}..."
curl -k -s -L "$BASE_URL/{tar_fn}" | tar -xz -C "$BOOKS_DIR/"
"""

    sync_sh += f"""
MSG="Cloud GitHub: Da dong bo {len(synced_archives)} truyen ({now_str})"
echo "$MSG" > "$BOOKS_DIR/.sync_status"
echo "$MSG" > "/sdcard/Books/.sync_status"
echo 1 > "$BOOKS_DIR/.wake_trigger"
echo 1 > "/sdcard/Books/.wake_trigger"
echo "[OK] $MSG"
"""

    sh_path = os.path.join(DIST_DIR, "xteink_cloud_sync.sh")
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sync_sh)
    print(f"\nGenerated phone sync script: {sh_path}")
    print(f"Total synced comics: {len(synced_archives)}")

if __name__ == '__main__':
    process()
