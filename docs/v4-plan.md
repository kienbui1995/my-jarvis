# MY JARVIS V4 — Product Experience Layer

> **Status:** 📋 Plan
> **Date:** 2026-03-12
> **Goal:** Biến JARVIS từ "architecture tốt" thành "product wow" — đóng gap Must-be vs đối thủ

---

## 1. Tại sao cần V4

V3 hoàn thành Intelligence Layer (11 modules) nhưng competitive analysis cho thấy:

| Dimension | V3 Score | Gap |
|---|---|---|
| Architecture | 8/10 | ✅ Ahead of most |
| Product Experience | 5/10 | ❌ Thiếu mobile, deep integrations, proactive |
| Market Position | Unique nhưng fragile | ⚠️ Moat chỉ là Vietnamese + Zalo |

Kano insight: **V3 mạnh Delighter (memory, preferences) nhưng thiếu Must-be (mobile, integrations).** User không thấy wow nếu không dùng được trên điện thoại.

### Đối thủ đã có gì V4 cần đuổi

- Lindy: 400K users, $50/mo, 50+ integrations, event-driven proactive
- Manus: Meta $2B acquisition, autonomous browse/code/deploy
- Viktor: 3000+ integrations, weeks-long context, Slack/Teams native
- ChatGPT: 300M users, advanced voice, mobile app, plugin ecosystem

---

## 2. V4 Modules — RICE Prioritized

### Scoring: RICE = (Reach × Impact × Confidence) / Effort

| # | Module | R | I | C | E | RICE | Priority |
|---|---|---|---|---|---|---|---|
| M12 | Advanced Voice (Whisper STT + Cloud TTS) | 9 | 9 | 9 | 3 | **243** | P0 |
| M13 | Zalo Mini App | 10 | 10 | 8 | 8 | **100** | P0 |
| M14 | Event-driven Proactive Engine | 6 | 7 | 8 | 4 | **84** | P1 |
| M15 | Vietnamese Service Integrations | 7 | 8 | 7 | 5 | **78** | P1 |
| M16 | Auto-TTS (speak responses automatically) | 8 | 6 | 9 | 2 | **216** | P1 |
| M17 | File & Image Understanding | 5 | 7 | 8 | 4 | **70** | P2 |
| M18 | Browser Automation | 4 | 6 | 6 | 7 | **21** | P2 |

---

## 3. Module Specs

### M12: Advanced Voice Pipeline (P0)

**Problem:** Web Speech API quality thấp, không hoạt động offline, không có trên Zalo.

**Solution:**
```
User Voice → Backend STT (Whisper/Viettel AI) → Text → Agent → Response → Cloud TTS → Audio stream
```

**Components:**
- `backend/voice/stt.py` — Whisper v3 large (self-hosted) hoặc Viettel AI STT API
- `backend/voice/tts.py` — Google Cloud TTS (vi-VN-Wavenet) hoặc Viettel AI TTS
- `backend/api/v1/voice.py` — POST /voice/transcribe (audio → text), GET /voice/speak (text → audio stream)
- `frontend/lib/hooks/use-voice.ts` — Upgrade: record audio blob → send to backend → play response audio

**Acceptance Criteria:**
- STT accuracy ≥ 90% cho tiếng Việt conversational
- TTS latency < 500ms first byte
- Streaming audio playback (không đợi full response)
- Fallback to Web Speech API nếu backend unavailable

**Effort:** 3 sprints

---

### M13: Zalo Mini App (P0)

**Problem:** 73M smartphone users VN, mobile-first. Web-only = mất 80% TAM.

**Solution:** Zalo Mini App (ZMP framework) — native-like experience trong Zalo app.

**Components:**
- `zalo-mini-app/` — ZMP project (React-based)
  - Chat interface (voice-first)
  - Task list view
  - Calendar view
  - Quick actions (expense log, reminders)
- `backend/channels/zalo_mini_app.py` — ZMP auth + API adapter
- Deep link: `zalo://miniapp/{app_id}`

**Acceptance Criteria:**
- Chat + voice input hoạt động trong Zalo app
- Push notifications qua Zalo
- < 3s initial load
- Offline: show cached conversations

**Effort:** 8 sprints

---

### M14: Event-driven Proactive Engine (P1)

**Problem:** V3 chỉ có cron (morning briefing). Đối thủ có real-time triggers.

**Solution:** Event bus + trigger rules engine.

**Components:**
- `backend/services/event_bus.py` — Redis Streams event bus
- `backend/services/triggers.py` — Rule engine: condition → action
- `backend/api/v1/triggers.py` — CRUD trigger rules

**Built-in Triggers:**
```
- deadline_approaching: Task due trong 2h → nhắc qua Zalo
- budget_exceeded: Chi tiêu vượt ngưỡng → cảnh báo
- calendar_conflict: 2 events trùng giờ → hỏi user
- memory_insight: Phát hiện pattern → gợi ý proactive
- morning_briefing: 7:00 AM → tóm tắt ngày (existing, migrate)
```

**Effort:** 4 sprints

---

### M15: Vietnamese Service Integrations (P1)

**Problem:** 13 tools hiện tại là generic. Thiếu integrations đặc thù VN.

**New Tools (priority order):**

| Tool | Integration | Use case |
|---|---|---|
| `google_calendar_sync` | Google Calendar API | 2-way sync events |
| `gmail_read` | Gmail API | Đọc/tóm tắt email |
| `gmail_send` | Gmail API | Gửi email |
| `momo_check` | MoMo API | Check số dư, lịch sử GD |
| `bank_balance` | VN banking open API | Check tài khoản |
| `grab_order` | Grab API | Đặt xe, đồ ăn |
| `weather_vn` | OpenWeather | Thời tiết theo tỉnh/thành |
| `news_vn` | VnExpress/Tuổi Trẻ RSS | Tin tức Việt Nam |

**Effort:** 5 sprints (2 tools/sprint)

---

### M16: Auto-TTS Response (P1)

**Problem:** User phải bấm 🔊 để nghe. Voice-first experience cần auto-speak.

**Solution:**
- User preference: `auto_tts: bool` (default false)
- Khi enabled: AI response tự động stream audio
- Voice mode toggle trong chat UI (icon headphones)
- Khi voice mode ON: auto-listen sau khi TTS xong → hands-free conversation loop

**Effort:** 2 sprints (depends on M12)

---

### M17: File & Image Understanding (P2)

**Problem:** Không xử lý được file/ảnh. User gửi hóa đơn, receipt, screenshot → JARVIS không hiểu.

**Solution:**
- `backend/voice/vision.py` — Gemini 2.0 Flash vision API
- Upload via MinIO → extract text/data → feed to agent
- Use cases: OCR hóa đơn → auto expense_log, đọc screenshot, analyze documents

**Effort:** 4 sprints

---

### M18: Browser Automation (P2)

**Problem:** Manus có thể browse web, fill forms, deploy code. JARVIS chỉ có web_search.

**Solution:**
- `backend/tools/browser.py` — Playwright-based browser tool
- Sandboxed execution (Docker container per session)
- Actions: navigate, click, fill, screenshot, extract

**Effort:** 7 sprints

---

## 4. Roadmap

```
2026 Q2 (Apr-Jun)                    2026 Q3 (Jul-Sep)
┌─────────────────────────┐          ┌─────────────────────────┐
│ Sprint 1-3: M12 Voice   │          │ Sprint 7-10: M13 Zalo   │
│ Sprint 4-5: M16 AutoTTS │          │   Mini App (cont.)      │
│ Sprint 6: M14 Proactive │          │ Sprint 11-12: M15 VN    │
│   Engine (start)        │          │   Integrations (cont.)  │
└─────────────────────────┘          └─────────────────────────┘

2026 Q4 (Oct-Dec)
┌─────────────────────────┐
│ Sprint 13-16: M17 Vision│
│ Sprint 17+: M18 Browser │
│ + Polish + Launch       │
└─────────────────────────┘
```

### Milestones

| Date | Milestone | Success Metric |
|---|---|---|
| 2026-05 | V4-alpha: Voice pipeline live | STT ≥90% accuracy, TTS <500ms |
| 2026-06 | V4-beta: Proactive + AutoTTS | 5 trigger types active |
| 2026-08 | V4-rc: Zalo Mini App beta | 100 beta users on Zalo |
| 2026-10 | V4-ga: Full integrations | 20+ tools, 8 VN services |
| 2026-12 | V4.1: Vision + Browser | Feature parity with Manus basic |

---

## 5. Success Metrics

| Metric | V3 Baseline | V4 Target |
|---|---|---|
| DAU | 0 | 500 |
| Voice usage rate | 0% | 40% |
| Mobile (Zalo) users | 0% | 60% of DAU |
| Proactive message open rate | N/A | 35% |
| Avg tools/session | ~2 | 4+ |
| User retention D7 | N/A | 40% |
| NPS | N/A | 50+ |

---

## 6. Risks

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Zalo Mini App approval delay | High | High | Submit early, have Telegram bot as fallback |
| Whisper self-host cost (GPU) | Medium | Medium | Start with Viettel AI STT API, migrate later |
| MoMo/Bank API access | High | Medium | Start with read-only, manual auth flow |
| Voice latency > 1s | Medium | High | Edge TTS cache, streaming, pre-warm |
| Zalo builds competing AI | Low | Critical | Move fast, build user lock-in via memory + preferences |

---

## 7. Dependencies

```
M12 (Voice) ──→ M16 (AutoTTS) ──→ M13 (Zalo Mini App voice)
                                         │
M14 (Proactive) ─────────────────────────┘
M15 (VN Integrations) ── independent
M17 (Vision) ── independent
M18 (Browser) ── independent
```

Critical path: **M12 → M16 → M13 voice integration**
