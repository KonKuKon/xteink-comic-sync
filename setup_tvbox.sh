#!/data/data/com.termux/files/usr/bin/bash
# ==============================================================================
# XTEINK COMIC SYNC - AUTO SETUP CHO TERMUX TRÊN FPT TV BOX
# ==============================================================================
set -e

echo "=== [1/5] Cập nhật gói phần mềm Termux ==="
pkg update -y || true
pkg install -y python git curl cronie openssh || true

echo "=== [2/5] Cài đặt thư viện Python (curl-cffi) ==="
pip install --upgrade pip || true
pip install curl-cffi || true

echo "=== [3/5] Tải bộ đồng bộ truyện XTEINK từ GitHub ==="
cd ~
if [ -d "xteink-comic-sync" ]; then
    echo "Đã có thư mục, cập nhật mới nhất..."
    cd xteink-comic-sync
    git reset --hard HEAD || true
    git pull origin main || true
else
    git clone https://github.com/KonKuKon/xteink-comic-sync.git ~/xteink-comic-sync
    cd ~/xteink-comic-sync
fi

echo "=== [4/5] Cấu hình tự động chạy mỗi ngày lúc 6:00 sáng ==="
CRON_CMD="0 6 * * * cd $HOME/xteink-comic-sync && git pull origin main && python sync_comics.py >> $HOME/sync_comics.log 2>&1"
(crontab -l 2>/dev/null | grep -v "sync_comics.py" || true; echo "$CRON_CMD") | crontab -

# Khởi động dịch vụ cron và ssh
pkill crond || true
crond
sshd || true

# Tự khởi động crond mỗi khi mở Termux
if ! grep -q "crond" ~/.bashrc 2>/dev/null; then
    echo "crond" >> ~/.bashrc
    echo "sshd" >> ~/.bashrc
fi

echo "=== [5/5] Chạy thử đồng bộ ngay bây giờ ==="
python sync_comics.py

echo ""
echo "=============================================================================="
echo "  THIẾT LẬP THÀNH CÔNG 100%! FPT TV BOX ĐÃ SẴN SÀNG LÀM MÁY CHỦ CÀO TRUYỆN!"
echo "  - Mỗi ngày đúng 6:00 sáng, TV Box sẽ tự kiểm tra comics.txt trên GitHub"
echo "  - Tự tải các chap mới, nén và đẩy thẳng lên GitHub Release"
echo "  - Đẩy xong sẽ tự dọn sạch bộ nhớ (chiếm 0 MB trên TV Box)"
echo "=============================================================================="
