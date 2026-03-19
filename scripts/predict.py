import json
import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

with open("features.json") as f:
    feat = json.load(f)

entropy_level = "HIGH" if feat["entropy"] > 0.8 else ("MED" if feat["entropy"] > 0.3 else "LOW")
text = (
    f"[CHG] +{feat['la']} -{feat['ld']} nf:{feat['nf']} ns:{feat['ns']} nd:{feat['nd']} | "
    f"[CMP] E:{entropy_level} LT:{feat['lt']} NUC:{feat['nuc']} AGE:{feat['age']} | "
    f"[EXP] DEV:{feat['ndev']} exp:{feat['exp']} rexp:{feat['rexp']} sexp:{feat['sexp']}"
)

model_name = os.environ.get("HF_MODEL", "twoteenn/codebert-jit-defect")
cache_dir = "/tmp/hf_cache"

print(f"Loading model: {model_name}")
tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
model = AutoModelForSequenceClassification.from_pretrained(model_name, cache_dir=cache_dir)
model.eval()

inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=384, padding=True)
with torch.no_grad():
    outputs = model(**inputs)
    probs = torch.softmax(outputs.logits, dim=1)
    prob_defect = probs[0][1].item()

if prob_defect >= 0.60:
    risk = "🔴 HIGH"
    advice = "Thorough code review and additional test coverage strongly recommended before merging."
elif prob_defect >= 0.30:
    risk = "🟡 MEDIUM"
    advice = "Code review recommended before merging."
else:
    risk = "🟢 LOW"
    advice = "Low risk — safe to proceed with standard review."

result = f"""## 🤖 AI Defect Prediction — CodeBERT v2

**Risk Level: {risk}** ({prob_defect*100:.1f}% defect probability)

| Metric | Value |
|--------|-------|
| Lines Added | {feat['la']} |
| Lines Deleted | {feat['ld']} |
| Files Changed | {feat['nf']} |
| Entropy | {entropy_level} |
| Developer Experience | {feat['exp']} commits |

**Recommendation:** {advice}

---
*Model: [twoteenn/codebert-jit-defect](https://huggingface.co/twoteenn/codebert-jit-defect) | Trained on JIT-Defects4J (16,374 commits) | F1=30.41%*
"""

with open("prediction_result.txt", "w") as f:
    f.write(result)

print(f"Risk: {risk} | Probability: {prob_defect*100:.1f}%")
