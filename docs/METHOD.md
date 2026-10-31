# MEMO method on YAM

Source: [Christie et al., From Local Corrections to Generalized Skills:
Improving Neuro-Symbolic Policies with MEMO](https://collab.me.vt.edu/memo/),
IROS2026; [authors' code](https://github.com/VT-Collab/memo/).

The runtime coding agent remains the policy. At each semantic subtask it chooses
ACTION(object), retrieves text guidance and code templates, observes the current
scene, writes a program, executes through the authors' unchanged client and
checks fresh observations. A correction is stored raw and delivered in the next
observation/context. The model paraphrases it into position-independent guidance;
after observed success it may save a parameterized function with source/capture
hashes. Silence and command completion do not establish task success.

Semantic retrieval uses the pinned MiniLM encoder with separate action/object
context vectors and the existing0.75/0.25 similarity weighting. Each run pins a
retrieval revision. A newly saved lesson changes future runs; it does not silently
change the current snapshot. Raw corrections and all superseded entries remain
available in their historical revisions. Consolidation keeps source IDs, motion
constraints and conflicts, and never mixes unrelated kinds.

The standalone adaptation uses real YAM RGB/depth/calibration and a10Hz public
trajectory API rather than simulator object truth, Panda dimensions or fixed
scene coordinates. Owner-scoped memories are private to this browser across
its tasks; the site does not silently publish personal corrections into a
shared multi-user dataset. This is an implementation of the MEMO loop on a
different robot, not a reproduction of the paper's reported benchmark scores.

Refinement is an explicitly offline phase, consistent with the authors'
[overview](https://collab.me.vt.edu/memo/#overview) describing offline clustering
of skillbook entries. It has no robot session and its command backend always
rejects motion. It is not a physical Run and is never counted as a physical
15-second success. Physical task runs retain their own timing/evidence records.
