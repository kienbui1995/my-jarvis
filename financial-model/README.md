# MY JARVIS — Financial Model

## 📁 File Structure

| File | Nội dung |
|------|---------|
| `01_assumptions.csv` | Tất cả giả định: pricing, growth, costs, funding |
| `02_revenue_model.csv` | User growth 24 tháng, conversion, MRR/ARR |
| `03_cost_model.csv` | LLM costs, infra, team, marketing chi tiết |
| `04_pnl_cashflow.csv` | P&L, cash flow, runway, funding milestones |
| `05_unit_economics.csv` | Unit economics, CAC/LTV, sensitivity analysis |

## 📊 Cách Import

### Google Sheets
1. Mở Google Sheets → File → Import
2. Upload file CSV → chọn "Replace spreadsheet" hoặc "Insert new sheet"
3. Import từng file thành 1 sheet riêng
4. Đặt tên sheet theo tên file

### Excel
1. File → Open → chọn file CSV
2. Hoặc: Data → From Text/CSV → Import

## 🔑 Key Metrics Summary

| Metric | M6 | M12 | M18 | M24 |
|--------|-----|------|------|------|
| Total Users | 5K | 50K | 150K | 400K |
| Paid Users | 250 | 3,500 | 12,000 | 34,000 |
| MRR | $1.1K | $16.1K | $55.2K | $156.4K |
| ARR | $13.4K | $187K | $643K | $1.88M |
| Gross Margin | 26% | 37% | 50% | 59% |
| EBITDA | -$11K | -$15K | -$10K | +$45K |
| Cash Balance | $102K | $750K | $633K | $713K |
| LTV:CAC | 3.0x | 14.0x | 13.9x | 25.2x |

## 💰 Funding Plan

| Round | Timing | Amount | Valuation | Milestone |
|-------|--------|--------|-----------|-----------|
| Pre-Seed | M1 | $150K | $1.2M post | MVP + 1K users |
| Seed | M9 | $750K | $6M post | 15K users, $4.5K MRR |
| Series A | M18-24 | $3.5M | $25M post | 150K+ users, $55K+ MRR |

## ⚠️ Key Assumptions to Validate

1. **Paid conversion 8.5% by M24** — benchmark: top consumer AI apps 3-10%
2. **Monthly paid churn 5%** — benchmark: consumer SaaS 5-8%
3. **LLM cost reduction 8%/quarter** — trend: prices dropped 80% in 2025
4. **User growth 20-80% MoM** — depends heavily on product-market fit
5. **99K VNĐ price point** — needs validation via user interviews

## 🎯 Break-even Analysis

- **Operating break-even: ~Month 21** (EBITDA positive)
- **Cumulative break-even: ~Month 30+** (recover all invested capital)
- **Without Seed funding**: runway runs out ~M8-9
- **With Seed funding**: comfortable runway through M24+

## 📈 Sensitivity Scenarios

| Scenario | ARR M24 | Break-even | Risk Level |
|----------|---------|------------|------------|
| Bear (5% conversion, slow growth) | $938K | M24+ | Need more funding |
| **Base (8.5% conversion)** | **$1.88M** | **M21** | **Manageable** |
| Bull (12% conversion, fast growth) | $2.82M | M18 | Strong position |

## 🔧 How to Customize

1. Mở `01_assumptions.csv` → thay đổi giả định
2. Recalculate các file khác dựa trên assumptions mới
3. Key levers to adjust:
   - **Pricing** (Pro/Pro+ price)
   - **Conversion rate** (biggest impact on revenue)
   - **User growth rate** (biggest impact on scale)
   - **LLM cost per user** (biggest impact on margins)
   - **Team size & timing** (biggest impact on burn rate)

---
*Model created: March 2026 | Currency: USD | Market: Vietnam*
