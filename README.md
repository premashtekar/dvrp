# Dynamic Vehicle Routing Problem (DVRP) Pilot

A prototype evaluation of DVRP strategies: Greedy Insertion, Greedy + 2-Opt* Repair, and Tabu Search.

## Setup & Run
1. Install Python dependencies: `pip install -r requirements.txt`
2. Install frontend dependencies: `cd web && npm ci`
3. Generate data: `python run_experiment.py` (or `python run_sync.py`)
4. Build frontend: `npm run build`

## Pilot Coverage & Limitations
Batch `pilot_v2` executes:
- Customers: 50
- Dynamism: [0.1, 0.4, 0.8]
- Strategies: A (Greedy), B (Greedy + 2-Opt*), C (Tabu Search)
- Seeds: 1-3
- Tabu Search evaluation budget was reduced to 200 for faster execution.
- The Adaptive Selector was skipped (future work).

## Research Questions
- How does dynamism affect solution quality across strategies?
- Does 2-Opt* provide significant improvement over Greedy?
- Is Tabu Search's compute cost justified by its quality?

## Vercel Deployment
- Framework: Vite
- Root Directory: `web`
- No Environment Variables needed.
- Contains a static `results.json` precomputed from the backend.
