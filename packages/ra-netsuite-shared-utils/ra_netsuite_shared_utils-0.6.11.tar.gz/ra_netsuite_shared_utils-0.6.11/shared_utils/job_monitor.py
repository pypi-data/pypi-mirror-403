import functions_framework
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from google.cloud import tasks_v2
from shared_utils.mailer_helper import MailerHelper
from shared_utils.netsuite_helper import NetsuiteHelper


class JobMonitorConfig:
    """Configuration class for job monitor"""
    
    def __init__(self, env: str, netsuite_secrets: Dict[str, str], 
                 recipient_emails: list, gcp_project_id: str, 
                 gcp_sa_email: str, gcp_task_queue: str, 
                 job_monitor_function_url: str, daakiya_url: str, 
                 bundle_uuid: str, sender_email: str, debug_logging: bool = False,
                 max_attempts: int = 5):
        self.ENV = env
        self.NETSUITE_CONSUMER_KEY = netsuite_secrets.get('NETSUITE_CONSUMER_KEY')
        self.NETSUITE_CONSUMER_SECRET = netsuite_secrets.get('NETSUITE_CONSUMER_SECRET')
        self.NETSUITE_ACCESS_TOKEN = netsuite_secrets.get('NETSUITE_ACCESS_TOKEN')
        self.NETSUITE_TOKEN_SECRET = netsuite_secrets.get('NETSUITE_TOKEN_SECRET')
        self.NETSUITE_REALM = netsuite_secrets.get('NETSUITE_REALM')
        self.RECIPIENT_EMAILS = recipient_emails
        self.GCP_PROJECT_ID = gcp_project_id
        self.GCP_SA_EMAIL = gcp_sa_email
        self.GCP_TASK_QUEUE = gcp_task_queue
        self.JOB_MONITOR_FUNCTION_URL = job_monitor_function_url
        self.DAAKIYA_URL = daakiya_url
        self.BUNDLE_UUID = bundle_uuid
        self.SENDER_EMAIL = sender_email
        self.DEBUG_LOGGING = debug_logging
        self.MAX_ATTEMPTS = max_attempts


class JobMonitor:
    """Generic NetSuite job monitor with configurable logging"""
    
    def __init__(self, config: JobMonitorConfig):
        self.config = config
        self.mailer_helper = MailerHelper(
            config.ENV,
            daakiya_url=config.DAAKIYA_URL,
            bundle_uuid=config.BUNDLE_UUID,
            sender_email_id=config.SENDER_EMAIL,
            recipient_emails=config.RECIPIENT_EMAILS
        )
    
    def _debug_log(self, message: str):
        """Debug logging helper - only logs if debug logging is enabled"""
        if self.config.DEBUG_LOGGING:
            print(message)
    
    def create_retry_task(self, job_id: str, execution_date: str, posting_period: str, 
                         attempt_count: int, subsidiary: Optional[str] = None, 
                         business_unit: Optional[str] = None) -> Optional[Any]:
        """Create a retry task for job monitoring with 5-minute delay"""
        try:
            client = tasks_v2.CloudTasksClient()
            location = 'asia-south1'
            queue_path = client.queue_path(self.config.GCP_PROJECT_ID, location, self.config.GCP_TASK_QUEUE)
            
            payload = {
                "job_id": job_id,
                "execution_date": execution_date,
                "posting_period": posting_period,
                "attempt_count": attempt_count,
                "subsidiary": subsidiary,
                "business_unit": business_unit
            }
            
            task = tasks_v2.Task(
                http_request=tasks_v2.HttpRequest(
                    http_method=tasks_v2.HttpMethod.POST,
                    url=self.config.JOB_MONITOR_FUNCTION_URL,
                    oidc_token=tasks_v2.OidcToken(
                        service_account_email=self.config.GCP_SA_EMAIL,
                    ),
                    headers={'Content-type': 'application/json'},
                    body=json.dumps(payload).encode()
                ),
            )
            
            schedule_time = datetime.utcnow() + timedelta(minutes=5)
            task.schedule_time = schedule_time.isoformat() + 'Z'
            
            result = client.create_task(
                tasks_v2.CreateTaskRequest(
                    parent=queue_path,
                    task=task,
                )
            )
            
            self._debug_log(f"Created retry task for job ID: {job_id}, attempt {attempt_count + 1}")
            return result
            
        except Exception as e:
            self._debug_log(f"Error creating retry task: {e}")
            return None
    
    def handle_completed_job(self, job_id: str, execution_date: str, posting_period: str, 
                           attempt_count: int, subsidiary: Optional[str], 
                           business_unit: Optional[str]) -> Optional[str]:
        """Handle completed job status"""
        if attempt_count >= self.config.MAX_ATTEMPTS:
            self.mailer_helper.send_job_failure_mail(job_id, execution_date, business_unit, subsidiary)
            return f'Job {job_id} completed with issues after 30 minutes of monitoring'
        else:
            self._debug_log(f"Job {job_id} completed with issues, continuing monitoring until 30 minutes")
            if attempt_count < self.config.MAX_ATTEMPTS:
                retry_result = self.create_retry_task(
                    job_id, execution_date, posting_period, attempt_count + 1, subsidiary, business_unit
                )
                if retry_result:
                    return f'Job {job_id} completed with issues, continuing monitoring (attempt {attempt_count + 1}/{self.config.MAX_ATTEMPTS + 1})'
                else:
                    return f'Job {job_id} completed with issues, failed to schedule monitoring continuation'
        return None
    
    def handle_failed_job(self, job_id: str, execution_date: str, subsidiary: Optional[str], 
                         business_unit: Optional[str]) -> str:
        """Handle failed job status"""
        self._debug_log(f"Job {job_id} failed - sending failure notification")
        self.mailer_helper.send_job_failure_mail(job_id, execution_date, business_unit, subsidiary)
        return f'Job {job_id} failed - failure notification sent'
    
    def handle_in_progress_job(self, job_id: str, execution_date: str, posting_period: str,
                              attempt_count: int, subsidiary: Optional[str], 
                              business_unit: Optional[str]) -> Optional[str]:
        """Handle in-progress job status"""
        if attempt_count < self.config.MAX_ATTEMPTS:
            self._debug_log(f"Job {job_id} still in progress, scheduling retry in 5 minutes (attempt {attempt_count + 1}/{self.config.MAX_ATTEMPTS + 1})")
            retry_result = self.create_retry_task(
                job_id, execution_date, posting_period, attempt_count + 1, subsidiary, business_unit
            )
            if retry_result:
                return f'Job {job_id} still in progress, retry scheduled in 5 minutes (attempt {attempt_count + 1}/{self.config.MAX_ATTEMPTS + 1})'
            else:
                return f'Job {job_id} still in progress, failed to schedule retry'
        else:
            self._debug_log(f"Job {job_id} still in progress after {self.config.MAX_ATTEMPTS + 1} attempts (30 minutes)")
            self.mailer_helper.send_job_timeout_mail(job_id, execution_date, business_unit, subsidiary)
            return f'Job {job_id} still in progress after 30 minutes ({self.config.MAX_ATTEMPTS + 1} attempts) - manual check required'
    
    def process_job_status(self, job_status: Dict[str, Any], job_id: str, execution_date: str, 
                          posting_period: str, attempt_count: int, subsidiary: Optional[str], 
                          business_unit: Optional[str]) -> str:
        """Process job status and return appropriate response"""
        if job_status['status'] == 'completed':
            self._debug_log(f"Job {job_id} completed successfully!")
            
            if job_status['progress'] == 'succeeded':
                self._debug_log(f"Job {job_id} completed with success status - sending success notification")
                self.mailer_helper.send_job_success_mail(job_id, execution_date, business_unit, subsidiary)
                return f'Job {job_id} completed successfully - notification sent'
            else:
                self._debug_log(f"Job {job_id} completed but with progress: {job_status.get('progress', 'unknown')}")
                result = self.handle_completed_job(
                    job_id, execution_date, posting_period, attempt_count, subsidiary, business_unit
                )
                if result:
                    return result
            
        elif job_status['status'] == 'failed':
            self._debug_log(f"Job {job_id} failed!")
            result = self.handle_failed_job(job_id, execution_date, subsidiary, business_unit)
            if result:
                return result
            
        elif job_status['status'] == 'in_progress':
            result = self.handle_in_progress_job(
                job_id, execution_date, posting_period, attempt_count, subsidiary, business_unit
            )
            if result:
                return result
        
        else:
            error_msg = f"Unknown job status encountered for job {job_id}: {job_status}"
            self._debug_log(error_msg)
            raise RuntimeError(error_msg)
        
        return ""
    
    def monitor_job(self, request_data: Dict[str, Any]) -> tuple[str, int]:
        """Main job monitoring function"""
        try:
            if not hasattr(self, '_mailer_initialized'):
                try:
                    self.mailer_helper = MailerHelper(
                        self.config.ENV,
                        daakiya_url=self.config.DAAKIYA_URL,
                        bundle_uuid=self.config.BUNDLE_UUID,
                        sender_email_id=self.config.SENDER_EMAIL,
                        recipient_emails=self.config.RECIPIENT_EMAILS
                    )
                    self._mailer_initialized = True
                except Exception as mailer_error:
                    return f'Error initializing MailerHelper: {str(mailer_error)}', 500
            
            job_id = request_data.get('job_id')
            execution_date = request_data.get('execution_date')
            posting_period = request_data.get('posting_period')
            attempt_count = request_data.get('attempt_count', 0)
            subsidiary = request_data.get('subsidiary')
            business_unit = request_data.get('business_unit')
            
            self._debug_log("Job Monitor Request Data: " + str(request_data))
            
            if not job_id:
                error_msg = "No job ID provided"
                self._debug_log(error_msg)
                raise RuntimeError(error_msg)
            
            self._debug_log(f"Monitoring NetSuite job {job_id} for execution date {execution_date} (attempt {attempt_count + 1}/{self.config.MAX_ATTEMPTS + 1}) - Business Unit: {business_unit}")
            
            netsuite_monitor = NetsuiteHelper(
                self.config.ENV,
                self.config.NETSUITE_CONSUMER_KEY,
                self.config.NETSUITE_CONSUMER_SECRET,
                self.config.NETSUITE_ACCESS_TOKEN,
                self.config.NETSUITE_TOKEN_SECRET,
                self.config.NETSUITE_REALM
            )
            
            job_status = netsuite_monitor.check_job_status(job_id)
            self._debug_log(f"Job {job_id} status: {job_status}")
            
            return self.process_job_status(
                job_status, job_id, execution_date, posting_period, 
                attempt_count, subsidiary, business_unit
            ), 200
                
        except Exception as e:
            self._debug_log(f"Error in job monitor function: {e}")

            try:
                self.mailer_helper.send_job_monitor_error_mail(
                    job_id, execution_date, str(e), business_unit, subsidiary
                )
            except Exception as mail_error:
                self._debug_log(f"Error sending error notification email: {mail_error}")
            
            return f'Error monitoring job: {str(e)}', 500


def create_job_monitor_function(config_factory_func):
    """Factory function to create a job monitor Cloud Function"""
    
    @functions_framework.http
    def monitor_netsuite_job(request):
        """Cloud Function to monitor NetSuite job status"""
        try:
            config = config_factory_func()
            job_monitor = JobMonitor(config)
            
            event = request.get_json()
            return job_monitor.monitor_job(event)
            
        except Exception as e:
            return f'Error initializing job monitor: {str(e)}', 500
    
    return monitor_netsuite_job
