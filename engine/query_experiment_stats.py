import os, sqlite3, json, sys

def main():
    db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data', 'dvrp.db'))
    if not os.path.exists(db_path):
        print('Database not found at', db_path, file=sys.stderr)
        sys.exit(1)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM runs')
    total = cur.fetchone()[0]
    cur.execute('SELECT strategy, COUNT(*) FROM runs GROUP BY strategy')
    strat_counts = cur.fetchall()
    cur.execute('SELECT customers, dynamism, COUNT(*) FROM runs GROUP BY customers, dynamism')
    cust_dyn = cur.fetchall()
    cur.execute('SELECT DISTINCT seed FROM runs')
    seeds = [row[0] for row in cur.fetchall()]
    print('TOTAL', total)
    print('STRATEGY_COUNTS', strat_counts)
    print('CUSTOMER_DYNAMISM', cust_dyn)
    print('SEEDS', seeds)

if __name__ == '__main__':
    main()
