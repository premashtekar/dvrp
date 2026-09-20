# ADR-006 — Route Disruption Definition

**Status:** Accepted  
**Applies to:** metrics package, all strategies, reporting

## Decision
**Route disruption** = edges removed from mutable routes by an update  
                     + customers moved between vehicles.  

Also reported:  
- **Normalized disruption** = disruption / number of mutable edges before the update.  
- **Excess over insertion minimum**: because greedy insertion necessarily removes 1 edge,  
  excess = disruption − 1 (for insertion-only events). This isolates the disruption added by repair.

The same definition is applied to all strategies. Reported per update event and aggregated per run.

## Alternatives considered
- Customers whose relative order changed — harder to compute; not standard.  
- Edges added — symmetric to edges removed for simple cases; adds no information.  
- Route edit distance — correct but expensive; overkill for the comparison goal.  
- Percentage of affected route — conflates route length with disruption severity.

## Rationale
Edges-removed + customers-moved captures both structural and ownership disruption.  
Normalization enables cross-scenario comparison.  
Excess-over-minimum reveals whether 2-opt* or Tabu adds disruption beyond what insertion alone would.

## Consequences
The metrics module must record mutable-edge count before each update event.  
Unit test: disruption on a known edit gives the expected count.
