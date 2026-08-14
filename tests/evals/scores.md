# Eval scores

run: 20260814T203837Z
model: unsloth/Qwen3.8-27B-GGUF:Q4_K_XL
elapsed: 15m 5s

✗ adam_duplicate_merge_1       pass@1  80%  pass^5  33%  (4/5 trials)  score 96%
  trial 0: ✗  (9 steps, score 78%)
    ✗ creates
       expected creates in [0, 0], got 1
    ✗ deletes
       expected deletes in [0, 0], got 1

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

summary: mean pass^k 83%, mean score 99%
