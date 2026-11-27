---
path: README.md
agent: human
branch_id: null
period: null
updated_at: 2026-11-27
source: manual
pii: none
---

# mars-ai-vault (skelet)

Bu papka — Obsidian vault'ning **repo ichidagi skeleti**. To'liq vault (embedding
indeksi, shaxsiy yozuvlar) repo'ga kirmaydi; bu yerda faqat tuzilma va qoidalar.

| Papka | Kim yozadi | Nima |
|---|---|---|
| `00_system/` | odam | qoidalar, RBAC havolasi |
| `01_ceo/` | `ceo-strategist` | brifinglar, KPI |
| `02_academic/` | `academic-manager`, `mentor-assistant` | mentor kartalari, retention, intern |
| `03_branch/` | `branch-manager` | kundalik operatsiya, akustika, zamena |
| `04_finance/` | `finance-payroll` | kassa, qarzdorlik, maosh |
| `05_audit/` | `auditor-security` | loglar, nizolar, incidentlar |
| `06_self_improve/` | `auditor-security` | `lessons_learned.md` |

Qoida: har fayl boshida YAML metadata (`path`, `agent`, `branch_id`, `period`,
`updated_at`, `source`, `pii`). `pii: none` bo'lmasa indeksga tushmaydi.
