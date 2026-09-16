#!/bin/bash
set -euo pipefail
export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y software-properties-common nginx ufw curl
add-apt-repository -y universe
apt-get update
# Ubuntu 20.04: Python 3.9 from universe (deadsnakes GPG often times out)
apt-get install -y python3.9 python3.9-venv python3.9-dev build-essential

ufw allow OpenSSH || true
ufw allow 80/tcp || true
ufw allow 443/tcp || true
yes | ufw enable || true

cd /opt/pecf09
python3.9 -m venv venv
export PIP_NO_CACHE_DIR=1
./venv/bin/pip install -U pip
./venv/bin/pip install -r requirements.txt

install -m 644 /opt/pecf09/deploy/nginx-pecf09.conf /etc/nginx/sites-available/pecf09
ln -sf /etc/nginx/sites-available/pecf09 /etc/nginx/sites-enabled/pecf09
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

install -m 644 /opt/pecf09/deploy/pecf09-web.service /etc/systemd/system/pecf09-web.service
install -m 644 /opt/pecf09/deploy/pecf09-bot.service /etc/systemd/system/pecf09-bot.service
systemctl daemon-reload
systemctl enable --now pecf09-web pecf09-bot
systemctl --no-pager --full status pecf09-web || true
systemctl --no-pager --full status pecf09-bot || true
curl -I http://127.0.0.1:5050/ || true
echo SETUP_DONE
