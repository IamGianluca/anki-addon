# Eval scores

run: 20260802T172344Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  20%  pass^5 0  (1/5 trials)  score 84%
  trial 1: ✗  (5 steps, score 78%)
    ✗ edits
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 2: ✗  (7 steps, score 89%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 3: ✗  (7 steps, score 89%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 4: ✗  (8 steps, score 67%)
    ✗ creates
    ✗ deletes
    ✗ must_not_touch_3

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✗ split_compound_note_1        pass@1  20%  pass^5 0  (1/5 trials)  score 85%
  trial 1: ✗  (7 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 2: ✗  (6 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 3: ✗  (5 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 4: ✗  (5 steps, score 82%)
    ✗ fact_first moment
    ✗ fact_second moment

summary: 1/3 tasks pass^k, mean pass@1 47%, mean score 90%
