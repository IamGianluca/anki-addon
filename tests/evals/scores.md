# Eval scores

run: 20260803T025119Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  80%  pass^5 0  (4/5 trials)  score 93%
  trial 1: ✗  (8 steps, score 67%)
    ✗ deletes
    ✗ must_not_touch_3
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✗ split_compound_note_1        pass@1  80%  pass^5 0  (4/5 trials)  score 96%
  trial 0: ✗  (6 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes

summary: 1/3 tasks pass^k, mean pass@1 87%, mean score 97%
