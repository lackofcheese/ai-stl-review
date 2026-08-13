#!/usr/bin/env python3
"""Dispatch one content-bound hint to the private Discord worker.

This is a source-side wakeup only.  It never reads worker contents, loads a
Discord credential, reconciles source state, or claims that delivery occurred.
"""
import argparse
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sys
import time
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode, urlparse
from urllib.request import Request, urlopen


WORKER_REPOSITORY = 'lackofcheese/ai-stl-discord'
WORKER_WORKFLOW = 'reconcile.yml'
WORKER_REF = 'main'
SOURCE_REPOSITORIES = frozenset({
    'lackofcheese/ai-stl-pipeline',
    'lackofcheese/ai-stl-review',
})
COMMIT_RE = re.compile(r'^[0-9a-f]{40}$')
REQUEST_RE = re.compile(r'^discord-wakeup-[0-9a-f]{64}$')
RUN_STATUSES = frozenset({
    'requested', 'waiting', 'pending', 'queued', 'in_progress', 'completed',
})


class WakeupError(RuntimeError):
    """The worker wakeup could not be dispatched or proved exactly."""


def canonical_digest(value):
    encoded = json.dumps(
        value, ensure_ascii=False, separators=(',', ':'), sort_keys=True,
    ).encode('utf-8')
    return hashlib.sha256(encoded).hexdigest()


def request_id(*, source_repository, source_commit, source_workflow_run_id,
               requested_at):
    fields = {
        'source_repository': source_repository,
        'source_commit': source_commit,
        'source_workflow_run_id': source_workflow_run_id,
        'requested_at': requested_at,
    }
    return f'discord-wakeup-{canonical_digest({"discord_wakeup_v1": fields})}'


@dataclass(frozen=True)
class WakeupRequest:
    request_id: str
    source_repository: str
    source_commit: str
    source_workflow_run_id: int
    requested_at: int

    @classmethod
    def create(cls, *, source_repository, source_commit,
               source_workflow_run_id, requested_at):
        fields = {
            'source_repository': source_repository,
            'source_commit': source_commit,
            'source_workflow_run_id': source_workflow_run_id,
            'requested_at': requested_at,
        }
        return cls(request_id=request_id(**fields), **fields)

    def __post_init__(self):
        if self.source_repository not in SOURCE_REPOSITORIES:
            raise ValueError('source_repository is not an authorized wakeup source')
        if not COMMIT_RE.fullmatch(self.source_commit):
            raise ValueError('source_commit must be a lowercase 40-character commit')
        for value, name in (
                (self.source_workflow_run_id, 'source_workflow_run_id'),
                (self.requested_at, 'requested_at')):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f'{name} must be a positive integer')
        expected = request_id(
            source_repository=self.source_repository,
            source_commit=self.source_commit,
            source_workflow_run_id=self.source_workflow_run_id,
            requested_at=self.requested_at,
        )
        if not REQUEST_RE.fullmatch(self.request_id) or self.request_id != expected:
            raise ValueError('request_id does not match the exact source wakeup')

    def inputs(self):
        return {
            'request_id': self.request_id,
            'source_repository': self.source_repository,
            'source_commit': self.source_commit,
            'source_workflow_run_id': str(self.source_workflow_run_id),
            'requested_at': str(self.requested_at),
        }


@dataclass(frozen=True)
class WorkerRun:
    run_id: int
    run_attempt: int
    head_sha: str
    url: str
    dispatched: bool


def default_transport(method, url, headers, body, timeout):
    request = Request(url, data=body, headers=dict(headers), method=method)
    try:
        with urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except HTTPError as error:
        return error.code, error.read()
    except (OSError, URLError) as error:
        raise WakeupError(f'GitHub Actions request failed: {error}') from error


class ActionsClient:
    """Dispatch the fixed worker workflow and prove its exact successful run."""

    def __init__(self, token, *, transport=None, api_url='https://api.github.com',
                 request_timeout=15.0):
        if not token:
            raise ValueError('token must not be empty')
        parsed = urlparse(api_url)
        if (parsed.scheme not in {'http', 'https'} or not parsed.netloc
                or parsed.username or parsed.password):
            raise ValueError('api_url must be an absolute credential-free HTTP(S) URL')
        if request_timeout <= 0:
            raise ValueError('request_timeout must be positive')
        self.token = token
        self.transport = transport or default_transport
        self.api_url = api_url.rstrip('/')
        self.request_timeout = request_timeout

    def dispatch_and_resolve(self, wakeup, *, timeout=30.0, poll_interval=2.0,
                             settle_time=2.0, monotonic=time.monotonic,
                             sleep=time.sleep, wall_time=time.time):
        if timeout < 0 or poll_interval <= 0 or settle_time < 0:
            raise ValueError('timeouts must be non-negative and poll interval positive')
        now = int(wall_time())
        if wakeup.requested_at > now + 300 or wakeup.requested_at < now - 3600:
            raise WakeupError('wakeup request is outside the bounded dispatch window')

        existing = self._matching_run(wakeup, now=now)
        if existing is not None:
            match = self._settled_match(
                wakeup, existing, now=now, timeout=timeout,
                poll_interval=poll_interval, settle_time=settle_time,
                monotonic=monotonic, sleep=sleep,
            )
            return WorkerRun(**match, dispatched=False)

        body = json.dumps(
            {'ref': WORKER_REF, 'inputs': wakeup.inputs()},
            ensure_ascii=False, separators=(',', ':'), sort_keys=True,
        ).encode('utf-8')
        status, response = self._request(
            'POST', self._workflow_path('/dispatches'), body,
        )
        if status != 204:
            raise WakeupError(
                f'GitHub workflow dispatch returned HTTP {status}: '
                f'{safe_error(response)}')

        deadline = monotonic() + timeout
        first_seen_at = None
        candidate = None
        while True:
            matched = self._matching_run(wakeup, now=now)
            if matched is not None:
                if candidate is None:
                    candidate = matched
                    first_seen_at = monotonic()
                elif matched != candidate:
                    raise WakeupError(
                        'the exact workflow run changed during resolution')
                if monotonic() - first_seen_at >= settle_time:
                    return WorkerRun(**candidate, dispatched=True)
            elif candidate is not None:
                raise WakeupError(
                    'the exact workflow run disappeared during resolution')
            if monotonic() >= deadline:
                raise WakeupError('the exact dispatched workflow run did not appear')
            sleep(min(poll_interval, max(0.0, deadline - monotonic())))

    def wait_for_success(self, wakeup, worker_run, *, timeout=360.0,
                         poll_interval=3.0, monotonic=time.monotonic,
                         sleep=time.sleep, wall_time=time.time):
        if timeout < 0 or poll_interval <= 0:
            raise ValueError('timeout must be non-negative and poll interval positive')
        deadline = monotonic() + timeout
        path = f'/repos/{WORKER_REPOSITORY}/actions/runs/{worker_run.run_id}'
        while True:
            status, body = self._request('GET', path, None)
            if status != 200:
                raise WakeupError(
                    f'GitHub workflow-run status returned HTTP {status}: '
                    f'{safe_error(body)}')
            payload = parse_object(body, 'workflow-run status')
            self._validate_run_identity(payload, wakeup, worker_run)
            run_status = payload.get('status')
            conclusion = payload.get('conclusion')
            if run_status not in RUN_STATUSES:
                raise WakeupError('the exact workflow run has an unknown status')
            if run_status == 'completed':
                if conclusion != 'success':
                    raise WakeupError(
                        f'the exact worker workflow completed with {conclusion!r}')
                final = self._matching_run(wakeup, now=int(wall_time()))
                expected = {
                    'run_id': worker_run.run_id,
                    'run_attempt': worker_run.run_attempt,
                    'head_sha': worker_run.head_sha,
                    'url': worker_run.url,
                }
                if final != expected:
                    raise WakeupError(
                        'the exact workflow run changed after completion')
                status, body = self._request('GET', path, None)
                if status != 200:
                    raise WakeupError(
                        f'GitHub workflow-run status returned HTTP {status}: '
                        f'{safe_error(body)}')
                final_payload = parse_object(body, 'workflow-run status')
                self._validate_run_identity(final_payload, wakeup, worker_run)
                if (final_payload.get('status') != 'completed'
                        or final_payload.get('conclusion') != 'success'):
                    raise WakeupError(
                        'the exact workflow run changed after completion')
                return {
                    'status': 'success',
                    'request_id': wakeup.request_id,
                    **asdict(worker_run),
                }
            if conclusion is not None:
                raise WakeupError('an unfinished workflow run has a conclusion')
            if monotonic() >= deadline:
                raise WakeupError('the exact worker workflow did not complete in time')
            sleep(min(poll_interval, max(0.0, deadline - monotonic())))

    def _settled_match(self, wakeup, initial, *, now, timeout, poll_interval,
                       settle_time, monotonic, sleep):
        deadline = monotonic() + timeout
        first_seen_at = monotonic()
        matched = initial
        while monotonic() - first_seen_at < settle_time:
            if monotonic() >= deadline:
                raise WakeupError('the exact workflow run did not remain unique')
            sleep(min(poll_interval, max(0.0, deadline - monotonic())))
            matched = self._matching_run(wakeup, now=now)
            if matched is None:
                raise WakeupError('the exact workflow run disappeared during resolution')
            if matched != initial:
                raise WakeupError('the exact workflow run changed during resolution')
        return matched

    def _matching_run(self, wakeup, *, now):
        matches = []
        created = f'{iso8601(wakeup.requested_at - 300)}..{iso8601(now + 300)}'
        page = 1
        while True:
            query = urlencode({
                'event': 'workflow_dispatch', 'branch': WORKER_REF,
                'per_page': 100, 'page': page, 'created': created,
            })
            status, body = self._request(
                'GET', self._workflow_path(f'/runs?{query}'), None,
            )
            if status != 200:
                raise WakeupError(
                    f'GitHub workflow-run lookup returned HTTP {status}: '
                    f'{safe_error(body)}')
            payload = parse_object(body, 'workflow-run collection')
            runs = payload.get('workflow_runs')
            total = payload.get('total_count')
            if (not isinstance(runs, list) or isinstance(total, bool)
                    or not isinstance(total, int) or total < 0):
                raise WakeupError('GitHub returned an invalid workflow-run collection')
            if total > 1000:
                raise WakeupError(
                    'dispatch-window workflow history exceeds the bounded uniqueness scan')
            for item in runs:
                if not isinstance(item, dict):
                    raise WakeupError('GitHub returned a malformed workflow run')
                if not self._is_matching_identity(item, wakeup):
                    continue
                matches.append(self._run_identity(item))
            if page * 100 >= total:
                break
            if not runs:
                raise WakeupError('GitHub truncated the workflow-run uniqueness scan')
            page += 1
        if len(matches) > 1:
            raise WakeupError('multiple workflow runs match the supposedly unique request id')
        return matches[0] if matches else None

    @staticmethod
    def _is_matching_identity(payload, wakeup):
        expected = f'.github/workflows/{WORKER_WORKFLOW}'
        return (
            payload.get('display_title') == wakeup.request_id
            and payload.get('event') == 'workflow_dispatch'
            and payload.get('head_branch') == WORKER_REF
            and payload.get('path') in {expected, f'{expected}@{WORKER_REF}'}
        )

    @staticmethod
    def _run_identity(payload):
        run_id = payload.get('id')
        run_attempt = payload.get('run_attempt')
        head_sha = payload.get('head_sha')
        url = payload.get('html_url')
        if (isinstance(run_id, bool) or not isinstance(run_id, int) or run_id < 1
                or isinstance(run_attempt, bool)
                or not isinstance(run_attempt, int) or run_attempt < 1
                or not isinstance(head_sha, str) or not COMMIT_RE.fullmatch(head_sha)
                or not isinstance(url, str)
                or not url.startswith('https://github.com/')):
            raise WakeupError('the exact workflow run has malformed identity fields')
        return {
            'run_id': run_id,
            'run_attempt': run_attempt,
            'head_sha': head_sha,
            'url': url,
        }

    def _validate_run_identity(self, payload, wakeup, worker_run):
        if not self._is_matching_identity(payload, wakeup):
            raise WakeupError('the resolved workflow run changed identity')
        if self._run_identity(payload) != {
                'run_id': worker_run.run_id,
                'run_attempt': worker_run.run_attempt,
                'head_sha': worker_run.head_sha,
                'url': worker_run.url}:
            raise WakeupError('the resolved workflow run changed identity')

    @staticmethod
    def _workflow_path(suffix):
        workflow = quote(WORKER_WORKFLOW, safe='')
        return (f'/repos/{WORKER_REPOSITORY}/actions/workflows/'
                f'{workflow}{suffix}')

    def _request(self, method, path, body):
        return self.transport(
            method, f'{self.api_url}{path}', {
                'Accept': 'application/vnd.github+json',
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json',
                'X-GitHub-Api-Version': '2022-11-28',
            }, body, self.request_timeout,
        )


def parse_object(body, source):
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise WakeupError(f'GitHub returned invalid {source} JSON') from error
    if not isinstance(payload, dict):
        raise WakeupError(f'GitHub returned an invalid {source}')
    return payload


def safe_error(body):
    try:
        payload = json.loads(body)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return 'unparseable response'
    if isinstance(payload, dict) and isinstance(payload.get('message'), str):
        return payload['message'][:240]
    return 'unexpected response'


def iso8601(timestamp):
    return datetime.fromtimestamp(max(0, timestamp), timezone.utc).strftime(
        '%Y-%m-%dT%H:%M:%SZ')


def parser():
    result = argparse.ArgumentParser(
        description='Wake the private Discord reconciler and prove its exact run')
    result.add_argument('--source-repository', required=True)
    result.add_argument('--source-commit', required=True)
    result.add_argument('--source-workflow-run-id', required=True, type=int)
    result.add_argument('--requested-at', required=True, type=int)
    result.add_argument('--token-environment',
                        default='AI_STL_DISCORD_ACTIONS_TOKEN')
    result.add_argument('--resolve-timeout', type=float, default=30.0)
    result.add_argument('--completion-timeout', type=float, default=360.0)
    return result


def public_success(wakeup, outcome):
    """Return the public-log-safe proof of one successful worker wakeup."""
    if (outcome.get('status') != 'success'
            or outcome.get('request_id') != wakeup.request_id):
        raise WakeupError('worker success does not match the exact wakeup request')
    return {'request_id': wakeup.request_id, 'status': 'success'}


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        token = os.environ.get(args.token_environment)
        if not token:
            raise WakeupError(
                f'required token environment {args.token_environment!r} is unset')
        wakeup = WakeupRequest.create(
            source_repository=args.source_repository,
            source_commit=args.source_commit,
            source_workflow_run_id=args.source_workflow_run_id,
            requested_at=args.requested_at,
        )
        client = ActionsClient(token)
        worker_run = client.dispatch_and_resolve(
            wakeup, timeout=args.resolve_timeout)
        outcome = client.wait_for_success(
            wakeup, worker_run, timeout=args.completion_timeout)
        json.dump(public_success(wakeup, outcome), sys.stdout,
                  ensure_ascii=False, indent=2, sort_keys=True)
        sys.stdout.write('\n')
        return 0
    except (ValueError, WakeupError) as error:
        print(f'discord_wakeup: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
