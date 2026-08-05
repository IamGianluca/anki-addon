# Eval scores

run: 20260804T172549Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  60%  pass^5 0  (3/5 trials)  score 91%
  trial 1: ✗  (7 steps, score 78%)
    ✗ creates
    ✗ deletes
  trial 2: ✗  (12 steps, score 78%)
    ✗ creates
    ✗ deletes

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^5 1  (5/5 trials)  score 100%

summary: 3/4 tasks pass^k, mean pass@1 90%, mean score 98%
