import json
import re
import time
from typing import Optional

import requests

from relationalai_gnns.common.exceptions import JobManagerError, JobMonitorError
from relationalai_gnns.common.job_models import JobStatus, JobTypes, PayloadTypes

from .api_request_handler import APIRequestHandler
from .connector import BaseConnector
from .utils import get_results_views


class JobHandler:
    def __init__(self, connector: BaseConnector):
        self.connector = connector
        self.base_url = f"{connector.endpoint_url}/v1alpha1"
        # Initalize API Handler
        self.api_handler = APIRequestHandler(self.connector)

    @staticmethod
    def _print_json(response: requests.Response):
        """Helper function, print .json payload of a Response object."""
        json_payload = response.json()
        print(json.dumps(json_payload, indent=4))


class JobMonitor(JobHandler):
    """Helper class to monitor a single job."""

    def __init__(self, connector: BaseConnector, job_id: str, job_type: Optional[str] = None):
        super().__init__(connector)
        self.job_id = job_id
        self.job_type = job_type

    def get_status(self):
        """Get the current job status."""
        try:
            payload = {"payload_type": PayloadTypes.REQUEST_JOB_STATUS, "job_id": self.job_id}

            response_data = self.api_handler.make_request(payload)

            if self.job_type in [JobTypes.INFERENCE, JobTypes.TRAIN_INFERENCE] and self.connector.is_native_app:
                source_views = get_results_views(response_data, self.connector.app_name)
                if source_views:
                    response_data["source_views"] = source_views

            return response_data

        except Exception as e:
            raise JobMonitorError(f"❌ Error retrieving job status: {str(e)}", code="get_status:Exception")

    @property
    def model_run_id(self) -> str:
        """
        Return the model run ID if the job is completed.

        Raises:
            JobMonitorError: If no model has been trained yet.
        """
        status_response = self.get_status()
        if status_response.get("status") == "COMPLETED":
            return self.job_id

        raise JobMonitorError(
            "❌ No model has been trained. Please train a model first.", code="model_run_id:RequestException"
        )

    @property
    def experiment_name(self):
        """Get the experiment name for the current job."""

        try:
            payload = {"payload_type": PayloadTypes.REQUEST_JOB_STATUS, "job_id": self.job_id}
            response_data = self.api_handler.make_request(payload)
            return response_data["experiment_name"]

        except Exception as e:
            raise JobMonitorError(f"❌ Error retrieving job experiment name: {e}", code="experiment_name:Exception")

    def register_model(
        self, model_name: str, version_name: str, database_name: str, schema_name: str, comment: Optional[str] = None
    ):
        """
        Registers a model in the Model Registry for the current job.

        This method attempts to register a trained model under the specified name.
        Registration is only allowed for jobs of type TRAIN or TRAIN_INFERENCE, and if
        a valid `model_run_id` exists. Duplicate version names for a job are not allowed.

        :param model_name: The name to assign to the registered model.
        :type model_name: str
        """

        if self.job_type is None:
            raise JobMonitorError(
                "❌ Cannot register model: job type is not set. The job may not have been fetched properly.",
                code="register_model:no_job_type",
            )

        if self.job_type not in [JobTypes.TRAIN, JobTypes.TRAIN_INFERENCE]:
            raise JobMonitorError(
                f"❌ Cannot register model for job type {self.job_type.value}.", code="register_model:bad_job_type"
            )

        if not self.model_run_id:
            raise JobMonitorError(
                "❌ Cannot register model with missing model_run_id.", code="register_model:no_model_run_id"
            )

        payload = {
            "payload_type": PayloadTypes.REGISTER_MODEL,
            "model_name": model_name,
            "version_name": version_name,
            "database_name": database_name,
            "schema_name": schema_name,
            "model_run_id": self.model_run_id,
            "experiment_name": self.experiment_name,
            "comment": comment,
        }

        try:
            registered_model = self.api_handler.make_request(payload)

            print(
                f"✅ Successfully registered model "
                f"'{registered_model['database_name']}.{registered_model['schema_name']}."
                f"{registered_model['model_name']}.{registered_model['version_name']}' "
                f"for job '{self.job_id}'"
            )

        except Exception as e:
            error_msg = re.sub(r"To auto-generate `version_name`, skip that argument\.", "", str(e)).strip()
            raise JobMonitorError(f"❌ Error during model registration: {error_msg}", code="register_model:Exception")

    def cancel(self):
        """Removes a job from the queue if the job is in the queue or terminates a running job if the job is active."""
        try:
            if not self.connector.is_native_app:
                url = f"{self.base_url}/jobs/cancel/{self.job_id}"
                response = requests.post(url, headers=self.connector.headers, timeout=60)
                response.raise_for_status()
                return self._print_json(response)
            else:
                self.connector.cancel_job(self.job_id)

        except requests.RequestException:
            error_message = self.api_handler._parse_request_exception(response)
            raise JobMonitorError(error_message, code="cancel:RequestException")

        except Exception as e:
            raise JobMonitorError(f"❌ Error canceling job: {e}", code="cancel:Exception")

    def stream_logs(self):
        """Monitor logs for a specific job ID and display them to the user."""

        print(f"\nMonitoring logs for job ID: {self.job_id}")
        print("-" * 80)

        try:
            if self.connector.is_native_app:
                self._stream_logs_is_native_app()
            else:
                self._stream_logs_http_approach()
        except KeyboardInterrupt:
            print("\nStopped log streaming.")
        except Exception as e:
            raise JobMonitorError(f"❌ Error streaming logs: {e}", code="stream_logs:Exception")

        print("\nLog monitoring completed!")

    def _stream_logs_http_approach(self):
        """Stream logs using HTTP streaming approach."""
        url = f"{self.base_url}/jobs/logs/{self.job_id}"

        with requests.get(url, headers=self.connector.headers, stream=True, timeout=None) as response:
            if response.status_code != 200:
                raise JobMonitorError(
                    f"❌ Error accessing logs. Status code: {response.status_code}", code="stream_logs:exception"
                )

            for line in response.iter_lines():
                if not line:
                    continue

                decoded_line = line.decode("utf-8")
                print(self.clean_log_message(decoded_line))

                # Stop after training completes
                if f"JOB_END:{self.job_id}" in decoded_line:
                    print(decoded_line)
                    print("-" * 80)
                    print(f"Training job {self.job_id} completed!")
                    break

    def _stream_logs_is_native_app(self):
        """Stream logs using SQL approach with continuation token."""
        continuation_token = ""

        while True:
            response = self.connector.get_job_events(self.job_id, continuation_token)

            # Print event logs to stdout
            for event in response["events"]:
                print(self.clean_log_message(event["event"]["message"]))

            # Check if we need to continue fetching more logs
            continuation_token = response["continuation_token"]
            if not continuation_token:
                break

    @staticmethod
    def clean_log_message(log: str):
        if "| user_id" in log:
            clean_log = log.split("| user_id")[0].strip()
        else:
            clean_log = log

        return clean_log

    def materialize_results(self):
        """Export job results to permanent tables after completion."""
        job_status = self._wait_for_completion()

        if job_status["status"] == JobStatus.COMPLETED:
            self._create_tables(job_status)
        else:
            raise RuntimeError(f"Job failed: {job_status}")

    def _wait_for_completion(self):
        """Poll job status until completion."""
        while True:
            status = self.get_status()

            if status["status"] not in [JobStatus.RUNNING, JobStatus.QUEUED]:
                return status

            time.sleep(5)

        # TODO: updtate the connector after some time to avoid sesssions errors

    def _create_tables(self, job_status):
        """Create all result tables from job export paths."""
        job_id = job_status["job_id"].replace("-", "_")
        export_paths = job_status["export_paths"]

        # Get all table paths
        all_paths = [export_paths["predictions"]]

        if "embeddings" in export_paths:
            all_paths += list(export_paths["embeddings"].values())

        for table_path in all_paths:
            table_name = table_path.split(".")[-1]
            view_name = f"job_{job_id}_{table_name}"
            source_view = f"{self.connector.app_name}.RESULTS.{view_name}"

            sql = f"CREATE TABLE {table_path} AS SELECT * FROM {source_view}"
            self.connector._exec(sql)
            # Drop the corresponding internal table after export
            internal_table_name = f"{view_name}_INTERNAL"
            self.connector._exec(f"call {self.connector.app_name}.api.drop_result_table('{internal_table_name}');")


class JobManager(JobHandler):
    """Helper class to monitor all jobs in queue."""

    def show_jobs(self):
        """Returns the queue status."""
        payload = {"payload_type": PayloadTypes.REQUEST_QUEUE_STATUS}

        try:
            return self.api_handler.make_request(payload)
        except Exception:
            raise JobManagerError("❌ Error getting queue status.", code="show_jobs:Exception")

    def fetch_job(self, job_id: str) -> JobMonitor:
        """
        Fetch a job by its ID.

        :param job_id: Unique identifier of the job to fetch.
        :type job_id: str
        :returns: A dictionary or object representing the fetched job and its metadata.
        :rtype: dict or Job
        :raises JobManagerError: If the job ID is invalid or the job cannot be found.
        """
        job = JobMonitor(connector=self.connector, job_id=job_id)
        try:
            status = job.get_status()
            # Populate job_type from status response if available
            if "job_type" in status and status["job_type"]:
                job.job_type = status["job_type"]
        except JobMonitorError:
            raise JobManagerError("❌ Unknown job status: None", code="fetch_job:Exception")
        return job

    def cancel_job(self, job_id: str):
        """
        Cancel a job by its ID.

        Removes the job from the queue if it is queued, or terminates it if it is currently running.

        :param job_id: Unique identifier of the job to cancel.
        :type job_id: str
        :returns: The result of the cancel operation.
        :rtype: Any
        :raises JobManagerError: If the job cannot be found or is in a non-cancellable state.
        """
        try:
            job = self.fetch_job(job_id)
        except JobManagerError:
            raise JobManagerError("❌ Unknown job status: None", code="cancel_job:Exception")

        return job.cancel()
