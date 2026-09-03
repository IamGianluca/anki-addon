# Eval scores

run: 20260904T023839Z
model: qwen3.8-27b
elapsed: 29m 1s

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ recall_direction_docker_dangling_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_git_stash_1 pass@1   0%  pass^3   0%  (0/3 trials)  score 67%
  trial 0: ✗  (5 steps, score 67%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ judge_The_change_set_creates_active-recall_car
       The assertion claims that the change set creates new active-recall cards
       testing the command direction (e.g., a card asking what `git stash pop`
       or `git stash apply` does). However, the proposed changes are explicitly
       'No changes proposed.' No new cards were added, so the assertion's claim
       that 'at least one new card tests the command direction' is false.
    ✗ judge_The_two_similar_commands_`git_stash_pop`
       The assertion is a compound claim: (1) no card bundles both commands in
       one question, and (2) the tests convey the distinguishing behavior (pop
       removes, apply does not). Part (1) is vacuously true since no such card
       exists. However, part (2) requires that active-recall tests actually
       convey the distinguishing behavior. The agent proposed no changes, so no
       cards test `git stash pop` or `git stash apply` in any direction. The
       only mention of these commands is in the Extra field of Note 1, which is
       passive context, not an active recall test. Since there are no tests at
       all for these commands, the…
  trial 1: ✗  (5 steps, score 67%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ judge_The_change_set_creates_active-recall_car
       The proposed changes state 'No changes proposed.' No new cards were
       created to test the command direction (what `git stash pop` or `git
       stash apply` does). The assertion requires that at least one new card
       testing the command direction was added, but the change set is empty.
       Therefore the assertion is not satisfied.
    ✗ judge_The_two_similar_commands_`git_stash_pop`
       The assertion has two parts: (1) no card bundles both commands in one
       question, and (2) the tests convey the distinguishing behavior (pop
       removes, apply does not). Part 1 is technically true since no card tests
       either command at all. However, part 2 is false: the agent proposed NO
       changes, meaning no new cards were created for `git stash pop` or `git
       stash apply`. The distinguishing behavior (pop removes the stash, apply
       does not) appears only in the untested Extra field of the seed note,
       which is passive context, not an active-recall test. Therefore, no test
       conveys the distinguishing behavio…
  trial 2: ✗  (7 steps, score 67%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ judge_The_change_set_creates_active-recall_car
       The proposed changes section explicitly states 'No changes proposed.' No
       new cards were created to test the command direction (git stash pop or
       git stash apply). The assertion requires at least one new card whose
       front asks what git stash pop or git stash apply does. Since no cards
       were added, the assertion is not satisfied.
    ✗ judge_The_two_similar_commands_`git_stash_pop`
       The assertion has two conditions: (1) no card bundles both commands into
       one question, and (2) the tests convey the distinguishing behavior (pop
       removes, apply does not). Condition (1) is trivially true since no card
       asks about either command. However, condition (2) is false: there are no
       cards that test `git stash pop` or `git stash apply` at all. The
       distinguishing behavior appears only in the Extra field of the seed
       note, which is supplementary context shown passively after a correct
       answer—it is not an active-recall test. Since the agent proposed no
       changes, no dedicated atomic cards were …

✗ recall_direction_git_stash_derive_1 pass@1   0%  pass^3   0%  (0/3 trials)  score 44%
  trial 0: ✗  (8 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (git stash pop / git stash apply). However, the proposed
       changes section explicitly states 'No changes proposed,' and the agent's
       closing summary confirms 'No changes proposed.' No new cards were added
       at all, so the assertion is factually incorrect.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion presupposes that command cards for `git stash pop` and
       `git stash apply` were added and evaluates their factual correctness and
       distinguishability. However, the agent proposed no changes at all — no
       command cards were created. The task explicitly required the agent to
       derive the missing command-direction cards for the canonical confusable
       pair. Since no such cards exist in the proposed changes, the assertion
       about their correctness and distinguishability cannot be satisfied.
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
       explicitly state 'No changes proposed' and the agent's closing summary
       confirms the same. No cards were added. The first clause of the
       assertion (seed tests only definition direction, no stash command in
       cluster) is true, but the second clause (cards were added) is factually
       false based on the information shown.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all. There are no added command cards
       in the cluster. The assertion describes 'added command cards' that are
       factually correct and distinguishable, but no such cards exist. Since no
       cards were added, the assertion cannot be satisfied.
  trial 2: ✗  (8 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The proposed changes section explicitly states 'No changes proposed.'
       The agent's closing summary also confirms no changes were made.
       Therefore, no new cards for the command direction (git stash pop or git
       stash apply) were added. The assertion that the change set 'adds cards
       for the command direction' is directly contradicted by the evidence.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all — no command cards were added. The
       assertion evaluates the factual correctness and distinguishability of
       'added command cards,' but no such cards exist in the proposed changes.
       Since the agent failed to create any cards for the git stash pop / git
       stash apply confusable pair, the assertion about their correctness and
       design cannot be satisfied.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 30 trials
summary: mean pass^k 80%, mean score 91%
