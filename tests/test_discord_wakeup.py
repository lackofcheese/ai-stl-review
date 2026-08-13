import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import discord_wakeup  # noqa: E402


COMMIT = 'a' * 40
HEAD = 'b' * 40
NOW = 2_000_000_000


def run_payload(request_id, *, run_id=123, run_attempt=1, status='queued',
                conclusion=None):
    return {
        'id': run_id,
        'run_attempt': run_attempt,
        'display_title': request_id,
        'event': 'workflow_dispatch',
        'head_branch': 'main',
        'head_sha': HEAD,
        'path': '.github/workflows/reconcile.yml@main',
        'html_url': (
            f'https://github.com/lackofcheese/ai-stl-discord/actions/runs/{run_id}'),
        'status': status,
        'conclusion': conclusion,
    }


class WakeupRequestTests(unittest.TestCase):
    def test_isolated_entrypoint_ignores_script_directory_imports(self):
        with tempfile.TemporaryDirectory() as directory:
            scripts = Path(directory) / 'scripts'
            scripts.mkdir()
            helper = scripts / 'discord_wakeup.py'
            shutil.copy2(ROOT / 'scripts/discord_wakeup.py', helper)
            marker = scripts / 'shadow-loaded'
            (scripts / 'argparse.py').write_text(
                "from pathlib import Path\n"
                "Path(__file__).with_name('shadow-loaded').write_text('loaded')\n"
                "raise RuntimeError('shadow module loaded')\n",
                encoding='utf-8',
            )
            environment = os.environ.copy()
            environment['AI_STL_DISCORD_ACTIONS_TOKEN'] = 'test-only-token'
            result = subprocess.run(
                [sys.executable, '-I', '-B', str(helper), '--help'],
                capture_output=True,
                check=False,
                env=environment,
                text=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse(marker.exists())

    def test_request_id_matches_the_private_worker_contract_vector(self):
        request = discord_wakeup.WakeupRequest.create(
            source_repository='lackofcheese/ai-stl-review',
            source_commit=COMMIT,
            source_workflow_run_id=42,
            requested_at=NOW,
        )
        self.assertEqual(
            request.request_id,
            'discord-wakeup-018f9f5ed3cee423f4e5d970d745de95e170bb5a952'
            '900461e0b1fe8008e64cb',
        )
        self.assertEqual(request.inputs()['source_workflow_run_id'], '42')

    def test_request_rejects_unapproved_source_and_boolean_run_id(self):
        with self.assertRaisesRegex(ValueError, 'authorized wakeup source'):
            discord_wakeup.WakeupRequest.create(
                source_repository='example/other', source_commit=COMMIT,
                source_workflow_run_id=42, requested_at=NOW)
        with self.assertRaisesRegex(ValueError, 'positive integer'):
            discord_wakeup.WakeupRequest.create(
                source_repository='lackofcheese/ai-stl-review',
                source_commit=COMMIT, source_workflow_run_id=True,
                requested_at=NOW)

    def test_public_success_redacts_private_worker_identity(self):
        request = discord_wakeup.WakeupRequest.create(
            source_repository='lackofcheese/ai-stl-review',
            source_commit=COMMIT, source_workflow_run_id=42,
            requested_at=NOW)
        outcome = {
            'status': 'success', 'request_id': request.request_id,
            'run_id': 123, 'run_attempt': 2, 'head_sha': HEAD,
            'url': 'https://github.com/private/actions/runs/123',
            'dispatched': True,
        }
        public = discord_wakeup.public_success(request, outcome)
        self.assertEqual(public, {
            'request_id': request.request_id, 'status': 'success'})
        rendered = json.dumps(public)
        for private in ('run_id', 'run_attempt', 'head_sha', 'url', 'dispatched'):
            self.assertNotIn(private, rendered)

        outcome['request_id'] = 'discord-wakeup-' + '0' * 64
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'does not match'):
            discord_wakeup.public_success(request, outcome)


class ActionsClientTests(unittest.TestCase):
    def setUp(self):
        self.request = discord_wakeup.WakeupRequest.create(
            source_repository='lackofcheese/ai-stl-review',
            source_commit=COMMIT,
            source_workflow_run_id=42,
            requested_at=NOW,
        )

    def test_dispatch_resolves_only_exact_run_without_sending_token_in_body(self):
        calls = []
        responses = iter([
            (200, json.dumps({'total_count': 0, 'workflow_runs': []}).encode()),
            (204, b''),
            (200, json.dumps({'total_count': 2, 'workflow_runs': [
                run_payload('another-request', run_id=122),
                run_payload(self.request.request_id),
            ]}).encode()),
        ])

        def transport(method, url, headers, body, timeout):
            calls.append((method, url, headers, body, timeout))
            return next(responses)

        result = discord_wakeup.ActionsClient(
            'secret-token', transport=transport).dispatch_and_resolve(
                self.request, timeout=0, settle_time=0,
                wall_time=lambda: NOW)
        self.assertTrue(result.dispatched)
        self.assertEqual(result.run_id, 123)
        dispatched = json.loads(calls[1][3])
        self.assertEqual(dispatched['inputs'], self.request.inputs())
        self.assertNotIn('secret-token', calls[1][3].decode())

    def test_existing_exact_run_is_an_idempotent_retry(self):
        calls = []

        def transport(method, _url, _headers, _body, _timeout):
            calls.append(method)
            return 200, json.dumps({
                'total_count': 1,
                'workflow_runs': [run_payload(self.request.request_id)],
            }).encode()

        result = discord_wakeup.ActionsClient(
            'token', transport=transport).dispatch_and_resolve(
                self.request, settle_time=0, wall_time=lambda: NOW)
        self.assertFalse(result.dispatched)
        self.assertEqual(calls, ['GET'])

    def test_settlement_rejects_run_replacement_in_both_resolution_paths(self):
        first = run_payload(self.request.request_id, run_id=123)
        replacement = run_payload(self.request.request_id, run_id=124)
        responses = iter([
            (200, json.dumps({'total_count': 0, 'workflow_runs': []}).encode()),
            (204, b''),
            (200, json.dumps({
                'total_count': 1, 'workflow_runs': [first]}).encode()),
            (200, json.dumps({
                'total_count': 1, 'workflow_runs': [replacement]}).encode()),
        ])
        client = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: next(responses))
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'changed'):
            client.dispatch_and_resolve(
                self.request, timeout=5, settle_time=1,
                monotonic=lambda: 0.0, sleep=lambda _: None,
                wall_time=lambda: NOW)

        responses = iter([
            (200, json.dumps({
                'total_count': 1, 'workflow_runs': [first]}).encode()),
            (200, json.dumps({
                'total_count': 1, 'workflow_runs': [replacement]}).encode()),
        ])
        client = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: next(responses))
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'changed'):
            client.dispatch_and_resolve(
                self.request, timeout=5, settle_time=1,
                monotonic=lambda: 0.0, sleep=lambda _: None,
                wall_time=lambda: NOW)

    def test_request_window_and_api_origin_fail_closed(self):
        with self.assertRaisesRegex(ValueError, 'credential-free'):
            discord_wakeup.ActionsClient('token', api_url='https://secret@example.test')
        stale = discord_wakeup.WakeupRequest.create(
            source_repository='lackofcheese/ai-stl-review',
            source_commit=COMMIT, source_workflow_run_id=42,
            requested_at=NOW - 3601)
        client = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: self.fail('must not contact GitHub'))
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'bounded'):
            client.dispatch_and_resolve(stale, wall_time=lambda: NOW)

    def test_zero_multiple_and_malformed_matches_fail_closed(self):
        responses = iter([
            (200, json.dumps({'total_count': 0, 'workflow_runs': []}).encode()),
            (204, b''),
            (200, json.dumps({'total_count': 0, 'workflow_runs': []}).encode()),
        ])
        client = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: next(responses))
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'did not appear'):
            client.dispatch_and_resolve(
                self.request, timeout=0, settle_time=0,
                wall_time=lambda: NOW)

        duplicates = json.dumps({'total_count': 2, 'workflow_runs': [
            run_payload(self.request.request_id, run_id=123),
            run_payload(self.request.request_id, run_id=124),
        ]}).encode()
        client = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: (200, duplicates))
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'multiple'):
            client.dispatch_and_resolve(
                self.request, settle_time=0, wall_time=lambda: NOW)

        malformed = run_payload(self.request.request_id)
        malformed['head_sha'] = 'not-a-commit'
        client = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: (200, json.dumps({
                'total_count': 1, 'workflow_runs': [malformed]}).encode()))
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'malformed'):
            client.dispatch_and_resolve(
                self.request, settle_time=0, wall_time=lambda: NOW)

    def test_completion_waits_for_exact_success_and_rejects_failure(self):
        worker_run = discord_wakeup.WorkerRun(
            run_id=123, run_attempt=1, head_sha=HEAD,
            url='https://github.com/lackofcheese/ai-stl-discord/actions/runs/123',
            dispatched=True)
        responses = iter([
            (200, json.dumps(run_payload(
                self.request.request_id, status='requested')).encode()),
            (200, json.dumps(run_payload(
                self.request.request_id, status='waiting')).encode()),
            (200, json.dumps(run_payload(
                self.request.request_id, status='pending')).encode()),
            (200, json.dumps(run_payload(
                self.request.request_id, status='queued')).encode()),
            (200, json.dumps(run_payload(
                self.request.request_id, status='in_progress')).encode()),
            (200, json.dumps(run_payload(
                self.request.request_id, status='completed',
                conclusion='success')).encode()),
            (200, json.dumps({'total_count': 1, 'workflow_runs': [
                run_payload(self.request.request_id)]}).encode()),
            (200, json.dumps(run_payload(
                self.request.request_id, status='completed',
                conclusion='success')).encode()),
        ])
        result = discord_wakeup.ActionsClient(
            'token', transport=lambda *_: next(responses)).wait_for_success(
                self.request, worker_run, timeout=1, poll_interval=.1,
                monotonic=lambda: 0.0, sleep=lambda _: None,
                wall_time=lambda: NOW)
        self.assertEqual(result['status'], 'success')
        self.assertEqual(result['run_id'], 123)

        failed = json.dumps(run_payload(
            self.request.request_id, status='completed',
            conclusion='failure')).encode()
        with self.assertRaisesRegex(discord_wakeup.WakeupError, "'failure'"):
            discord_wakeup.ActionsClient(
                'token', transport=lambda *_: (200, failed)).wait_for_success(
                    self.request, worker_run, timeout=0)

    def test_completion_final_scan_rejects_a_delayed_duplicate(self):
        worker_run = discord_wakeup.WorkerRun(
            run_id=123, run_attempt=1, head_sha=HEAD,
            url='https://github.com/lackofcheese/ai-stl-discord/actions/runs/123',
            dispatched=True)
        completed = run_payload(
            self.request.request_id, status='completed', conclusion='success')
        duplicate = json.dumps({'total_count': 2, 'workflow_runs': [
            run_payload(self.request.request_id, run_id=123),
            run_payload(self.request.request_id, run_id=124),
        ]}).encode()
        responses = iter([(200, json.dumps(completed).encode()), (200, duplicate)])
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'multiple'):
            discord_wakeup.ActionsClient(
                'token', transport=lambda *_: next(responses)).wait_for_success(
                    self.request, worker_run, timeout=0, wall_time=lambda: NOW)

    def test_completion_rejects_changed_run_identity(self):
        worker_run = discord_wakeup.WorkerRun(
            run_id=123, run_attempt=1, head_sha=HEAD,
            url='https://github.com/lackofcheese/ai-stl-discord/actions/runs/123',
            dispatched=True)
        changed = run_payload(
            self.request.request_id, run_id=124, status='completed',
            conclusion='success')
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'changed identity'):
            discord_wakeup.ActionsClient(
                'token', transport=lambda *_: (
                    200, json.dumps(changed).encode())).wait_for_success(
                    self.request, worker_run, timeout=0)

    def test_completion_rechecks_attempt_after_the_uniqueness_scan(self):
        worker_run = discord_wakeup.WorkerRun(
            run_id=123, run_attempt=1, head_sha=HEAD,
            url='https://github.com/lackofcheese/ai-stl-discord/actions/runs/123',
            dispatched=True)
        completed = run_payload(
            self.request.request_id, status='completed', conclusion='success')
        rerun = run_payload(
            self.request.request_id, run_attempt=2, status='in_progress')
        responses = iter([
            (200, json.dumps(completed).encode()),
            (200, json.dumps({'total_count': 1, 'workflow_runs': [
                run_payload(self.request.request_id)]}).encode()),
            (200, json.dumps(rerun).encode()),
        ])
        with self.assertRaisesRegex(discord_wakeup.WakeupError, 'changed identity'):
            discord_wakeup.ActionsClient(
                'token', transport=lambda *_: next(responses)).wait_for_success(
                    self.request, worker_run, timeout=0, wall_time=lambda: NOW)


class WorkflowContractTests(unittest.TestCase):
    def test_workflow_is_main_only_and_has_no_discord_capability(self):
        workflow = (ROOT / '.github/workflows/discord-wakeup.yml').read_text()
        self.assertIn('push:\n    branches:\n      - main', workflow)
        self.assertNotIn('    paths:', workflow)
        self.assertNotIn('workflow_dispatch:', workflow)
        self.assertIn('permissions:\n  contents: read', workflow)
        self.assertIn(
            'uses: actions/checkout@'
            'de0fac2e4500dabe0009e67214ff5f5447ce83dd', workflow)
        helper_digest = hashlib.sha256(
            (ROOT / 'scripts/discord_wakeup.py').read_bytes()).hexdigest()
        verification = (
            f'echo "{helper_digest}  scripts/discord_wakeup.py"\n'
            '          | sha256sum --check --strict -')
        self.assertIn(verification, workflow)
        self.assertLess(
            workflow.index('      - name: Verify fixed wakeup helper'),
            workflow.index('      - name: Dispatch and prove exact worker run'))
        dispatch = workflow.split(
            '      - name: Dispatch and prove exact worker run\n', 1)[1]
        self.assertIn('        env:\n          AI_STL_DISCORD_ACTIONS_TOKEN:',
                      dispatch)
        self.assertIn('python -I -B scripts/discord_wakeup.py', dispatch)
        self.assertNotIn('    env:\n', workflow.split('    steps:\n', 1)[0])
        self.assertIn('--source-workflow-run-id "$GITHUB_RUN_ID"', workflow)
        self.assertNotIn('DISCORD_TOKEN', workflow)
        self.assertNotIn('contents: write', workflow)


if __name__ == '__main__':
    unittest.main()
