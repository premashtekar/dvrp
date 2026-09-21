import sqlite3, json

def main():
    db_path = 'data/dvrp.db'
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # total rows
    cur.execute('SELECT COUNT(*) FROM experiment_runs')
    total = cur.fetchone()[0]
    # per strategy
    cur.execute('SELECT strategy, COUNT(*) FROM experiment_runs GROUP BY strategy')
    strat_counts = cur.fetchall()
    # per (customers,dynamism)
    cur.execute("""
        SELECT 
            json_extract(params_json, '$.scenario.customers') AS cust,
            json_extract(params_json, '$.scenario.dynamism') AS dyn,
            COUNT(*)
        FROM experiment_runs
        GROUP BY cust, dyn
    """)
    cust_dyn_counts = cur.fetchall()
    # seeds present
    cur.execute("SELECT DISTINCT json_extract(params_json, '$.seed') FROM experiment_runs")
    seeds = [row[0] for row in cur.fetchall() if row[0] is not None]
    # output
    print('Total rows:', total)
    print('Per strategy:')
    for strat, cnt in strat_counts:
        print(f'  {strat}: {cnt}')
    print('Per (customers,dynamism):')
    for cust, dyn, cnt in cust_dyn_counts:
        print(f'  customers={cust}, dynamism={dyn}: {cnt}')
    print('Seeds present:', seeds)
    conn.close()

if __name__ == '__main__':
    main()
