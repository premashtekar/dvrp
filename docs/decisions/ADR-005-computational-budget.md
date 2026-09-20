# ADR-005 — Computational Budget Definition

**Status:** Accepted  
**Applies to:** all strategies, experiment runner, storage

## Decision
The **primary budget** is an **evaluation limit** (count of candidate-move cost-delta computations).  
One evaluation = one candidate position's delta d(A,X)+d(X,B)−d(A,B) (greedy) or one  
tail-exchange cost-delta (2-opt*) or one neighbourhood-move cost-delta (Tabu).  
Wall-clock time is recorded and used only as a safety cap; it does not terminate the primary run.  
Secondary: iteration limit (Tabu).  

Default limits (configurable in YAML):  
- greedy_insertion: 1000 evaluations  
- two_opt_star: 5000 evaluations  
- tabu_periodic: 10000 evaluations  

Every strategy receives the same budget *definition*; no strategy gets hidden extra compute.  
The exact budget and parameter values are stored with every experiment row.

## Rationale
Evaluation counts are deterministic and machine-independent; wall-clock limits break reproducibility.  
Storing the budget with every row makes comparisons transparent.

## Consequences
Strategy implementations must increment and check an `evaluations` counter.  
A budget overrun is a bug; unit test: budget overruns are impossible.
