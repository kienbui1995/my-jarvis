# MY JARVIS — Roadmap V8→V14: Trợ lý Toàn năng

> **Target**: Hoàn thành V8→V14 trong tháng 4/2026 (Apr 15-30)
> **Vision**: Từ chatbot → trợ lý toàn năng → platform
> **Reference**: Hermes Agent (NousResearch) — skills learning loop, MCP maturity, plugin hooks

---

## Timeline

```
Apr 15-16  V8:  Nền tảng Thông minh (5 modules)
Apr 17-19  V9:  Tài chính & Đời sống (9 modules)
Apr 20-22  V10: Kết nối Thế giới (10 modules)
Apr 23-24  V11: Sức khỏe & Phát triển (9 modules)
Apr 25-27  V12: Tự chủ Hoàn toàn (9 modules)
Apr 28-29  V13: Mobile & Voice-first (7 modules)
Apr 30     V14: Platform & Ecosystem (7 modules)
```

~56 modules trong 16 ngày. Consistent với velocity V3→V7 (49 modules / 14 ngày).

---

## V8.0.0 — Nền tảng Thông minh (Apr 15-16)

Làm agent thông minh hơn trước khi thêm features.

### Apr 15

| # | Module | Mô tả |
|---|--------|-------|
| M45 | Memory Consolidation | Wire `consolidation.py` vào ARQ worker, weekly cron job, compress + extract facts + cleanup |
| M46 | Memory Decay | `last_accessed` tracking, decay_factor field, low-importance cleanup |
| M47 | Skills Learning Loop | `Skill` + `SkillExecution` DB models, post-task skill extraction, trigger matching, self-improvement |

### Apr 16

| # | Module | Mô tả |
|---|--------|-------|
| M48 | Deep Research | Multi-step search graph: plan_searches → execute_parallel → verify → cross-check → cite with confidence |
| M49 | MCP Gateway | Proxy layer (sanitize, rate limit, SSRF, audit), curated registry (Google, GitHub, Notion), dynamic tool loader |
| M50 | Document Generation | Report/email/summary templates, markdown + PDF export |

**Milestone**: Agent biết học, biết nghiên cứu sâu, kết nối external tools.

---

## V9.0.0 — Tài chính & Đời sống (Apr 17-19)

Quản lý tiền bạc và cuộc sống hàng ngày.

### Apr 17

| # | Module | Mô tả |
|---|--------|-------|
| M51 | Receipt OCR | Chụp hóa đơn → Gemini vision → auto-categorize → log expense |
| M52 | Financial Dashboard | Tổng quan chi tiêu, xu hướng, so sánh tháng, budget alerts |
| M53 | Bill Reminders | Recurring bills (điện, nước, internet, thuê nhà), auto-remind |
| M54 | Subscription Tracker | Track Netflix, Spotify, gym... nhắc hết hạn, tổng chi phí subscriptions |

### Apr 18

| # | Module | Mô tả |
|---|--------|-------|
| M55 | Contact CRM | Quản lý quan hệ: ai, gặp khi nào, thích gì, relationship context |
| M56 | Birthday/Anniversary | Auto-remind + gợi ý quà dựa trên preferences + budget |

### Apr 19

| # | Module | Mô tả |
|---|--------|-------|
| M57 | Document Vault | Lưu CCCD, passport, bảo hiểm, hợp đồng — encrypted MinIO, quick retrieve |
| M58 | Travel Planner | Trip planning: flights, hotels, itinerary, packing list, budget estimate |
| M59 | Shopping Lists | Shared lists, recurring items, location-aware reminders |

**Milestone**: Jarvis quản lý tiền, nhắc deadline, hiểu quan hệ xã hội, giữ giấy tờ.

---

## V10.0.0 — Kết nối Thế giới (Apr 20-22)

Tích hợp services bên ngoài qua MCP + APIs.

### Apr 20

| # | Module | Mô tả |
|---|--------|-------|
| M60 | Notion Sync | 2-way sync tasks/notes qua MCP server |
| M61 | GitHub Integration | PR reviews, issue tracking, code search qua MCP |
| M62 | Spotify/Music | Play, pause, recommend, create playlists |
| M63 | Restaurant Finder | Google Maps/Foursquare, Vietnamese reviews, nearby suggestions |

### Apr 21

| # | Module | Mô tả |
|---|--------|-------|
| M64 | E-commerce Tracking | Track đơn Shopee/Lazada/Tiki — status, delivery date |
| M65 | Traffic & Navigation | Google Maps traffic, gợi ý giờ đi, route alternatives |
| M66 | Grab Integration | Estimate fare, booking history, frequent routes |

### Apr 22

| # | Module | Mô tả |
|---|--------|-------|
| M67 | Home Assistant | IoT control qua HA API: đèn, điều hòa, camera, scenes |
| M68 | Vietnamese Banking | Transaction notification parsing (SMS/email), balance overview |
| M69 | ZaloPay/MoMo | Transaction parsing, spending by category |

**Milestone**: Jarvis là hub trung tâm kết nối mọi service.

---

## V11.0.0 — Sức khỏe & Phát triển (Apr 23-24)

Chăm sóc sức khỏe và học tập.

### Apr 23

| # | Module | Mô tả |
|---|--------|-------|
| M70 | Health Tracking | Log sleep, exercise, water, mood — trend analysis, weekly report |
| M71 | Medication Reminders | Nhắc uống thuốc, tái khám, theo dõi triệu chứng |
| M72 | Spaced Repetition | Flashcards SM-2 algorithm, tiếng Anh, kiến thức chuyên môn |
| M73 | Book Notes | Tóm tắt sách, extract highlights, connect to knowledge graph |

### Apr 24

| # | Module | Mô tả |
|---|--------|-------|
| M74 | Daily Reflection | Cuối ngày: hôm nay thế nào? → mood tracking + pattern insights |
| M75 | Fitness Coach | Gợi ý bài tập, track progress, workout plans |
| M76 | Nutrition VN | Calories thức ăn Việt (phở, bún bò, cơm tấm...), daily intake |
| M77 | Meditation Timer | Guided breathing, meditation sessions, streak tracking |
| M78 | Screen Time | Nhắc nghỉ mắt, đứng dậy, Pomodoro timer |

**Milestone**: Jarvis chăm sóc sức khỏe thể chất + tinh thần + trí tuệ.

---

## V12.0.0 — Tự chủ Hoàn toàn (Apr 25-27)

JARVIS thực sự — proactive, autonomous, context-aware.

### Apr 25

| # | Module | Mô tả |
|---|--------|-------|
| M79 | Context Awareness | Location (GPS), activity (calendar), mood (pattern) inference |
| M80 | Cross-domain Reasoning | Signal graph: "họp sáng + traffic + ngủ muộn → nhắc dậy sớm" |

### Apr 26

| # | Module | Mô tả |
|---|--------|-------|
| M81 | Autonomous Multi-day | Tasks kéo dài nhiều ngày: research project, trip planning |
| M82 | Proactive Patterns | Phát hiện: "3 tuần vượt budget → cảnh báo + gợi ý cắt giảm" |
| M83 | Life Dashboard | Tổng quan: tài chính, sức khỏe, công việc, quan hệ, mục tiêu |
| M84 | Weekly Digest | Auto-generate weekly summary gửi qua preferred channel |

### Apr 27

| # | Module | Mô tả |
|---|--------|-------|
| M85 | Digital Twin | Đại diện user: trả lời email routine, schedule meetings, decline invitations |
| M86 | Goal System | OKR cá nhân: set goals → track → weekly review → adjust |
| M87 | Decision Journal | Log quyết định → review outcomes → learn patterns |
| M88 | Predictive Scheduling | Dựa trên patterns: auto-block calendar, suggest optimal times |

**Milestone**: Jarvis chủ động hành động, hiểu context đa chiều, đại diện user.

---

## V13.0.0 — Mobile & Voice-first (Apr 28-29)

Trong túi 24/7.

### Apr 28

| # | Module | Mô tả |
|---|--------|-------|
| M89 | React Native App | Expo managed, auth + chat + voice screen |
| M90 | Widgets | Home screen: weather, tasks, spending, next event |
| M91 | Push Notifications | Native push thay vì chỉ channel messages |
| M92 | Offline Cache | Cache tasks, calendar, contacts — sync khi có mạng |

### Apr 29

| # | Module | Mô tả |
|---|--------|-------|
| M93 | Always-on Voice | Wake word "Hey Jarvis" → continuous listening |
| M94 | Location Triggers | Đến công ty → tasks. Đến siêu thị → shopping list |
| M95 | Biometric Auth | FaceID/fingerprint |

**Milestone**: Jarvis trong túi, luôn sẵn sàng, voice-first.

---

## V14.0.0 — Platform & Ecosystem (Apr 30)

Từ product → platform. **Split: Community + Enterprise.**

### Community (open source)

| # | Module | Mô tả |
|---|--------|-------|
| M96 | VN Gov Services | Tra cứu BHXH, thuế, đăng ký xe, lịch tiêm |
| M97 | AI Financial Advisor | Phân tích chi tiêu cá nhân → gợi ý tiết kiệm/đầu tư |

### Enterprise (proprietary — separate repo/package)

| # | Module | Mô tả |
|---|--------|-------|
| E1 | Multi-tenant / Teams | Team workspaces, shared calendar, tasks, expenses |
| E2 | RBAC | Role-based access: admin, manager, member |
| E3 | SSO | SAML 2.0, OIDC (Google Workspace, Azure AD) |
| E4 | Admin Dashboard | User management, usage analytics, cost control |
| E5 | White-label API | Businesses embed Jarvis engine cho chatbot riêng |
| E6 | Automation Builder | Visual workflow: IF trigger THEN action (no-code) |
| E7 | Agent-to-Agent | Inter-org communication protocol |
| E8 | Skill Marketplace | Enterprise approval workflow for shared skills |
| E9 | Compliance | Data retention, audit export, GDPR |

**Milestone**: Community = trợ lý cá nhân hoàn chỉnh. Enterprise = nền tảng cho doanh nghiệp.

---

## Nguyên tắc phát triển

1. **MCP-first** — Dùng MCP servers có sẵn, tự build cho VN services
2. **Skills > Hard-coded** — Feature mới = skill agent có thể học
3. **Proactive > Reactive** — Mỗi module có trigger trong Proactive Engine
4. **Vietnamese context** — VND, VN banks, Shopee/Lazada, Grab, lunar calendar
5. **Privacy-first** — Vault encrypted, health data local, financial data never shared
6. **Architecture-first** — 30 phút design mỗi sáng, rồi vibe code liên tục
7. **Batch migrations** — 1 migration per phase
8. **Skip polish** — Ship working, polish sau

## Risk Flags

| Module | Risk | Mitigation |
|--------|------|-----------|
| Cross-domain Reasoning | Signal graph design | Design trước, implement sau |
| React Native | Toolchain setup | Expo managed, skip native modules |
| Vietnamese Banking | No public API | SMS/email transaction parsing first |
| Agent-to-Agent | Protocol design | MVP: shared calendar invite qua email |
| Offline Mode | Sync conflicts | Server always wins |

---

## DB Models mới (ước tính)

| Phase | Models |
|-------|--------|
| V8 | Skill, SkillExecution |
| V9 | Contact, ContactInteraction, Document, BillReminder, Subscription, TripPlan, ShoppingList, ShoppingItem |
| V10 | Integration, IntegrationSync |
| V11 | HealthLog, MedicationReminder, Flashcard, FlashcardReview, BookNote, MeditationSession |
| V12 | LocationContext, LifeGoal, GoalCheckIn, Decision, WeeklyDigest, PredictivePattern |
| V13 | PushToken, OfflineQueue |
| V14 | Family, FamilyMember, MarketplaceSkill, AutomationWorkflow |

---

*Created: 2026-04-15. Scope: V8.0.0 → V14.0.0 (M45→M102, 58 modules)*
*Previous: V1→V7 = M1→M44 (44 modules, Jan-Mar 2026)*
