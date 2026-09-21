# Project specification

The project compares seeded DVRP route repairs for dynamic demand. A is deterministic cheapest feasible insertion, B is A plus best-improvement inter-route 2-opt*, and C is the same insertion path plus a 500-candidate Tabu re-optimization budget per run. Every final comparison uses identical generated scenarios, copied for each strategy.

The evaluation export contains distance, response time, disruption, compute time, evaluations, service counts, feasibility, confidence intervals, and paired Friedman/Wilcoxon-Holm statistics. Final seeds are 1–5; tuning seeds are 101–105 and are isolated from reported values. The executed cut retained 50 customers and five dynamism levels after the larger design projected beyond eight minutes.

The static site reads only `web/public/demo/results.json` and its companion CSV. It does not calculate research outcomes. Known limitations are synthetic Euclidean demand, instantaneous simulated planning, a single depot, homogeneous vehicles, and no traffic or uncertainty.
