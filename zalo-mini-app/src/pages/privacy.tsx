import React from "react";
import { Page, Box, Text } from "zmp-ui";

export default function PrivacyPage() {
  return (
    <Page>
      <Box style={{ padding: 16 }}>
        <Text size="xLarge" bold style={{ marginBottom: 16 }}>Chính sách bảo mật</Text>
        <Text size="small" style={{ lineHeight: 1.6, color: "#ccc" }}>
          {`MY JARVIS ("ứng dụng") cam kết bảo vệ quyền riêng tư của bạn.

1. Dữ liệu thu thập
- Thông tin Zalo: tên, ảnh đại diện (qua Zalo OAuth)
- Tin nhắn: nội dung chat với AI assistant
- Tasks, lịch, chi tiêu: dữ liệu bạn tự tạo
- Voice: audio ghi âm chỉ được xử lý tạm thời, không lưu trữ

2. Mục đích sử dụng
- Cung cấp dịch vụ trợ lý AI cá nhân
- Cá nhân hóa trải nghiệm (ghi nhớ sở thích)
- Gửi thông báo proactive (nhắc deadline, briefing)

3. Bảo mật
- Dữ liệu mã hóa khi truyền tải (HTTPS/TLS)
- Mật khẩu hash bằng bcrypt
- Token JWT có thời hạn

4. Chia sẻ dữ liệu
- KHÔNG chia sẻ dữ liệu cá nhân với bên thứ ba
- Chỉ gửi nội dung chat đến AI provider (Google Gemini) để xử lý

5. Quyền của bạn
- Xóa tài khoản và toàn bộ dữ liệu bất cứ lúc nào
- Xem, xuất dữ liệu cá nhân
- Tắt/bật từng tính năng (voice, proactive, tools)

6. Liên hệ
- Email: support@pmai.space`}
        </Text>
      </Box>
    </Page>
  );
}
