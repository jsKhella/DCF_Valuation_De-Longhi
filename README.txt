What is one De'Longhi share Worth according to DCF? Is the current market price reasonable in this sense?
 

RESULT
| **DCF value per share (base case)** | **€56.47** |
| Market price (close, 6 Nov 2026)    | €45.32 (19.7% below the base case) |
| 80% Monte Carlo range               | €44.34 – €74.08 |
| WACC / terminal growth              | 6.52% / 2.00% |
| Implied exit multiple               | 11.7x EV/EBITDA (sector peers: 9.5x Europe, 10.6x Global) |
**Key caveat:** 
The result heavily depends on the industry beta. With the global-sector beta, WACC rises to 9.62% and DCF value drops to €35.60, BELOW current market price. The note covers this in detail.
 

DELIVERABLES
- 📄 Valuation note.pdf: AN investment-style write-up
- 📊 Workbook.csv: statements, WACC, forecast, DCF, sensitivities, Monte Carlo, checks
- 🎞️ Process Guide.pdf


METHOD
1. Cleaned data from historical statements (annual reports), adjusted for non-recurring items. IFRS 16 leases are treated as debt.
2. Conducted the WACC discount rate calculation employing CAPM with a Damodaran unlevered sector beta, the Italian 10Y yield as the risk-free rate (ECB data), a country risk premium, and the actual cost of debt.
3. Forecast of FY2026E–FY2030E: revenue growth fades from 5% to 2%. The margin is anchored on management's €680m EBITDA guidance.
4. FCFF DCF with a Gordon-growth terminal value, then an equity bridge (net financial position, H1 2026 distributions, minorities).
5. Sensitivity and risk measurements: WACC × g grid and a 10,000-run Monte Carlo with correlated growth and margin shocks.
6. Exit-multiple cross-check against Damodaran EV/EBITDA multiples.



DATA
| Source                                              | Content |

| De'Longhi annual reports FY2021–25, H1 2026 interim | Financial statements |
| Aswath Damodaran (NYU Stern)                        | Sector betas, multiples, country risk premiums, tax rates |
| European Central Bank                               | Italian and German 10Y government bond yields |
| Yahoo Finance | Share price                         |
Full URLs, download dates and checksums are in "REPRODUCIBILITY/data/raw/SOURCES.md".


LIMITATIONS 
Minorities are valued at book value. The cost of equity counts Italy's country risk twice (once in the BTP yield, once in the default spread), which makes it conservative. Value against price is sensitive to beta, as shown above. 

REPRODUCIBILITY
Sources, data and code necessary to reproduce the project's findings are available in dedicated folders.

ABOUT ME
Mina Khella. BSc Statistics & Economics, Università degli studi di Milano-Bicocca. 
Linkedin -> https://www.linkedin.com/in/mina-khella-812113182/
e-mail   -> mina.khellas@gmail.com