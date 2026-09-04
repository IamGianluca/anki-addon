# Eval scores

run: 20260904T033031Z
model: qwen3.8-27b
elapsed: 39m 21s

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ recall_direction_docker_dangling_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

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
       The assertion claims that the change set adds at least one new card
       asking what `git stash pop` or `git stash apply` does. However, the
       proposed changes section explicitly states 'No changes proposed,' and
       the agent's closing summary confirms 'No changes needed.' No new cards
       were added at all, so the assertion's claim that cards for the command
       direction were added is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion describes 'added command cards' for `git stash pop` and
       `git stash apply`, but the agent proposed no changes at all. No such
       cards were added. Since the cards referenced by the assertion do not
       exist in the proposed changes, the assertion cannot be satisfied.
  trial 1: ✗  (6 steps, score 44%)
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
       confirms 'No changes needed.' No new cards were added at all, so the
       assertion's central claim is directly contradicted by the evidence.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' are factually correct
       and distinguish the two commands. However, the proposed changes
       explicitly state 'No changes proposed,' and the agent's summary confirms
       'No changes needed.' No command cards were added at all, so the
       assertion's premise that cards exist in the proposal is false. The agent
       failed to add the required `git stash pop` and `git stash apply` cards,
       making the assertion about their correctness and distinguishability
       inapplicable and unsatisfied.
  trial 2: ✗  (6 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The first part of the assertion is correct: the seed note tests only the
       definition direction and the cluster contains no mention of any stash
       command. However, the second part of the assertion claims that 'the
       change set nevertheless adds cards for the command direction' and that
       'at least one new card asks what git stash pop or git stash apply does.'
       This is factually incorrect. The proposed changes section explicitly
       states 'No changes proposed,' and the agent's closing summary confirms
       'No changes proposed.' No new cards were added at all, so the
       assertion's claim that cards for the comman…
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all, as confirmed by both the 'Proposed
       changes' section ('No changes proposed') and the closing summary. The
       assertion evaluates the factual correctness and distinguishability of
       'added command cards,' but no such cards exist in the proposed changes.
       Since the agent did not add any cards for `git stash pop` or `git stash
       apply`, the assertion's premise (that added cards exist and are correct)
       is not satisfied.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 30 trials
summary: mean pass^k 90%, mean score 94%
