# Eval scores

run: 20260807T024826Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  60%  pass^5   8%  (3/5 trials)  score 93%
  trial 1: ✗  (5 steps, score 78%)
    ✗ edits
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 2: ✗  (8 steps, score 89%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

✗ split_compound_note_1        pass@1  80%  pass^5  33%  (4/5 trials)  score 96%
  trial 0: ✗  (14 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes

✓ split_non_atomic_note_1      pass@1 100%  pass^5 100%  (5/5 trials)  score 100%

summary: mean pass^k 60%, mean score 97%
