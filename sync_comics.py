import os
import sys
import time
import tarfile
import re
import requests
from playwright.sync_api import sync_playwright

COMICS = [
    {
        'folder': '01_Huong_Dan_Sinh_Ton_Trong_Hoc_Vien',
        'title': 'Hướng Dẫn Sinh Tồn Trong Học Viện',
        'slug': 'huong-dan-sinh-ton-trong-hoc-vien'
    },
    {
        'folder': '02_Helmut_Dua_Tre_Bi_Lang_Quen',
        'title': 'Helmut - Đứa Trẻ Bị Lãng Quên',
        'slug': 'helmut-dua-tre-bi-lang-quen'
    },
    {
        'folder': '03_Sat_Thu_Tai_Sinh_Thanh_Kiem_Si',
        'title': 'Sát Thủ Tái Sinh Thành Một Kiếm Sĩ Thiên Tài',
        'slug': 'sat-thu-tai-sinh-thanh-mot-kiem-si-thien-tai'
    },
    {
        'folder': '04_Phap_Su_Thien_Tai_Giau_Nghe',
        'title': 'Pháp Sư Thiên Tài Giấu Nghề',
        'slug': 'phap-su-thien-tai-giau-nghe'
    },
    {
        'folder': '05_Chuyen_Sinh_Thanh_Con_Ngoai_Gia_Thu',
        'title': 'Chuyển Sinh Thành Con Ngoài Giá Thú Của Gia Đình Kiếm Thuật Danh Tiếng',
        'slug': 'chuyen-sinh-thanh-con-ngoai-gia-thu-cua-gia-dinh-kiem-thuat-danh-tieng'
    },
    {
        'folder': '06_Vo_Han_Phap_Su',
        'title': 'Vô Hạn Pháp Sư',
        'slug': 'vo-han-phap-su'
    },
    {
        'folder': '07_Ke_Song_Sot_Vua_Kiem',
        'title': 'Kẻ Sống Sót Vua Kiếm',
        'slug': 'ke-song-sot-vua-kiem'
    }
]

DIST_DIR = 'dist'
os.makedirs(DIST_DIR, exist_ok=True)

HEADERS = {
    'Referer': 'https://goctruyentranhvui41.com/',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}

def clean_chapter_name(text):
    m = re.search(r'(ch[uư][oơ]ng\s*\d+(\.\d+)?)', text, re.IGNORECASE)
    if m:
        c = m.group(1).title().replace(' ', '_')
        return c
    clean = re.sub(r'[^\w\d_-]', '_', text)
    return clean[:30]

def process():
    synced_archives = []
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(
            user_agent=HEADERS['User-Agent'],
            viewport={'width': 1280, 'height': 800}
        )
        page = context.new_page()

        for c in COMICS:
            comic_url = f"https://goctruyentranhvui41.com/truyen/{c['slug']}"
            print(f"\n==========================================")
            print(f"Checking: {c['title']} ({comic_url})")
            
            try:
                page.goto(comic_url, wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(2500)
                
                # Check for chapter links
                links = page.evaluate("""() => {
                    const res = [];
                    const anchors = document.querySelectorAll('a[href*="/chuong-"]');
                    anchors.forEach(a => {
                        const href = a.href;
                        const text = a.innerText.trim();
                        if (href && text && !res.some(r => r.href === href)) {
                            res.push({ href, text });
                        }
                    });
                    return res;
                }""")
                
                if not links:
                    print(f"Warning: No chapter links found on {comic_url}")
                    continue
                    
                latest = links[0]
                chap_name = clean_chapter_name(latest['text'])
                print(f"Latest Chapter: {latest['text']} -> {latest['href']} (Folder: {chap_name})")
                
                # Navigate to chapter page
                page.goto(latest['href'], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(3000)
                
                # Scroll down in stages to trigger lazy loading
                for _ in range(8):
                    page.evaluate("window.scrollBy(0, 2000)")
                    page.wait_for_timeout(800)
                    
                # Extract image URLs
                img_urls = page.evaluate("""() => {
                    const urls = [];
                    document.querySelectorAll('img').forEach(img => {
                        const src = img.currentSrc || img.src || img.getAttribute('data-src') || '';
                        if (src && src.includes('gtt-bk.pro/image/') && !src.includes('/image/c/')) {
                            if (!urls.includes(src)) urls.push(src);
                        }
                    });
                    return urls;
                }""")
                
                print(f"Found {len(img_urls)} comic pages for {chap_name}")
                if not img_urls:
                    print("No images found, skipping archive creation.")
                    continue
                
                # Download images into staging directory
                chap_dir = os.path.join("staging", c['folder'], chap_name)
                os.makedirs(chap_dir, exist_ok=True)
                
                downloaded_count = 0
                for idx, u in enumerate(img_urls):
                    page_num = f"{idx+1:03d}.jpg"
                    dest_file = os.path.join(chap_dir, page_num)
                    try:
                        r = requests.get(u, headers=HEADERS, timeout=15)
                        if r.status_code == 200 and len(r.content) > 1000:
                            with open(dest_file, 'wb') as f:
                                f.write(r.content)
                            downloaded_count += 1
                    except Exception as ex:
                        print(f"Err downloading page {idx+1}: {ex}")
                
                print(f"Successfully downloaded {downloaded_count}/{len(img_urls)} pages.")
                
                # Create tar.gz archive for this comic
                tar_filename = f"{c['folder']}.tar.gz"
                tar_path = os.path.join(DIST_DIR, tar_filename)
                
                with tarfile.open(tar_path, "w:gz") as tar:
                    tar.add(os.path.join("staging", c['folder']), arcname=c['folder'])
                
                print(f"Created archive: {tar_path} ({os.path.getsize(tar_path)} bytes)")
                synced_archives.append((c['folder'], tar_filename))
                
            except Exception as e:
                print(f"Error processing {c['title']}: {e}")
                
        browser.close()

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
