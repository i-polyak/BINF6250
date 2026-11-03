# Secret Spot: Surf Forecasting for Uncharted Breaks via Graph-Based Wave Refraction

---

# Recap of Project
**Research question:** Can seafloor shape (bathymetry), combined with buoy wave energy
and wind, predict which swells will produce surf at a beach that has no existing
forecast?

**Algorithm and class:** Graph algorithms, specifically multi-source Dijkstra's
shortest path. The seafloor is a grid of cells (nodes) connected to their neighbors
(edges), weighted by how long a wave takes to cross between them. Since waves follow
the fastest path and slow down in shallow water, Dijkstra's shortest paths trace how
swell bends toward shore. Running it for 36 swell directions produces a "swell window"
profile for any chosen point, which a scoring step combines with buoy energy and wind
into a "worth checking / not worth it" verdict.

**Data:** gridded bathymetry (GEBCO globally, NOAA Coastal Relief Model for Maine),
NOAA NDBC buoy data including spectral density (44007 for Pine Point and East End
Beach, 44097 for Narragansett), NOAA WaveWatch III swell forecasts for Nicaragua, and
forecast wind. Synthetic grids (flat, mound, slope) are used for testing.

**Changes since Part 1:** the code will live in a single notebook, with one function
per cell, each followed by a test cell; wave speed now uses the full wave speed
equation instead of the shallow-water formula.

# Inputs, Outputs, and Assumptions

## Inputs
| Input | Type and format |
|---|---|
| Depth grid | 2D array of depths in meters, `depth_grid[row][col]`; loaded from a GEBCO or NOAA file, or generated synthetically |
| Bathymetry bounds | (south, north, west, east) in degrees |
| Cell size | (dy, dx) in meters; computed from the file, or set for synthetic grids |
| Pin | (row, col) grid position just offshore of the beach of interest |
| Buoy reading | peak energy (m²/Hz), peak period (s), peak direction (degrees), height (ft) |
| Wind | speed (knots), direction (degrees) |
| Offshore direction | the wind direction (degrees) that blows offshore at this spot |
| Cutoffs | energy_min, period_min, exposure_min, light_wind_max, offshore_tolerance |
| Settings | radius around the pin (cells), neighbors per cell (8 or 16) |

## Outputs
| Output | Meaning |
|---|---|
| Swell window profile | Dictionary of 36 directions (0°, 10°, ..., 350°) → number of distinct offshore source cells whose fastest paths reach the area around the pin. Higher = more exposed or focused; 0 = blocked |
| Verdict | "worth checking," "not worth it," or "not enough data" |
| Reasons | List of plain-English explanations, e.g., "spot is blocked from this swell direction" |
| Swell numbers | Buoy height, period, and direction, so the surfer can decide for themselves |

## Assumptions
- **Grid:** rectangular, with row 0 at the north edge and column 0 at the west edge. Water cells have positive depth; land is 0 or negative.
- **Directions:** degrees clockwise from north, describing where swell and wind come *from* (the convention buoys and Surfline use).
- **Edge weights are positive** travel times, which Dijkstra requires.
- **Swell arrives as one straight wave front** from a single direction with a single period (the buoy's peak), entering at the grid edge.
- **The buoy reading represents the swell at the grid's offshore edge.**
- **Depth is fixed:** tides are not included, even though the tide at Pine Point can change depth by several meters.
- **Only refraction is modeled:** no diffraction, wave breaking, currents, or local wind waves.
- **Wind is a single reading** for the whole area.

# Algorithm Notes for Pseudocode

### A. Initialization (before any searching)
1. List every node. Every node in the graph needs an entry in each of the tables below.
2. Create a distance table. Give every node a distance of infinity, meaning "not reached yet."
3. Create a predecessor table. Give every node a predecessor of "none." This records which node each node was reached from.
4. Create a finalized set. Start it empty. A node goes here once its shortest distance is locked in.
5. Create a priority queue. Start it empty. It always hands back the node with the smallest distance first.

### B. Load the starting nodes
1. Set each starting node's distance to its start time. In this project, these are the offshore cells where the swell enters the grid; each gets a start time based on when the wave front reaches it.
2. Add each starting node to the priority queue with its start time.

### C. Main loop (repeat while the priority queue is not empty)
1. **Extract-min:** remove the closest node from the queue (the one with the smallest distance). Call it the current node.
2. Skip it if it's already finalized. The same node can be added to the queue more than once with different distances; only the first (smallest) one counts. If it's already finalized, go back to C1.
3. Finalize it. Add the current node to the finalized set. Its shortest distance is now permanent.
4. **Relaxation:** check each neighbor of the current node:
    - a. Skip the neighbor if it's already finalized.
    - b. Compute a new distance: current node's distance + weight of the edge between them.
    - c. Compare: is the new distance smaller than the neighbor's distance in the table?
    - d. If yes, update: set the neighbor's distance to the new distance, set its predecessor to the current node, and add the neighbor to the queue with its new distance.
    - e. If no, do nothing. The neighbor already has a shorter route.
5. Go back to C1.

### D. Termination
1. Stop when the queue is empty. Every reachable node is now finalized.
2. Identify unreachable nodes. Any node still at infinity was never reached, such as cells behind land.

### E. Path reconstruction
1. Shortest distance: each node's value in the distance table.
2. Shortest path to any node: start at that node, step to its predecessor, then that node's predecessor, and so on, until you hit a starting node (predecessor "none").
3. Reverse that list so the path reads from start to finish.

### General Dijkstra vs. This Project
| General Dijkstra | This Project |
|---|---|
| Node | A seafloor grid cell with a depth |
| Edge weight | Distance between cells ÷ wave speed at that depth |
| Distance table | Travel time for swell to reach each cell |
| Starting nodes | The offshore cells where the swell enters, for one swell direction |
| Predecessor trail | The path the swell took to reach each cell |
| Unreachable nodes | Land cells, or water fully blocked behind land |

### Data Flow
```
depth grid → build_graph → for each direction: get_source_cells → dijkstra → count_converging_paths → swell_window_profile → score_conditions → verdict
```

# Detailed Pseudocode

## Imports
`heapq` (the priority queue), `math` (square roots, angles), and `numpy` (the depth grid). Reading real bathymetry files will need one more library, to be decided in Part 3.

## Shared Conventions
```
GRID:        depth_grid[row][col], depths in meters
             water = positive depth; land = 0 or negative
             row 0 = north edge, col 0 = west edge
CELL:        a (row, col) pair
CELL SIZE:   cell_size = (dy, dx) in meters (north-south, east-west)
DIRECTIONS:  degrees clockwise from north; swell direction = where the swell comes FROM
             (same convention buoys and Surfline use)
```

## make_synthetic_grid
```
function make_synthetic_grid(shape, rows, cols, base_depth, cell_size):
    # Input: shape ("flat", "mound", or "slope"), rows and cols (int),
    #        base_depth in meters (float), cell_size (dy, dx) in meters
    # Returns: depth_grid (2D array, rows x cols)

    if rows < 1 or cols < 1:
        raise error "grid must have at least one row and column"

    create depth_grid of size rows x cols, every cell = base_depth

    if shape == "flat":
        return depth_grid                      # uniform depth everywhere

    else if shape == "mound":
        center = (rows // 2, cols // 2)
        radius = min(rows, cols) // 4
        peak_depth = base_depth / 4            # mound rises to a quarter of base depth
        for each cell (r, c):
            d = distance from (r, c) to center, in cells
            if d < radius:
                # depth shrinks smoothly from base_depth at the edge to peak_depth at the center
                depth_grid[r][c] = peak_depth + (base_depth - peak_depth) * (d / radius)
        return depth_grid

    else if shape == "slope":
        # shore along the east edge: depth falls linearly from base_depth (west) to 0 (east)
        for each cell (r, c):
            depth_grid[r][c] = base_depth * (1 - c / (cols - 1))
        return depth_grid                      # last column = 0 = land (the beach)

    else:
        raise error "unknown shape"
```

## load_bathymetry
```
function load_bathymetry(file_path, bounds):
    # Input: file_path (string), bounds = (south, north, west, east) in degrees
    # Returns: depth_grid (2D array), cell_size (dy, dx) in meters

    read elevation values, latitudes, and longitudes from file
    keep only points inside bounds

    if no points remain:
        raise error "bounds contain no data"

    # GEBCO and NOAA store ELEVATION: negative below sea level
    depth_grid = -elevation                    # flip sign so water depth is positive

    for each cell with a missing value:
        set depth to 0                         # treat as land, so no wave path crosses it
        record a warning with the count of missing cells

    # convert grid spacing from degrees to meters
    dy = latitude spacing  * 111,000
    dx = longitude spacing * 111,000 * cos(average latitude)

    return depth_grid, (dy, dx)
```

## wave_speed
```
function wave_speed(depth, period):
    # Input: depth in meters (float), period in seconds (float)
    # Returns: wave speed in m/s (float), or NONE for land

    if period <= 0:
        raise error "period must be positive"
    if depth <= 0:
        return NONE                            # land: waves can't travel here

    deep_wavelength = g * period^2 / (2 * pi)  # wavelength in deep water
    wavelength = deep_wavelength               # starting guess

    repeat up to 100 times:
        new_wavelength = deep_wavelength * tanh(2 * pi * depth / wavelength)
        if |new_wavelength - wavelength| < 0.001:
            stop                               # converged
        wavelength = new_wavelength

    return wavelength / period                 # speed = wavelength / period
```

## build_graph
```
function build_graph(depth_grid, cell_size, period, neighbors):
    # Input: depth_grid (2D array), cell_size (dy, dx), period in seconds,
    #        neighbors (8 or 16)
    # Returns: graph (dictionary: cell -> list of (neighbor_cell, travel_time))

    if neighbors == 8:
        offsets = the 8 surrounding cells (up, down, left, right, 4 diagonals)
    else if neighbors == 16:
        offsets = those 8 plus 8 "knight moves" (e.g., 1 down, 2 right)
    else:
        raise error "neighbors must be 8 or 16"

    # compute each cell's speed once, not once per edge
    speed_grid = wave_speed(depth, period) for every cell

    graph = empty dictionary
    for each cell (r, c):
        if speed_grid[r][c] is NONE:
            continue                           # land cells get no node
        graph[(r, c)] = empty list

        for each offset (dr, dc):
            (nr, nc) = (r + dr, c + dc)
            if (nr, nc) is outside the grid or speed_grid[nr][nc] is NONE:
                continue
            if the move passes through or corners past a land cell:
                continue                       # EDGE CASE: no shortcuts through land

            distance = sqrt((dr * dy)^2 + (dc * dx)^2)
            # average "slowness" of the two cells, so slow shallow cells count fully
            travel_time = (distance / 2) * (1 / speed_grid[r][c] + 1 / speed_grid[nr][nc])
            append ((nr, nc), travel_time) to graph[(r, c)]

    return graph
```

## get_source_cells
```
function get_source_cells(depth_grid, cell_size, period, swell_direction):
    # Input: depth_grid (2D array), cell_size (dy, dx), period in seconds,
    #        swell_direction in degrees (where swell comes FROM)
    # Returns: sources (dictionary: cell -> start_time in seconds);
    #          empty if no water edge faces the swell

    travel_bearing = (swell_direction + 180) mod 360   # swell travels AWAY from where it comes from
    travel_north = cos(travel_bearing)
    travel_east  = sin(travel_bearing)

    # find edge cells where the swell enters the grid
    candidates = empty set
    if travel_north < 0: add every cell in the top row (north edge)       # swell heading south
    if travel_north > 0: add every cell in the bottom row (south edge)    # swell heading north
    if travel_east  > 0: add every cell in the left column (west edge)    # swell heading east
    if travel_east  < 0: add every cell in the right column (east edge)   # swell heading west
    remove land cells from candidates

    if candidates is empty:
        return empty dictionary                # EDGE CASE: swell comes from the land side

    # stagger start times along the wave front
    reference_speed = average wave_speed(depth, period) over candidates
    for each cell (r, c) in candidates:
        north_position = -r * dy               # rows increase southward
        east_position  =  c * dx
        position_along_travel[cell] = north_position * travel_north + east_position * travel_east

    earliest = minimum of position_along_travel
    sources = empty dictionary
    for each cell in candidates:
        sources[cell] = (position_along_travel[cell] - earliest) / reference_speed

    return sources
```

## dijkstra
```
function dijkstra(graph, sources):
    # Input: graph (cell -> list of (neighbor, travel_time)),
    #        sources (cell -> start_time)
    # Returns: travel_times (cell -> fastest arrival time, INFINITY if unreached),
    #          predecessors (cell -> previous cell on the fastest path, NONE for sources)

    # --- A. Initialization ---
    for each cell in graph:
        travel_times[cell] = INFINITY
        predecessors[cell] = NONE
    finalized = empty set
    queue = empty priority queue               # always returns the smallest time first

    # --- B. Load the starting cells ---
    for each (cell, start_time) in sources:
        if cell not in graph:
            continue                           # skip sources that are land
        travel_times[cell] = start_time
        add (start_time, cell) to queue

    # --- C. Main loop ---
    while queue is not empty:
        (time, current) = remove smallest from queue      # C1. extract-min
        if current in finalized:
            continue                                      # C2. skip outdated queue entries
        add current to finalized                          # C3. finalize

        for each (neighbor, edge_time) in graph[current]: # C4. relaxation
            if neighbor in finalized:
                continue
            new_time = travel_times[current] + edge_time
            if new_time < travel_times[neighbor]:
                travel_times[neighbor] = new_time
                predecessors[neighbor] = current
                add (new_time, neighbor) to queue

    # --- D. Termination ---
    # queue is empty: every reachable cell is finalized;
    # cells still at INFINITY were never reached (blocked by land)

    return travel_times, predecessors
```

## reconstruct_path
```
function reconstruct_path(predecessors, travel_times, cell):
    # Input: predecessors and travel_times (from dijkstra), cell (row, col)
    # Returns: path (list of cells from offshore source to cell);
    #          empty list if the cell was never reached

    # --- E. Path reconstruction ---
    if cell not in travel_times or travel_times[cell] == INFINITY:
        return empty list                      # EDGE CASE: unreachable cell

    path = [cell]
    while predecessors[path's last cell] is not NONE:
        append predecessors[path's last cell] to path
        if path is longer than the number of cells in the graph:
            raise error "cycle in predecessors"   # safety check: should never happen

    reverse path                               # now reads source -> cell
    return path
```

## count_converging_paths
```
function count_converging_paths(predecessors, travel_times, pin, radius):
    # Input: predecessors and travel_times (from dijkstra),
    #        pin (row, col), radius in cells (int)
    # Returns: count (int) of distinct offshore source cells whose paths end near the pin

    nearby_water = every cell in travel_times within radius of pin

    if nearby_water is empty:
        raise error "no water near pin: move the pin or increase radius"   # EDGE CASE: pin on land

    feeding_sources = empty set
    for each cell in nearby_water:
        path = reconstruct_path(predecessors, travel_times, cell)
        if path is not empty:
            add path[0] to feeding_sources     # path[0] = the offshore starting cell

    return size of feeding_sources             # 0 means fully blocked from this direction
```

## swell_window_profile
```
function swell_window_profile(depth_grid, cell_size, pin, period, directions, radius, neighbors):
    # Input: depth_grid, cell_size, pin, period, directions (list of degrees,
    #        i.e., 0, 10, ..., 350), radius (int), neighbors (8 or 16)
    # Returns: profile (dictionary: direction -> converging path count)

    graph = build_graph(depth_grid, cell_size, period, neighbors)   # built ONCE

    profile = empty dictionary
    for each direction in directions:
        sources = get_source_cells(depth_grid, cell_size, period, direction)
        if sources is empty:
            profile[direction] = 0             # swell from the land side: blocked
            continue
        travel_times, predecessors = dijkstra(graph, sources)
        profile[direction] = count_converging_paths(predecessors, travel_times, pin, radius)

    return profile
```

## angle_difference
```
function angle_difference(a, b):
    # Input: two directions in degrees (float)
    # Returns: smallest angle between them, 0 to 180 (float)

    diff = |a - b| mod 360
    if diff > 180:
        diff = 360 - diff                      # EDGE CASE: wrap around north
    return diff
```

## score_conditions
```
function score_conditions(profile, buoy_reading, wind, offshore_direction, cutoffs):
    # Input: profile (direction -> path count, from swell_window_profile),
    #        buoy_reading (peak_energy in m²/Hz, peak_period in s, peak_direction in degrees, height in ft),
    #        wind (speed in knots, direction in degrees, where it comes FROM),
    #        offshore_direction in degrees (wind direction that blows offshore at this spot),
    #        cutoffs (energy_min, period_min, exposure_min, light_wind_max, offshore_tolerance)
    # Returns: verdict ("worth checking", "not worth it", or "not enough data"),
    #          reasons (list of strings), swell numbers for display (or NONE)

    if any buoy_reading or wind value is missing:
        return "not enough data", ["missing buoy or wind data"], NONE   # EDGE CASE

    reasons = empty list

    # --- Is there something? ---
    nearest_direction = buoy peak_direction rounded to the nearest 10 degrees (360 -> 0)
    exposed = profile[nearest_direction] >= cutoffs.exposure_min
    enough_energy = buoy peak_energy >= cutoffs.energy_min
    long_enough = buoy peak_period >= cutoffs.period_min
    something = exposed and enough_energy and long_enough
    for each check that failed: add an explanation to reasons
        # i.e., "spot is blocked from this swell direction", "low wave energy"

    # --- Is it clean? ---
    light_wind = wind speed <= cutoffs.light_wind_max
    offshore = angle_difference(wind direction, offshore_direction) <= cutoffs.offshore_tolerance
    clean = light_wind or offshore
    if not clean: add "onshore or cross-shore wind" to reasons

    if something and clean:
        verdict = "worth checking"
    else:
        verdict = "not worth it"

    return verdict, reasons, (height, peak_period, peak_direction)
```

## run_forecast
```
function run_forecast(pin, bathymetry_file, bounds, buoy_reading, wind, offshore_direction, cutoffs, radius, neighbors):
    # Input: pin (row, col), bathymetry_file (string), bounds (south, north, west, east),
    #        buoy_reading, wind, offshore_direction, cutoffs (as in score_conditions),
    #        radius (int), neighbors (8 or 16)
    # Returns: report (verdict, reasons, swell numbers, swell window profile)

    depth_grid, cell_size = load_bathymetry(bathymetry_file, bounds)

    if pin is outside the grid:
        raise error "pin is outside the bathymetry bounds"           # EDGE CASE

    period = buoy_reading.peak_period
    directions = [0, 10, 20, ..., 350]

    profile = swell_window_profile(depth_grid, cell_size, pin, period, directions, radius, neighbors)
    verdict, reasons, swell_numbers = score_conditions(profile, buoy_reading, wind, offshore_direction, cutoffs)

    return report containing verdict, reasons, swell_numbers, profile
```

# Complexity and Bottlenecks

## Notation
| Symbol | Meaning |
|---|---|
| R, C | Rows and columns in the depth grid |
| N | Number of cells (N = R × C) |
| k | Neighbors per cell (8 or 16) |
| E | Number of edges (about k × N) |
| D | Number of swell directions (36) |
| I | Iterations in `wave_speed` (at most 100) |
| r | Radius around the pin, in cells |

## Per-function complexity
| Function | Time | Space | Notes |
|---|---|---|---|
| `make_synthetic_grid` | O(N) | O(N) | Visits each cell once |
| `load_bathymetry` | O(N) | O(N) | Reading and converting the file |
| `wave_speed` | O(I) | O(1) | Fixed-point iteration, capped at 100 |
| `build_graph` | O(N × I + k × N) | O(k × N) | One speed per cell, then k edges per cell |
| `get_source_cells` | O((R + C) × I) | O(R + C) | Only edge cells |
| `dijkstra` | O(E log E) ≈ O(k × N log N) | O(N + E) | Binary-heap priority queue; a cell can be queued more than once |
| `reconstruct_path` | O(L) | O(L) | L = path length, at most N |
| `count_converging_paths` | O(r² × L) | O(r²) | One path trace per water cell near the pin |
| `swell_window_profile` | O(N × I + D × k × N log N) | O(k × N) | Graph built once, Dijkstra run D times |
| `angle_difference`, `score_conditions` | O(1) | O(1) | Fixed number of checks |

**Overall:** about **O(D × k × N log N)**, dominated by running Dijkstra once per swell direction.

## When performance becomes a problem
Grid resolution matters most, because halving the cell size quadruples N. For a 10 km × 10 km box around the pin:

| Data | Cell size | Cells (N) | Expected runtime |
|---|---|---|---|
| GEBCO | ~450 m | ~500 | Under a second |
| NOAA Coastal Relief Model | ~90 m | ~12,000 | Seconds |
| Fine synthetic or resampled grid | 50 m | ~40,000 | Possibly around a minute in pure Python |

Runtimes are rough estimates to be measured in Part 3. Performance would also suffer with a larger box, 16 neighbors instead of 8, or repeated runs for many days or periods (each new period requires rebuilding the graph).

## Mitigation ideas
- **Early stopping:** the program only needs paths that reach the pin, so Dijkstra can stop once every water cell near the pin is finalized, instead of covering the whole grid.
- **Track each cell's source during Dijkstra:** recording which offshore cell each path started from during relaxation lets `count_converging_paths` look it up directly, avoiding a full path trace per cell (O(r²) instead of O(r² × L)).
- **Cache graphs by period:** reuse a built graph when the same swell period comes up again.
- **Keep the box small** around the pin, and use 8 neighbors unless the flat-bottom test shows zigzag artifacts.
- **Measure first:** time each function on synthetic grids of increasing size before running real data.

# Validation and Testing Plan

## 1. Small hand-crafted examples (known answers)

**A. Dijkstra on a published worked example.** Before using grids, `dijkstra` will be
tested on the 6-node example graph from Javaid's "Understanding Dijkstra's Algorithm"
(nodes A–F, source A). The paper works the solution out step by step, so the expected
output is known:

| Node | Expected shortest distance | Expected path |
|---|---|---|
| B | 2 | A-B |
| C | 3 | A-D-E-C |
| D | 1 | A-D |
| E | 2 | A-D-E |
| F | 4 | A-D-E-F |

**B. A 3 × 3 flat grid, worked by hand.** With every cell the same depth, wave speed
is the same everywhere, so travel time from a single corner source is just
distance ÷ speed. A straight neighbor should take dy ÷ speed (or dx ÷ speed), and a
diagonal should take √(dy² + dx²) ÷ speed. These values can be computed by hand and
compared with the output of `build_graph` and `dijkstra`.

**C. Known physical limits for `wave_speed`.** For a 10 s period:
- Deep water (1,000 m): speed should match g × T ÷ 2π ≈ 15.6 m/s
- Very shallow water (1 m): speed should approach √(g × depth) ≈ 3.1 m/s
- Land (depth ≤ 0): should return NONE

## 2. Synthetic datasets (behavior and stress tests)
| Grid | Expected result |
|---|---|
| Flat bottom | Paths stay straight at any angle, including 45°; swell window counts are similar across all open directions |
| Single shallow mound | Paths bend toward the mound and converge behind it; a pin behind the mound gets a higher count than a pin at the same spot on a flat grid |
| Slope toward an east-facing beach | Paths turn so they approach the shore nearly head-on, whatever angle they started at |
| Flat grids of increasing size (100 × 100, 200 × 200, 400 × 400) | Runtime grows roughly as N log N; used to check the complexity estimates |

## 3. Real data
| Spot | Expected result |
|---|---|
| Pine Point, ME | Swell window peaks in the directions Surfline lists as best |
| East End Beach, ME (negative control) | Count of 0 or near 0 for the swell directions that reach Pine Point |
| Narragansett, RI | Matches Surfline's best swell directions |
| The Boom, Nicaragua | Peaks for S–SSW swell, matching Surfnerd |

## 4. Evidence that the algorithm is behaving incorrectly
- Travel times that decrease along a path, or any negative travel time
- A source cell whose final travel time differs from its start time
- A path that passes through or cuts the corner of a land cell
- Curved paths on a flat-bottom grid
- No focusing behind the mound
- A nonzero count for a swell direction coming from the land side
- `wave_speed` faster than the deep-water limit, or slower in deeper water than in shallower water
- East End Beach showing high exposure

## 5. Automated tests
**Unit tests:** each function in the notebook is followed by a test cell, using the
examples above (e.g., the IEEE graph for `dijkstra`, the wave speed limits for
`wave_speed`, `angle_difference(350, 10) == 20`).

**Property (invariant) checks** that must hold after any Dijkstra run:
- For every edge, travel_time[neighbor] ≤ travel_time[cell] + edge_time
- Travel times strictly increase along every reconstructed path
- Every path starts at a source cell and contains no land cells
- On a flat grid, mirror-image swell directions give equal counts

**Comparison to a standard tool:** travel times will be compared with NetworkX's
built-in Dijkstra on the same graph. To handle staggered start times, a single extra
"super-source" node is connected to each source cell with an edge weight equal to
that cell's start time; both implementations should then give identical travel times.

**End-to-end test:** `run_forecast` on a synthetic grid with a made-up buoy reading
and wind should return the expected verdict (e.g., an exposed pin with high energy
and offshore wind returns "worth checking").

# Updated Pitfall and Risk Log

## Part 1 pitfalls revisited
| Pitfall | Status | How the design addresses it |
|---|---|---|
| Coarse bathymetry (GEBCO ~450 m cells) | Still relevant | `load_bathymetry` returns the true cell size, so results can be compared across GEBCO and the higher-resolution NOAA data for the same Maine spots |
| Few buoys off Nicaragua | Still relevant, plus a new detail | WaveWatch III is the swell source. New: it provides swell height, period, and direction rather than a full spectrum, so the energy cutoff in `score_conditions` may need an equivalent built from height and period there |
| Shallow-water speed formula | **Resolved in the design** | `wave_speed` uses the full wave speed equation, which works at any depth; tests check both the deep and shallow limits |
| Grid zigzag artifacts | Addressed | `build_graph` supports 8 or 16 neighbors; the flat-bottom 45° test checks for staircase paths |
| Dijkstra finds only the fastest path (no diffraction or breaking) | Still relevant | Counts are treated as a relative ranking between directions, not a wave height |
| Limited ground truth in Nicaragua | Still relevant | The Boom (Surfnerd) is the Nicaragua validation spot; undocumented spots are reported as unvalidated |
| Surfline is a model, not the truth | Still relevant | East End Beach remains the negative control, based on local knowledge |
| Cutoffs may not transfer between regions | Still relevant | All cutoffs are passed in as inputs to `score_conditions`, so they can be tuned per region without changing code |

## New pitfalls found while writing the pseudocode
| Risk | Why it matters | How the design addresses it |
|---|---|---|
| **Elevation sign** | GEBCO and NOAA store elevation, negative below sea level; using it directly would turn the ocean into land | `load_bathymetry` flips the sign; a test checks that a known offshore point has positive depth |
| **Missing values in bathymetry files** | Treating missing cells as land could wrongly block real water | Missing cells are set to land, but a warning reports how many, so a large count gets noticed |
| **Shortcuts through land** | Diagonal or knight moves could jump across a narrow island or point | `build_graph` skips any move that passes through or cuts the corner of a land cell |
| **Non-square cells** | At Maine's latitude, an east-west degree is about 27% shorter than a north-south one | Cell size is stored as a pair (dy, dx) and used for all distances |
| **Path counts not comparable across directions** | Corner angles enter along two edges, giving more source cells and inflated counts | Each count will be compared against a flat-bottom run of the same direction |
| **One reference speed for the wave front** | Start times assume the offshore edge has roughly uniform depth | Choose the grid box so its offshore edge is in fairly uniform water; check edge depths before running |
| **Only the peak swell is used** | Buoys often report several swells at once (e.g., a 10 s swell plus short-period wind swell), but the design uses only the peak period and direction | Noted as a limitation; a stretch option is running the profile for each major swell component |
| **Graph depends on swell period** | Wave speed depends on period, so a new period means rebuilding the graph | Graphs can be cached by period (see Complexity) |
| **Pin radius choice** | A larger radius includes more cells and raises counts | The same radius is used for every comparison, and results will be checked at a few radius values |
| **Rounding direction to 10°** | A swell at 135° falls between 130° and 140° bins | Acceptable at this resolution; finer steps are possible at extra runtime |
| **Pin entered as row/column** | Real users drop a pin as latitude/longitude | Converting lat/lon to a grid position is planned for Part 3 |
| **Runtime on fine grids** | Halving cell size quadruples the number of cells | Early stopping and tracking each cell's source during Dijkstra are planned for Part 3 |

# References
Javaid, A. Understanding Dijkstra’s Algorithm. IEEE.

# Generative AI Disclosure
