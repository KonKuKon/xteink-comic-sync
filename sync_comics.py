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

DIST_DIR = 'dist'
os.makedirs(DIST_DIR, exist_ok=True)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://nettruyenar.com/'
}

API_HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Referer': 'https://nettruyenar.com/',
    'X-Requested-With': 'XMLHttpRequest'
}

session = requests.Session(impersonate="chrome124")

FOLDER_MAPPING = {
    'thanh-mai-truc-ma-cua-de-nhat-thien-ha': '01_Thanh_Mai_Truc_Ma_Cua_De_Nhat_Thien_Ha',
    'thiet-huyet-kiem-si-hoi-quy': '02_Thiet_Huyet_Kiem_Si_Hoi_Quy',
    'sat-long-nhan-hoi-quy-sieu-viet': '03_Sat_Long_Nhan_Hoi_Quy_Sieu_Viet',
    'quy-toc-luoi-bieng-tro-thanh-thien-tai': '04_Quy_Toc_Luoi_Bieng_Tro_Thanh_Thien_Tai',
    'huong-dan-sinh-ton-trong-hoc-vien': '05_Huong_Dan_Sinh_Ton_Trong_Hoc_Vien',
    'helmut-dua-tre-bi-ruong-bo': '06_Helmut_Dua_Tre_Bi_Lang_Quen',
    'helmut-dua-tre-bi-lang-quen': '06_Helmut_Dua_Tre_Bi_Lang_Quen',
    'moi-linh-danh-thue-tro-ve-deu-co-mot-ke-hoach': '07_Moi_Linh_Danh_Thue_Tro_Ve_Deu_Co_Mot_Ke_Hoach',
    'chuyen-gia-con-trung-tai-duong-gia-tu-xuyen': '08_Chuyen_Gia_Con_Trung_Tai_Duong_Gia_Tu_Xuyen',
    'con-trai-ut-cua-ba-tuoc-la-mot-nguoi-choi': '09_Con_Trai_Ut_Cua_Ba_Tuoc_La_Mot_Nguoi_Choi',
}

DEFAULT_COMICS = [
    {
        'url': 'https://nettruyenar.com/truyen-tranh/thanh-mai-truc-ma-cua-de-nhat-thien-ha-25478',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/thiet-huyet-kiem-si-hoi-quy-14340',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/sat-long-nhan-hoi-quy-sieu-viet-26629',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/quy-toc-luoi-bieng-tro-thanh-thien-tai-11503',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/huong-dan-sinh-ton-trong-hoc-vien-18036',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/helmut-dua-tre-bi-ruong-bo-12894',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/moi-linh-danh-thue-tro-ve-deu-co-mot-ke-hoach-26273',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/chuyen-gia-con-trung-tai-duong-gia-tu-xuyen-26309',
        'from_chap': 1,
        'to_chap': 10
    },
    {
        'url': 'https://nettruyenar.com/truyen-tranh/con-trai-ut-cua-ba-tuoc-la-mot-nguoi-choi-17413',
        'from_chap': 1,
        'to_chap': 10
    }
]

def http_get(url, is_api=False):
    hdrs = API_HEADERS if is_api else HEADERS
    for _ in range(3):
        try:
            r = session.get(url, headers=hdrs, timeout=25)
            if r.status_code == 200:
                return r
        except Exception:
            time.sleep(1)
    return None

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

def parse_chap_spec(spec_str):
    s = spec_str.lower().strip()
    if any(k in s for k in ['latest', 'moi', 'mới']):
        return 'latest', 'latest'
    m_range = re.search(r'(\d+(?:\.\d+)?)\s*(?:->|-|to|:|\.\.)\s*(\d+(?:\.\d+)?)', s)
    if m_range:
        return float(m_range.group(1)), float(m_range.group(2))
    m_num = re.search(r'(\d+(?:\.\d+)?)', s)
    if m_num:
        return float(m_num.group(1)), None
    return 1, 10

def parse_comics_txt():
    comics = []
    txt_path = 'comics.txt'
    if os.path.exists(txt_path):
        with open(txt_path, 'r', encoding='utf-8') as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith('#') or re.match(r'^\d*#', line):
                    continue
                if not line.startswith('http') and '/' not in line and '-' not in line:
                    continue
                parts = [p.strip() for p in line.split('|')]
                url_or_slug = parts[0]
                from_chap = 1
                to_chap = 10
                if len(parts) >= 3:
                    try:
                        from_chap = float(parts[1])
                        to_chap = float(parts[2])
                    except ValueError:
                        from_chap, to_chap = parse_chap_spec(parts[1])
                elif len(parts) == 2:
                    from_chap, to_chap = parse_chap_spec(parts[1])
                else:
                    from_chap, to_chap = 1, 10 # Mac dinh tai 10 chap dau de doc thu

                comics.append({
                    'url': url_or_slug,
                    'from_chap': from_chap,
                    'to_chap': to_chap
                })

    if not comics:
        comics = DEFAULT_COMICS
    return comics

def get_comic_meta(target):
    # Determine slug and comic_id
    slug = None
    comic_id = None
    url = target if target.startswith('http') else f"https://nettruyenar.com/truyen-tranh/{target}"
    
    m = re.search(r'truyen-tranh/([a-zA-Z0-9_-]+?)(?:-(\d+))?/?$', url)
    if m:
        slug = m.group(1)
        if m.group(2):
            comic_id = m.group(2)

    resp = http_get(url)
    title = slug.replace('-', ' ').title() if slug else "Comic"
    if resp:
        html = resp.text
        m_title = re.search(r'<h1[^>]*class=[\'"][^\'"]*title-detail[^\'"]*[\'"][^>]*>(.*?)</h1>', html, re.DOTALL | re.IGNORECASE)
        if m_title:
            title = m_title.group(1).strip()
        if not comic_id:
            m_id = re.search(r'data-id=[\'"](\d+)[\'"]', html)
            if not m_id:
                m_id = re.search(r'comicId\s*[:=]\s*[\'"]?(\d+)', html, re.IGNORECASE)
            if m_id:
                comic_id = m_id.group(1)

    return slug, comic_id, title, url

def fetch_chapters_via_api(slug, comic_id, from_chap, to_chap):
    api_url = 'https://nettruyenar.com/Comic/Services/ComicService.asmx/ChapterList'
    try:
        resp = session.get(api_url, params={'slug': slug, 'comicId': comic_id}, headers=API_HEADERS, timeout=20)
        print(f"    API Response: status={resp.status_code}, length={len(resp.text)}, preview={resp.text[:120]!r}")
        if resp.status_code != 200:
            return []
        data = resp.json()
    except Exception as e:
        print(f"    API Exception: {e}")
        return []
    raw_chaps = data.get('data', [])
    if not raw_chaps:
        return []

    # Handle 'latest'
    if from_chap == 'latest' or to_chap == 'latest':
        latest_ch = max(raw_chaps, key=lambda x: float(x.get('chapter_num', 0)))
        return [latest_ch]

    # Filter by range
    filtered = []
    for c in raw_chaps:
        try:
            num = float(c.get('chapter_num', 0))
            if num >= from_chap and (to_chap is None or num <= to_chap):
                filtered.append(c)
        except Exception:
            pass

    # Clean duplicates: if whole number chapter (e.g. 3) exists, exclude fractional parts (3.1, 3.2...)
    int_nums = set(int(float(c.get('chapter_num', 0))) for c in filtered if float(c.get('chapter_num', 0)).is_integer())
    clean_chaps = []
    for c in filtered:
        num = float(c.get('chapter_num', 0))
        if num.is_integer():
            clean_chaps.append(c)
        else:
            if int(num) not in int_nums:
                clean_chaps.append(c)

    # Sort ascending by chapter_num
    clean_chaps.sort(key=lambda x: float(x.get('chapter_num', 0)))
    return clean_chaps

def process():
    comic_list = parse_comics_txt()
    print(f"Loaded {len(comic_list)} comic entries to process.")

    synced_archives = []

    for idx, item in enumerate(comic_list, 1):
        target = item['url']
        from_chap = item['from_chap']
        to_chap = item['to_chap']

        slug, comic_id, title, full_url = get_comic_meta(target)
        if not slug or not comic_id:
            print(f"[{idx}] Error resolving slug/comic_id for {target}")
            continue

        folder = FOLDER_MAPPING.get(slug)
        if not folder:
            parts = [p.capitalize() for p in slug.replace('_', '-').split('-') if p]
            folder = f"{idx:02d}_{'_'.join(parts)}"

        print(f"\n==========================================")
        print(f"[{idx}/{len(comic_list)}] {title}")
        print(f"  Slug: {slug} | ComicID: {comic_id} | Range: {from_chap} -> {to_chap}")
        print(f"  Target Folder: {folder}")

        chapters = fetch_chapters_via_api(slug, comic_id, from_chap, to_chap)
        print(f"  Found {len(chapters)} chapters to sync: {[c.get('chapter_num') for c in chapters]}")
        if not chapters:
            continue

        for ch in chapters:
            c_num = float(ch.get('chapter_num', 0))
            chap_clean = f"Chuong_{int(c_num) if c_num.is_integer() else c_num}"
            chap_dir = os.path.join("staging", folder, chap_clean)
            os.makedirs(chap_dir, exist_ok=True)

            existing = [f for f in os.listdir(chap_dir) if f.endswith(('.jpg', '.png', '.webp'))]
            if len(existing) >= 5:
                print(f"    {chap_clean}: already has {len(existing)} pages, skipping.")
                continue

            chap_url = f"https://nettruyenar.com/truyen-tranh/{slug}/{ch.get('chapter_slug')}/{ch.get('chapter_id')}"
            ch_resp = http_get(chap_url)
            if not ch_resp:
                print(f"    {chap_clean}: Failed to load chapter page.")
                continue

            # Extract page images
            img_tags = re.findall(r'<img[^>]+(?:data-original|data-sv1|data-src|src)=[\'"]([^\'"]+)[\'"][^>]*>', ch_resp.text, re.IGNORECASE)
            reading_imgs = [img for img in img_tags if '/thumb/' not in img and re.search(r'nettruyen/.*\.(?:jpg|jpeg|png|webp)', img, re.I)]
            seen = set()
            ordered_imgs = []
            for img in reading_imgs:
                if img.startswith('//'):
                    img = 'https:' + img
                if img not in seen:
                    seen.add(img)
                    ordered_imgs.append(img)

            if not ordered_imgs:
                print(f"    {chap_clean}: No images found.")
                continue

            dl_args = []
            for p_idx, u in enumerate(ordered_imgs, 1):
                dest_file = os.path.join(chap_dir, f"{p_idx:03d}.jpg")
                dl_args.append((u, dest_file))

            with ThreadPoolExecutor(max_workers=12) as pool:
                results = list(pool.map(download_file, dl_args))

            success_cnt = sum(1 for r in results if r)
            print(f"    {chap_clean}: Downloaded {success_cnt}/{len(ordered_imgs)} pages.")

        # Pack archive for this comic
        staging_dir = os.path.join("staging", folder)
        if os.path.exists(staging_dir) and os.listdir(staging_dir):
            tar_filename = f"{folder}.tar.gz"
            tar_path = os.path.join(DIST_DIR, tar_filename)
            with tarfile.open(tar_path, "w:gz") as tar:
                tar.add(staging_dir, arcname=folder)

            size_bytes = os.path.getsize(tar_path)
            size_mb = size_bytes / (1024 * 1024)
            print(f"  ==> Created archive: {tar_path} ({size_mb:.2f} MB, {size_bytes} bytes)")
            synced_archives.append((folder, title, tar_filename, size_bytes))
        else:
            print(f"  Warning: No content to pack for {title}")

    # Generate xteink_cloud_sync.sh
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

    # Kiểm tra xem bộ truyện này đã có sẵn trên máy chưa (chỉ tải truyện còn thiếu)
    COMIC_FOLDER="${{TAR_NAME%.tar.gz}}"
    TARGET_DIR="$BOOKS_DIR/$COMIC_FOLDER"
    if [ ! -f "$BOOKS_DIR/.force_sync" ] && [ -d "$TARGET_DIR" ] && [ -n "$(/data/adb/xteink/busybox ls "$TARGET_DIR" 2>/dev/null || ls "$TARGET_DIR" 2>/dev/null)" ]; then
        TOTAL_MB=$((TOTAL_BYTES / 1048576))
        [ "$TOTAL_MB" -eq 0 ] && TOTAL_MB=1
        OVERALL_PCT=$(( INDEX * 100 / TOTAL ))
        echo "$INDEX|$TOTAL|$NAME|$TOTAL_MB|$TOTAL_MB|100|-|skipped|$OVERALL_PCT" > "$PROGRESS_FILE"
        write_msg "[$INDEX/$TOTAL] $NAME: Đã có sẵn trên máy (Bỏ qua)"
        echo "[$INDEX/$TOTAL] $NAME: Đã có trên máy -> Bỏ qua tải lại"
        sleep 0.3
        return 0
    fi

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

    for idx, (folder, title, tar_fn, size_bytes) in enumerate(synced_archives, 1):
        sync_sh += f'download_comic {idx} {total_archives} "{title}" "{tar_fn}" {size_bytes}\n'

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
    print(f"Total synced comics: {total_archives}")

if __name__ == '__main__':
    process()
