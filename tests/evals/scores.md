# Eval scores

run: 20260802T180633Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  40%  pass^5 0  (2/5 trials)  score 91%
  trial 0: ✗  (7 steps, score 78%)
    ✗ deletes
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 1: ✗  (7 steps, score 89%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 2: ✗  (7 steps, score 89%)
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✗ split_compound_note_1        pass@1  20%  pass^5 0  (1/5 trials)  score 85%
  trial 0: ✗  (6 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 1: ✗  (9 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 2: ✗  (6 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes
  trial 3: ✗  (7 steps, score 82%)
    ✗ creates
    ✗ judge_After_the_split,_each_resulting_note_tes

summary: 1/3 tasks pass^k, mean pass@1 53%, mean score 92%
