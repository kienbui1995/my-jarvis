# Hướng dẫn tích hợp Zalo — MY JARVIS

## Tổng quan 3 hình thức

| Hình thức | Mô tả | User experience |
|-----------|-------|-----------------|
| **Zalo OA** | Chat text qua Official Account | Follow OA → nhắn tin → JARVIS trả lời |
| **Zalo Chatbot** | Rich messages + menu + auto-greeting | Buttons, quick replies, persistent menu |
| **Zalo Mini App** | Full UI dashboard trong Zalo | Tasks, calendar, notifications — như web app |

---

## 1. Zalo OA + Chatbot Setup

### Bước 1: Tạo Zalo OA
1. Truy cập [oa.zalo.me](https://oa.zalo.me)
2. Đăng nhập bằng tài khoản Zalo cá nhân
3. Tạo OA mới → chọn loại "Dịch vụ" hoặc "Cửa hàng"
4. Điền thông tin: tên OA, mô tả, avatar, cover

### Bước 2: Tạo Zalo App (lấy API credentials)
1. Truy cập [developers.zalo.me](https://developers.zalo.me)
2. Tạo App mới → liên kết với OA vừa tạo
3. Lấy: **App ID**, **App Secret**, **OA Secret Key**
4. Tạo **OA Access Token** (có thời hạn, cần refresh)

### Bước 3: Config webhook
1. Trong Zalo App → Webhook → thêm URL:
   ```
   https://jarvis.pmai.space/api/v1/webhooks/zalo
   ```
2. Chọn events cần nhận:
   - `user_send_text` — tin nhắn text
   - `follow` — user follow OA
   - `user_submit_info` — user gửi thông tin

### Bước 4: Cập nhật .env
```env
ZALO_OA_ACCESS_TOKEN=your_oa_access_token
ZALO_OA_SECRET_KEY=your_oa_secret_key
```

### Bước 5: Set persistent menu (chạy 1 lần)
```python
# Trong Python shell hoặc startup script
from channels.zalo import ZaloAdapter
import asyncio
asyncio.run(ZaloAdapter().set_persistent_menu())
```

### Bước 6: Test
1. Mở Zalo → tìm OA → Follow
2. Nhận auto-greeting với quick replies
3. Nhắn "Tạo task mua sữa" → JARVIS tạo task + trả lời với suggestions

---

## 2. Zalo Mini App Setup

### Bước 1: Đăng ký Mini App
1. Truy cập [mini.zalo.me](https://mini.zalo.me)
2. Tạo Mini App mới → liên kết với Zalo App
3. Lấy **Mini App ID**

### Bước 2: Build & Deploy
```bash
cd zalo-mini-app
npm install
# Thay __API_URL__ trong src/api.ts bằng URL backend thật
npm run build
# Upload build output lên mini.zalo.me
```

### Bước 3: Config Zalo OAuth
1. Trong Zalo App → OAuth → thêm redirect URL
2. Backend cần endpoint `/api/v1/auth/zalo` để exchange Zalo token → JWT

### Bước 4: Submit review
1. Upload screenshots + mô tả
2. Zalo review trong 3-7 ngày làm việc
3. Sau khi approved → Mini App xuất hiện trong Zalo

---

## 3. Backend endpoint cần thêm cho Zalo OAuth

Thêm vào `api/v1/auth.py`:

```python
@router.post("/zalo")
async def zalo_login(req: ZaloLoginRequest, db: AsyncSession = Depends(get_db)):
    # 1. Verify Zalo access token → get Zalo user info
    # 2. Find or create user by zalo_id
    # 3. Return JWT
    ...
```

---

## Checklist go-live

### Zalo OA + Chatbot
- [ ] Zalo OA đã tạo và verified
- [ ] Zalo App đã tạo, liên kết OA
- [ ] Webhook URL: `https://jarvis.pmai.space/api/v1/webhooks/zalo`
- [ ] `ZALO_OA_ACCESS_TOKEN` và `ZALO_OA_SECRET_KEY` trong .env
- [ ] Persistent menu đã set
- [ ] Token refresh mechanism (OA token hết hạn sau 90 ngày)

### Zalo Bot Platform
- [ ] Tạo bot qua Zalo Bot Manager (tìm OA "Zalo Bot Manager" trong Zalo)
- [ ] Lấy Bot Token từ tin nhắn Zalo
- [ ] Set webhook: gọi API `setWebhook` với URL `https://jarvis.pmai.space/api/v1/webhooks/zalo-bot`
- [ ] `ZALO_BOT_TOKEN` và `ZALO_BOT_SECRET_TOKEN` trong .env
- [ ] Test: nhắn tin cho bot → nhận phản hồi từ JARVIS

### Zalo Mini App
- [ ] Mini App submitted và approved
- [ ] Zalo OAuth endpoint hoạt động

### Chung
- [ ] Backend deployed với HTTPS (Traefik + Let's Encrypt)
- [ ] Test: follow OA → greeting → chat → proactive notification
- [ ] Test: nhắn Zalo Bot → JARVIS trả lời
