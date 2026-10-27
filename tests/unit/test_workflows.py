import re
import subprocess
from pathlib import Path

import pytest
import yaml

WORKFLOWS_DIR = Path(__file__).resolve().parents[2] / '.github' / 'workflows'
WORKFLOW_FILES = sorted([*WORKFLOWS_DIR.glob('*.yml'), *WORKFLOWS_DIR.glob('*.yaml')])
RELEASE_WORKFLOWS = ['deploy.yml', 'test_on_deploy.yml']
# GitHub matches runner labels case-insensitively.
SELF_HOSTED_RUNNER = re.compile(r'\b(mdb-dev|mdb-prod|self-hosted)\b', re.IGNORECASE)
PINNED_ACTION = re.compile(r'uses:\s+[^@\s]+@[0-9a-f]{40}\s+#\s*v\d')


def _load(name):
    return yaml.safe_load((WORKFLOWS_DIR / name).read_text())


def _integration_test_step(job):
    return next(step for step in job['steps'] if 'pytest tests/integration' in step.get('run', ''))


@pytest.mark.parametrize('path', WORKFLOW_FILES, ids=lambda path: path.name)
def test_workflow_names_no_self_hosted_runner(path):
    """GitHub recommends GitHub-hosted runners for public repositories such as this one.

    The check reads the raw file, so it also catches a label passed as a matrix value or as an
    input to a reusable workflow.
    """
    match = SELF_HOSTED_RUNNER.search(path.read_text())
    assert match is None, f'{path.name} names the self-hosted runner {match.group(0)!r}'


def test_release_tests_get_the_env_vars_the_integration_suite_reads():
    """tests/integration/config.py reads MINDS_API_BASE_URL and MINDS_API_TOKEN.

    Without MINDS_API_BASE_URL the suite fails at import, so the release run ends before any test
    runs.
    """
    pytest_step = _integration_test_step(_load('test_on_deploy.yml')['jobs']['test'])
    assert {'MINDS_API_BASE_URL', 'MINDS_API_TOKEN'} <= set(pytest_step['env'])


def test_a_failing_release_test_fails_the_release_run():
    """deploy.yml publishes only after a successful release run.

    continue-on-error on the job or the step, or '|| true' after pytest, would make every release run
    succeed, so a release whose tests failed would still publish.
    """
    job = _load('test_on_deploy.yml')['jobs']['test']
    pytest_step = _integration_test_step(job)
    assert 'continue-on-error' not in job
    assert 'continue-on-error' not in pytest_step
    assert '||' not in pytest_step['run']


def test_publish_runs_only_after_a_successful_release_run_from_this_repository():
    """deploy.yml's workflow_run trigger fires when any workflow named "Run Integration Tests on
    Release" completes, whatever its event or head repository.

    These conditions let only a successful release run from this repository publish to PyPI.
    """
    condition = ' '.join(_load('deploy.yml')['jobs']['deploy_to_pypi']['if'].split())
    assert '||' not in condition
    assert set(condition.split(' && ')) >= {
        "github.event.workflow_run.conclusion == 'success'",
        "github.event.workflow_run.event == 'release'",
        "github.event.workflow_run.head_repository.full_name == github.repository",
    }


def test_publish_has_no_trigger_besides_workflow_run():
    """The zizmor ignore on deploy.yml's workflow_run line silences dangerous-triggers for every
    trigger under on:, so zizmor would stay quiet about a second one such as pull_request_target.
    """
    # PyYAML reads the bare key on as the boolean True.
    assert set(_load('deploy.yml')[True]) == {'workflow_run'}


def test_publish_builds_the_commit_the_release_tests_ran_on():
    """Without a ref, checkout under workflow_run takes the default branch's head, which can be newer
    than the release."""
    steps = _load('deploy.yml')['jobs']['deploy_to_pypi']['steps']
    checkout = next(step for step in steps if step.get('uses', '').startswith('actions/checkout@'))
    assert checkout.get('with', {}).get('ref') == '${{ github.event.workflow_run.head_sha }}'


def _publish_steps():
    return _load('deploy.yml')['jobs']['deploy_to_pypi']['steps']


def _git(repo, *args):
    return subprocess.run(['git', '-C', str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


@pytest.fixture
def history(tmp_path):
    """A clone whose origin/main holds one commit, and a release commit that never merged."""
    _git(tmp_path, 'init', '-q')
    _git(tmp_path, '-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-q', '--allow-empty', '-m', 'main')
    on_main = _git(tmp_path, 'rev-parse', 'HEAD')
    _git(tmp_path, 'update-ref', 'refs/remotes/origin/main', on_main)
    _git(tmp_path, '-c', 'user.name=t', '-c', 'user.email=t@example.com', 'commit', '-q', '--allow-empty', '-m', 'branch')
    return tmp_path, on_main, _git(tmp_path, 'rev-parse', 'HEAD')


def _check_main_holds(repo, head_sha):
    step = next(step for step in _publish_steps() if step.get('name') == 'Check that main holds the commit')
    assert step['env'] == {'HEAD_SHA': '${{ github.event.workflow_run.head_sha }}'}
    return subprocess.run(
        ['bash', '-e', '-c', step['run']], cwd=repo, env={'HEAD_SHA': head_sha, 'PATH': '/usr/bin:/bin'},
        capture_output=True, text=True,
    )


def test_publish_refuses_a_release_commit_that_main_does_not_hold(history):
    """A writer can tag a branch commit, and that commit's test workflow can pass."""
    repo, _, off_main = history
    result = _check_main_holds(repo, off_main)
    assert result.returncode == 1
    assert f'::error::{off_main} is not on main' in result.stdout


def test_publish_builds_a_release_commit_that_main_holds(history):
    repo, on_main, _ = history
    assert _check_main_holds(repo, on_main).returncode == 0


def test_the_main_check_has_the_history_and_runs_before_the_upload():
    steps = _publish_steps()
    checkout = next(step for step in steps if step.get('uses', '').startswith('actions/checkout@'))
    assert checkout['with']['fetch-depth'] == 0
    names = [step.get('name') for step in steps]
    assert names.index('Check that main holds the commit') < names.index('Build and publish')


@pytest.mark.parametrize('name', RELEASE_WORKFLOWS)
def test_release_workflows_pin_every_action_to_a_commit(name):
    """These workflows run with PYPI_PASSWORD or MINDS_API_KEY. Whoever moves an action's tag decides
    what that action runs, so each one is pinned to a commit.

    The check reads the raw file, because the parsed YAML drops the version comment.
    """
    lines = [line.strip() for line in (WORKFLOWS_DIR / name).read_text().splitlines() if 'uses:' in line]
    assert [line for line in lines if not PINNED_ACTION.search(line)] == []


@pytest.mark.parametrize('name', RELEASE_WORKFLOWS)
def test_release_checkouts_keep_the_token_out_of_git_config(name):
    """Without persist-credentials: false, checkout writes the job's GITHUB_TOKEN into .git/config,
    where every later step, including setup.py and the integration tests, can read it."""
    steps = [step for job in _load(name)['jobs'].values() for step in job['steps']]
    checkouts = [step for step in steps if step.get('uses', '').startswith('actions/checkout@')]
    assert all(step.get('with', {}).get('persist-credentials') is False for step in checkouts)
