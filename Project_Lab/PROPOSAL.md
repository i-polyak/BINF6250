# PROPOSAL.md — Scaffold

---

## Project Title

Secret Spot: Surf Forecasting for Uncharted Breaks via Graph-Based Wave Refraction

---

## Research Question

On two surf trips to Nicaragua, I was talking to the surf hostel owner about how there are no surf reports there and he said they rely on old school weather and wave pattern prediciton.
This inspired me to consider a program that can give a surf report for less known breaks locally and international areas without forecasting abilities.
Commercial forecasts like Surfline's LOTUS are propreitary and cover known spots.  HopeWaves (Rhode Island specific) shows that a free NOAA WaveWatch III data plus local tuning and surfer feedback can produce a reliable forecast.
I talked to my good friend Brennan Phillips who is an oceanographic engineer and surfer in Rhode Island and he told me that spectral density can be best predictor of a good wave to surf
My core question for this project is if seafloor shape (bathymetry), combined with buoy wave energy and wind, predict which swells will produce surf at a beach that has no existing forecast.
What's innovative about my project would be using a graph shortest-path algorithm to trace how swell bends over the seafloor toward any user-chosen point ("drop a pin").

---

## Algorithm and Algorithm Class

Class: graph algorithms
Algorithm: multi-source Dijkstra's shortest path on a grid graph
  - Nodes = grid cells of the seafloor, each with a depth
  - Edges = connections to neighboring cells (8 or 16 neighbors, not 4)
  - Edge weight = travel time = distance ÷ wave speed at that depth
  - Sources = a line of offshore cells facing the incoming swell direction, all starting at time 0
Waves travel along least-time paths and slow down in shallow water, so shortest paths approximate how swell refracts (bends) toward shore.
Output: a "swell window" profile for the pin, showing how many wave paths converge on the spot for each swell direction (10° steps).
Supporting scoring step (not the core algorithm): combine the profile with buoy peak spectral energy, peak period, and wind direction into a rating.
Stretch goal (if time allows): analog forecasting using dynamic time warping to match current buoy patterns to similar past days.

---

## Data Plan

### Sources

| Data | Source | Type | Access / licensing |
|---|---|---|---|
| Bathymetry (global) | GEBCO grid | Gridded depths | Free; attribution required |
| Bathymetry (Maine, higher res) | NOAA NCEI Coastal Relief Model | Gridded depths | Free, U.S. government |
| Buoy waves incl. spectral density | NOAA NDBC (e.g., a Gulf of Maine buoy) [choose station] | Time series + spectra | Free, U.S. government |
| Offshore swell (Nicaragua) | NOAA WaveWatch III | Model forecast | Free, U.S. government |
| Wind | Open-Meteo or NOAA GFS | Forecast | Free |
| Comparison reference | Surfline spot pages | Ratings, best swell direction | Read manually only, no scraping (Terms of Use) |
| Expert feedback | Surf hostel staff in Nicaragua | Qualitative ratings | By email |

### Prototype data

- Synthetic seafloor grids built in code, each with a known expected result:
  1. Flat bottom: wave paths should stay straight at any angle.
  2. Single shallow mound: paths should converge (focus) behind the mound.
  3. Gentle slope toward a straight beach: paths should turn to meet the shore nearly head-on.
- Then real data for 2–3 spots (Pine Point, ME, a negative control in ME, and Narragansett, RI), then one Nicaraguan spot (The Boom in Aposentillo).

---

## Success Criteria

Notes:
- Expected outputs: swell-direction profile per spot, a focusing map, and a simple rating that combines swell and wind.
- Checks:
  1. Synthetic grids behave as physics predicts (straight / focusing / turning).
  2. Maine spot profiles match Surfline's listed best swell directions, including at least one sheltered spot where the model should say "blocked" (negative control).
- Hypothesis to test: good surf at Pine Point coincides with buoy peak spectral energy above ~2 m²/Hz *and* a long enough period (e.g., > ~9 s).

---

## Pitfall Scan

**Data**
- Coarse bathymetry: GEBCO cells (~450 m) can miss sandbars and reefs.
  Detect: compare against higher-res Maine data. Mitigate: measure how results change with resolution; describe output as swell exposure, not exact wave shape.
- Few buoys off Nicaragua. Mitigate: use WaveWatch III; estimate its error in Maine by comparing it with a real buoy.

**Algorithmic**
- The √(g × depth) speed formula only holds in shallow water; deep-water speed depends on wave period. Detect: compare speeds in deep cells. 
  Mitigate: start the wave front where water is shallow enough, or use period-dependent speed (optionally run a few period bands weighted by spectral energy).
- Grid zigzag artifacts. Detect: flat-bottom test at 45°. Mitigate: 8 or 16 neighbors.
- Dijkstra finds only the fastest path (no diffraction or breaking). Mitigate: treat focusing as a relative ranking, not wave height in feet.

**Evaluation**
- No ground truth in Nicaragua. Mitigate: validate in Maine first, then structured expert feedback.
- Surfline is another model, not the truth. Mitigate: include negative controls of known beaches with blocked surf.
- A single energy threshold can rate short-period wind swell as good (friend's example of a 2.5 m²/Hz peak at ~6.7 s). Mitigate: score energy together with period.
- Feedback from Nicaragua is small, subjective, possibly slow. Mitigate: predictions sent in advance with a simple rating scale; Maine validation carries the project.

---

## Planned Repository Structure (Initial Sketch)

```
Projet_Lab/
├── README.md            # overview + Quick Start (Part 4)
├── PROPOSAL.md          # this document
├── data/
│   ├── synthetic/       # generated test grids
│   ├── raw/             # downloaded bathymetry, buoy, wind files
│   └── processed/
├── src/
│   ├── grid.py          # build grid graph from depths
│   ├── refraction.py    # multi-source Dijkstra
│   ├── scoring.py       # swell + wind rating
│   └── fetch_data.py    # download helpers
├── tests/               # synthetic-grid tests
├── notebooks/           # exploration and figures
└── docs/                # progress reports (Parts 2–3), figures
```

---

## Generative AI Disclosure

Anthropic Claude opus 5 was used in creating this proposal.  
I gave Claude the list of algorithms we will cover in the class and gave a detailed idea of my secret spot surf forecast program and asked if would fit in any of those algorithm classes.  Claude said that my bathymetry question fits nicely into Djikstra's graph algorithms. I fed Claude all of the information I received from my oceanographic engineer surfer friend about wave refraction and spectral density, so that it could help me flesh out the proposal more soundly. Since we haven't covered graph algorithms yet in class (next lesson), I had Claude explain Djikstra's graph algorithms to me and help me write the pitfalls section.  All proposal text and ideas are original and written by me.
