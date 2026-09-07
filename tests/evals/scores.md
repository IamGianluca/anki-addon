# Eval scores

run: 20260907T205538Z
model: qwen3.8-27b
elapsed: 52m 7s

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_code_formatting_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_command_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_docker_dangling_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 97%
  trial 0: ✗  (11 steps, score 91%)
    ✗ fact_tagged
       fact 'tagged' is missing from the notes after applying the change set

✓ recall_direction_git_stash_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_git_stash_derive_1 pass@1   0%  pass^3   0%  (0/3 trials)  score 44%
  trial 0: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds new cards for the command
       direction (git stash pop or git stash apply). However, the proposed
       changes section explicitly states 'No changes proposed,' and the agent's
       closing summary reiterates 'No changes proposed.' No new cards were
       added at all, so the assertion is factually incorrect.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion presupposes that command cards for `git stash pop` and
       `git stash apply` were added. However, the agent proposed no changes at
       all — the closing summary explicitly states 'No changes proposed' and
       the 'Proposed changes' section is empty. Since no command cards were
       added, the assertion that they are factually correct and keep the two
       commands distinguishable cannot be satisfied. The agent failed to add
       the required recall-direction cards for the canonical confusable pair.
  trial 1: ✗  (5 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds at least one new card
       asking what `git stash pop` or `git stash apply` does. However, the
       proposed changes are explicitly 'No changes proposed,' and the agent's
       closing summary confirms no cards were added. The assertion's premise
       that new cards were added is directly contradicted by the shown
       information.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' are factually correct
       and keep the two commands distinguishable. However, the proposed changes
       explicitly state 'No changes proposed.' No command cards were added at
       all. The agent left the cluster with only the original seed note. Since
       no cards addressing `git stash pop` or `git stash apply` were proposed,
       the assertion's premise is not met — there are no cards to evaluate for
       correctness or distinguishability.
  trial 2: ✗  (7 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that 'the change set nevertheless adds cards for
       the command direction' and that 'at least one new card asks what git
       stash pop or git stash apply does.' However, the proposed changes
       explicitly state 'No changes proposed,' and the agent's closing summary
       confirms no cards were added. No new cards for git stash pop or git
       stash apply exist in the change set. The assertion is factually
       incorrect about the proposed changes.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all, explicitly stating 'No changes
       proposed' in both the proposed changes section and the closing summary.
       Since no command cards for `git stash pop` or `git stash apply` were
       added, the assertion that 'the added command cards are factually correct
       and keep the two similar commands distinguishable' cannot be satisfied.
       There are no cards to evaluate for factual correctness or
       distinguishability.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 42 trials
summary: mean pass^k 88%, mean score 96%
