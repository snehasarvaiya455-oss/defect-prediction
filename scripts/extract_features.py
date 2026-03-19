import subprocess
import json
import math
import os
from collections import Counter

def run_git(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, shell=True)
        return result.stdout.strip()
    except:
        return ""

def get_entropy(file_changes):
    total = sum(file_changes.values())
    if total == 0:
        return 0
    probs = [v/total for v in file_changes.values()]
    return -sum(p * math.log2(p) for p in probs if p > 0)

diff = run_git("git diff HEAD~1 HEAD --numstat")
lines = [l.split('\t') for l in diff.split('\n') if l.strip()]

la, ld, files = 0, 0, []
file_changes = {}
for parts in lines:
    if len(parts) == 3:
        try:
            added = int(parts[0]) if parts[0] != '-' else 0
            deleted = int(parts[1]) if parts[1] != '-' else 0
            fname = parts[2]
            la += added
            ld += deleted
            files.append(fname)
            file_changes[fname] = added + deleted
        except:
            pass

nf = len(files)
subsystems = set(f.split('/')[0] for f in files if '/' in f)
dirs = set(os.path.dirname(f) for f in files if '/' in f)
ns = len(subsystems)
nd = len(dirs)
entropy = round(get_entropy(file_changes), 4)

author = run_git("git log -1 --format='%ae'")
exp = int(run_git(f"git log --author='{author}' --oneline | wc -l") or 0)
rexp = int(run_git(f"git log --author='{author}' --since='90 days ago' --oneline | wc -l") or 0)
sexp = int(run_git(f"git log --author='{author}' --oneline -- {' '.join(files[:5])} | wc -l") or 0) if files else 0

ndev_vals, lt_vals, nuc_vals, age_vals = [], [], [], []
for f in files[:10]:
    ndev_vals.append(int(run_git(f"git log --follow --format='%ae' -- '{f}' | sort -u | wc -l") or 1))
    lt_vals.append(int(run_git(f"git show HEAD~1:'{f}' | wc -l") or 0))
    nuc_vals.append(int(run_git(f"git log --oneline -- '{f}' | wc -l") or 1))
    date_out = run_git(f"git log -1 --format='%ct' -- '{f}'")
    if date_out:
        import time
        age_days = (time.time() - int(date_out)) / 86400
        age_vals.append(round(age_days, 2))

ndev = max(ndev_vals) if ndev_vals else 1
lt = sum(lt_vals)
nuc = sum(nuc_vals)
age = round(sum(age_vals)/len(age_vals), 2) if age_vals else 0

features = {
    "la": la, "ld": ld, "nf": nf, "ns": ns, "nd": nd,
    "entropy": entropy, "ndev": ndev, "lt": lt, "nuc": nuc,
    "age": age, "exp": exp, "rexp": rexp, "sexp": sexp
}

with open("features.json", "w") as f:
    json.dump(features, f)

print("Features extracted:", features)
