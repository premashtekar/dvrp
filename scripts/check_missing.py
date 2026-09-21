import sqlite3, json
from collections import defaultdict

DB = 'data/dvrp.db'
conn = sqlite3.connect(DB)
cur = conn.cursor()

# fetch all rows
cur.execute('SELECT params_json, strategy FROM experiment_runs')
rows = cur.fetchall()

expected_customers = {50, 100}
expected_dynamism = {0.1, 0.4, 0.8}
strategies = {'greedy_insertion', 'insertion_2opt_star', 'tabu_search'}

observed = defaultdict(set)  # (cust, dyn, seed) -> set of strategies
seeds = set()
for params_json, strategy in rows:
    p = json.loads(params_json)
    scenario = p.get('scenario', {})
    cust = scenario.get('customers')
    dyn = scenario.get('dynamism')
    seed = p.get('seed')
    if cust is None or dyn is None or seed is None:
        continue
    seeds.add(seed)
    observed[(cust, dyn, seed)].add(strategy)

missing = []
for cust in expected_customers:
    for dyn in expected_dynamism:
        for seed in sorted(seeds):
            present = observed.get((cust, dyn, seed), set())
            if present != strategies:
                missing.append({
                    'customers': cust,
                    'dynamism': dyn,
                    'seed': seed,
                    'present': list(present),
                    'missing': list(strategies - present)
                })

# Summary output
print('Total rows:', len(rows))
print('Seeds present:', sorted(seeds))
print('Observed combos:', len(observed))
print('Missing combos count:', len(missing))
for m in missing:
    print(m)

conn.close()
