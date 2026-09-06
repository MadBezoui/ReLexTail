# Source and identity verification — 2026-09-06

This note records the external checks used in the manuscript revision. It is an
audit trail, not a bibliography to be copied wholesale into the paper.

## Sources cited in the revised paper

| DOI / record | Verified metadata | Use in manuscript |
|---|---|---|
| 10.1007/s10462-025-11307-6 | Paradowski, Wątróbski & Sałabun (2025), *Artificial Intelligence Review*, “Novel coefficients for improved robustness in multi-criteria decision analysis” | Ranking-sensitivity context |
| 10.1016/j.engappai.2024.109699 | Więckowski & Sałabun (2025), *Engineering Applications of Artificial Intelligence* 140, 109699 | Unknown weights versus uncertain normalisation |
| 10.1002/mcda.70019 | Huber, Rojas Gonzalez & Astudillo (2025), *Journal of Multi-Criteria Decision Analysis* 32(3), e70019 | Interactive preference elicitation |
| 10.1002/mcda.70011 | Erwig & Kumar (2025), *Journal of Multi-Criteria Decision Analysis* 32(1), e70011 | Contrastive explanation |
| 10.1017/S0962492924000084 | Kuhn, Shafiee & Wiesemann (2025), *Acta Numerica* 34, 579–804 | Distributional versus bound uncertainty |
| 10.24432/C51307 | Tsanas & Xifara (2012), UCI Energy Efficiency dataset | Public application-oriented simulation benchmark |

Publisher pages used:

- https://onlinelibrary.wiley.com/doi/10.1002/mcda.70019
- https://onlinelibrary.wiley.com/doi/10.1002/mcda.70011
- https://www.cambridge.org/core/journals/acta-numerica/article/distributionally-robust-optimization/5B4E65E3A5A2AEF24E218A6B34E6EAA2
- https://archive.ics.uci.edu/dataset/242/energy%2Befficiency

Crossref/publisher metadata were also checked for every DOI below. The records
exist and the title/author/year combination in `autoreview.md` is materially
correct unless noted:

- 10.1016/j.dajour.2025.100618
- 10.1007/s00704-025-05617-6
- 10.1007/s40305-025-00626-8
- 10.1016/j.ijar.2024.109333
- 10.1016/j.ijar.2025.109528
- 10.1109/TEVC.2025.3583302
- 10.1609/aaai.v40i43.40998
- 10.1214/24-STS955
- 10.1007/s40314-025-03446-x
- 10.23919/COMEX.2026XBL0017
- 10.3390/su18021100
- 10.1016/j.asoc.2025.113058
- 10.1016/j.ejor.2022.07.002
- 10.1007/s10589-018-0052-9
- 10.1007/978-3-031-59933-0_7

The claimed record 10.17535/crorr.2026.0023 could not be independently resolved
in the final check (Crossref throttling and DOI resolution failure in the
available client). It was therefore not cited. This is an unresolved metadata
claim, not evidence that the record is false.

## ORCID identity

The manuscript identifier `0000-0002-8342-7039` is the canonical public ORCID
record for Madani Bezoui. Querying the ORCID public API with the older identifier
`0000-0001-6930-1088` returned the canonical record path
`0000-0002-8342-7039`, consistent with an ORCID merge/redirect. The current
record exposes the CESI LINEACT affiliation and the manuscript email. HAL/DBLP
pages that still display the older identifier should be updated, but the paper
must retain `0000-0002-8342-7039`.

- Canonical record: https://orcid.org/0000-0002-8342-7039
- Legacy identifier checked: https://pub.orcid.org/v3.0/0000-0001-6930-1088

## Public benchmark provenance

The official UCI page states 768 simulated building designs, eight features,
two responses, no missing values and CC BY 4.0. The downloaded CSV has SHA-256
`db44dbe453acd464b5cf65be2fb01a28aa9c5b2630300e65fbe28cde35f5d96f`.
The paper calls this an application-oriented simulation benchmark and does not
claim field or stakeholder validation.
