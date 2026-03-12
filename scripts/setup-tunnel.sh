#!/usr/bin/env bash
# Setup Cloudflare Tunnel for MY JARVIS
# Usage: ./scripts/setup-tunnel.sh
set -euo pipefail

DOMAIN="jarvis.pmai.space"

echo "🚀 MY JARVIS — Cloudflare Tunnel Setup"
echo "========================================"
echo ""
echo "Bước 1: Tạo tunnel trên Cloudflare Dashboard"
echo "  1. Vào https://one.dash.cloudflare.com → Networks → Tunnels"
echo "  2. Click 'Create a tunnel' → chọn 'Cloudflared'"
echo "  3. Đặt tên: my-jarvis"
echo "  4. Copy TUNNEL TOKEN (chuỗi dài bắt đầu bằng eyJ...)"
echo ""
read -rp "Paste Tunnel Token: " TUNNEL_TOKEN

if [[ -z "$TUNNEL_TOKEN" ]]; then
  echo "❌ Token không được để trống"
  exit 1
fi

echo ""
echo "Bước 2: Cấu hình Public Hostname trên Dashboard"
echo "  Thêm 2 hostname sau trong tab 'Public Hostname':"
echo ""
echo "  ┌─────────────────────────────────────────────────────┐"
echo "  │ Hostname: ${DOMAIN}                                 │"
echo "  │ Path:     /api                                      │"
echo "  │ Service:  HTTP://backend:8000                       │"
echo "  │ ⚙ Additional settings → HTTP Settings:              │"
echo "  │   ✓ WebSockets = ON                                 │"
echo "  ├─────────────────────────────────────────────────────┤"
echo "  │ Hostname: ${DOMAIN}                                 │"
echo "  │ Path:     (để trống)                                │"
echo "  │ Service:  HTTP://frontend:3000                      │"
echo "  └─────────────────────────────────────────────────────┘"
echo ""
echo "  ⚠ Thêm rule /api TRƯỚC rule catch-all (kéo lên trên)"
echo ""
read -rp "Đã cấu hình xong? (y/N): " CONFIRMED
if [[ "$CONFIRMED" != "y" && "$CONFIRMED" != "Y" ]]; then
  echo "Hãy cấu hình xong rồi chạy lại script."
  exit 0
fi

# Update .env
echo ""
echo "Bước 3: Cập nhật .env..."

# Set tunnel token
if grep -q "^CLOUDFLARE_TUNNEL_TOKEN=" .env 2>/dev/null; then
  sed -i "s|^CLOUDFLARE_TUNNEL_TOKEN=.*|CLOUDFLARE_TUNNEL_TOKEN=${TUNNEL_TOKEN}|" .env
else
  echo "" >> .env
  echo "# Cloudflare Tunnel" >> .env
  echo "CLOUDFLARE_TUNNEL_TOKEN=${TUNNEL_TOKEN}" >> .env
fi

# Set production URLs
if grep -q "^NEXT_PUBLIC_API_URL=" .env 2>/dev/null; then
  sed -i "s|^NEXT_PUBLIC_API_URL=.*|NEXT_PUBLIC_API_URL=https://${DOMAIN}/api/v1|" .env
else
  echo "NEXT_PUBLIC_API_URL=https://${DOMAIN}/api/v1" >> .env
fi

if grep -q "^NEXT_PUBLIC_WS_URL=" .env 2>/dev/null; then
  sed -i "s|^NEXT_PUBLIC_WS_URL=.*|NEXT_PUBLIC_WS_URL=wss://${DOMAIN}/api/v1/ws/chat|" .env
else
  echo "NEXT_PUBLIC_WS_URL=wss://${DOMAIN}/api/v1/ws/chat" >> .env
fi

sed -i "s|^DOMAIN=.*|DOMAIN=${DOMAIN}|" .env
sed -i "s|^DEBUG=.*|DEBUG=false|" .env 2>/dev/null || echo "DEBUG=false" >> .env

echo "✅ .env updated"

# Restart with tunnel
echo ""
echo "Bước 4: Khởi động tunnel..."
docker compose --profile tunnel up -d cloudflared
echo ""
echo "✅ Tunnel đang chạy!"
echo ""
echo "Bước 5: Restart frontend để nhận env mới..."
docker compose up -d --force-recreate frontend
echo ""
echo "🎉 Done! Truy cập: https://${DOMAIN}"
echo ""
echo "📋 Checklist:"
echo "  - [ ] Thêm https://${DOMAIN} vào Google Console Authorized Origins"
echo "  - [ ] Test: https://${DOMAIN} (frontend)"
echo "  - [ ] Test: https://${DOMAIN}/api/v1/health (backend)"
echo "  - [ ] Test: WebSocket chat"
