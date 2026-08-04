# Eval scores

run: 20260804T150034Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  60%  pass^5 0  (3/5 trials)  score 96%
  trial 1: ✗  (10 steps, score 78%)
    ✗ must_not_touch_3
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 3: ✗  (7 steps, score 100%)
    ? judge_After_the_merge,_no_two_notes_ask_the_sa

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✗ split_compound_note_1        pass@1  60%  pass^5 0  (3/5 trials)  score 89%
  trial 0: ✗  (5 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 4: ✗  (7 steps, score 64%)
    ✗ creates
    ✗ fact_first moment
    ✗ fact_second moment
    ✗ judge_After_the_split,_each_resulting_note_tes

✓ split_non_atomic_note_1      pass@1 100%  pass^5 1  (5/5 trials)  score 100%

summary: 2/4 tasks pass^k, mean pass@1 80%, mean score 96%
