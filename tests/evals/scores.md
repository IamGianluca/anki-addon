# Eval scores

run: 20260804T130522Z
model: unsloth/Qwen3.6-27B-MTP-GGUF:Q4_K_XL

✗ adam_duplicate_merge_1       pass@1  60%  pass^5 0  (3/5 trials)  score 91%
  trial 2: ✗  (4 steps, score 78%)
    ✗ edits
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa
  trial 4: ✗  (4 steps, score 78%)
    ✗ edits
    ✗ judge_After_the_merge,_no_two_notes_ask_the_sa

✓ clean_cluster_no_changes_1   pass@1 100%  pass^5 1  (5/5 trials)  score 100%

✓ split_compound_note_1        pass@1 100%  pass^5 1  (5/5 trials)  score 100%

summary: 2/3 tasks pass^k, mean pass@1 87%, mean score 97%
