"""Load tests for HGitaly.

This simple script assumes that the HGitaly server has a given set of
repositories:

They must absolutely be dedicated to the task, because the load tests
may involve mutation calls. Hence the script expects the HGitaly server
to operate on its own separate repositories root and will clone everything
if needed.

Future facilities:

- configuring and launching RHGitaly
"""
import argparse
import json
import logging
import random
import statistics
import threading
import multiprocessing as mp
import time
from urllib.parse import urlparse

import grpc

from hgitaly import feature
from hgitaly.servicer import (
    SKIP_HOOKS_MD_KEY,
    NATIVE_PROJECT_MD_KEY,
)

from hgitaly.stub.commit_pb2_grpc import CommitServiceStub
from hgitaly.stub.commit_pb2 import (
    CountCommitsRequest,
    FindCommitsRequest,
)
from hgitaly.stub.mercurial_operations_pb2 import (
    InvalidateMergeAnalysisRequest,
    MergeAnalysisRequest,
)
from hgitaly.stub.mercurial_operations_pb2_grpc import (
    MercurialOperationsServiceStub,
)
from hgitaly.stub.mercurial_repository_pb2_grpc import (
    MercurialRepositoryServiceStub,
)
from hgitaly.stub.mercurial_repository_pb2 import (
    HgCallRequest,
)
from hgitaly.stub.repository_pb2_grpc import RepositoryServiceStub
from hgitaly.stub.repository_pb2 import (
    CreateRepositoryRequest,
    RepositoryExistsRequest,
)
from hgitaly.stub.shared_pb2 import (
    Repository,
)

FOSS_HEPTAPOD = 'https://foss.heptapod.net'

logger = logging.getLogger(__name__)


def gl_repo(relpath):
    return Repository(storage_name='default', relative_path=relpath)


class LoadWorker:

    weighted_methods = (
        ('find_commits_mercurial_devel', 9),
        ('sleep_a_bit', 1),
        ('merge_analysis_mercurial_devel', 1),
    )
    repositories = {
        'mercurial-devel': FOSS_HEPTAPOD + '/mercurial/mercurial-devel',
    }
    feature_flags = ()

    @classmethod
    def compute_random_thresholds(cls):
        total_weight = sum(wm[1] for wm in cls.weighted_methods)

        thresholds = []
        current = 0
        for meth, weight in cls.weighted_methods:
            thresholds.append((current, meth))
            current += weight / total_weight
        cls.random_thresholds = thresholds

    @classmethod
    def random_method(cls):
        rand = random.random()
        candidate = cls.random_thresholds[0][0]
        for thr, name in cls.random_thresholds:
            if thr > rand:
                break
            candidate = name
        return candidate

    def __init__(self, url, queue, wid=None):
        self.url = url = urlparse(url)
        self.queue = queue

        if url.scheme != 'tcp':
            raise RuntimeError("Unsupported URL scheme: %r" % url.scheme)
        if wid is not None:
            logger.info("Worker %d starting", wid)
        self.channel = grpc.insecure_channel(url.netloc)
        self.hg_operations_service = MercurialOperationsServiceStub(
            self.channel)
        self.hg_repository_service = MercurialRepositoryServiceStub(
            self.channel)
        self.repository_service = RepositoryServiceStub(self.channel)
        self.commit_service = CommitServiceStub(self.channel)

    def close(self):
        self.channel.close()

    def grpc_metadata(self):
        mds = feature.as_grpc_metadata(self.feature_flags)
        mds.append((SKIP_HOOKS_MD_KEY, 'true'))
        mds.append((NATIVE_PROJECT_MD_KEY, 'true'))
        return mds

    def repo_exists(self, relpath):
        return self.repository_service.RepositoryExists(
            RepositoryExistsRequest(repository=gl_repo(relpath))
        ).exists

    def ensure_repos(self):
        for relpath in self.repositories:
            if self.repo_exists(relpath):
                logger.info("Repository %r is present", relpath)
            else:
                self.import_repo(relpath)

    def import_repo(self, relpath):
        logger.warning("Importing repository %r", relpath)
        self.repository_service.CreateRepository(
            CreateRepositoryRequest(repository=gl_repo(relpath))
        )

        src_url = self.repositories[relpath]
        self.hg_call(relpath,
                     (b"pull", b"-q",
                      b"--config", b"heptapod.initial-import=yes",
                      src_url.encode('ascii')),
                     timeout=3600)

    def hg_call(self, relpath, args, timeout=30):
        exit_code = -1
        for resp in self.hg_repository_service.HgCall(
            HgCallRequest(repository=gl_repo(relpath),
                          args=args),
            metadata=self.grpc_metadata(),
            timeout=timeout,
        ):
            exit_code = resp.exit_code
        if exit_code != 0:
            raise RuntimeError(f"HgCall exit code {exit_code}")

    def run_one(self, name):
        start = time.time()
        try:
            getattr(self, name)()
            code = 'OK'
        except grpc.RpcError as exc:
            code = exc.code().name
            if self.queue is None:
                logger.error(
                    "Failed request when checking before actual load test"
                )
                raise

        elapsed = time.time() - start

        if self.queue is None:
            logger.info("Ran %r in %d ms", name, elapsed * 1000)
        else:
            self.queue.put((name, code, elapsed), block=False, timeout=1)

    def run_test(self, iterations):
        for i in range(iterations):
            meth = self.random_method()
            logger.info("Iteration %d, running %r", i + 1, meth)
            self.run_one(meth)

    def sleep_a_bit(self):
        # this can make RHGitaly find there are too many idle workers
        # and recycle them, leading to interesting problems because of
        # long HGitaly startup time.
        time.sleep(2)

    def find_commits_mercurial_devel(self):
        count = 0
        future = self.commit_service.FindCommits(FindCommitsRequest(
            repository=gl_repo('mercurial-devel'),
            revision=b'branch/default',
            limit=100000,
            paths=[b'rust/hg-core/Cargo.toml'],
        ))

        # see also `streaming_future_with_cancellation()`
        for resp in future:
            count += len(resp.commits)

        logger.debug("Got FindCommits response with %d commits", count)

    def count_commits_mercurial_devel(self):
        resp = self.commit_service.CountCommits(CountCommitsRequest(
            repository=gl_repo('mercurial-devel'),
            revision=b'branch/default',
        ))
        logger.debug("Got FindCommits response with %d commits", resp.count)

    def merge_analysis_mercurial_devel(self):
        repo = gl_repo('mercurial-devel')
        self.hg_operations_service.InvalidateMergeAnalysis(
            InvalidateMergeAnalysisRequest(repository=repo)
        )
        # an actual merge, without conflicts
        future = self.hg_operations_service.MergeAnalysis.future(
            MergeAnalysisRequest(
                repository=repo,
                source_revision=b'412fd1f5d8bc',
                target_revision=b'ff85442d08d7',
            ),
            timeout=120)
        future.result()  # see also unary_future_with_cancellation()

    def assert_requests(self):
        """Run all requiests exactly once.

        If one of them fails (typically due to a programming mistake),
        better to know it before running thousands of them
        """
        for (name, _w) in self.weighted_methods:
            if name != 'sleep_a_bit':
                self.run_one(name)  # TODO check exit code


def cancel_in(future, ms):
    time.sleep(ms / 1000)
    logger.info("Client-side cancellation")
    future.cancel()


def spawn_cancel_thread(*args):
    t = threading.Thread(target=cancel_in, args=args)
    t.start()
    return t


def unary_future_with_cancellation(future, cancel_in_ms):
    """Actually send the request, but cancel it first."""
    t = spawn_cancel_thread(future, cancel_in_ms)
    try:
        return future.result()
    finally:
        t.join()


def streaming_future_with_cancellation(future, cancel_in_ms):
    """Actually send the request, but cancel it first."""
    t = spawn_cancel_thread(future, cancel_in_ms)
    try:
        for resp in future:
            yield resp
    finally:
        t.join()


LoadWorker.compute_random_thresholds()
x = LoadWorker.random_method()
x = LoadWorker.random_method()
x = LoadWorker.random_method()


def worker(wid, url, queue, iterations):
    worker = LoadWorker(url, queue, wid=wid)
    worker.run_test(iterations)
    queue.put(('DONE', wid))


def load_test():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        description=__doc__)

    parser.add_argument('--url', '--rhgitaly-url',
                        help="URL of the RHGitaly server",
                        default='tcp://127.0.0.1:9237')
    parser.add_argument('-c', '--concurrency', type=int, default=6)
    parser.add_argument('--iterations', type=int, default=1000,
                        help="Number of iteration per client worker")
    parser.add_argument('-l', '--logging-level', default='info')
    cl_args = parser.parse_args()

    logging.basicConfig(level=getattr(logging,
                                      cl_args.logging_level.upper()))

    concurrency = cl_args.concurrency

    prepare_worker = LoadWorker(cl_args.url, queue=None)
    prepare_worker.ensure_repos()
    prepare_worker.assert_requests()
    prepare_worker.close()

    logger.warning("Preflight check of all requests passed. Proceeding to "
                   "actual load test")

    queue = mp.Queue()

    ctx = mp.get_context('fork')
    processes = [ctx.Process(target=worker,
                             args=(i, cl_args.url, queue, cl_args.iterations))
                 for i in range(concurrency)]

    for p in processes:
        p.start()

    done_process_ids = []
    results = {}
    while len(done_process_ids) < len(processes):
        res = queue.get()
        if res[0] == 'DONE':
            wid = res[1]
            processes[wid].join()
            done_process_ids.append(wid)
            logger.warning("Worker %d is done", wid)
        else:
            (results.setdefault(res[1], {})
             .setdefault(res[0], [])
             .append(res[2])
             )

    error_stats = {}
    for code, details in results.items():
        if code != 'OK':
            for name, times in details.items():
                error_stats.setdefault(name, {})[code] = dict(
                    count=len(times),
                    mean_time=statistics.mean(times)
                )

    successes = results.get('OK', {})
    stats = {}
    for name, times in successes.items():
        mstats = stats[name] = dict(
            count=len(times),
            median=statistics.mean(times),
            mean=statistics.median(times),
            standard_deviation=statistics.pstdev(times),
        )
        if len(times) > 1:

            deciles = statistics.quantiles(times, method='inclusive', n=10)
            centiles = statistics.quantiles(times, method='inclusive',
                                            n=100)
            mstats["best_centile"] = centiles[0]
            mstats["best_decile"] = deciles[0],
            mstats["worst_centile"] = centiles[-1],
            mstats["worst_decile"] = deciles[-1],

            print(f"\n\nRESULTS for concurrency={concurrency}: ")
    print(json.dumps(stats, indent=2))

    if error_stats:
        print(f"\n\nERRORS for concurrency={concurrency}: ")
        print(json.dumps(error_stats, indent=2))
