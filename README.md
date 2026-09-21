# DVRP Research Lab

A reproducible Dynamic Vehicle Routing Problem (DVRP) comparison engine with a FastAPI service and static React results interface. DVRP matters because delivery requests can arrive after routes are planned, creating a measurable quality, computation, and disruption trade-off.

## Install and run

`pip install -r requirements.txt` and `cd web && npm ci` install dependencies. Run the backend from the repository root with `uvicorn api.main:app --reload`; run the frontend with `cd web && npm run dev`. Execute `pytest -q -x`, generate batches with `python -m scripts.run_batches`, and export data with `python -m scripts.export_static`.

## Configuration and executed batches

The final and tuning batches each used customers `[50]`, dynamism `[0.1, 0.2, 0.4, 0.6, 0.8]`, strategies A/B/C, one worker, and five seeds. Final uses seeds `1–5`; tuning uses `101–105` and is excluded from reported results. The original 300-run design was cut to five seeds and 50 customers after the preflight projection exceeded eight minutes. Tabu has a per-run, 500-candidate re-optimization budget; feasible greedy insertion remains mandatory and its evaluations are included in the reported total.

## Findings and research questions

H1: final mean distance was 1198.268 for A, 1009.931 for B, and 1198.268 for C, with all strategies serving 50 customers per run. H2: B’s lower final mean distance coincided with 12797.640 mean evaluations versus 667.240 for A. H3: C matched A’s final distance after the service-count correction, while its mean total evaluations were 1167.240. H4: tuning data is reserved for the optional selector and is not used in these reported values.

## Limitations

Demand is synthetic on a Euclidean plane; planning is instantaneous in simulation time; the model has one depot, identical vehicles, simplified service, and no traffic, failures, or travel-time uncertainty. Empirical runtime is not Big-O.

## Vercel

Set Root Directory to `web`, select Vite, and leave environment variables empty. `web/vercel.json` rewrites every route to `index.html`.
