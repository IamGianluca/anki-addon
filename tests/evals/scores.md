# Eval scores

run: 20260805T111037Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  80%  pass^5 0  (4/5 trials)  score 96%
  trial 0: ✗  (5 steps, score 78%)
    ✗ edits
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✗ split_compound_note_1        pass@1  80%  pass^5 0  (4/5 trials)  score 95%
  trial 3: ✗  (13 steps, score 75%)
    ✗ creates
    ✗ read_before_propose_edit_1001
    ✗ judge_After_the_split,_each_resulting_note_tes

✓ split_non_atomic_note_1      pass@1 100%  pass^5 1  (5/5 trials)  score 100%

summary: 2/4 tasks pass^k, mean pass@1 90%, mean score 98%
