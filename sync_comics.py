import os
import sys
import time
import tarfile
import re
import shutil
import json
import gc
import base64
from urllib.parse import urlparse, urljoin
from concurrent.futures import ThreadPoolExecutor
try:
    from curl_cffi import requests
    import requests as std_requests
    HAS_CFFI = True
except ImportError:
    import requests
    std_requests = requests
    HAS_CFFI = False

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

session = requests.Session(impersonate="chrome124") if HAS_CFFI else requests.Session()
std_session = std_requests.Session()
std_session.headers.update({'User-Agent': 'Mozilla/5.0'})

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

def http_get(url, is_api=False, referer=None):
    if 'nettruyen' in url.lower():
        hdrs = API_HEADERS if is_api else HEADERS
        cli = session
    else:
        hdrs = {'User-Agent': 'Mozilla/5.0'}
        if referer:
            hdrs['Referer'] = referer
        cli = std_session
    for _ in range(3):
        try:
            r = cli.get(url, headers=hdrs, timeout=25)
            if r.status_code == 200:
                return r
        except Exception:
            time.sleep(1)
    return None

def download_file(args):
    url, dest = args[0], args[1]
    referer = args[2] if len(args) > 2 else None
    if os.path.exists(dest) and os.path.getsize(dest) > 1000:
        return True
    hdrs = dict(HEADERS)
    if referer:
        hdrs['Referer'] = referer
    for _ in range(3):
        try:
            r = session.get(url, headers=hdrs, timeout=25)
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
    target_clean = target.strip()
    
    m = re.search(r'(?:truyen-tranh/)?([a-zA-Z0-9_-]+?)(?:-(\d+))?/?$', target_clean)
    if m:
        slug = m.group(1).strip('/-')
        if m.group(2):
            comic_id = m.group(2)

    url = f"https://nettruyenar.com/truyen-tranh/{slug}" + (f"-{comic_id}" if comic_id else "")
    resp = http_get(url)
    title = slug.replace('-', ' ').title() if slug else "Comic"
    
    if (not resp or not comic_id) and slug:
        search_kw = slug.replace('-', ' ')
        s_resp = http_get(f"https://nettruyenar.com/tim-truyen?keyword={search_kw}")
        if s_resp:
            m_match = re.search(r'href=[\'"][^\'"]*truyen-tranh/([a-zA-Z0-9_-]+?)-(\d+)[\'"]', s_resp.text)
            if m_match:
                slug = m_match.group(1)
                comic_id = m_match.group(2)
                url = f"https://nettruyenar.com/truyen-tranh/{slug}-{comic_id}"
                resp = http_get(url)

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

def get_goctruyentranh_comic(target, from_chap, to_chap):
    parsed = urlparse(target.strip())
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    slug = parsed.path.strip('/').split('/')[-1]
    resp = http_get(target.strip())
    if not resp:
        return slug, slug.replace('-', ' ').title(), [], base_url + '/'
    html = resp.text
    title = slug.replace('-', ' ').title()
    m_title = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
    if m_title:
        title = re.sub(r'\s*\[.*?\]\s*$', '', m_title.group(1)).strip()

    chap_nums = set(re.findall(r'chuong-(\d+(?:\.\d+)?)', html))
    if chap_nums:
        max_chap = int(max(float(n) for n in chap_nums))
        all_nums = set(str(i) for i in range(1, max_chap + 1)) | chap_nums
    else:
        all_nums = set()
    raw_chaps = [{'chapter_num': n, 'chap_str': n} for n in all_nums]
    chapters = filter_chapters_range(raw_chaps, from_chap, to_chap)
    if not chapters:
        return slug, title, [], base_url + '/'

    # Fetch comicId from the first available chapter page (or chap 1)
    first_num = chapters[0]['chap_str']
    ch_page = http_get(f"{base_url}/truyen/{slug}/chuong-{first_num}", referer=base_url + '/')
    comic_id = None
    if ch_page:
        m_id = re.search(r'id:\s*`(\d+)`', ch_page.text)
        if m_id:
            comic_id = m_id.group(1)

    for ch in chapters:
        ch['_provider'] = 'goctruyentranh'
        ch['_base_url'] = base_url
        ch['_slug'] = slug
        ch['_comic_id'] = comic_id
    return slug, title, chapters, base_url + '/'

def get_truyenqq_or_generic_comic(target, from_chap, to_chap):
    parsed = urlparse(target.strip())
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    path_parts = [p for p in parsed.path.strip('/').split('/') if p]
    slug = re.sub(r'\.html$', '', path_parts[-1]) if path_parts else 'comic'
    resp = http_get(target.strip())
    if not resp:
        return slug, slug.replace('-', ' ').title(), [], base_url + '/'
    html = resp.text
    title = slug.replace('-', ' ').title()
    m_h1 = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
    if m_h1:
        title = re.sub(r'<[^>]+>', '', m_h1.group(1)).strip()

    # Extract chapter links matching common Vietnamese comic URL patterns
    links = re.findall(r'href=[\'"]([^\'"]+)[\'"]', html, re.IGNORECASE)
    chap_map = {}
    for href in links:
        m_ch = re.search(r'(?:chuong|chap|chapter|ep)[-_]?(\d+(?:\.\d+)?)', href, re.IGNORECASE)
        if m_ch:
            num_str = m_ch.group(1)
            full_ch_url = urljoin(target.strip(), href)
            if num_str not in chap_map:
                chap_map[num_str] = {'chapter_num': num_str, 'url': full_ch_url}

    chapters = filter_chapters_range(list(chap_map.values()), from_chap, to_chap)
    for ch in chapters:
        ch['_provider'] = 'generic'
        ch['_base_url'] = base_url
    return slug, title, chapters, base_url + '/'

def filter_chapters_range(raw_chaps, from_chap, to_chap):
    if not raw_chaps:
        return []
    if from_chap == 'latest' or to_chap == 'latest':
        return [max(raw_chaps, key=lambda x: float(x.get('chapter_num', 0)))]
    filtered = []
    for c in raw_chaps:
        try:
            num = float(c.get('chapter_num', 0))
            if num >= from_chap and (to_chap is None or num <= to_chap):
                filtered.append(c)
        except Exception:
            pass
    int_nums = set(int(float(c.get('chapter_num', 0))) for c in filtered if float(c.get('chapter_num', 0)).is_integer())
    clean_chaps = []
    for c in filtered:
        num = float(c.get('chapter_num', 0))
        if num.is_integer() or int(num) not in int_nums:
            clean_chaps.append(c)
    clean_chaps.sort(key=lambda x: float(x.get('chapter_num', 0)))
    return clean_chaps

def fetch_chapter_images_universal(ch, slug):
    prov = ch.get('_provider', 'nettruyen')
    if prov == 'goctruyentranh':
        base_url = ch['_base_url']
        cid = ch.get('_comic_id')
        if not cid:
            return []
        try:
            post_hdrs = {'User-Agent': 'Mozilla/5.0', 'Referer': base_url + '/', 'X-Requested-With': 'XMLHttpRequest'}
            post_data = {'comicId': cid, 'chapterNumber': ch['chap_str'], 'nameEn': ch['_slug']}
            r = std_session.post(f"{base_url}/api/chapter/loadAll", data=post_data, headers=post_hdrs, timeout=20)
            if r.status_code == 200:
                imgs = r.json().get('result', {}).get('data') or []
                return [u.replace('/c/code', '/c/web') for u in imgs]
        except Exception:
            pass
        return []

    if prov == 'generic':
        ch_resp = http_get(ch['url'])
        if not ch_resp:
            return []
        img_tags = re.findall(r'<img[^>]+(?:data-original|data-sv1|data-lazy-src|data-src|src)=[\'"]([^\'"]+)[\'"][^>]*>', ch_resp.text, re.IGNORECASE)
        ordered = []
        seen = set()
        for img in img_tags:
            if any(bad in img.lower() for bad in ['/thumb/', 'logo', 'icon', 'avatar', 'banner', '.svg', '.gif', 'loading', 'ads']):
                continue
            if not re.search(r'\.(?:jpg|jpeg|png|webp)|/image/', img, re.I):
                continue
            if img.startswith('//'):
                img = 'https:' + img
            elif img.startswith('/'):
                img = ch['_base_url'] + img
            if img not in seen:
                seen.add(img)
                ordered.append(img)
        return ordered

    # Default: NetTruyen
    chap_url = f"https://nettruyenar.com/truyen-tranh/{slug}/{ch.get('chapter_slug')}/{ch.get('chapter_id')}"
    ch_resp = http_get(chap_url)
    if not ch_resp:
        return []
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
    return ordered_imgs

def get_github_release_ctx():
    token = os.environ.get('GITHUB_TOKEN', '').strip()
    if not token and os.path.exists('.gh_token'):
        with open('.gh_token', 'r', encoding='utf-8') as tf:
            token = tf.read().strip()
    release_id = '453912919'
    repo = 'KonKuKon/xteink-comic-sync'
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    existing = {}
    try:
        r = std_session.get(f'https://api.github.com/repos/{repo}/releases/{release_id}/assets', headers=headers, timeout=20)
        if r.status_code == 200:
            for a in r.json():
                existing[a['name']] = {'id': a['id'], 'size': a['size']}
    except Exception as e:
        print(f"Lỗi kiểm tra assets cũ: {e}")
    return token, release_id, repo, headers, existing

def upload_single_asset(fpath, fn, token, release_id, repo, headers, existing_assets):
    if fn in existing_assets:
        try:
            std_session.delete(f"https://api.github.com/repos/{repo}/releases/assets/{existing_assets[fn]['id']}", headers=headers, timeout=15)
        except Exception:
            pass
    size_mb = os.path.getsize(fpath) / 1048576
    print(f"  -> Đang tải lên GitHub: {fn} ({size_mb:.1f} MB)...")
    content_type = 'application/gzip' if fn.endswith('.tar.gz') else 'application/x-sh'
    up_headers = {
        'Authorization': f'token {token}',
        'Content-Type': content_type
    }
    with open(fpath, 'rb') as f_data:
        up_url = f'https://uploads.github.com/repos/{repo}/releases/{release_id}/assets?name={fn}'
        try:
            up_resp = std_session.post(up_url, headers=up_headers, data=f_data.read(), timeout=180)
            if up_resp.status_code in [200, 201]:
                print(f"  -> Tải lên thành công: {fn}")
                if fn.endswith('.tar.gz') and os.path.exists(fpath):
                    os.remove(fpath)
                    print(f"  -> Đã xóa file tạm {fn}")
                return True
            else:
                print(f"  -> Thất bại: status={up_resp.status_code}")
        except Exception as e:
            print(f"  -> Lỗi tải lên {fn}: {e}")
    return False

def process():
    comic_list = parse_comics_txt()
    print(f"Loaded {len(comic_list)} comic entries to process.")

    token, release_id, repo, gh_headers, existing_assets = get_github_release_ctx()
    state_file = 'sync_state.json'
    state = {}
    if os.path.exists(state_file):
        try:
            with open(state_file, 'r', encoding='utf-8') as sf:
                state = json.load(sf)
        except Exception:
            state = {}

    synced_archives = []

    for idx, item in enumerate(comic_list, 1):
        target = item['url']
        from_chap = item['from_chap']
        to_chap = item['to_chap']

        lower_t = target.lower()
        referer = None
        if 'goctruyentranh' in lower_t:
            slug, title, chapters, referer = get_goctruyentranh_comic(target, from_chap, to_chap)
            comic_id = chapters[0].get('_comic_id') if chapters else 'GTT'
        elif lower_t.startswith('http') and 'nettruyen' not in lower_t:
            slug, title, chapters, referer = get_truyenqq_or_generic_comic(target, from_chap, to_chap)
            comic_id = 'WEB'
        else:
            slug, comic_id, title, full_url = get_comic_meta(target)
            if not slug or not comic_id:
                print(f"[{idx}] Error resolving slug/comic_id for {target}")
                continue
            chapters = fetch_chapters_via_api(slug, comic_id, from_chap, to_chap)
            referer = HEADERS['Referer']

        folder = FOLDER_MAPPING.get(slug)
        if not folder:
            parts = [p.capitalize() for p in slug.replace('_', '-').split('-') if p]
            folder = f"{idx:02d}_{'_'.join(parts)}"

        print(f"\n==========================================")
        print(f"[{idx}/{len(comic_list)}] {title}")
        print(f"  Slug: {slug} | SourceID: {comic_id} | Range: {from_chap} -> {to_chap}")
        print(f"  Target Folder: {folder}")
        print(f"  Found {len(chapters)} chapters: {[c.get('chapter_num') for c in chapters[:5]]}{'...' if len(chapters) > 5 else ''}")
        if not chapters:
            continue

        tar_filename = f"{folder}.tar.gz"
        max_ch_val = str(chapters[-1].get('chapter_num'))
        prev_st = state.get(folder, {})
        if prev_st.get('max_chap') == max_ch_val and str(prev_st.get('from_chap')) == str(from_chap) and tar_filename in existing_assets:
            print(f"  [SKIP] Đã có bản mới nhất trên GitHub (chap {max_ch_val}), bỏ qua tải lại.")
            synced_archives.append((folder, title, tar_filename, existing_assets[tar_filename]['size']))
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

            ordered_imgs = fetch_chapter_images_universal(ch, slug)

            if not ordered_imgs:
                print(f"    {chap_clean}: No images found.")
                continue

            dl_args = []
            for p_idx, u in enumerate(ordered_imgs, 1):
                dest_file = os.path.join(chap_dir, f"{p_idx:03d}.jpg")
                dl_args.append((u, dest_file, referer))

            with ThreadPoolExecutor(max_workers=2) as pool:
                results = list(pool.map(download_file, dl_args))

            success_cnt = sum(1 for r in results if r)
            print(f"    {chap_clean}: Downloaded {success_cnt}/{len(ordered_imgs)} pages.")
            gc.collect()

        # Pack archive for this comic
        staging_dir = os.path.join("staging", folder)
        if os.path.exists(staging_dir) and os.listdir(staging_dir):
            tar_path = os.path.join(DIST_DIR, tar_filename)
            with tarfile.open(tar_path, "w:gz", compresslevel=1) as tar:
                tar.add(staging_dir, arcname=folder)

            size_bytes = os.path.getsize(tar_path)
            size_mb = size_bytes / (1024 * 1024)
            print(f"  ==> Created archive: {tar_path} ({size_mb:.2f} MB, {size_bytes} bytes)")
            shutil.rmtree(staging_dir, ignore_errors=True)
            if upload_single_asset(tar_path, tar_filename, token, release_id, repo, gh_headers, existing_assets):
                state[folder] = {'max_chap': max_ch_val, 'from_chap': str(from_chap)}
                with open(state_file, 'w', encoding='utf-8') as sf:
                    json.dump(state, sf, indent=2)
            synced_archives.append((folder, title, tar_filename, size_bytes))
            gc.collect()
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

    # Upload xteink_cloud_sync.sh only if we have at least 1 comic
    if total_archives > 0:
        upload_single_asset(sh_path, "xteink_cloud_sync.sh", token, release_id, repo, gh_headers, existing_assets)
    else:
        print("Warning: 0 comics synced, skipping xteink_cloud_sync.sh upload to preserve existing feed.")
    shutil.rmtree('staging', ignore_errors=True)
    print("--- HOÀN TẤT ĐỒNG BỘ VÀ ĐẨY LÊN GITHUB RELEASE ---\n")

if __name__ == '__main__':
    process()
