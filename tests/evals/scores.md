# Eval scores

run: 20260915T133235Z
model: qwen3.8-27b
elapsed: 1h 5m

✓ adam_duplicate_merge_1       pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ clean_cluster_no_changes_1   pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ clean_code_formatting_1      pass@1  67%  pass^3  30%  (2/3 trials)  score 83%
  trial 0: ✗  (11 steps, score 50%)
    ✗ empty_change_set
       expected an empty change set, got 1 proposal(s)

✓ fix_code_formatting_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_command_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_code_formatting_prompt_markers_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_math_delimiters_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ fix_second_person_phrasing_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ follow_instruction_convert_abbreviation_1 pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ recall_direction_docker_dangling_1 pass@1  67%  pass^3  30%  (2/3 trials)  score 97%
  trial 2: ✗  (14 steps, score 91%)
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
       section explicitly states 'No changes proposed,' and the agent's closing
       summary confirms 'No changes proposed.' No new cards were added at all,
       so the assertion's core claim about added command-direction cards is
       factually incorrect based on what is shown.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that 'added command cards' exist and are factually
       correct regarding git stash pop vs. git stash apply. However, the
       proposed changes explicitly state 'No changes proposed.' No command
       cards were added at all. The agent's summary confirms this: 'There is no
       canonical confusable counterpart to add.' Since no cards were added, the
       assertion's premise—that such cards exist and are correct—is not met.
       The assertion cannot be satisfied.
  trial 1: ✗  (5 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims the change set adds at least one new card asking
       what `git stash pop` or `git stash apply` does. However, the proposed
       changes section explicitly states 'No changes proposed,' and the agent's
       closing summary confirms no changes were made. No new cards were added
       to the cluster. The assertion is contradicted by the evidence shown.
    ✗ judge_The_added_command_cards_are_factually_co
       The assertion claims that added command cards exist and are factually
       correct, distinguishing `git stash pop` (applies and removes) from `git
       stash apply` (applies without removing). However, the agent proposed no
       changes at all. No cards were added. Since the prerequisite of the
       assertion (that command cards were added) is false, the assertion fails.
  trial 2: ✗  (7 steps, score 44%)
    ✗ creates
       expected creates in [2, 2], got 0
    ✗ fact_pop
       fact 'pop' is missing from the notes after applying the change set
    ✗ fact_apply
       fact 'apply' is missing from the notes after applying the change set
    ✗ judge_The_seed_note_tests_only_the_definition_
       The assertion claims that the change set adds cards for the command
       direction (git stash pop or git stash apply). However, the proposed
       changes explicitly state 'No changes proposed' and the agent's closing
       summary confirms 'No changes proposed.' No new cards of any kind were
       added. The assertion is contradicted by the evidence.
    ✗ judge_The_added_command_cards_are_factually_co
       The agent proposed no changes at all — no command cards for `git stash
       pop` or `git stash apply` were added. The assertion claims that 'the
       added command cards are factually correct and keep the two similar
       commands distinguishable,' but no such cards exist in the proposed
       changes. The premise of the assertion is not met.

✓ split_compound_note_1        pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✓ split_non_atomic_note_1      pass@1 100%  pass^3 100%  (3/3 trials)  score 100%

✗ split_topic_label_grpc_1     pass@1  33%  pass^3   4%  (1/3 trials)  score 89%
  trial 0: ✗  (9 steps, score 83%)
    ✗ fact_binary
       fact 'binary' is missing from the notes after applying the change set
    ✗ judge_After_applying_the_change_set,_the_three
       The structural split into three separate cards is correct: one for the
       RPC framework identity, one for the serialization format, and one for
       the transport protocol. However, the serialization card's back reads
       only 'Protocol Buffers,' dropping the word 'binary' that was present in
       the original back ('binary Protocol Buffers'). The assertion explicitly
       states the card should test 'binary Protocol Buffers' as the
       serialization format. While the structural separation is achieved, the
       serialization card does not fully preserve the fact as stated in the
       original back, since 'binary' is a meaningful…
  trial 1: ✗  (8 steps, score 83%)
    ✗ fact_binary
       fact 'binary' is missing from the notes after applying the change set
    ✗ judge_After_applying_the_change_set,_the_three
       The assertion requires that the serialization format card's answer be
       'binary Protocol Buffers' (matching the original back's description).
       However, the proposed new note for serialization has the back simply
       'Protocol Buffers', omitting the qualifier 'binary'. The original seed
       back explicitly states 'binary Protocol Buffers,' and the assertion
       specifically names the fact as 'that it serializes with binary Protocol
       Buffers' and expects a card for 'the serialization format (binary
       Protocol Buffers)'. The dropped word 'binary' means the card does not
       fully preserve the fact as stated in the ass…

formatting: ✓ no violations across 45 trials
summary: mean pass^k 78%, mean score 94%
