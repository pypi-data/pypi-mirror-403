# Copyright 2026 Splunk Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import json
import logging
import subprocess

from .search_client import SearchClient
from ..jobs.cli_job import CLIAssertionJob, CLISimpleJob
from ..jobs.job import Job

_LOGGER = logging.getLogger(__name__)


class CLISearchClient(SearchClient):
    """Search client responsible for running jobs on CLI."""

    jobs_dict = {}

    def __init__(self, cli_bench=None):
        """Initialize CLISearchClient with optional bench parameter.

        Args:
            cli_bench: Number of events to use for benchmarking (adds -b and -n flags)
        """
        self.cli_bench = cli_bench

    @staticmethod
    def create_job(
        test_module: str, code_file_name: str, code_to_test: str, test_statement: str
    ) -> Job:
        """Creates a job for unit test run."""
        return CLIAssertionJob(
            test_module, code_file_name, code_to_test, test_statement
        ).create()

    def create_simple_job(
        self, source: str, code_module_name: str, code_module_content, test_name
    ) -> Job:
        """Creates a job for box test run."""

        return CLISimpleJob(
            source, code_module_name, code_module_content, test_name, self.cli_bench
        ).create()

    def run_job(self, job):
        """Run a job on CLI."""
        result = subprocess.run(
            job.job_content["command"],
            input=job.job_content["input_data"],  # Pass data to stdin
            text=True,  # Encode input_data as string
            capture_output=True,
        )

        # When cli_bench is enabled, print output and always succeed
        if self.cli_bench is not None:
            # Set empty result to avoid json parsing errors
            job.result = {}

            self._print_bench_results(job, result)
            return

        # Normal mode - raise errors as before
        if result.stderr:
            raise RuntimeError(result.stderr)

        job.result = json.loads(result.stdout)
        return

    def _print_bench_results(self, job, result):
        """Print benchmark results to logs."""
        _LOGGER.info("=" * 80)
        _LOGGER.info("CLI BENCH MODE - Test: %s", job.test_name)
        _LOGGER.info("=" * 80)

        if result.stdout:
            _LOGGER.info("STDOUT:\n%s", result.stdout)

        if result.stderr:
            _LOGGER.info("STDERR:\n%s", result.stderr)

        _LOGGER.info("=" * 80)
        _LOGGER.info("Return Code: %s", result.returncode)
        _LOGGER.info("=" * 80)

    def get_job_results(self, job: Job) -> dict:
        """Get results of a job."""
        # When cli_bench is enabled, return empty results to skip validation
        if self.cli_bench is not None:
            return {}

        tmp = {  # remove job_ prefix
            k.replace("job_", ""): v for k, v in job.result.items()
        }  # TODO for python>3.9 use str.remove_prefix

        results = self._cast_results(tmp)
        return results
