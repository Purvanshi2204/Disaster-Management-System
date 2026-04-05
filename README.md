# Disaster Shield — Intelligent Relief Routing for Uttarakhand

A smart, algorithm-driven disaster management system that helps authorities make quick and effective decisions during natural disasters like landslides, floods, and earthquakes — built specifically for Uttarakhand but designed to scale.

> "Computing and compassion — showing how the algorithms we study can make a real difference when it matters most."

---

## The Problem

Uttarakhand faces recurring natural disasters. In emergencies, delays in evacuation, rescue, and supply delivery cost lives. Existing systems often lack real-time intelligence for routing, resource allocation, and shelter assignment under dynamic conditions.

## What Disaster Shield Does

Disaster Shield combines classical DAA-based algorithms with an interactive desktop dashboard to optimize four critical emergency operations simultaneously:

- **Evacuation routing** — finds the safest and fastest paths avoiding affected zones
- **Rescue team allocation** — assigns teams based on proximity and availability
- **Relief supply distribution** — delivers resources based on demand and stock levels
- **Shelter assignment** — allocates nearest safe shelter considering real-time capacity

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Core Logic | C++ (STL, File I/O) |
| Pathfinding | Modified Dijkstra's Algorithm, BFS |
| Resource Allocation | Greedy Strategies, Dynamic Programming |
| Frontend Dashboard | Python, PyQt5, QWebEngineView |
| Data Processing | Pandas, NumPy, Geopy |
| Visualization | Live map with type-based color coding and popups |

---

## System Architecture

```
Disaster Event Triggered
        ↓
C++ Backend (Core Logic)
├── graph.cpp          → Graph construction & pathfinding
├── shelter_manager.cpp → Shelter assignment & supply dispatch
└── main.cpp           → Module coordination

        ↓ (subprocess calls via shared CSV/TXT files)

Python Frontend (PyQt5 Dashboard)
├── Interactive map (QWebEngineView)
├── Affected zones, shelters, hospitals, warehouses
├── Real-time route descriptions
└── Supply availability & capacity display
```

---

## Algorithms Used

**Modified Dijkstra's Algorithm** — computes safest evacuation paths while avoiding affected or high-risk zones.

**BFS (Breadth-First Search)** — locates nearest available shelters based on graph traversal.

**Greedy Strategies** — distributes relief supplies based on demand, proximity, and stock availability.

**Priority Queues** — allocates limited resources like food, water, and medicine efficiently.

---

## Dataset

Since no open-source dataset matched our exact needs, we created synthetic datasets modeled on real Dehradun geography using publicly available maps and government reports:

- `disaster_nodes_dehradun.csv` — locations, hospitals, shelters, warehouses
- `disaster_edges_dehradun.csv` — road network connections
- `rescue_teams_dehradun.csv` — team availability and base locations
- `relief_supplies_dehradun.csv` — supply stock and vehicle capacity
- `disaster_zones_dehradun.csv` — affected zone boundaries

---

## Features

- Real-time evacuation route planning with affected-area avoidance
- Rescue team dispatch with follow-up routing to nearest hospital or shelter
- Dynamic shelter reassignment when capacity is full
- Supply distribution prioritized by demand, distance, and stock levels
- Interactive PyQt5 dashboard with live map rendering
- Fully integrated C++ backend and Python frontend via standardized data files

---

## Testing Status

| Test | Status |
|------|--------|
| Data consistency across backend/frontend | Pass |
| Evacuation route calculation | Pass |
| Shelter assignment | Pass |
| Rescue team allocation | Pass |
| Relief supply dispatch | Pass |
| Dashboard map rendering | Pass |
| Edge case: no available shelter | Pass |

---

## Team

| Name | Role |
|------|------|
| Purvanshi Girdhar (Team Lead) | Route optimization, Data collection, Backend integration |
| Archita Saxena | Relief supply dispatch logic, Data preprocessing |
| Madhav Mahajan | Rescue team allocation, Data processing |
| Archita Agarwal | Shelter allocation module, Stock & capacity integration |

---

## Future Scope

- **IoT & Drone Integration** — real-time inputs for flood levels, landslides, and road blockages
- **ML-based Predictive Risk Analysis** — pre-position rescue teams and supplies before disaster worsens
- **Mobile App** — convert PyQt5 dashboard to Kivy or Flutter for field workers

