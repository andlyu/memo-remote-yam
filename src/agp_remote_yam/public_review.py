"""Public demo review; runner contacts and browser/control capabilities stay private."""
import re

PRIVATE_KEYS = {'owner', 'namespace', 'email', 'csrf', 'session_capability',
                'lease_id', 'episode_id', 'executor_token', 'token'}
EMAIL = re.compile(r'[A-Za-z0-9.!#$%&\'*+/=?^_`{|}~-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+')


def redact(value):
    if isinstance(value, dict):
        return {k:redact(v) for k,v in value.items() if k not in PRIVATE_KEYS}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return EMAIL.sub('[private contact]', value)
    return value


def is_demo(run):
    return run.get('approach') == 'MEMO'


def readable_file(name):
    # Share generated programs and observations, never transport/internal files.
    return name.startswith(('frames/', 'scratch/', 'goal/')) or name in (
        'FINAL.json', 'INITIAL_OBSERVATION.json', 'TASK.md', 'MEMO_CONTEXT.json')


def review(run, *, owned, foundation_model):
    value = redact(run)
    value.update(owned=owned, model='MEMO', foundation_model=run.get('foundation_model', foundation_model))
    if 'files' in value and not owned:
        value['files'] = [name for name in value['files'] if readable_file(name)]
    return value
