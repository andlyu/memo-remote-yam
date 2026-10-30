"""Attach the confirmed runner to the existing public queue contract."""
from .dependency import runner_root

runner_root()
from remote_yam.session import HttpSessionAPI


class AttributedSessionAPI(HttpSessionAPI):
    def __init__(self, *args, runner, **kwargs):
        super().__init__(*args, **kwargs)
        self.runner = runner

    def create_session(self, prompt, run_duration_s=300, **kwargs):
        return super().create_session(prompt, run_duration_s,
            runner_name=self.runner["name"], email=self.runner.get("email") or "")
