# Large refactor — multiple subsystems changed
import os
import sys
import json
import math
import random
import hashlib
import datetime
import threading
import subprocess
import collections

def process_commit_data(data):
    results = []
    for item in data:
        score = math.sqrt(item['lines_added'] + item['lines_deleted'])
        entropy = -sum(p * math.log2(p) for p in [0.1,0.2,0.3,0.4] if p > 0)
        results.append({'score': score, 'entropy': entropy, 'hash': hashlib.md5(str(item).encode()).hexdigest()})
    return results

def analyse_subsystems(commits):
    subsystems = collections.defaultdict(list)
    for c in commits:
        for f in c.get('files', []):
            parts = f.split('/')
            subsystem = parts[0] if len(parts) > 1 else 'root'
            subsystems[subsystem].append(c)
    return dict(subsystems)

def calculate_developer_metrics(history):
    exp = len(history)
    rexp = sum(1 for h in history if (datetime.datetime.now() - h['date']).days < 90)
    sexp = collections.Counter(h['subsystem'] for h in history)
    return {'exp': exp, 'rexp': rexp, 'sexp': dict(sexp)}

def run_pipeline(config_path):
    with open(config_path) as f:
        config = json.load(f)
    threads = []
    for task in config.get('tasks', []):
        t = threading.Thread(target=process_commit_data, args=([task],))
        threads.append(t)
        t.start()
    for t in threads:
        t.join()
    return {'status': 'complete', 'tasks': len(threads)}

def evaluate_model(predictions, labels):
    tp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 1)
    fp = sum(1 for p, l in zip(predictions, labels) if p == 1 and l == 0)
    fn = sum(1 for p, l in zip(predictions, labels) if p == 0 and l == 1)
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
    return {'precision': precision, 'recall': recall, 'f1': f1}
