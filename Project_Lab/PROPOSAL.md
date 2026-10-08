# Secret Spot: Surf Forecasting for Uncharted Breaks via Graph-Based Wave Refraction

---

## Research Question

On a surf trip to Nicaragua, the owner of the hostel I stayed at explained that there are no surf reports for most of the local breaks. Surfers there predict conditions the old-school way, by reading weather and wave patterns, often unsuccessfully. This inspired me to build a program that can produce a surf report for lesser-known breaks, both locally in Maine and in places with no forecasting at all.

Commercial forecasts such as Surfline's LOTUS model are proprietary and only cover known spots. HopeWaves, a free Rhode Island forecast, shows that NOAA WaveWatch III data combined with local tuning and surfer feedback can produce a reliable local forecast. My friend Brennan Phillips, an oceanographic engineer and surfer in Rhode Island, pointed out that buoy spectral density, a measure of total wave energy, is a better indicator of surfable waves than reported wave height alone.

**Core question:** Can seafloor shape (bathymetry), combined with buoy wave energy and wind, predict which swells will produce surf at a beach that has no existing forecast?

*What's innovative:** using a graph shortest-path algorithm to trace how swell bends over the seafloor toward any user-chosen point ("drop a pin").

I will validate the program in Maine and Rhode Island, then at The Boom in Nicaragua, a well-known break whose conditions are documented. Once validated, the tool can be applied to the many undocumented breaks nearby in Nicaragua, as well as new spots in Maine I want to scout.

---

## Algorithm and Algorithm Class

**Class:** Graph algorithms

**Algorithm:** Multi-source Dijkstra's shortest path on a grid graph

Bathymetry data is already a grid of depths, so it maps directly onto a graph. Each cell is a node, and neighboring cells are connected by edges. Waves follow the path of least travel time and slow down in shallow water, so finding how swell bends (refracts) toward a beach is a shortest-path problem, with depth setting the travel time. Dijkstra's algorithm runs in O(N log N) time, fast enough to analyze any dropped pin across all swell directions. The other algorithm classes in the course model sequences or patterns over time, while this question is about how swell moves through space.

### Graph design

| Graph element | Ocean equivalent |
|---|---|
| Nodes | Grid cells of the seafloor, each with a depth |
| Edges | Connections to neighboring cells (8 or 16 neighbors, not 4) |
| Edge weight | Travel time = distance ÷ wave speed at that depth |
| Sources | A line of offshore cells facing the incoming swell direction, all starting at time 0 |

**Output:** a "swell window" profile for the pin, showing how many wave paths converge on the spot for each swell direction (10° steps).

**Supporting scoring step (not the core algorithm):** A spot is "worth checking" when there's something and it's clean. "Something" means the swell window shows the spot is exposed to the incoming swell direction and the buoy's peak spectral energy is above a cutoff. "Clean" means light or offshore wind and a clear swell peak rather than mostly short-period chop. The output shows this verdict alongside the buoy's swell height, period, and direction, so surfers can decide for themselves.  Sometimes we get desperate in Maine and so "Surf is good" can be too subjective of a statement.

**Stretch goal (if time allows):** Analog forecasting using dynamic time warping to match current buoy patterns to similar past days and estimate wave height.

---

## Data Plan

### Sources

| Data | Source | Type | Access / licensing |
|---|---|---|---|
| Bathymetry (global) | GEBCO grid | Gridded depths | Free; attribution required |
| Bathymetry (Maine, higher resolution) | NOAA NCEI Coastal Relief Model | Gridded depths | Free, U.S. government |
| Buoy waves incl. spectral density | NOAA NDBC buoy 44007 (Portland, ME) for Pine Point and East End Beach; buoy 44097 (Block Island, RI) for Narragansett | Time series + spectra | Free, U.S. government |
| Offshore swell (Nicaragua) | NOAA WaveWatch III | Model forecast | Free, U.S. government |
| Wind | Open-Meteo or NOAA GFS | Forecast | Free |
| U.S. comparison reference | Surfline spot pages | Ratings, best swell direction | Read manually only; no scraping (Terms of Use) |
| Nicaragua comparison reference | Surfnerd (The Boom) | Best swell direction, offshore wind | Read manually only; no scraping |

### Study spots

| Spot | Role | Buoy / swell source | Compared against |
|---|---|---|---|
| Pine Point, ME | Main test spot | 44007 | Surfline |
| East End Beach, Portland, ME | Negative control (sheltered by Casco Bay islands) | 44007 | Local knowledge: gets chop but never surfable waves |
| Narragansett, RI | Second test spot | 44097 | Surfline, HopeWaves |
| The Boom, Aposentillo, Nicaragua | Nicaragua validation spot | WaveWatch III | Surfnerd |

### Prototype data

Before using real data, I will test the algorithm on synthetic seafloor grids built in code, each with a known expected result:

1. Flat bottom: wave paths should stay straight at any angle.
2. Single shallow mound: paths should converge (focus) behind the mound.
3. Gentle slope toward a straight beach: paths should turn to meet the shore nearly head-on.

Synthetic grids use the same format as real bathymetry (a grid of depth values), so once the code passes these tests, real data from the study spots can be swapped in directly.

---

## Success Criteria

**Expected outputs:** a swell window profile per spot, a focusing map, and a "worth checking or not worth it" verdict with the buoy's swell numbers.

**Checks:**

1. Synthetic grids behave as physics predicts (straight, focusing, turning).
2. Swell window profiles for Pine Point and Narragansett match Surfline's listed best swell directions.
3. East End Beach comes out "blocked" whenever Pine Point is exposed to swell from the same buoy reading.
4. The Boom's swell window profile matches Surfnerd's best swell direction (S–SSW).

**Hypothesis to test:** Pine Point is worth checking when buoy 44007's peak spectral energy is above a cutoff and the wind is light or offshore. Starting cutoffs (~2 m²/Hz at a period of ~6 s or longer) come from a New England rule of thumb and will be tuned against Surfline ratings on real days.

---

## Pitfall Scan

### Data

**Coarse bathymetry.** GEBCO grid cells are roughly 450 m wide, but the sandbars and reefs that shape a break can be much smaller, and even the islands sheltering East End Beach are only a few kilometers across. Nicaragua, my target region, only has this coarse global data.
*Detect:* compare GEBCO results against the higher-resolution NOAA data for the Maine spots.
*Mitigate:* measure how much results change with resolution, and describe the output as swell exposure rather than exact wave shape.

**Few buoys off Nicaragua.** The buoy network is dense along the U.S. coast but sparse in Central America, so there is no nearby buoy for The Boom.
*Detect:* an NDBC radial search found no wave buoys on the Pacific side within about 500 nautical miles of The Boom.
*Mitigate:* use WaveWatch III model data, and estimate its error in Maine by comparing it against buoy 44007 on the same days.

### Algorithmic

**Shallow-water speed formula.** The √(g × depth) formula is only accurate when water is shallow relative to the wavelength; in deeper water, wave speed depends on the wave period. Buoy 44007 sits in 49 m of water, so much of the grid between it and shore is in the range where the formula is inaccurate for typical swell periods.
*Detect:* compare formula speeds in deep cells against the deep-water speed for the swell's period.
*Mitigate:* start the wave front where the water is shallow enough, or use period-dependent wave speed.

**Grid zigzag artifacts.** On a grid, paths can only step in fixed directions. With 4 neighbors, a swell arriving at 30° has to staircase, adding extra distance, which makes some swell directions look artificially slow and biases the swell window profile, the main output.
*Detect:* run the flat-bottom test with a 45° swell; paths should be straight.
*Mitigate:* connect each cell to 8 or 16 neighbors.

**Dijkstra finds only the fastest path.** Real waves wrap around obstacles (diffraction), for example around Peaks Island toward East End Beach, and lose energy when breaking over shoals. Dijkstra gives each cell one fastest arrival and can represent neither, which could make East End look too exposed or too blocked.
*Detect:* check for the expected focusing behind the synthetic mound, check that East End comes out blocked on days when Pine Point doesn't, and check that the results for Pine Point and Narragansett match Surfline.
*Mitigate:* report estimated heights as broad ranges, standard knee to waist rating, rather than exact feet, and check them against Surfline's reported heights.

### Evaluation

**Limited ground truth in Nicaragua.** Surfnerd's documentation of The Boom provides one reference point, but the undocumented spots the tool is designed for can't be checked directly.  I will email contacts but don't want to rely on reported data for sake of timing.
*Mitigate:* validate in Maine and Rhode Island first, then at The Boom, and clearly present results for undocumented spots as unvalidated predictions.

**Surfline is a model, not the truth.** Matching Surfline shows agreement, not correctness, and its best-swell-direction labels are broad ranges that could match partly by chance.
*Mitigate:* include East End Beach as a negative control, where the expected answer ("blocked") comes from local knowledge rather than another model.

**Cutoffs may not transfer between regions.** The ~2 m²/Hz at ~6 s rule of thumb comes from New England surfers; Nicaragua differs in swell exposure and typical periods.
*Detect:* check whether the same cutoffs match known conditions at Pine Point and Narragansett (Surfline) and at The Boom (Surfnerd).
*Mitigate:* score energy together with period, and tune cutoffs per region.

---

## Planned Repository Structure

```
Project_Lab/
├── README.md            # Part 4: final release and Quick Start
├── PROPOSAL.md          # Part 1: this document
├── PSEUDOCODE.md        # Part 2: conceptual progress report
├── PROTOTYPE.md         # Part 3: implementation progress report
├── LICENSE
├── .gitignore
├── data/
│   ├── synthetic/       # generated test grids
│   ├── raw/             # downloaded bathymetry, buoy, and wind files
│   └── processed/
├── src/
│   ├── grid.ipynb           # build grid graph from depths
│   ├── refraction.ipynb     # multi-source Dijkstra
│   ├── scoring.ipynb        # swell and wind verdict
│   └── fetch_data.ipynb     # download helpers
├── tests/               # synthetic-grid tests
└── notebooks/           # exploration and figures
```

---

## Generative AI Disclosure

Anthropic Claude opus 5.5 was used in creating this proposal.  
I described my idea for a surf forecasting program based on how swell moves over bathymetry, gave Claude the list of algorithm classes covered in the course, and asked which would fit. Claude suggested wave refraction modeled with Dijkstra's shortest-path algorithm (graph algorithms). I fed Claude all of the information I received from my oceanographic engineer surfer friend about wave refraction and spectral density, so that it could help me flesh out the proposal more soundly. Since we haven't covered graph algorithms yet in class (next lesson), I relied on Claude to explain Djikstra's graph algorithms to me and how it would work with my project idea.  Claude help me write the algorirthm and pitfalls section.  All proposal text and ideas are original.
