import os, sqlite3, json

def chk(name, cond):
    print(f"{name}: {'DONE' if cond else 'MISSING'}")
    return 5 if cond else 0

def f_exists(p): return os.path.exists(p)
def c_contains(p, s):
    try: return s in open(p).read()
    except: return False

score = 0
score += chk('1 models, distance', f_exists('engine/models.py') and f_exists('engine/distance.py') and f_exists('engine/state.py'))
score += chk('2 scenario generator', f_exists('engine/scenarios.py') and c_contains('engine/scenarios.py', 'dynamism'))
score += chk('3 simulator frozen prefix', f_exists('engine/simulator.py'))
score += chk('4 greedy insertion', f_exists('engine/algorithms/greedy_insertion.py'))
score += chk('5 real 2-opt*', f_exists('engine/algorithms/two_opt_star.py'))
score += chk('6 Tabu Search', f_exists('engine/algorithms/tabu_search.py'))
score += chk('7 metrics', c_contains('engine/simulator.py', 'response_time') or c_contains('engine/experiment_runner.py', 'metrics'))
score += chk('8 JSONL trace', c_contains('engine/experiment_runner.py', '.jsonl'))
score += chk('9 config runner', f_exists('engine/experiment_runner.py'))
score += chk('10 raw rows, CSV', f_exists('scripts/export_static.py'))
score += chk('11 stats (Friedman, Wilcoxon)', f_exists('engine/stats.py') and c_contains('engine/stats.py', 'wilcoxon'))

db = 'data/dvrp.db'
if os.path.exists(db):
    try:
        conn = sqlite3.connect(db)
        cur = conn.cursor()
        cur.execute("SELECT count(1) FROM experiment_runs WHERE experiment_id='pilot_v2'")
        count = cur.fetchone()[0]
        score += chk('12 pilot data', count == 27)
    except:
        score += chk('12 pilot data', False)
else:
    score += chk('12 pilot data', False)

score += chk('13 dark neon theme', c_contains('web/src/index.css', '--bg-color: #0B0F0A'))
score += chk('14 3D replay', f_exists('web/src/pages/SimulationReplay.tsx') and c_contains('web/src/pages/SimulationReplay.tsx', 'three'))
score += chk('15 Scenario Lab page', f_exists('web/src/pages/ScenarioLab.tsx') or c_contains('web/src/App.tsx', 'ScenarioLab'))
score += chk('16 Results page', c_contains('web/src/App.tsx', 'Results') and c_contains('web/src/App.tsx', 'Charts'))
score += chk('17 Compare page', c_contains('web/src/App.tsx', 'Compare'))
score += chk('18 Overview and Methodology', c_contains('web/src/App.tsx', 'Methodology'))
score += chk('19 README, gitignore, vercel.json', f_exists('README.md') and f_exists('.gitignore') and f_exists('web/vercel.json'))

pushed = False
if os.path.exists('.git'):
    try:
        output = os.popen('git log -1 --pretty=format:%s').read()
        pushed = 'pilot_v2' in output
    except:
        pass
score += chk('20 Vercel ready, pushed', pushed)

print(f"Total: {score}%")
