# MEMO: corrections and generalized skills

The running coding agent remains the policy. Before each atomic subtask, identify
ACTION(object) (or GENERAL) and derive scene context from current images/state.
Do not use simulator object truth, Panda dimensions or historical coordinates.

1. Retrieve context: `python memo_client.py context '{"action":"PICK(block)","scene":"block towel"}'`.
   Use returned guidance and templates as hypotheses, recomputing all geometry
   from this run. MEMO_CONTEXT.json records the exact retrieval version and IDs.
2. Observe/program/act/check using the original robot client. Every state/frames
   response also includes new owner corrections. A correction changes the next
   decision once; it does not request repeating a relative motion. Poll context
   again before the next motion. Stop ends the run; never auto-resume or replay
   a timed-out movement. There is no physical checkpoint restoration.
3. Paraphrase corrections into position-independent, actionable guidance using
   `python memo_client.py remember '{"kind":"guidance","action":"PICK(block)","content":"..."}'`.
   Preserve the raw correction separately from your interpretation. Later
   contradictory observations or corrections should be represented explicitly.
4. After observing evidence of subtask success, generalize the code into one
   parameterized function; save with kind template, content, and evidence paths
   from frames/ or scratch/. Literal XYZ triplets are refused. Never label motion
   completion or silence as task success. Saved skills are agent-authored and
   unverified, including when the run uses a mock robot.
5. For redundant/conflicting entries, generate a consolidated guidance/template
   with `consolidate`, kind, content, action, scene and source_ids. Preserve all
   motion constraints and conflicts; keep scene coordinates as parameters. The
   old entries remain available at their historical version. Never consolidate
   unrelated kinds or erase raw corrections. Consolidation changes future runs;
   the current run's retrieval snapshot stays pinned.

Continue observing, programming, acting and checking within the same coding turn.
Poll context before each movement; state/frames/context return owner corrections
while this turn is active. Do not restart merely after inspection or each atomic
subtask. Return status continue only when another coding turn is necessary. Use
done only after fresh visual verification of the whole task; otherwise give_up.
The workspace retains your programs, observations and notes between turns.
With MEMO off, corrections still reach this run, but no skillbook is reused or
updated. All durable memory is scoped to this browser/hosted visitor.
