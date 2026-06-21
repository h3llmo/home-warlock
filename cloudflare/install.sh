#!/usr/bin/env bash
set -e

echo "=== Installation Cloudflare Tunnel ==="

curl -fsSL --output /tmp/cloudflared.deb \
  https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
sudo dpkg -i /tmp/cloudflared.deb

echo "Authentification Cloudflare..."
cloudflared tunnel login

echo "Création du tunnel energy-dashboard..."
cloudflared tunnel create energy-dashboard

echo ""
echo "Copie config.yml.example → config.yml et remplace <TUNNEL_ID> par l'ID affiché ci-dessus."
echo "Puis : sudo cloudflared service install"
