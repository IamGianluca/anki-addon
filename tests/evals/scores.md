# Eval scores

run: 20260920T172111Z
model: qwen3.8-27b
elapsed: 1h 12m

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_code_formatting_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ fix_code_formatting_1        pass@1  67%  pass^3  30%  (2/3 trials)  score 98%
  trial 1: ✗  (11 steps, score 94%)
    ✗ creates
       expected creates in [0, 0], got 1

✓ fix_code_formatting_command_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_yes_no_question_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_docker_dangling_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 94%
  trial 2: ✗  (14 steps, score 82%)
    ✗ fact_untagged
       fact 'untagged' is missing from the notes after applying the change set
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
       The assertion claims that 'the change set nevertheless adds cards for
       the command direction' and that 'at least one new card asks what git
       stash pop or git stash apply does.' However, the proposed changes
       section explicitly states 'No changes proposed.' No new cards were
       added. The agent chose to make no modifications to the cluster, so the
       assertion's claim about added cards is false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' exist and are factually
       correct and distinguishable. However, the agent proposed NO changes
       whatsoever — no new cards were added. The agent explicitly stated 'No
       changes proposed' and justified this by incorrectly claiming 'no
       canonical confusable counterpart exists for the stash concept.' Since no
       command cards (for git stash pop vs. git stash apply) were added, the
       assertion's subject does not exist, making the assertion false.
  trial 1: ✗  (4 steps, score 44%)
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
       section explicitly states 'No changes proposed.' The agent's closing
       summary also confirms no changes were made. No new cards of any kind
       were added, so the assertion is factually incorrect about the content of
       the change set.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' exist and are factually
       correct regarding `git stash pop` and `git stash apply`. However, the
       agent proposed 'No changes proposed' and explicitly states no cards were
       added. Since no cards were added, the assertion's premise is false —
       there are no added command cards to evaluate for factual correctness or
       distinguishability. The assertion cannot be satisfied.
  trial 2: ✗  (5 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (git stash pop or git stash apply). However, the proposed
       changes explicitly state 'No changes proposed,' and the agent's closing
       summary confirms this: 'No changes proposed.' No new cards were added at
       all, so the assertion that cards for the command direction were added is
       false.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion refers to 'added command cards' for `git stash pop` and
       `git stash apply`, but the agent proposed NO changes at all. There are
       no added cards in the cluster—only the original seed note remains. Since
       no command cards were added, the assertion that they are 'factually
       correct' and 'keep the two similar commands distinguishable' cannot be
       satisfied. The agent failed to derive and propose the missing command-
       direction cards as the task required.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_topic_label_grpc_1     pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

formatting: ✓ no violations across 48 trials
summary: mean pass^k 85%, mean score 96%
