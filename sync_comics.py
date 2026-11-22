import os
import sys
import time
import tarfile
import re
from concurrent.futures import ThreadPoolExecutor
from curl_cffi import requests

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
        'folder': '01_Thanh_Mai_Truc_Ma_Cua_De_Nhat_Thien_Ha',
        'title': 'Thanh Mai Trúc Mã Của Đệ Nhất Thiên Hạ',
        'url': 'https://nettruyenar.com/truyen-tranh/thanh-mai-truc-ma-cua-de-nhat-thien-ha-25478',
        'slug': 'thanh-mai-truc-ma-cua-de-nhat-thien-ha',
        'from_chap': 109
    },
    {
        'folder': '02_Thiet_Huyet_Kiem_Si_Hoi_Quy',
        'title': 'Thiết Huyết Kiếm Sĩ Phục Thù',
        'url': 'https://nettruyenar.com/truyen-tranh/thiet-huyet-kiem-si-hoi-quy',
        'slug': 'thiet-huyet-kiem-si-hoi-quy',
        'from_chap': 190
    },
    {
        'folder': '03_Sat_Long_Nhan_Hoi_Quy_Sieu_Viet',
        'title': 'Sát Long Nhân Hồi Quy Siêu Việt',
        'url': 'https://nettruyenar.com/truyen-tranh/sat-long-nhan-hoi-quy-sieu-viet-26629',
        'slug': 'sat-long-nhan-hoi-quy-sieu-viet',
        'from_chap': 80
    },
    {
        'folder': '04_Quy_Toc_Luoi_Bieng_Tro_Thanh_Thien_Tai',
        'title': 'Quý Tộc Lười Biếng Trở Thành Thiên Tài',
        'url': 'https://nettruyenar.com/truyen-tranh/quy-toc-luoi-bieng-tro-thanh-thien-tai-11503',
        'slug': 'quy-toc-luoi-bieng-tro-thanh-thien-tai',
        'from_chap': 139
    },
    {
        'folder': '05_Huong_Dan_Sinh_Ton_Trong_Hoc_Vien',
        'title': 'Hướng Dẫn Sinh Tồn Trong Học Viện',
        'url': 'https://nettruyenar.com/truyen-tranh/huong-dan-sinh-ton-trong-hoc-vien-18036',
        'slug': 'huong-dan-sinh-ton-trong-hoc-vien',
        'from_chap': 133
    },
    {
        'folder': '06_Helmut_Dua_Tre_Bi_Lang_Quen',
        'title': 'Helmut - Đứa Trẻ Bị Lãng Quên',
        'url': 'https://nettruyenar.com/truyen-tranh/helmut-dua-tre-bi-ruong-bo-12894',
        'slug': 'helmut-dua-tre-bi-ruong-bo',
        'from_chap': 142
    },
    {
        'folder': '07_Moi_Linh_Danh_Thue_Tro_Ve_Deu_Co_Mot_Ke_Hoach',
        'title': 'Mỗi Lính Đánh Thuê Trở Về Đều Có Một Kế Hoạch',
        'url': 'https://nettruyenar.com/truyen-tranh/moi-linh-danh-thue-tro-ve-deu-co-mot-ke-hoach-26273',
        'slug': 'moi-linh-danh-thue-tro-ve-deu-co-mot-ke-hoach',
        'from_chap': 110
    },
    {
        'folder': '08_Chuyen_Gia_Con_Trung_Tai_Duong_Gia_Tu_Xuyen',
        'title': 'Chuyên Gia Côn Trùng Tại Đường Gia Tứ Xuyên',
        'url': 'https://nettruyenar.com/truyen-tranh/chuyen-gia-con-trung-tai-duong-gia-tu-xuyen-26309',
        'slug': 'chuyen-gia-con-trung-tai-duong-gia-tu-xuyen',
        'from_chap': 71
    },
    {
        'folder': '09_Con_Trai_Ut_Cua_Ba_Tuoc_La_Mot_Nguoi_Choi',
        'title': 'Con Trai Út Của Bá Tước Là Một Người Chơi',
        'url': 'https://nettruyenar.com/truyen-tranh/con-trai-ut-cua-ba-tuoc-la-mot-nguoi-choi-17413',
        'slug': 'con-trai-ut-cua-ba-tuoc-la-mot-nguoi-choi',
        'from_chap': 1
    }
]

DIST_DIR = 'dist'
os.makedirs(DIST_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://nettruyenar.com/'
}

session = requests.Session(impersonate="chrome124")

def http_get(url):
    for _ in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=20)
            if r.status_code == 200:
                return r.text
        except Exception:
            time.sleep(1)
    return ""

def download_file(args):
    url, dest = args
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return True
    for _ in range(3):
        try:
            r = session.get(url, headers=HEADERS, timeout=25)
            if r.status_code == 200 and len(r.content) > 1000:
                with open(dest, 'wb') as f:
                    f.write(r.content)
                return True
        except Exception:
            time.sleep(1)
    return False

def process():
    synced_archives = []

    for c in COMICS:
        print(f"\n==========================================")
        print(f"Checking: {c['title']} (from Chap {c['from_chap']})")

        try:
            html = http_get(c['url'])
            if not html:
                print(f"Error fetching {c['url']}")
                continue

            # Find all chapter links for this comic
            re_chap = re.compile(r'<a[^>]+href="((?:https://nettruyenar\.com)?/truyen-tranh/[^"]+/(?:chapter|chuong)-(\d+(?:\.\d+)?)[^"]*)"[^>]*>', re.IGNORECASE)
            chapters = []
            for m in re_chap.finditer(html):
                href = m.group(1)
                if href.startswith('/'):
                    href = 'https://nettruyenar.com' + href
                if c['slug'] in href:
                    num = float(m.group(2))
                    if num >= c['from_chap']:
                        chapters.append({'href': href, 'num': num, 'raw_num': m.group(2)})

            if not chapters:
                print(f"Warning: No chapters >= {c['from_chap']} found for {c['title']}")
                continue

            # Sort ascending by chapter number
            chapters.sort(key=lambda x: x['num'])
            
            # Deduplicate by chapter number
            unique_chapters = []
            seen_nums = set()
            for ch in chapters:
                if ch['num'] not in seen_nums:
                    seen_nums.add(ch['num'])
                    unique_chapters.append(ch)

            print(f"Found {len(unique_chapters)} chapters to download (from {unique_chapters[0]['num']} to {unique_chapters[-1]['num']})")

            total_imgs_downloaded = 0
            for ch in unique_chapters:
                chap_clean = f"Chuong_{int(ch['num']) if ch['num'].is_integer() else ch['num']}"
                chap_dir = os.path.join("staging", c['folder'], chap_clean)
                os.makedirs(chap_dir, exist_ok=True)

                existing = [f for f in os.listdir(chap_dir) if f.endswith(('.jpg', '.png', '.webp'))]
                if len(existing) >= 5:
                    print(f"  {chap_clean} already has {len(existing)} pages, skipping.")
                    continue

                chap_html = http_get(ch['href'])
                img_urls = re.findall(r'https?://[^"\'\s]+/nettruyen/[^"\'\s]+\.(?:jpg|jpeg|png|webp)', chap_html, re.IGNORECASE)
                
                # Deduplicate while preserving order
                seen_urls = set()
                ordered_imgs = []
                for u in img_urls:
                    if u not in seen_urls:
                        seen_urls.add(u)
                        ordered_imgs.append(u)

                if not ordered_imgs:
                    print(f"  Warning: No images found for {chap_clean}")
                    continue

                # Download pages concurrently with ThreadPool
                dl_args = []
                for idx, u in enumerate(ordered_imgs):
                    dest_file = os.path.join(chap_dir, f"{idx+1:03d}.jpg")
                    dl_args.append((u, dest_file))

                with ThreadPoolExecutor(max_workers=8) as pool:
                    results = list(pool.map(download_file, dl_args))

                success_cnt = sum(1 for r in results if r)
                total_imgs_downloaded += success_cnt
                print(f"  {chap_clean}: Downloaded {success_cnt}/{len(ordered_imgs)} pages.")

            # Create tar.gz archive
            staging_comic_dir = os.path.join("staging", c['folder'])
            if os.path.exists(staging_comic_dir) and os.listdir(staging_comic_dir):
                tar_filename = f"{c['folder']}.tar.gz"
                tar_path = os.path.join(DIST_DIR, tar_filename)

                with tarfile.open(tar_path, "w:gz") as tar:
                    tar.add(staging_comic_dir, arcname=c['folder'])

                size_bytes = os.path.getsize(tar_path)
                size_mb = size_bytes / (1024 * 1024)
                print(f"Created archive: {tar_path} ({size_mb:.2f} MB, {size_bytes} bytes)")
                synced_archives.append((c['folder'], c['title'], tar_filename, size_bytes))
            else:
                print(f"No chapters downloaded for {c['title']}, archive not created.")

        except Exception as e:
            print(f"Error processing {c['title']}: {e}")

    # Generate xteink_cloud_sync.sh for the ASUS ZenFone 4 Max
    now_str = time.strftime('%H:%M %d/%m')
    total_archives = len(synced_archives)
    
    sync_sh = f"""#!/system/bin/sh
# Real-time Cloud Sync with Live Progress for ASUS ZenFone XTEINK
# Generated by Git Auto Cloud at {now_str}
BOOKS_DIR="/data/media/0/Books"
[ ! -d "$BOOKS_DIR" ] && BOOKS_DIR="/sdcard/Books"
mkdir -p "$BOOKS_DIR"

STATUS_FILE="/data/local/tmp/xteink_wifi_status.txt"
PROGRESS_FILE="/data/local/tmp/xteink_sync_progress.txt"
PID_FILE="/data/local/tmp/xteink_sync.pid"
SYNC_BANNER="$BOOKS_DIR/.sync_status"
SYNC_BANNER_SD="/sdcard/Books/.sync_status"
WAKE_FILE="$BOOKS_DIR/.wake_trigger"
WAKE_FILE_SD="/sdcard/Books/.wake_trigger"

echo "$$" > "$PID_FILE"
trap 'rm -f "$PID_FILE"' EXIT INT TERM

BASE_URL="https://github.com/KonKuKon/xteink-comic-sync/releases/download/latest"

write_msg() {{
    echo "$1" > "$SYNC_BANNER" 2>/dev/null
    echo "$1" > "$SYNC_BANNER_SD" 2>/dev/null
    echo "$1" > "$STATUS_FILE" 2>/dev/null
}}

download_comic() {{
    INDEX="$1"
    TOTAL="$2"
    NAME="$3"
    TAR_NAME="$4"
    TOTAL_BYTES="$5"
    URL="$BASE_URL/$TAR_NAME"
    TMP_TAR="/data/local/tmp/$TAR_NAME"

    rm -f "$TMP_TAR"
    TOTAL_MB=$((TOTAL_BYTES / 1048576))
    [ "$TOTAL_MB" -eq 0 ] && TOTAL_MB=1

    OVERALL_START=$(( ((INDEX - 1) * 100) / TOTAL ))
    echo "$INDEX|$TOTAL|$NAME|0|$TOTAL_MB|0|0 KB/s|connecting|$OVERALL_START" > "$PROGRESS_FILE"
    write_msg "[$INDEX/$TOTAL] $NAME: Đang kết nối tải..."

    curl -4 -k -s -L "$URL" -o "$TMP_TAR" &
    PID=$!

    PREV_BYTES=0
    while kill -0 $PID 2>/dev/null; do
        sleep 0.8
        CUR_BYTES=$(stat -c%s "$TMP_TAR" 2>/dev/null || echo 0)
        CUR_MB=$((CUR_BYTES / 1048576))

        if [ "$TOTAL_MB" -gt 0 ]; then
            PCT=$((CUR_MB * 100 / TOTAL_MB))
        else
            PCT=0
        fi
        [ "$PCT" -lt 0 ] && PCT=0
        [ "$PCT" -gt 100 ] && PCT=100

        SPEED_KB=$(((CUR_BYTES - PREV_BYTES) / 1024))
        PREV_BYTES=$CUR_BYTES

        if [ "$SPEED_KB" -ge 1024 ]; then
            SPEED_STR="$((SPEED_KB / 1024)).$(((SPEED_KB % 1024) / 100)) MB/s"
        else
            SPEED_STR="${{SPEED_KB}} KB/s"
        fi

        OVERALL_PCT=$(( ((INDEX - 1) * 100 + PCT) / TOTAL ))
        [ "$OVERALL_PCT" -lt 0 ] && OVERALL_PCT=0
        [ "$OVERALL_PCT" -gt 100 ] && OVERALL_PCT=100

        echo "$INDEX|$TOTAL|$NAME|$CUR_MB|$TOTAL_MB|$PCT|$SPEED_STR|downloading|$OVERALL_PCT" > "$PROGRESS_FILE"
        write_msg "[$INDEX/$TOTAL] $NAME: $CUR_MB/$TOTAL_MB MB ($PCT%) $SPEED_STR"
    done

    wait $PID
    STATUS_CODE=$?

    if [ "$STATUS_CODE" -eq 0 ] && [ -s "$TMP_TAR" ]; then
        OVERALL_PCT=$(( INDEX * 100 / TOTAL ))
        echo "$INDEX|$TOTAL|$NAME|$TOTAL_MB|$TOTAL_MB|100|-|extracting|$OVERALL_PCT" > "$PROGRESS_FILE"
        write_msg "[$INDEX/$TOTAL] $NAME: Đang giải nén vào Kệ sách..."
        /data/adb/xteink/busybox tar -xzf "$TMP_TAR" -C "$BOOKS_DIR/" 2>/dev/null || tar -xzf "$TMP_TAR" -C "$BOOKS_DIR/" 2>/dev/null
        rm -f "$TMP_TAR"
    else
        echo "$INDEX|$TOTAL|$NAME|0|$TOTAL_MB|0|0|error|0" > "$PROGRESS_FILE"
        write_msg "[$INDEX/$TOTAL] $NAME: Lỗi tải về!"
    fi
}}

echo "=== BẮT ĐẦU ĐỒNG BỘ {total_archives} BỘ TRUYỆN CLOUD ==="
write_msg "Đang kết nối Git Auto Cloud..."

"""

    for idx, (folder, title, tar_fn, size_bytes) in enumerate(synced_archives):
        sync_sh += f'download_comic {idx+1} {total_archives} "{title}" "{tar_fn}" {size_bytes}\n'

    sync_sh += f"""
NOW_STR=$(date +'%H:%M %d/%m')
MSG="Đã cập nhật {total_archives} truyện lúc $NOW_STR (Git Auto)"
echo "{total_archives}|{total_archives}|Hoàn tất tất cả|100|100|100|-|done|100" > "$PROGRESS_FILE"
write_msg "$MSG"
echo "$(date +%s)" > "$WAKE_FILE" 2>/dev/null
echo "$(date +%s)" > "$WAKE_FILE_SD" 2>/dev/null
echo "[HOÀN TẤT] $MSG"
"""

    sh_path = os.path.join(DIST_DIR, "xteink_cloud_sync.sh")
    with open(sh_path, "w", encoding="utf-8") as f:
        f.write(sync_sh)
    print(f"\nGenerated phone sync script: {sh_path}")
    print(f"Total synced comics: {len(synced_archives)}")

if __name__ == '__main__':
    process()
