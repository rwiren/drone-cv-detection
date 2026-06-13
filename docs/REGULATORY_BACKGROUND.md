# Regulatory Background — The 1:1 Rule

This document summarizes the distance-keeping regulations that patent WO2025034145A1 addresses.

## EU — EASA Commission Implementing Regulation (EU) 2019/947

**Source:** [EUR-Lex 2019/947](https://eur-lex.europa.eu/legal-content/EN/TXT/?uri=CELEX%3A32019R0947)

The EU drone regulation defines three categories: Open, Specific, and Certified.

In the **Open Category** (subcategories A1, A2, A3):

### Subcategory A2 (Close to People)
- The remote pilot must maintain a **safe horizontal distance of at least 30 metres** from uninvolved persons.
- In "low speed mode" this may be reduced to **5 metres** horizontal distance.

### The 1:1 Rule (UAS.OPEN.020)
- Applies in subcategories A1 and A3.
- The remote pilot shall keep the UA at a distance from uninvolved persons that is **not less than the height** at which the UA is being operated.
- Formally: **d_lateral ≥ 1 × altitude** (the "1:1 rule")
- Example: Flying at 50m altitude → must maintain at least 50m horizontal distance from uninvolved persons.
- Some Member States or operators apply a safety margin (e.g., 1.1× or 1.2×) to account for reaction time and braking distance.

### Key References in EU 2019/947:
- Article 4 — Open category operations
- UAS.OPEN.020(1) — Flight rules for Open category
- UAS.OPEN.040(1)(b) — A2 subcategory: 30m/5m rule
- Annex, Part A — Operational limitations

---

## Finland — Traficom (droneinfo.fi)

**Source:** [Traficom Droneinfo](https://www.droneinfo.fi/en/flying-a-drone)

Finland applies the EU regulation directly (EASA member state). Additional Finnish specifics:

- Registration required for all drones ≥250g or with a camera
- Online operator exam required (A1/A3 competency)
- A2 Certificate of Competency (CofC) required for flying close to people
- Geographic zones defined by Traficom (airports, military, nature reserves)
- Maximum altitude: 120m AGL (open category)
- The 1:1 rule applies as per EU 2019/947

Finnish geographic zone map: [https://kartta.droneinfo.fi](https://kartta.droneinfo.fi)

---

## USA — FAA Part 107 and Recreational Rules

**Source:** [FAA UAS](https://www.faa.gov/uas)

The FAA does **not** have an explicit "1:1 rule" equivalent. Instead:

### Part 107 (Commercial operations)
- No flight **over people** without waiver (unless Category 1-4 drone per Final Rule on Operations Over People, effective April 2021)
- No specific lateral distance requirement — instead requires maintaining safe distance and not operating in a careless/reckless manner
- Maximum altitude: 400ft (122m) AGL
- Visual Line of Sight (VLOS) required

### Recreational (Section 44809)
- Fly below 400ft AGL
- Keep away from other aircraft
- Fly in controlled airspace only with LAANC authorization
- No specific lateral distance rule — general "safe manner" requirement

### Key Difference from EU
The FAA relies on "see and avoid" principles and general recklessness standards rather than a specific numeric distance-to-persons rule. The EU 1:1 rule is more prescriptive and measurable, which is what makes the patent's automated calculation valuable for EU operations.

---

## Comparison Table

| Jurisdiction | Rule | Distance Requirement | Applies To |
|---|---|---|---|
| EU (EASA) | 1:1 Rule | d_lateral ≥ altitude | Open A1/A3, uninvolved persons |
| EU (EASA) | A2 Rule | 30m (or 5m low-speed) | Open A2, uninvolved persons |
| Finland | EU + national | Same as EU 2019/947 | All open category operations |
| USA (FAA) | Part 107 | No specific distance | General safe operation |
| USA (FAA) | Over People | No overflight without Cat 1-4 | All UAS operations |

---

## Patent WO2025034145A1 Relevance

The patent specifically targets the EU 1:1 rule because:
1. It is **quantifiable** (unlike FAA's "safe manner" standard)
2. It is **difficult for pilots to estimate** visually (distance perception from a remote screen)
3. It creates a clear **trigger condition** for automated warnings
4. The formula enables **real-time computation** using only monocular camera + telemetry

The determined value in the patent (≥1) allows for configurable safety margins beyond the minimum 1:1 ratio.
