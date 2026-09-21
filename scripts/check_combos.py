import sqlite3, json
from collections import defaultdict

DB = 'data/dvrp.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT params_json, strategy FROM experiment_runs')
rows = cur.fetchall()
# expected sets
customers_set = {50, 100}
dynamism_set = {0.1, 0.4, 0.8}
strategies = {'greedy_insertion', 'insertion_2opt_star', 'tabu_search'}
seeds = set()
# collect observed combos
observed = defaultdict(set)  # key (cust,dyn,seed) -> set of strategies
for params_json, strategy in rows:
    p = json.loads(params_json)
    cust = p.get('customers')
    dyn = p.get('dynamism')
    seed = p.get('seed')
    if cust is None or dyn is None or seed is None:
        continue
    seeds.add(seed)
    observed[(cust, dyn, seed)].add(strategy)

# compute missing combos (where not all three strategies present)
missing = []
for cust in customers_set:
    for dyn in dynamism_set:
        for seed in sorted(seeds):
            strat_set = observed.get((cust, dyn, seed), set())
            if strat_set != strategies:
                missing.append({
                    'customers': cust,
                    'dynamism': dyn,
                    'seed': seed,
                    'present': list(strat_set),
                    'missing': list(strategies - strat_set)
                })

print('Total rows:', len(rows))
print('Seeds present:', sorted(seeds))
print('Observed combos count:', len(observed))
print('Missing combos count:', len(missing))
for m in missing:
    print(m)
conn.close()
