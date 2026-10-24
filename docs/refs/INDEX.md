# Integration references

| Use case | Authoritative guidance |
| --- | --- |
| AgP client commands, units, images and scratch programs | agent-as-policy/interface.md; immutable upstream reference in dependency.lock.json |
| Non-interactive coding agent, permissions, JSONL events, structured final result | codex/non-interactive-mode.md; installed CLI --help at 0.157.0 |
| Queue/session, 10 Hz packets, source calibration and RGB-D | https://github.com/andlyu/blupe-remote-yam/blob/fb1aaa9a696ae4597d06aef41bf876bf2ec90e4d/docs/API.md |
| Matched execution, Stop, feedback and motion validation | Pinned dependency codex-runner/src/remote_yam/controller.py, session.py, mujoco_ik.py and api_depth.py |

Camera and joint timestamps are not hardware synchronized. Our interface exposes that limitation instead of claiming simultaneous captures. Motion timeouts are terminal; no automatic replay. A successful mock test is software evidence, never physical task success.

