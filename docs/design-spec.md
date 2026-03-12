# MY JARVIS — UI/UX Design Specification

> Tài liệu này mô tả chi tiết thiết kế giao diện cho MY JARVIS.
> Đủ chi tiết để designer hoặc AI có thể build trực tiếp từ spec này.

---

## 1. Brand Identity

### Personality
- **Thông minh nhưng gần gũi** — không phải robot lạnh lùng, mà là người bạn biết nhiều
- **Tối giản nhưng đầy đủ** — không rườm rà, mỗi pixel đều có mục đích
- **Đáng tin cậy** — dữ liệu rõ ràng, hành động minh bạch, user luôn kiểm soát

### Voice & Tone
- Tiếng Việt tự nhiên, không quá formal
- Dùng emoji vừa phải (1-2 per message, không spam)
- Ngắn gọn, đi thẳng vào vấn đề

### Logo Concept
- Chữ "J" cách điệu trong hình tròn, gradient xanh dương → tím
- Hoặc: icon robot tối giản (2 mắt tròn + antenna) trong khung tròn
- Favicon: chữ "J" trắng trên nền gradient

---

## 2. Design Principles

| # | Principle | Meaning |
|---|-----------|---------|
| 1 | **Chat-first** | Chat là trung tâm, mọi thứ khác là phụ trợ. 80% thời gian user ở chat. |
| 2 | **Glanceable** | Thông tin quan trọng nhìn 1 giây là hiểu. Dùng color, icon, spacing. |
| 3 | **Progressive disclosure** | Hiện ít trước, chi tiết khi cần. Không overwhelm user. |
| 4 | **Dark-first** | Dark mode là default (tiết kiệm pin, dễ nhìn lâu). Light mode là option. |
| 5 | **Mobile-ready** | Design cho mobile trước, scale lên desktop. Chat UI phải perfect trên phone. |

---

## 3. Design Tokens

### 3.1 Color Palette

```
── Background ──────────────────────────────
--bg-primary:      #0A0A0F      // Main background (near-black with blue tint)
--bg-secondary:    #12121A      // Cards, sidebar
--bg-tertiary:     #1A1A2E      // Input fields, hover states
--bg-elevated:     #222236      // Modals, dropdowns, tooltips

── Text ────────────────────────────────────
--text-primary:    #F0F0F5      // Main text (off-white, easier on eyes than pure white)
--text-secondary:  #8888A0      // Labels, timestamps, placeholders
--text-tertiary:   #555570      // Disabled text
--text-inverse:    #0A0A0F      // Text on light backgrounds

── Brand ───────────────────────────────────
--brand-primary:   #3B82F6      // Primary blue (buttons, links, active states)
--brand-hover:     #2563EB      // Blue hover
--brand-subtle:    #3B82F620    // Blue at 12% opacity (active sidebar item bg)
--brand-gradient:  linear-gradient(135deg, #3B82F6, #8B5CF6)  // Blue→Purple

── Accent ──────────────────────────────────
--accent-green:    #22C55E      // Success, done, online
--accent-yellow:   #EAB308      // Warning, in-progress, medium priority
--accent-red:      #EF4444      // Error, urgent, overdue
--accent-orange:   #F97316      // High priority
--accent-purple:   #8B5CF6      // AI/agent actions, memory

── Message Bubbles ─────────────────────────
--bubble-user:     #3B82F6      // User message background
--bubble-user-text:#FFFFFF      // User message text
--bubble-ai:       #1A1A2E      // AI message background
--bubble-ai-text:  #F0F0F5      // AI message text
--bubble-tool:     #8B5CF620    // Tool call result background (purple tint)

── Border ──────────────────────────────────
--border-default:  #27272A      // Default borders
--border-hover:    #3F3F50      // Hover borders
--border-focus:    #3B82F6      // Focus ring
```

### 3.2 Typography

```
── Font Family ─────────────────────────────
--font-sans:       'Inter', system-ui, -apple-system, sans-serif
--font-mono:       'JetBrains Mono', 'Fira Code', monospace

── Font Sizes ──────────────────────────────
--text-xs:         0.75rem   / 12px    line-height: 1rem
--text-sm:         0.875rem  / 14px    line-height: 1.25rem
--text-base:       1rem      / 16px    line-height: 1.5rem
--text-lg:         1.125rem  / 18px    line-height: 1.75rem
--text-xl:         1.25rem   / 20px    line-height: 1.75rem
--text-2xl:        1.5rem    / 24px    line-height: 2rem
--text-3xl:        1.875rem  / 30px    line-height: 2.25rem

── Font Weights ────────────────────────────
--font-normal:     400
--font-medium:     500
--font-semibold:   600
--font-bold:       700

── Usage ───────────────────────────────────
Page title:        text-2xl / semibold
Section header:    text-lg / semibold
Body text:         text-base / normal
Chat message:      text-base / normal (15px on mobile for readability)
Label:             text-sm / medium
Caption/timestamp: text-xs / normal / text-secondary
Code block:        text-sm / font-mono
```

### 3.3 Spacing Scale

```
--space-0:    0
--space-1:    0.25rem   / 4px
--space-2:    0.5rem    / 8px
--space-3:    0.75rem   / 12px
--space-4:    1rem      / 16px
--space-5:    1.25rem   / 20px
--space-6:    1.5rem    / 24px
--space-8:    2rem      / 32px
--space-10:   2.5rem    / 40px
--space-12:   3rem      / 48px
--space-16:   4rem      / 64px

── Common patterns ─────────────────────────
Page padding:          space-6 (desktop), space-4 (mobile)
Card padding:          space-4
Card gap:              space-3
Message gap:           space-3 (same sender), space-5 (different sender)
Sidebar item padding:  space-2 horizontal, space-2 vertical
Input padding:         space-3 horizontal, space-3 vertical
Button padding:        space-3 horizontal, space-2.5 vertical
```

### 3.4 Border Radius

```
--radius-sm:    0.375rem  / 6px     // Badges, small elements
--radius-md:    0.5rem    / 8px     // Buttons, inputs
--radius-lg:    0.75rem   / 12px    // Cards, modals
--radius-xl:    1rem      / 16px    // Large cards
--radius-full:  9999px              // Avatars, pills
--radius-bubble: 1.25rem  / 20px    // Message bubbles (rounded feel)
```

### 3.5 Shadows

```
--shadow-sm:    0 1px 2px rgba(0,0,0,0.3)
--shadow-md:    0 4px 12px rgba(0,0,0,0.4)
--shadow-lg:    0 8px 24px rgba(0,0,0,0.5)
--shadow-glow:  0 0 20px rgba(59,130,246,0.15)    // Blue glow for focus/active
```

### 3.6 Transitions

```
--transition-fast:    150ms ease
--transition-normal:  200ms ease
--transition-slow:    300ms ease
--transition-spring:  300ms cubic-bezier(0.34, 1.56, 0.64, 1)  // Bouncy feel
```

### 3.7 Z-Index Scale

```
--z-base:       0
--z-dropdown:   10
--z-sticky:     20
--z-overlay:    30
--z-modal:      40
--z-toast:      50
```

---

## 4. Component Library

### 4.1 Button

```
Variants:
┌─────────────────────────────────────────────────────────────┐
│ primary   │ bg: brand-primary, text: white, hover: brand-hover │
│ secondary │ bg: bg-tertiary, text: text-primary, hover: bg-elevated │
│ ghost     │ bg: transparent, text: text-secondary, hover: bg-tertiary │
│ danger    │ bg: accent-red, text: white, hover: #DC2626 │
└─────────────────────────────────────────────────────────────┘

Sizes:
┌──────────────────────────────────────────┐
│ sm │ text-sm, py-1.5, px-3, radius-md    │
│ md │ text-base, py-2.5, px-4, radius-md  │ ← default
│ lg │ text-lg, py-3, px-6, radius-md      │
│ icon │ p-2, radius-md, square            │
└──────────────────────────────────────────┘

States: default → hover (lighten bg) → active (darken bg) → disabled (opacity 50%, no pointer)
Loading: spinner icon replaces text, same width to prevent layout shift
```

### 4.2 Input

```
┌──────────────────────────────────────────────────────────────┐
│  🔍  Placeholder text...                                     │
└──────────────────────────────────────────────────────────────┘

bg: bg-tertiary
border: 1px solid border-default
border-focus: 1px solid border-focus + shadow-glow
text: text-primary
placeholder: text-secondary
padding: space-3
radius: radius-md
font: text-base

Variants:
- default: single line
- textarea: multi-line, auto-resize, max 6 rows
- search: left icon (magnifying glass), right clear button

Error state: border-color: accent-red, error message below in text-xs accent-red
```

### 4.3 Card

```
┌─────────────────────────────────────────┐
│  Card Title                    ⋮ menu  │
│                                         │
│  Card content goes here.                │
│  Can contain any elements.              │
│                                         │
│  ┌─────────┐  ┌─────────┐             │
│  │ Action 1│  │ Action 2│             │
│  └─────────┘  └─────────┘             │
└─────────────────────────────────────────┘

bg: bg-secondary
border: 1px solid border-default
radius: radius-lg
padding: space-4
hover: border-color → border-hover (if clickable)
shadow: none (flat design, borders define edges)
```

### 4.4 Modal / Dialog

```
┌─ Overlay (bg-primary at 60% opacity) ──────────────────────┐
│                                                              │
│    ┌─────────────────────────────────────────┐              │
│    │  Modal Title                       ✕    │              │
│    │─────────────────────────────────────────│              │
│    │                                         │              │
│    │  Modal content                          │              │
│    │                                         │              │
│    │─────────────────────────────────────────│              │
│    │              [Cancel]  [Confirm]        │              │
│    └─────────────────────────────────────────┘              │
│                                                              │
└──────────────────────────────────────────────────────────────┘

bg: bg-elevated
border: 1px solid border-default
radius: radius-xl
shadow: shadow-lg
max-width: 480px (sm), 640px (md), 800px (lg)
animation: fade in + scale from 95% → 100% (transition-normal)
Close: ✕ button top-right + click overlay + Escape key
```

### 4.5 Avatar

```
┌────┐
│ KN │   Sizes: sm (24px), md (32px), lg (40px), xl (56px)
└────┘

- Circular (radius-full)
- If image: object-fit cover
- If no image: initials on gradient background (brand-gradient)
- Text: font-semibold, text color white
- AI avatar: 🤖 emoji or JARVIS icon on brand-gradient bg
- Online indicator: 8px green dot, bottom-right, border 2px bg-primary
```

### 4.6 Badge / Tag

```
[urgent]  [3 tasks]  [Pro]  [Zalo]

Variants by color:
- default:  bg-tertiary, text-secondary
- blue:     brand-subtle bg, brand-primary text
- green:    accent-green/15 bg, accent-green text
- yellow:   accent-yellow/15 bg, accent-yellow text
- red:      accent-red/15 bg, accent-red text
- purple:   accent-purple/15 bg, accent-purple text

Size: text-xs, px-2, py-0.5, radius-full
Font: font-medium
```

### 4.7 Message Bubble

```
── User message (right-aligned) ────────────────────────────
                                    ┌──────────────────────┐
                                    │ Tạo task mua sữa     │
                                    │ cho con nhé           │
                                    └──────────────────────┘
                                                    14:32 ✓

bg: bubble-user (brand-primary)
text: bubble-user-text (white)
radius: radius-bubble, bottom-right: radius-sm (tail effect)
max-width: 75% (desktop), 85% (mobile)
padding: space-3
timestamp: text-xs, text-secondary, right-aligned below bubble


── AI message (left-aligned) ───────────────────────────────
🤖
┌──────────────────────────────────────────┐
│ ✅ Đã tạo task: "Mua sữa cho con"       │
│                                          │
│ Hạn: hôm nay 18:00                      │
│ Priority: medium                         │
│                                          │
│ Bạn cần thêm gì không?                  │
└──────────────────────────────────────────┘
14:32

bg: bubble-ai (bg-tertiary)
text: bubble-ai-text (text-primary)
radius: radius-bubble, bottom-left: radius-sm (tail effect)
max-width: 80% (desktop), 90% (mobile)
AI avatar: 24px, left of bubble, top-aligned


── Tool call result (inside AI message) ────────────────────
┌──────────────────────────────────────────┐
│ 🤖                                       │
│ Để tôi tạo task cho bạn...              │
│                                          │
│ ┌─ 🔧 task_create ──────────────────┐   │
│ │ title: "Mua sữa cho con"          │   │
│ │ priority: medium                   │   │
│ │ → ✅ Đã tạo (id: abc123)          │   │
│ └────────────────────────────────────┘   │
│                                          │
│ Đã xong! Task đã được thêm vào list.    │
└──────────────────────────────────────────┘

Tool call block:
  bg: bubble-tool (purple tint)
  border-left: 3px solid accent-purple
  radius: radius-md
  padding: space-2 space-3
  font: font-mono, text-sm
  Collapsible: click to expand/collapse args
  Status icon: ⏳ running → ✅ success / ❌ error
```

### 4.8 Toast / Notification

```
┌──────────────────────────────────────┐
│ ✅  Task đã được tạo thành công      │  ← auto-dismiss 4s
└──────────────────────────────────────┘

Position: top-right, space-4 from edges
bg: bg-elevated
border: 1px solid border-default
border-left: 3px solid (green/yellow/red based on type)
radius: radius-lg
shadow: shadow-md
animation: slide in from right (transition-spring)
Types: success (green), warning (yellow), error (red), info (blue)
```

### 4.9 Dropdown / Select

```
┌──────────────────────────┐
│  Selected option       ▾ │
├──────────────────────────┤
│  Option 1          ✓    │  ← active
│  Option 2                │
│  Option 3                │
│  ────────────────────    │  ← separator
│  Option 4                │
└──────────────────────────┘

Trigger: same style as Input
Dropdown: bg-elevated, border, radius-lg, shadow-md
Item: py-2, px-3, hover: bg-tertiary
Active: text brand-primary, checkmark right
Animation: fade + slide down 4px (transition-fast)
```

### 4.10 Sidebar Navigation Item

```
── Inactive ────────────────
│  💬  Chat                │   text-secondary, bg: transparent

── Active ──────────────────
│  💬  Chat                │   text: brand-primary, bg: brand-subtle

── Hover ───────────────────
│  💬  Chat                │   text: text-primary, bg: bg-tertiary/50

Icon: 18px, gap space-3 from label
Padding: space-2 vertical, space-3 horizontal
Radius: radius-lg
Transition: transition-fast (bg + color)
```

### 4.11 Skeleton Loader

```
┌──────────────────────────────────────────┐
│ ████████████████                         │  ← shimmer animation
│ ████████████████████████████             │
│ ██████████████                           │
└──────────────────────────────────────────┘

bg: bg-tertiary
Shimmer: linear-gradient sweep left→right, 1.5s infinite
radius: same as the element it replaces
Use for: message loading, page loading, card loading
```

### 4.12 Empty State

```
         ┌─────────┐
         │  📭     │
         └─────────┘
    Chưa có tin nhắn nào

  Bắt đầu trò chuyện với JARVIS
      để khám phá các tính năng

      [ Bắt đầu chat → ]

Icon/emoji: 48px, centered
Title: text-lg, font-semibold, text-primary
Description: text-sm, text-secondary, max-width 300px, centered
CTA button: primary, centered below
```

---

## 5. Chat Page — Primary UI

> Chat chiếm 80% thời gian sử dụng. Đây là trang quan trọng nhất.

### 5.1 Layout

```
┌─────────────────────────────────────────────────────────────────┐
│ SIDEBAR (w:240px)  │           CHAT AREA                        │
│                    │                                             │
│ 🤖 JARVIS          │  ┌─ Header ──────────────────────────────┐ │
│                    │  │ 🤖 JARVIS          [🔍] [⋮]          │ │
│ 💬 Chat       ←    │  └───────────────────────────────────────┘ │
│ ✅ Tasks           │                                             │
│ 📅 Lịch            │  ┌─ Message List (scrollable) ───────────┐ │
│ 📊 Thống kê        │  │                                       │ │
│ ⚙️ Cài đặt         │  │  [AI] Chào bạn! Tôi là JARVIS...     │ │
│                    │  │                                       │ │
│                    │  │              [User] Tạo task mua sữa  │ │
│                    │  │                                       │ │
│                    │  │  [AI] ✅ Đã tạo task...               │ │
│                    │  │                                       │ │
│                    │  │  [AI] ⏳ Đang tìm kiếm...            │ │
│                    │  │  ● ● ●                                │ │
│                    │  │                                       │ │
│                    │  └───────────────────────────────────────┘ │
│                    │                                             │
│ ──────────────     │  ┌─ Input Bar ───────────────────────────┐ │
│ 👤 Kiên            │  │ [📎] [Nhập tin nhắn...        ] [➤]  │ │
│ Free plan          │  └───────────────────────────────────────┘ │
│ [Nâng cấp Pro]     │                                             │
└─────────────────────────────────────────────────────────────────┘

Desktop: sidebar 240px + chat fills remaining
Tablet: sidebar collapses to icons only (56px)
Mobile: sidebar hidden, hamburger menu top-left
```

### 5.2 Chat Header

```
┌──────────────────────────────────────────────────────────────┐
│  🤖 JARVIS                                    [🔍]  [⋮]    │
│  ● Online                                                    │
└──────────────────────────────────────────────────────────────┘

Height: 56px
bg: bg-secondary
border-bottom: 1px solid border-default
Left: AI avatar (32px) + name (text-lg semibold) + status dot (green 8px) + "Online" (text-xs text-secondary)
Right: Search icon button (ghost) + More menu icon button (ghost)
More menu: New chat, Chat history, Export, Clear chat

Mobile: add hamburger ☰ icon left of avatar
```

### 5.3 Message List

```
Scroll behavior:
- Auto-scroll to bottom on new message
- If user scrolled up: show "↓ New messages" pill at bottom
- Smooth scroll animation

Message grouping:
- Same sender within 2 min: no avatar, reduced gap (space-1)
- Different sender or >2 min gap: full avatar + timestamp, gap space-5

Date separator:
──────── Hôm nay ────────
- Centered text, text-xs, text-secondary
- Horizontal lines: border-default

Typing indicator (AI is thinking):
┌──────────────────────┐
│ 🤖  ● ● ●            │
└──────────────────────┘
- 3 dots with staggered bounce animation
- bg: bubble-ai
- Shows immediately when request sent

Streaming text:
- Text appears character by character (as received from WebSocket)
- Cursor blink (│) at end of streaming text
- No bubble resize animation — bubble grows naturally with content

Welcome message (first visit):
┌──────────────────────────────────────────────────────────────┐
│ 🤖                                                           │
│ Chào bạn! Tôi là JARVIS — trợ lý AI cá nhân của bạn. 👋    │
│                                                              │
│ Tôi có thể giúp bạn:                                        │
│ • 📋 Quản lý công việc & nhắc nhở                           │
│ • 📅 Lên lịch & theo dõi sự kiện                            │
│ • 💰 Ghi chép chi tiêu                                      │
│ • 🔍 Tìm kiếm & tóm tắt thông tin                          │
│ • 🧠 Ghi nhớ thông tin quan trọng                           │
│                                                              │
│ Hãy thử nói gì đó!                                          │
└──────────────────────────────────────────────────────────────┘

Quick action chips below welcome:
[ Tạo task ] [ Xem lịch hôm nay ] [ Chi tiêu hôm nay ] [ Tìm kiếm ]
- Horizontal scroll on mobile
- bg: bg-tertiary, border, radius-full, text-sm
- Click → auto-fill input + send
```

### 5.4 Input Bar

```
┌──────────────────────────────────────────────────────────────┐
│  [📎]  Nhập tin nhắn cho JARVIS...                    [➤]   │
└──────────────────────────────────────────────────────────────┘

Layout:
- Sticky bottom
- bg: bg-secondary
- border-top: 1px solid border-default
- padding: space-3

Attach button [📎]:
- Icon button (ghost), left side
- Opens: file picker (images, documents, voice)
- Attached files show as chips above input:
  ┌──────────────────────────────────────────────────────────┐
  │  📄 report.pdf (2.3MB) ✕  │  🖼️ photo.jpg ✕            │
  ├──────────────────────────────────────────────────────────┤
  │  [📎]  Nhập tin nhắn...                          [➤]   │
  └──────────────────────────────────────────────────────────┘

Text input:
- Auto-resize textarea (1 row → max 6 rows)
- bg: bg-tertiary
- radius: radius-xl (pill shape when 1 row)
- placeholder: "Nhập tin nhắn cho JARVIS..."
- font: text-base
- Shift+Enter: new line
- Enter: send

Send button [➤]:
- Icon button
- Disabled (opacity 30%) when input empty
- Active: brand-primary bg, white icon
- Transforms to ■ (stop) button during streaming
- Click stop: cancel current generation

Voice input (future):
- Long-press send button → voice recording mode
- Waveform animation while recording
- Release → send voice → transcribe → process
```

### 5.5 Tool Call Display

```
When AI calls a tool, show inline in message:

── Pending ──────────────────────────────
┌─ 🔧 task_create ─────────── ⏳ ──────┐
│  ▸ Xem chi tiết                       │  ← collapsed by default
└────────────────────────────────────────┘

── Expanded ─────────────────────────────
┌─ 🔧 task_create ─────────── ⏳ ──────┐
│  title: "Mua sữa cho con"             │
│  priority: "medium"                    │
│  due_date: "2026-03-10"               │
└────────────────────────────────────────┘

── Completed ────────────────────────────
┌─ 🔧 task_create ─────────── ✅ ──────┐
│  ▸ Xem chi tiết                       │
│  → ✅ Đã tạo task (id: abc123)        │
└────────────────────────────────────────┘

── Error ────────────────────────────────
┌─ 🔧 web_search ──────────── ❌ ──────┐
│  ▸ Xem chi tiết                       │
│  → ❌ Timeout after 10s               │
└────────────────────────────────────────┘

Styling:
- bg: bubble-tool
- border-left: 3px solid accent-purple
- radius: radius-md
- Tool name: font-mono, text-sm, font-semibold
- Args: font-mono, text-sm, text-secondary
- Result: text-sm, prefixed with →
- Status icon: right side (⏳ spinning, ✅ green, ❌ red)
- Click to toggle expand/collapse (transition-normal)
```

### 5.6 Markdown Rendering in AI Messages

```
Support in AI messages:
- **Bold**, *italic*, ~~strikethrough~~
- `inline code` → bg-tertiary, font-mono, radius-sm, px-1
- Code blocks → bg-primary, font-mono, text-sm, radius-md, p-3
  - Syntax highlighting (highlight.js, dark theme)
  - Copy button top-right
  - Language label top-left
- Lists (bullet + numbered)
- Links → brand-primary, underline on hover
- Tables → bordered, bg-tertiary header
- Blockquotes → border-left 3px brand-primary, pl-3, text-secondary

Do NOT render:
- Images (show as link)
- HTML tags (escape)
- Headings (treat as bold)
```

### 5.7 Chat History / Conversations

```
Accessed via: header [⋮] → "Chat history" or sidebar sub-menu

┌─ Chat History ──────────────────────────┐
│ 🔍 Tìm kiếm...                         │
│                                          │
│ Hôm nay                                 │
│ ┌────────────────────────────────────┐  │
│ │ Quản lý task hàng ngày        14:32│  │
│ │ "Tạo task mua sữa cho con..."     │  │
│ └────────────────────────────────────┘  │
│ ┌────────────────────────────────────┐  │
│ │ Tìm hiểu về React 19         10:15│  │
│ │ "Tóm tắt những thay đổi..."       │  │
│ └────────────────────────────────────┘  │
│                                          │
│ Hôm qua                                 │
│ ┌────────────────────────────────────┐  │
│ │ Lên kế hoạch tuần             20:00│  │
│ └────────────────────────────────────┘  │
└──────────────────────────────────────────┘

- Slide-in panel from left (mobile) or sidebar replacement (desktop)
- Each item: auto-generated title (first user message), timestamp, preview
- Click → load conversation into chat area
- Swipe left to delete (mobile)
```

---

## 6. Tasks Page

### 6.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Tasks                              [+ Tạo task]  [⫶ Filter] │
│                                                               │
│  ┌─ Tabs ──────────────────────────────────────────────────┐ │
│  │ [Tất cả (12)]  [Todo (5)]  [Đang làm (3)]  [Xong (4)] │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ Task Card ─────────────────────────────────────────────┐ │
│  │ ○  Mua sữa cho con                    [urgent] 📅 10/3 │ │
│  │    Mua ở siêu thị gần nhà                        ⋮     │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ◉  Viết báo cáo Q1                    [high]   📅 15/3 │ │
│  │    Đang làm — 60%                                ⋮     │ │
│  └─────────────────────────────────────────────────────────┘ │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │ ✓  Gọi điện cho khách hàng            [medium]         │ │
│  │    Hoàn thành lúc 14:00                          ⋮     │ │
│  └─────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────┘

Header: page title (text-2xl) + create button (primary) + filter button (ghost)
Tabs: pill-style, bg-tertiary active, count badge
```

### 6.2 Task Card

```
┌──────────────────────────────────────────────────────────────┐
│  ○  Task title here                      [priority] 📅 date │
│     Description preview (1 line, truncated)            ⋮    │
└──────────────────────────────────────────────────────────────┘

Left: checkbox circle (○ todo, ◉ in_progress with fill animation, ✓ done with strikethrough)
  - Click: cycle todo → in_progress → done
  - Done: title gets text-secondary + line-through

Priority badge: color-coded (urgent=red, high=orange, medium=yellow, low=default)
Due date: 📅 icon + date, accent-red if overdue
More menu [⋮]: Edit, Change priority, Delete
Card: bg-secondary, border, radius-lg, hover: border-hover

Overdue visual: left border 3px accent-red, date text accent-red
Created by AI: small 🤖 icon next to title
```

### 6.3 Create/Edit Task Modal

```
┌─ Tạo task mới ──────────────────── ✕ ──┐
│                                          │
│  Tiêu đề *                               │
│  ┌────────────────────────────────────┐  │
│  │                                    │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Mô tả                                   │
│  ┌────────────────────────────────────┐  │
│  │                                    │  │
│  └────────────────────────────────────┘  │
│                                          │
│  Priority          Due date              │
│  [▾ Medium    ]    [📅 Chọn ngày    ]   │
│                                          │
│           [Hủy]  [Tạo task]             │
└──────────────────────────────────────────┘
```

---

## 7. Calendar Page

### 7.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Lịch                    [◀ Tháng 3, 2026 ▶]  [+ Sự kiện]  │
│                                                               │
│  ┌─ View Toggle ───────────────────────────────────────────┐ │
│  │ [Ngày]  [Tuần]  [Tháng]                                │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ── Day View (default) ──────────────────────────────────── │
│                                                               │
│  Hôm nay — Thứ 3, 10/03/2026                                │
│                                                               │
│  08:00  ┌─────────────────────────────────┐                  │
│         │ 🔵 Standup meeting              │                  │
│         │    Google Meet • 30 phút        │                  │
│  09:00  └─────────────────────────────────┘                  │
│                                                               │
│  10:00  ┌─────────────────────────────────┐                  │
│         │ 🟣 Review design spec           │                  │
│         │    Phòng họp A • 1 tiếng        │                  │
│  11:00  └─────────────────────────────────┘                  │
│                                                               │
│  14:00  ┌─────────────────────────────────┐                  │
│         │ 🟢 Gặp khách hàng              │                  │
│         │    Cafe ABC • 2 tiếng           │                  │
│  16:00  └─────────────────────────────────┘                  │
│                                                               │
│  Không có sự kiện nào khác hôm nay                           │
└──────────────────────────────────────────────────────────────┘

Time column: text-xs, text-secondary, 60px wide
Event blocks: colored left border (random from palette), bg-secondary, radius-md
  - Height proportional to duration
  - Click → expand detail / edit
  - Title: text-sm semibold
  - Subtitle: location + duration, text-xs text-secondary

Month view: standard calendar grid, dots for events on each day
Week view: 7-column time grid
```

### 7.2 Event Colors

```
Auto-assigned from rotating palette:
🔵 #3B82F6  🟣 #8B5CF6  🟢 #22C55E  🟠 #F97316  🔴 #EF4444  🟡 #EAB308
```

---

## 8. Analytics Page

### 8.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Thống kê                              [Tuần ▾]  [Tháng ▾]  │
│                                                               │
│  ┌─ Summary Cards ─────────────────────────────────────────┐ │
│  │ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │ │
│  │ │ 💬 142   │ │ ✅ 23    │ │ 💰 2.3M  │ │ 🧠 89    │   │ │
│  │ │ Tin nhắn │ │ Tasks    │ │ Chi tiêu │ │ Memories │   │ │
│  │ │ +12% ▲   │ │ done     │ │ VNĐ      │ │ saved    │   │ │
│  │ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ Usage Chart ───────────────────────────────────────────┐ │
│  │  Messages per day (bar chart)                           │ │
│  │  ▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐▐                     │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ┌─ Spending ──────────────┐ ┌─ AI Usage ────────────────┐  │
│  │  By category (donut)    │ │  Model distribution (pie) │  │
│  │  🟢 Ăn uống    45%     │ │  🔵 Gemini Flash  72%     │  │
│  │  🔵 Di chuyển  20%     │ │  🟣 Claude Haiku  20%     │  │
│  │  🟣 Giải trí   15%     │ │  🟠 Claude Sonnet  8%     │  │
│  │  ⚪ Khác       20%     │ │                            │  │
│  └─────────────────────────┘ └────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘

Summary cards: 4 columns (2 on mobile), bg-secondary, radius-lg
  - Number: text-2xl, font-bold
  - Label: text-sm, text-secondary
  - Trend: text-xs, green (up) / red (down) + arrow

Charts: use lightweight lib (Chart.js or recharts)
  - Dark theme: grid lines border-default, text text-secondary
  - Bar colors: brand-primary
  - Donut/pie: rotating palette
```

---

## 9. Settings Page

### 9.1 Layout

```
┌──────────────────────────────────────────────────────────────┐
│  Cài đặt                                                     │
│                                                               │
│  ┌─ Tabs ──────────────────────────────────────────────────┐ │
│  │ [Hồ sơ]  [Tùy chọn]  [Bộ nhớ]  [Kết nối]  [Gói]      │ │
│  └─────────────────────────────────────────────────────────┘ │
│                                                               │
│  ── Hồ sơ ──────────────────────────────────────────────── │
│                                                               │
│  ┌──────────┐                                                │
│  │  Avatar  │  Kiên Bùi                                      │
│  │   (xl)   │  kienbm@email.com                              │
│  └──────────┘  [Đổi ảnh]                                     │
│                                                               │
│  Tên hiển thị                                                │
│  ┌────────────────────────────────────┐                      │
│  │ Kiên Bùi                          │                      │
│  └────────────────────────────────────┘                      │
│                                                               │
│  Múi giờ                                                     │
│  [▾ Asia/Ho_Chi_Minh (UTC+7)     ]                          │
│                                                               │
│                              [Lưu thay đổi]                 │
│                                                               │
│  ── Tùy chọn ──────────────────────────────────────────── │
│                                                               │
│  Ngôn ngữ AI          [▾ Tiếng Việt        ]                │
│  Phong cách trả lời   [▾ Thân thiện        ]                │
│  Tin nhắn chủ động    [━━━●] Bật                             │
│  Tóm tắt buổi sáng   [━━━●] Bật                             │
│  Nhắc deadline        [━━━●] Bật                             │
│                                                               │
│  ── Bộ nhớ (Memory Browser) ──────────────────────────── │
│                                                               │
│  🔍 Tìm trong bộ nhớ...                                     │
│                                                               │
│  [semantic] Kiên thích cà phê đen, không đường      ✕       │
│  [semantic] Có con gái 3 tuổi tên Miu               ✕       │
│  [episodic] Đã lên kế hoạch trip Đà Lạt tháng 4     ✕       │
│  [procedural] Thường check task vào 8h sáng          ✕       │
│                                                               │
│  ── Kết nối ──────────────────────────────────────────── │
│                                                               │
│  Zalo OA        ● Đã kết nối                    [Ngắt]      │
│  Telegram       ○ Chưa kết nối                  [Kết nối]   │
│  Google Cal     ○ Chưa kết nối                  [Kết nối]   │
│                                                               │
│  ── Gói dịch vụ ─────────────────────────────────────── │
│                                                               │
│  Gói hiện tại: Free                                          │
│  Tin nhắn hôm nay: 8/20                                      │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  [Nâng cấp Pro — 99.000đ/tháng]                     │   │
│  │  ✓ Không giới hạn tin nhắn                           │   │
│  │  ✓ Model AI cao cấp hơn                              │   │
│  │  ✓ Bộ nhớ không giới hạn                             │   │
│  └──────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘

Tabs: horizontal, underline active style
Form fields: standard Input component
Toggle switches: pill shape, brand-primary when on
Memory browser: searchable list, each item shows type badge + content + delete button
  - Delete: confirm modal "Xóa memory này?"
  - User has full control over their data (GDPR principle)
```

---

## 10. Auth Flow

### 10.1 Login Page

```
┌──────────────────────────────────────────────────────────────┐
│                                                               │
│                     🤖                                        │
│                  MY JARVIS                                    │
│          Trợ lý AI cá nhân thông minh                        │
│                                                               │
│  ┌────────────────────────────────────────────────────────┐  │
│  │                                                        │  │
│  │  Email                                                 │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ email@example.com                                │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                        │  │
│  │  Mật khẩu                                              │  │
│  │  ┌──────────────────────────────────────────────────┐ │  │
│  │  │ ••••••••                                    👁   │ │  │
│  │  └──────────────────────────────────────────────────┘ │  │
│  │                                                        │  │
│  │  [          Đăng nhập          ]                       │  │
│  │                                                        │  │
│  │  ─────────── hoặc ───────────                         │  │
│  │                                                        │  │
│  │  [ 🔵 Đăng nhập bằng Zalo    ]                       │  │
│  │  [ 🔵 Đăng nhập bằng Telegram]                       │  │
│  │                                                        │  │
│  │  Chưa có tài khoản? Đăng ký                           │  │
│  │                                                        │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                               │
└──────────────────────────────────────────────────────────────┘

- Centered card (max-width 400px) on bg-primary
- Logo + tagline above card
- Card: bg-secondary, radius-xl, shadow-lg, p-8
- Social login buttons: outlined style, full width
- Toggle password visibility: eye icon
- "Đăng ký" link: brand-primary
- Error: red border on field + error text below
```

### 10.2 Register Page

```
Same layout as login, with additional fields:
- Tên hiển thị (text input)
- Email
- Mật khẩu (with strength indicator: weak/medium/strong bar)
- Xác nhận mật khẩu
- [Đăng ký] button
- "Đã có tài khoản? Đăng nhập"
```

---

## 11. Onboarding Flow (First-time user)

```
After first login → 3-step onboarding (skippable)

── Step 1/3: Giới thiệu ──────────────────────────────────
┌──────────────────────────────────────────────────────────┐
│                                                          │
│              🤖 Chào mừng đến với JARVIS!                │
│                                                          │
│  Tôi là trợ lý AI cá nhân — càng dùng, tôi càng hiểu   │
│  bạn. Mọi dữ liệu thuộc về bạn.                        │
│                                                          │
│  ● ○ ○                                                   │
│                                                          │
│              [Tiếp tục →]    [Bỏ qua]                   │
└──────────────────────────────────────────────────────────┘

── Step 2/3: Cá nhân hóa ─────────────────────────────────
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Cho tôi biết thêm về bạn (optional):                   │
│                                                          │
│  Bạn muốn tôi gọi bạn là gì?                           │
│  ┌──────────────────────────────────────────────────┐   │
│  │ Kiên                                             │   │
│  └──────────────────────────────────────────────────┘   │
│                                                          │
│  Bạn quan tâm điều gì nhất?                             │
│  [✓ Quản lý công việc]  [  Tài chính cá nhân  ]        │
│  [  Lên lịch & nhắc nhở]  [✓ Tìm kiếm & nghiên cứu]   │
│                                                          │
│  ● ● ○                                                   │
│              [Tiếp tục →]    [Bỏ qua]                   │
└──────────────────────────────────────────────────────────┘

── Step 3/3: Kết nối ──────────────────────────────────────
┌──────────────────────────────────────────────────────────┐
│                                                          │
│  Kết nối kênh chat để dùng JARVIS mọi lúc:             │
│                                                          │
│  [ 🔵 Kết nối Zalo     ]  ← recommended                │
│  [ 🔵 Kết nối Telegram ]                                │
│  [    Dùng web trước   ]                                │
│                                                          │
│  ● ● ●                                                   │
│              [Bắt đầu dùng JARVIS →]                    │
└──────────────────────────────────────────────────────────┘

- Full-screen modal or dedicated page
- Progress dots at bottom
- Skip always available
- Interests → saved to user preferences → affects AI behavior
- After completion → redirect to chat with welcome message
```

---

## 12. Responsive Breakpoints

```
── Breakpoints ─────────────────────────────────────────────
--mobile:    < 640px     (phone)
--tablet:    640-1024px  (tablet, small laptop)
--desktop:   > 1024px    (laptop, desktop)

── Layout Changes ──────────────────────────────────────────

Mobile (< 640px):
  - Sidebar: hidden, accessible via hamburger ☰ top-left
  - Sidebar opens as overlay (slide from left, overlay bg)
  - Chat: full width, no padding
  - Message bubbles: max-width 85%
  - Input bar: full width, smaller padding
  - Tasks/Calendar: single column
  - Analytics cards: 2 columns
  - Settings tabs: horizontal scroll

Tablet (640-1024px):
  - Sidebar: collapsed to icons only (56px wide)
  - Hover sidebar item → tooltip with label
  - Chat: fills remaining width
  - Message bubbles: max-width 75%
  - Tasks: single column
  - Analytics cards: 2 columns

Desktop (> 1024px):
  - Sidebar: full width (240px) with labels
  - Chat: fills remaining
  - Message bubbles: max-width 65%
  - Tasks: can show 2-column if many tasks
  - Analytics: 4-column summary cards
  - Settings: sidebar tabs (vertical) + content area
```

---

## 13. Micro-interactions & Animations

```
── Message send ────────────────────────────────────────────
1. User presses Enter
2. Input clears instantly
3. User bubble slides up from bottom (transition-spring, 200ms)
4. Typing indicator appears (300ms delay)
5. AI response streams in (character by character)
6. Typing indicator fades out as first character appears

── Task checkbox ───────────────────────────────────────────
○ → ◉ (in_progress): fill animation from center, 200ms
◉ → ✓ (done): checkmark draws in (SVG stroke animation, 300ms)
✓ → ○ (reopen): reverse, 200ms
Title: strikethrough animates left→right on done

── Sidebar navigation ─────────────────────────────────────
- Active indicator: left border slides to new position (transition-normal)
- Background: crossfade (transition-fast)

── Page transitions ────────────────────────────────────────
- Content: fade in (opacity 0→1, 150ms)
- No full page transitions (SPA, instant feel)

── Pull to refresh (mobile) ────────────────────────────────
- Pull down → spinner appears → release → refresh
- Spinner: brand-primary rotating circle

── Scroll ──────────────────────────────────────────────────
- Smooth scroll everywhere
- Scroll shadows: top/bottom gradient when content overflows
- "Back to bottom" pill: appears when scrolled up in chat
  - Fade in, fixed bottom-center of message list
  - Click → smooth scroll to bottom

── Loading states ──────────────────────────────────────────
- Skeleton loaders for initial page load
- Spinner for button actions
- Progress bar (top of page, thin, brand-primary) for page navigation

── Hover effects ───────────────────────────────────────────
- Cards: border-color transition (transition-fast)
- Buttons: bg-color transition (transition-fast)
- Links: underline appears (transition-fast)
- Icons: scale 1.1 (transition-fast)

── Error shake ─────────────────────────────────────────────
- Invalid form field: horizontal shake animation (3 cycles, 300ms)
- Red border appears simultaneously
```

---

## 14. Accessibility

```
- All interactive elements: focus-visible ring (2px brand-primary, offset 2px)
- Color contrast: WCAG AA minimum (4.5:1 for text, 3:1 for large text)
- Keyboard navigation: Tab through all interactive elements
- Screen reader: proper ARIA labels on icons, buttons, status indicators
- Reduced motion: respect prefers-reduced-motion (disable animations)
- Font scaling: rem-based, works with browser zoom
- Touch targets: minimum 44x44px on mobile
```

---

## 15. Implementation Notes

```
Tech stack:
- Next.js 15 App Router
- Tailwind CSS v4 (design tokens as CSS custom properties)
- shadcn/ui as component base (customize to match spec)
- Zustand for client state
- Lucide React for icons
- Recharts for analytics charts
- react-markdown + rehype-highlight for message rendering

File structure:
frontend/
├── app/                    # Pages (App Router)
├── components/
│   ├── ui/                 # Base components (button, input, card, modal...)
│   ├── chat/               # Chat-specific (message-bubble, input-bar, tool-call...)
│   ├── tasks/              # Task-specific (task-card, task-modal...)
│   ├── calendar/           # Calendar-specific
│   └── layout/             # Sidebar, header, mobile-nav
├── lib/
│   ├── api.ts              # Backend API client (fetch wrapper)
│   ├── ws.ts               # WebSocket client
│   ├── stores/             # Zustand stores (auth, chat, tasks, settings)
│   └── utils.ts            # cn() helper, formatters
└── public/                 # Static assets, favicon
```
