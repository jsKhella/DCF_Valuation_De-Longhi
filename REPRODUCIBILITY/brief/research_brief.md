# Research brief: De'Longhi DCF valuation
Date: 2026-11-09 · Approved by human: yes

> **Amendment 2026-11-09 (human-requested resize).** The project is resized to bachelor-level scope (target about 1.5-2 hours of agent work, 6 steps). Changes, all STATED by the human:
> - Statements are **condensed** to the lines FCFF needs (revenue, adjusted EBIT, D&A, capex, NWC items, tax, net financial position), still 5 years. Balance-sheet and cash-flow tie-out checks stay.
> - Only the 3-5 largest one-off adjustments are itemised, each with source.
> - Beta: Damodaran Europe beta relevered, plus one sensitivity line (no candidate-selection rule).
> - Peers: no Peers sheet. Damodaran Furn/Home Furnishings multiples are used only for the exit-multiple cross-check.
> - Minorities at book value, flagged as a simplification.
> - Country risk: the brief's formula is kept, with no memo lines, and double-counting is noted as a limitation.
> - Monte Carlo is kept (growth, EBIT margin, WACC, simple correlation). The WACC x g sensitivity grid is kept.
> - Steps (6): (1) statements and ratios, (2) WACC and equity bridge, (3) FCFF forecast and base-case valuation, (4) sensitivity and Monte Carlo, (5) Excel report, (6) .docx investment note (2 pages, in this run).
> - Section 6 sheets are amended accordingly: Statements_5Y is condensed and Peers is dropped (see section 6).

## 1. Question
What is De'Longhi S.p.A. worth per share on a free-cash-flow DCF basis, which assumptions drive that value, and is the current market price reasonable?

## 2. Definitions
| Term | Operational definition | Edge cases | Source |
|------|------------------------|------------|--------|
| Fiscal years | History: last 5 full fiscal years (FY2021-FY2025, December year-end). Forecast: the 5 years after (FY2026E-FY2030E). | If FY2025 is not yet published, use FY2020-FY2024 and say so. | INFERRED |
| Adjusted EBIT | Reported operating profit minus non-recurring items (restructuring, asset sale gains and losses, impairments). Each adjustment is listed with source page and amount. | Items not clearly one-off stay in and are logged. | STATED |
| FCFF | Adjusted EBIT x (1 - tax rate) + D&A - capex - increase in net working capital. | Leases: IFRS 16 treated as debt. Lease depreciation is added back, and lease payments are not deducted from FCFF. | STATED/INFERRED |
| Tax rate | Historical: income tax / pre-tax profit, with the effective rate normalised. Forecast: marginal rate for Italy (Damodaran), unless the history supports a different rate. | Negative or odd years are excluded and logged. | INFERRED |
| Net working capital | Trade receivables + inventories - trade payables (operating items only), as % of revenue. | | INFERRED |
| Cost of equity | Risk-free rate + relevered beta x (mature-market ERP + Italy default spread). Risk-free rate: 10-year BTP yield on the price date. Beta: Damodaran Europe industry unlevered beta, relevered at the target D/E. | | STATED/INFERRED |
| Cost of debt | Pre-tax cost: interest expense / average gross debt, cross-checked against the BTP yield plus a spread. After tax at the marginal rate. | | INFERRED |
| WACC | Market-value weights: market cap for equity, net debt plus leases for debt. | Target structure may be set to the industry average if the current one is unusual. | INFERRED |
| Terminal value | Gordon growth on the FY2030E FCFF (primary). Cross-check: EV/EBITDA exit multiple from peers or history. | g must stay below the risk-free rate. | STATED |
| Discounting | Year-end convention, discounted to the price date using year fractions. | | INFERRED |
| Net debt | Gross financial debt + lease liabilities - cash and equivalents, from the latest published balance sheet. | | STATED |
| Equity bridge | EV - net debt (incl. leases) - minorities (+ associates, if material) = equity value. Divided by diluted shares outstanding, excluding treasury shares. | | STATED |
| Market price | Latest closing price (Borsa Italiana or Yahoo Finance) on the data download date. | | INFERRED |
| Monte Carlo | 10,000 runs. Revenue growth, EBIT margin and WACC are drawn from distributions anchored on history, guidance and the sensitivity range (shapes and correlations agreed in the plan). Output: 10th-90th percentile range of value per share, median, and the market price's percentile. | Fixed seed for reproducibility. | STATED/INFERRED |

## 3. Scope
- Population: De'Longhi S.p.A. consolidated group.
- Time window: 5 years of history and 5 years of forecast (see Definitions).
- Geography / segments: group level. Segment detail is used only to justify forecast assumptions.
- Out of scope (explicitly): peer-by-peer full valuations (multiples cross-check only), M&A scenarios, brand-level analysis, any investment recommendation beyond comparing the value with the price.

## 4. Hypotheses and pre-registered expectations
- H1: The DCF value per share is not materially different from the market price. Neutral, since the human has no prior.
- Expected answer (human's prior): none [STATED].
- A result that would surprise the human (default smell tests, INFERRED):
  - DCF value more than 30% from the market price.
  - Terminal value above 80% of EV.
  - WACC outside 6-10%.
  - g of 2.5% or more.
  - Market price outside the Monte Carlo 10th-90th percentile range.

## 5. Assumptions
- [STATED] De'Longhi is the company. Data comes from annual reports, the latest strategic plan or guidance, Damodaran's data, the BTP yield, and a price source.
- [STATED] IFRS 16 leases are treated consistently as debt.
- [STATED] Gordon growth is primary, with an exit-multiple cross-check.
- [STATED] Sensitivity table: WACC x terminal growth rate.
- [STATED] The investment note is a separate .docx document.
- [INFERRED] EUR throughout. Forecast revenue growth is built from guidance plus history, not from new external assumptions.
- [INFERRED] Management targets are used as input but not accepted blindly, and any departure is justified.

## 6. Format of the final answer (MANDATORY)
Headline sentence: "De'Longhi is worth EUR __ per share (DCF base case, WACC __%, g __%); the 80% Monte Carlo range is EUR __ to EUR __; the market price of EUR __ sits at the __th percentile, i.e. __% above/below the base-case value."

**Excel workbook** (`report/<title>.xlsx`), values only, with a Checks sheet:
1. **Statements_5Y**: condensed statements for 5 years (only the lines needed for FCFF and the equity bridge), in a consistent format. Columns: FY; rows: line items; unit: EUR m.
2. **Adjustments_Ratios**: each adjustment with source, plus historical ratios (growth, EBIT margin, capex %, D&A %, NWC %, tax rate). Unit: EUR m and %.
3. **Forecast_FCFF**: 5 forecast years, with drivers and an assumption note for each. Unit: EUR m and %.
4. **WACC**: every input with its source. Unit: %.
5. **Valuation**: PV of FCFF, Gordon terminal value, exit-multiple cross-check, EV, equity bridge, value per share. Unit: EUR m and EUR per share.
6. **Sensitivity**: value per share, WACC (rows) x g (columns). Unit: EUR per share.
7. **MonteCarlo**: percentile table (5/10/25/50/75/90/95), market-price percentile, histogram, distribution parameters. Unit: EUR per share.
8. **Multiples_Check**: Damodaran Furn/Home Furnishings EV/EBITDA used for the exit-multiple cross-check. Unit: x. (Replaces the Peers sheet.)
9. **Checks**: balance sheet balances, cash flow reconciles with change in cash, FCFF tie-out, determinism.

**Investment note** (`report/<title>.docx`), 2 pages: thesis, main assumptions, valuation range, risks, conclusion vs market price. One chart allowed (football field or Monte Carlo histogram). Every number in it must appear in the verified workbook, and the Verifier checks this.

**Precision:** EUR m with no decimals, EUR per share to 2 decimals, percentages to 1 decimal (WACC and g to 2 decimals), multiples to 1 decimal.

## 7. Data hints
- Annual reports (5 years) and the latest strategic plan or guidance presentation, from De'Longhi investor relations.
- Price and shares: Borsa Italiana or Yahoo Finance.
- Risk-free: 10-year BTP yield from Banca d'Italia, ECB or MEF.
- Beta, ERP, default spread, marginal tax: Damodaran, Europe dataset (January 2026 update).
- Peer multiples: Yahoo Finance or peers' reports.
All unverified; the Planner will check.

## 8. Open questions / risks
- The investment note (.docx) is outside the standard single-Excel deliverable. The Planner must add a step for it, and the Verifier must check it against the workbook.
- Which pages to extract from the PDFs, and the parsing quality of the reports.
- The price date and the net debt date may differ (FY2025 year-end vs an H1 or Q3 2026 interim). The Planner proposes a treatment.
- Peer set: the Planner proposes, and the human approves at Gate 1.
- Monte Carlo distribution shapes and correlations: the Planner proposes them as a decision for the human.
- Fit in an afternoon is tight (PDF extraction, 5 years of statements, Monte Carlo, note). The Planner should flag any cut it recommends.
