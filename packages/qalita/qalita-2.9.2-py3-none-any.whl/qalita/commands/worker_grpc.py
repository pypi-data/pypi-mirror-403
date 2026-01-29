"""
# QALITA (c) COPYRIGHT 2025 - ALL RIGHTS RESERVED -
gRPC-based worker implementation for real-time communication with the backend
"""

import os
import sys
import asyncio
import json
import time
import random
import string
import tarfile
from datetime import datetime, timezone
from typing import Optional, Dict
from shutil import copy2

import semver
import croniter

from qalita.internal.utils import logger, get_version, validate_token
from qalita.internal.request import send_request
from qalita.internal.data_preview import preview_source, DataPreviewResult
from qalita.internal.action_executor import get_action_executor, ActionResult
from qalita.grpc import GrpcClient
from qalita.grpc.protos import qalita_pb2
from qalita.commands.pack import run_pack


# In-memory guard to avoid re-scheduling the same routine within the same cron window
ROUTINE_LAST_SCHEDULED_UTC: Dict[int, datetime] = {}


def _safe_extractall(tar: tarfile.TarFile, path: str) -> None:
    """
    Safely extract all members from a tarfile, preventing path traversal attacks.
    Uses the 'data' filter on Python 3.12+ for built-in security,
    falls back to manual validation on older versions.
    """
    # Python 3.12+ has built-in filter support
    if sys.version_info >= (3, 12):
        tar.extractall(path, filter="data")  # nosec B202
    else:
        # Manual validation for Python 3.10, 3.11
        abs_path = os.path.abspath(path)
        for member in tar.getmembers():
            member_path = os.path.join(abs_path, member.name)
            # Resolve the path and check it's within the target directory
            resolved_path = os.path.realpath(member_path)
            if not resolved_path.startswith(abs_path + os.sep) and resolved_path != abs_path:
                raise ValueError(f"Attempted path traversal in tar file: {member.name}")
            # Reject absolute paths and paths with ..
            if os.path.isabs(member.name) or ".." in member.name.split(os.sep):
                raise ValueError(f"Unsafe path in tar file: {member.name}")
        # Members have been validated above, safe to extract
        tar.extractall(path, members=tar.getmembers())  # nosec B202


class GrpcWorkerRunner:
    """
    gRPC-based worker runner for real-time job execution.
    
    Uses bidirectional streaming for:
    - Keep-alive signals
    - Job assignments (pushed from server)
    - Job status updates
    """
    
    def __init__(self, config, name: str, mode: str, token: str, url: str):
        self.config = config
        self.name = name
        self.mode = mode
        self.token = token
        self.url = url
        
        self.grpc_client: Optional[GrpcClient] = None
        self.worker_id: Optional[int] = None
        self.partner_id: Optional[int] = None
        self.user_info: Optional[dict] = None
        self.registries: list = []
        
        self._running = False
        self._jobs_path: Optional[str] = None
    
    async def authenticate(self) -> bool:
        """Authenticate and register the worker."""
        logger.info("------------- Worker Authenticate (gRPC) -------------")
        
        # Validate token
        validated_info = validate_token(self.token)
        user_id = validated_info.get("user_id")
        
        # Create gRPC client
        self.grpc_client = GrpcClient(
            url=self.url,
            token=self.token,
        )
        
        # Connect and authenticate
        if not await self.grpc_client.connect():
            logger.error("Failed to connect to gRPC server")
            return False
        
        auth_response = await self.grpc_client.authenticate()
        if not auth_response or not auth_response.authenticated:
            error = auth_response.error if auth_response else "Unknown error"
            logger.error(f"Authentication failed: {error}")
            return False
        
        self.user_info = {
            "id": auth_response.user.id,
            "email": auth_response.user.email,
            "name": auth_response.user.name,
            "partner_id": auth_response.user.partner_id,
        }
        self.partner_id = auth_response.user.partner_id
        
        logger.success(f"Authenticated as {self.user_info['email']}")
        
        # Register worker
        worker = await self.grpc_client.register_worker(
            name=self.name,
            mode=self.mode,
            status="online",
            is_active=True,
        )
        
        if not worker:
            logger.error("Failed to register worker")
            return False
        
        self.worker_id = worker.id
        logger.success(f"Worker '{self.name}' registered with ID {self.worker_id}")
        
        # Get registries
        self.registries = await self.grpc_client.get_registries()
        if not self.registries:
            logger.warning("No registries found")
        
        # Save worker config
        config_json = self.config.load_worker_config() if hasattr(self.config, 'load_worker_config') else {}
        config_json["user"] = self.user_info
        config_json["context"] = config_json.get("context", {})
        config_json["context"]["local"] = {
            "url": self.url,
            "token": self.token,
            "name": self.name,
            "mode": self.mode,
        }
        config_json["context"]["remote"] = {
            "id": self.worker_id,
            "name": worker.name,
            "mode": worker.mode,
            "status": worker.status,
        }
        config_json["registries"] = [
            {"id": r.id, "name": r.name, "url": r.url}
            for r in self.registries
        ]
        self.config.save_worker_config(config_json)
        
        return True
    
    async def run(self) -> None:
        """Run the worker in the specified mode."""
        logger.info("------------- Worker Run (gRPC) -------------")
        logger.info(f"Worker ID: {self.worker_id}")
        logger.info(f"Worker Mode: {self.mode}")
        
        # Create jobs folder
        self._jobs_path = self.config.get_worker_run_path()
        if not os.path.exists(self._jobs_path):
            os.makedirs(self._jobs_path)
        
        if self.mode == "worker":
            await self._run_worker_mode()
        elif self.mode == "job":
            logger.warning("Job mode not implemented for gRPC yet, use REST")
        else:
            logger.error(f"Unknown mode: {self.mode}")
    
    async def _run_worker_mode(self) -> None:
        """Run in continuous worker mode with gRPC streaming."""
        logger.info(f"Worker started at {time.strftime('%X %d-%m-%Y %Z')}")
        
        self._running = True
        self._agent_start_datetime = datetime.now(timezone.utc)
        
        # Load local source IDs for routine matching
        self._local_source_ids = self._get_local_source_ids()
        logger.info(f"Local source IDs: {self._local_source_ids}")
        
        # Set up callbacks for incoming messages
        self.grpc_client.on_job_received(self._handle_job_assignment)
        self.grpc_client.on_routine_received(self._handle_routine_trigger)
        self.grpc_client.on_data_preview_request(self._handle_data_preview_request)
        self.grpc_client.on_add_source_request(self._handle_add_source_request)
        self.grpc_client.on_agent_action_request(self._handle_agent_action_request)
        self.grpc_client.on_disconnect(self._handle_disconnect)
        
        try:
            # Start routine checking task alongside the stream
            routine_check_task = asyncio.create_task(self._routine_check_loop())
            
            try:
                # Start the bidirectional stream
                await self.grpc_client.start_stream()
            finally:
                routine_check_task.cancel()
                try:
                    await routine_check_task
                except asyncio.CancelledError:
                    pass
        except KeyboardInterrupt:
            logger.warning("KILLSIG detected. Gracefully exiting.")
            await self._shutdown()
        except Exception as e:
            logger.error(f"Worker error: {e}")
            await self._shutdown()
    
    def _get_local_source_ids(self) -> list[int]:
        """Get list of source IDs from local configuration."""
        try:
            source_conf = self.config.load_source_config(verbose=False)
            return [
                source["id"] for source in source_conf.get("sources", [])
                if "id" in source
            ]
        except Exception as e:
            logger.warning(f"Could not load local source config: {e}")
            return []
    
    async def _routine_check_loop(self) -> None:
        """Periodically check routines and create jobs if needed."""
        logger.info("Routine check loop started")
        
        # Wait a bit for the stream to be established
        await asyncio.sleep(2)
        
        while self._running:
            try:
                await self._check_routines()
                # Check routines every 10 seconds
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                logger.info("Routine check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in routine check loop: {e}")
                await asyncio.sleep(10)
    
    async def _check_routines(self) -> None:
        """
        Check routines from the platform and create jobs if needed.
        
        This mirrors the logic from the REST-based worker:
        1. Get all active routines
        2. Check if source_id is locally defined
        3. Check if a job is already running/pending for this routine
        4. Evaluate the schedule
        5. Create job if it's time
        """
        if not self._local_source_ids:
            return
        
        # Get all routines
        routines = await self.grpc_client.get_routines()
        if not routines:
            return
        
        for routine in routines:
            try:
                # Only process active routines
                if routine.status != "active":
                    continue
                
                # Check if source is locally defined
                if routine.source_id not in self._local_source_ids:
                    continue
                
                # Check if target (if any) is locally defined
                if routine.HasField('target_id') and routine.target_id not in self._local_source_ids:
                    continue
                
                # Check schedule using the is_time_for_job logic
                if self._is_time_for_job(routine):
                    routine_name = routine.name if routine.name else f"routine-{routine.id}"
                    logger.info(f"Routine {routine.id} ({routine_name}) is due, creating job...")
                    await self._create_job_for_routine(routine)
                    
            except Exception as e:
                logger.error(f"Error processing routine {routine.id}: {e}")
    
    def _is_time_for_job(self, routine: qalita_pb2.Routine) -> bool:
        """
        Evaluate if it's time to create a job for this routine based on cron schedule.
        """
        routine_id = routine.id
        cron_expression = routine.schedule
        
        if not cron_expression:
            return False
        
        # Get start_date from routine
        try:
            if routine.HasField('start_date') and routine.start_date.seconds > 0:
                start_date = routine.start_date.ToDatetime().replace(tzinfo=timezone.utc)
            else:
                start_date = datetime.min.replace(tzinfo=timezone.utc)
        except Exception:
            start_date = datetime.min.replace(tzinfo=timezone.utc)
        
        # Determine base datetime for cron calculation
        # Use the last scheduled time for this routine if available
        last_scheduled = ROUTINE_LAST_SCHEDULED_UTC.get(routine_id)
        if last_scheduled:
            base_dt = last_scheduled
        else:
            base_dt = self._agent_start_datetime
        
        try:
            # Initialize cron iterator
            cron = croniter.croniter(cron_expression, base_dt)
            next_run = cron.get_next(datetime)
            if next_run.tzinfo is None:
                next_run = next_run.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            
            # Check if it's time
            if now >= next_run and now >= start_date:
                return True
                
        except Exception as e:
            logger.warning(f"Error evaluating cron for routine {routine_id}: {e}")
        
        return False
    
    async def _create_job_for_routine(self, routine: qalita_pb2.Routine) -> None:
        """Create a job for a routine and execute it immediately."""
        try:
            # Prepare pack config override
            pack_config = routine.config if routine.config else None
            
            # Create the job
            job = await self.grpc_client.create_job(
                source_id=routine.source_id,
                pack_id=routine.pack_id,
                source_version_id=routine.source_version_id if routine.HasField('source_version_id') else None,
                target_id=routine.target_id if routine.HasField('target_id') else None,
                target_version_id=routine.target_version_id if routine.HasField('target_version_id') else None,
                pack_version_id=routine.pack_version_id if routine.HasField('pack_version_id') else None,
                routine_id=routine.id,
                pack_config_override=pack_config,
                job_type="routine",
            )
            
            if job:
                logger.info(f"Created job {job.id} for routine {routine.id}")
                # Record scheduling time to avoid duplicate scheduling
                ROUTINE_LAST_SCHEDULED_UTC[routine.id] = datetime.now(timezone.utc)
                
                # Claim and execute the job immediately
                claimed_job = await self.grpc_client.claim_job(job.id, self.worker_id)
                if claimed_job:
                    logger.info(f"Claimed job {job.id}, executing...")
                    await self._handle_job_assignment(claimed_job)
                else:
                    logger.warning(f"Failed to claim job {job.id}, another worker may have taken it")
            else:
                logger.error(f"Failed to create job for routine {routine.id}")
                
        except Exception as e:
            logger.error(f"Error creating job for routine {routine.id}: {e}")
    
    async def _handle_job_assignment(self, job: qalita_pb2.Job) -> None:
        """Handle a job assignment pushed from the server."""
        logger.info(f"Job assignment received: {job.id}")
        
        try:
            # Extract job details from proto
            source_id = job.source_id
            source_version_id = job.source_version_id if job.HasField('source_version_id') else None
            target_id = job.target_id if job.HasField('target_id') else None
            target_version_id = job.target_version_id if job.HasField('target_version_id') else None
            pack_id = job.pack_id
            pack_version_id = job.pack_version_id if job.HasField('pack_version_id') else None
            pack_config_override = job.pack_config_override if job.HasField('pack_config_override') else None
            
            # Check if source exists in local config before starting the job
            source_conf = self.config.load_source_config(verbose=False)
            local_sources = source_conf.get("sources", [])
            source_exists = any(str(s.get("id")) == str(source_id) for s in local_sources)
            
            if not source_exists:
                error_msg = f"Source {source_id} not found in local config. Job cannot be executed on this worker."
                logger.warning(error_msg)
                await self.grpc_client.send_job_status(job.id, "failed", error_message=error_msg)
                return
            
            # Check if target exists in local config (if specified)
            if target_id:
                target_exists = any(str(s.get("id")) == str(target_id) for s in local_sources)
                if not target_exists:
                    error_msg = f"Target {target_id} not found in local config. Job cannot be executed on this worker."
                    logger.warning(error_msg)
                    await self.grpc_client.send_job_status(job.id, "failed", error_message=error_msg)
                    return
            
            # Execute the job
            await self._execute_job(
                job_id=job.id,
                source_id=source_id,
                source_version_id=source_version_id,
                target_id=target_id,
                target_version_id=target_version_id,
                pack_id=pack_id,
                pack_version_id=pack_version_id,
                pack_config_override=pack_config_override,
            )
        except Exception as e:
            logger.error(f"Error executing job {job.id}: {e}")
            # Update job status to failed
            await self.grpc_client.send_job_status(job.id, "failed", error_message=str(e))
    
    async def _handle_routine_trigger(self, routine: qalita_pb2.Routine) -> None:
        """Handle a routine trigger pushed from the server."""
        logger.info(f"Routine trigger received: {routine.id}")
        
        # Create a job for the routine
        job = await self.grpc_client.create_job(
            source_id=routine.source_id,
            pack_id=routine.pack_id,
            target_id=routine.target_id if routine.HasField('target_id') else None,
            routine_id=routine.id,
            pack_config_override=routine.config if routine.config else None,
            job_type="routine",
        )
        
        if job:
            logger.info(f"Created job {job.id} for routine {routine.id}")
        else:
            logger.error(f"Failed to create job for routine {routine.id}")
    
    async def _handle_disconnect(self) -> None:
        """Handle disconnection from the server."""
        logger.warning("Disconnected from server")
        # The GrpcClient handles reconnection automatically
    
    async def _handle_data_preview_request(self, request: qalita_pb2.DataPreviewRequest) -> None:
        """
        Handle a data preview request from the platform.
        
        This is called when Studio requests a preview of a data source.
        The worker:
        1. Finds the source configuration locally
        2. Reads the data using the preview module
        3. Sends back a DataPreviewResponse via gRPC stream
        """
        request_id = request.request_id
        source_id = request.source_id
        limit = request.limit if request.HasField('limit') else 1000
        query = request.query if request.HasField('query') else None
        
        logger.info(f"Processing data preview request {request_id} for source {source_id}")
        
        try:
            # Find the source in local configuration
            source_conf = self.config.load_source_config(verbose=False)
            matching_sources = [
                s for s in source_conf.get("sources", [])
                if str(s.get("id")) == str(source_id)
            ]
            
            if not matching_sources:
                logger.warning(f"Source {source_id} not found in local config")
                await self.grpc_client.send_data_preview_response(
                    request_id=request_id,
                    ok=False,
                    data_type="error",
                    error=f"Source {source_id} not found in local configuration",
                )
                return
            
            source_config = matching_sources[0]
            logger.info(f"Found source config for {source_id}: type={source_config.get('type')}")
            
            # Generate the preview
            result: DataPreviewResult = preview_source(
                source_config=source_config,
                limit=limit,
                query=query,
            )
            
            # Send the response
            await self.grpc_client.send_data_preview_response(
                request_id=request_id,
                ok=result.ok,
                data_type=result.data_type,
                error=result.error,
                headers=result.headers if result.headers else None,
                rows=result.rows if result.rows else None,
                total_rows=result.total_rows,
                content=result.content,
                binary_base64=result.binary_base64,
                mime_type=result.mime_type,
            )
            
            if result.ok:
                logger.success(f"Data preview sent for source {source_id} (type={result.data_type})")
            else:
                logger.warning(f"Data preview error for source {source_id}: {result.error}")
                
        except Exception as e:
            logger.error(f"Error handling data preview request {request_id}: {e}")
            await self.grpc_client.send_data_preview_response(
                request_id=request_id,
                ok=False,
                data_type="error",
                error=f"Internal error: {str(e)}",
            )
    
    async def _handle_add_source_request(self, request: qalita_pb2.AddSourceRequest) -> None:
        """
        Handle an add source request from the platform.
        
        This is called when the Platform requests to add a new source configuration.
        The worker:
        1. Parses the source configuration
        2. Validates connectivity to the source
        3. Adds the source to local configuration
        4. Sends back an AddSourceResponse via gRPC stream
        """
        request_id = request.request_id
        source_name = request.name
        source_type = request.type
        
        logger.info(f"Processing add source request {request_id} for '{source_name}' (type={source_type})")
        
        try:
            # Parse the config JSON
            config_dict = json.loads(request.config_json)
            
            # Load current source configuration
            source_conf = self.config.load_source_config(verbose=False)
            sources = source_conf.get("sources", [])
            
            # Generate a new source ID (max existing ID + 1, or 1 if no sources)
            existing_ids = [s.get("id", 0) for s in sources if isinstance(s.get("id"), int)]
            new_source_id = max(existing_ids) + 1 if existing_ids else 1
            
            # Build the source configuration entry
            new_source = {
                "id": new_source_id,
                "name": source_name,
                "type": source_type,
                "description": request.description,
                "visibility": request.visibility,
                "reference": request.reference,
                "sensitive": request.sensitive,
                "config": config_dict,
            }
            
            # Validate connectivity before saving
            connectivity_verified = False
            validation_error = None
            
            try:
                # Try to validate the source using preview (a quick connectivity check)
                result: DataPreviewResult = preview_source(
                    source_config=new_source,
                    limit=1,  # Just check connectivity, don't load much data
                )
                connectivity_verified = result.ok
                if not result.ok:
                    validation_error = result.error
            except Exception as e:
                validation_error = str(e)
                logger.warning(f"Connectivity validation failed for '{source_name}': {e}")
            
            # If connectivity failed, report error but still add the source
            # (user may want to fix configuration later)
            if not connectivity_verified:
                logger.warning(f"Adding source '{source_name}' despite connectivity check failure")
            
            # Add the new source to the configuration
            sources.append(new_source)
            source_conf["sources"] = sources
            self.config.config = source_conf
            self.config.save_source_config()
            
            # Update local source IDs cache
            self._local_source_ids = self._get_local_source_ids()
            
            logger.success(f"Source '{source_name}' added with ID {new_source_id}")
            
            # Send success response
            await self.grpc_client.send_add_source_response(
                request_id=request_id,
                ok=True,
                source_id=new_source_id,
                connectivity_verified=connectivity_verified,
                error=validation_error if not connectivity_verified else None,
            )
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid configuration JSON: {str(e)}"
            logger.error(f"Error handling add source request {request_id}: {error_msg}")
            await self.grpc_client.send_add_source_response(
                request_id=request_id,
                ok=False,
                error=error_msg,
                connectivity_verified=False,
            )
        except Exception as e:
            error_msg = f"Internal error: {str(e)}"
            logger.error(f"Error handling add source request {request_id}: {error_msg}")
            await self.grpc_client.send_add_source_response(
                request_id=request_id,
                ok=False,
                error=error_msg,
                connectivity_verified=False,
            )
    
    async def _handle_agent_action_request(self, request: qalita_pb2.AgentActionRequest) -> None:
        """
        Handle an agent action request from the platform.
        
        This is called when the Studio LLM agent requests to execute an action
        on a data source (e.g., SQL query, read data, describe schema).
        The worker:
        1. Finds the source configuration locally
        2. Executes the action using the ActionExecutor
        3. Sends back an AgentActionResponse via gRPC stream
        """
        request_id = request.request_id
        action_type = request.action_type
        source_id = request.source_id
        params_json = request.parameters_json
        timeout = request.timeout_seconds if request.HasField('timeout_seconds') else None
        
        logger.info(f"Processing agent action request {request_id}: {action_type} on source {source_id}")
        
        try:
            # Parse parameters
            params = json.loads(params_json) if params_json else {}
            
            # Find the source in local configuration
            source_conf = self.config.load_source_config(verbose=False)
            matching_sources = [
                s for s in source_conf.get("sources", [])
                if str(s.get("id")) == str(source_id)
            ]
            
            if not matching_sources:
                logger.warning(f"Source {source_id} not found in local config")
                await self.grpc_client.send_agent_action_response(
                    request_id=request_id,
                    ok=False,
                    action_type=action_type,
                    error=f"Source {source_id} not found in local configuration",
                )
                return
            
            source_config = matching_sources[0]
            logger.info(f"Found source config for {source_id}: type={source_config.get('type')}")
            
            # Execute the action
            executor = get_action_executor()
            result: ActionResult = executor.execute(
                action_type=action_type,
                source_config=source_config,
                params=params,
                timeout_seconds=timeout,
            )
            
            # Convert DataPreviewResult to protobuf if present
            data_proto = None
            if result.data:
                data_proto = qalita_pb2.DataPreviewResponse(
                    request_id=request_id,
                    ok=result.data.ok,
                    data_type=result.data.data_type,
                )
                if result.data.error:
                    data_proto.error = result.data.error
                if result.data.headers:
                    data_proto.headers.extend(result.data.headers)
                if result.data.rows:
                    for row in result.data.rows:
                        data_row = qalita_pb2.DataRow(values=row)
                        data_proto.rows.append(data_row)
                if result.data.total_rows is not None:
                    data_proto.total_rows = result.data.total_rows
                if result.data.content:
                    data_proto.content = result.data.content
            
            # Send the response
            await self.grpc_client.send_agent_action_response(
                request_id=request_id,
                ok=result.ok,
                action_type=result.action_type,
                error=result.error,
                result_json=result.result_json,
                data=data_proto,
                execution_time_ms=result.execution_time_ms,
            )
            
            if result.ok:
                logger.success(f"Agent action '{action_type}' completed for source {source_id} in {result.execution_time_ms}ms")
            else:
                logger.warning(f"Agent action '{action_type}' failed for source {source_id}: {result.error}")
                
        except json.JSONDecodeError as e:
            error_msg = f"Invalid parameters JSON: {str(e)}"
            logger.error(f"Error handling agent action request {request_id}: {error_msg}")
            await self.grpc_client.send_agent_action_response(
                request_id=request_id,
                ok=False,
                action_type=action_type,
                error=error_msg,
            )
        except Exception as e:
            error_msg = f"Internal error: {str(e)}"
            logger.error(f"Error handling agent action request {request_id}: {error_msg}")
            await self.grpc_client.send_agent_action_response(
                request_id=request_id,
                ok=False,
                action_type=action_type,
                error=error_msg,
            )
    
    async def _execute_job(
        self,
        job_id: int,
        source_id: int,
        source_version_id: Optional[int],
        target_id: Optional[int],
        target_version_id: Optional[int],
        pack_id: int,
        pack_version_id: Optional[int],
        pack_config_override: Optional[str] = None,
    ) -> None:
        """Execute a job."""
        logger.info("------------- Job Run -------------")
        start_time = datetime.now(timezone.utc)
        logger.info(f"Start Time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Source {source_id}:{source_version_id}")
        if target_id:
            logger.info(f"Target {target_id}:{target_version_id}")
        logger.info(f"Pack {pack_id}:{pack_version_id}")
        
        # Update job status to running
        await self.grpc_client.send_job_status(job_id, "running", start_date=start_time)
        await self.grpc_client.send_worker_status(self.worker_id, "busy")
        
        try:
            # Get source info
            source = await self.grpc_client.get_source(source_id)
            if not source:
                raise ValueError(f"Source {source_id} not found")
            
            # Get latest source version if not specified
            if not source_version_id and source.versions:
                latest_source = max(source.versions, key=lambda v: semver.parse_version_info(v.sem_ver_id))
                source_version_id = latest_source.id
                logger.info(f"Using latest source version: {latest_source.sem_ver_id} (id={source_version_id})")
            elif not source_version_id:
                raise ValueError(f"Source {source_id} has no versions. Cannot proceed without a source version.")
            
            # Get pack info
            pack = await self.grpc_client.get_pack(pack_id)
            if not pack:
                raise ValueError(f"Pack {pack_id} not found")
            
            # Get latest version if not specified
            if not pack_version_id and pack.versions:
                latest = max(pack.versions, key=lambda v: semver.parse_version_info(v.sem_ver_id))
                pack_version_id = latest.id
                pack_asset_id = latest.asset_id
            else:
                # Find the version
                for v in pack.versions:
                    if v.id == pack_version_id:
                        pack_asset_id = v.asset_id
                        break
                else:
                    raise ValueError(f"Pack version {pack_version_id} not found")
            
            # Get asset URL
            asset = await self.grpc_client.get_asset_url(pack_asset_id)
            if not asset:
                raise ValueError(f"Asset {pack_asset_id} not found")
            
            # Pull and extract pack (uses REST for binary download)
            pack_file_path = await self._pull_pack(pack_id, asset)
            pack_folder = f"{pack_file_path.split('/')[-1].split('.')[0]}_pack"
            
            # Create temp folder for job
            datetime_string = start_time.strftime("%Y%m%d%H%M%S")
            random_seed = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(5))
            temp_folder_name = f"{self._jobs_path}/{datetime_string}_{random_seed}"
            os.makedirs(temp_folder_name)
            
            # Copy and extract pack
            copy2(pack_file_path, temp_folder_name)
            archive_name = pack_file_path.split("/")[-1]
            archive_path = os.path.join(temp_folder_name, archive_name)
            
            with tarfile.open(archive_path, "r:gz") as tar:
                _safe_extractall(tar, temp_folder_name)  # nosec B202
            os.remove(archive_path)
            
            # Setup source config
            source_conf = self.config.load_source_config()
            matching_sources = [s for s in source_conf.get("sources", []) if str(s.get("id")) == str(source_id)]
            if not matching_sources:
                raise ValueError(f"Source {source_id} not found in local config")
            
            source_local = matching_sources[0]
            with open(os.path.join(temp_folder_name, pack_folder, "source_conf.json"), "w") as f:
                json.dump(source_local, f, indent=4)
            
            # Setup target config if provided
            if target_id:
                # Get latest target version if not specified
                if not target_version_id:
                    target = await self.grpc_client.get_source(target_id)
                    if target and target.versions:
                        latest_target = max(target.versions, key=lambda v: semver.parse_version_info(v.sem_ver_id))
                        target_version_id = latest_target.id
                        logger.info(f"Using latest target version: {latest_target.sem_ver_id} (id={target_version_id})")
                
                matching_targets = [s for s in source_conf.get("sources", []) if str(s.get("id")) == str(target_id)]
                if matching_targets:
                    with open(os.path.join(temp_folder_name, pack_folder, "target_conf.json"), "w") as f:
                        json.dump(matching_targets[0], f, indent=4)
            
            # Setup pack config override
            if pack_config_override:
                config_data = json.loads(pack_config_override) if isinstance(pack_config_override, str) else pack_config_override
                with open(os.path.join(temp_folder_name, pack_folder, "pack_conf.json"), "w") as f:
                    json.dump(config_data, f, indent=4)
            
            # Create a thread-safe callback for log streaming
            # We use asyncio.run_coroutine_threadsafe to call the async method from the sync callback
            # Capture the running loop from the current async context
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:
                loop = asyncio.get_event_loop()
            
            grpc_client = self.grpc_client
            current_job_id = job_id
            
            def log_streaming_callback(line: str, level: str) -> None:
                """Callback to stream log lines via gRPC."""
                try:
                    # Schedule the async send_log_line on the event loop
                    future = asyncio.run_coroutine_threadsafe(
                        grpc_client.send_log_line(current_job_id, line, level),
                        loop
                    )
                    # Don't wait for the result to avoid blocking
                except Exception as e:
                    logger.debug(f"Log streaming error: {e}")
            
            # Run the pack with log streaming callback
            logger.info(f"Starting pack execution with live log streaming for job {job_id}")
            status = run_pack(os.path.join(temp_folder_name, pack_folder), log_callback=log_streaming_callback)
            
            # Upload results (still uses REST for file uploads)
            logs_id = await self._post_run(
                os.path.join(temp_folder_name, pack_folder),
                f"{datetime_string}_{random_seed}",
                pack_id,
                pack_version_id,
                source_id,
                source_version_id,
            )
            
            # Update final status
            end_time = datetime.now(timezone.utc)
            final_status = "succeeded" if status == 0 else "failed"
            
            await self.grpc_client.send_job_status(
                job_id,
                final_status,
                end_date=end_time,
                logs_id=logs_id,
            )
            await self.grpc_client.send_worker_status(self.worker_id, final_status)
            
            elapsed_time = end_time - start_time
            logger.success(f"Job {job_id} finished with status {final_status}")
            logger.info(f"End Time: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logger.info(f"Elapsed Time: {elapsed_time}")
            
        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            end_time = datetime.now(timezone.utc)
            await self.grpc_client.send_job_status(job_id, "failed", error_message=str(e), end_date=end_time)
            await self.grpc_client.send_worker_status(self.worker_id, "failed")
            raise
    
    async def _pull_pack(self, pack_id: int, asset: qalita_pb2.AssetUrl) -> str:
        """Download pack from S3 (uses REST for binary download)."""
        logger.info("------------- Pack Pull -------------")
        
        # Build cache path
        import re
        url_parts = asset.url.split("/")
        file_name = url_parts[-1] if url_parts else ""
        bucket_name = url_parts[3] if len(url_parts) > 3 else ""
        s3_folder = "/".join(url_parts[4:-1]) if len(url_parts) > 4 else ""
        
        # Validate path components
        safe_pattern = re.compile(r'^[\w\-\.]+$')
        if not file_name or not safe_pattern.match(file_name):
            raise ValueError(f"Invalid file name: {file_name}")
        
        cache_folder = os.path.join(self._jobs_path, bucket_name, s3_folder) if s3_folder else os.path.join(self._jobs_path, bucket_name)
        local_path = os.path.join(cache_folder, file_name)
        
        # Check cache
        if os.path.exists(local_path):
            logger.info(f"Using CACHED Pack at: {local_path}")
            return local_path
        
        if not os.path.exists(cache_folder):
            os.makedirs(cache_folder)
        
        # Download via REST (binary files still use HTTP)
        agent_conf = self.config.load_worker_config()
        api_url = agent_conf['context']['local']['url']
        
        response = send_request(
            request=f"{api_url}/api/v1/assets/{asset.id}/fetch",
            mode="get",
        )
        
        if response.status_code == 200:
            with open(local_path, "wb") as f:
                f.write(response.content)
            logger.info("Pack fetched successfully")
            return local_path
        else:
            raise ValueError(f"Failed to fetch pack: {response.text}")
    
    async def _post_run(
        self,
        run_path: str,
        name: str,
        pack_id: int,
        pack_version_id: int,
        source_id: int,
        source_version_id: int,
    ) -> Optional[int]:
        """Upload job results (uses REST for file uploads)."""
        logger.info("------------- Job Post Run -------------")
        
        agent_conf = self.config.load_worker_config()
        api_url = agent_conf['context']['local']['url']
        registry_id = agent_conf['registries'][0]['id']
        user_id = agent_conf['user']['id']
        
        logs_id = None
        
        # Upload logs
        logs_path = os.path.join(run_path, "logs.txt")
        if os.path.exists(logs_path):
            logger.info("Uploading logs...")
            response = send_request(
                request=f"{api_url}/api/v1/assets/upload",
                mode="post-multipart",
                file_path=logs_path,
                query_params={
                    "registry_id": registry_id,
                    "name": name,
                    "version": "1.0.0",
                    "bucket": "logs",
                    "type": "log",
                    "description": "job logs",
                    "user_id": user_id,
                },
            )
            if response.status_code == 200:
                logs_id = response.json().get("id")
                logger.success("Logs pushed")
            else:
                logger.error(f"Failed to push logs: {response.text}")
        
        # Upload metrics
        metrics_path = os.path.join(run_path, "metrics.json")
        if os.path.exists(metrics_path):
            logger.info("Uploading metrics...")
            response = send_request(
                request=f"{api_url}/api/v1/metrics/upload",
                mode="post-multipart",
                file_path=metrics_path,
                query_params={
                    "source_id": source_id,
                    "source_version_id": source_version_id,
                    "pack_id": pack_id,
                    "pack_version_id": pack_version_id,
                },
            )
            if response.status_code == 200:
                logger.success("Metrics pushed")
            else:
                logger.error(f"Failed to push metrics: {response.text}")
        
        # Upload recommendations
        recommendations_path = os.path.join(run_path, "recommendations.json")
        if os.path.exists(recommendations_path):
            logger.info("Uploading recommendations...")
            response = send_request(
                request=f"{api_url}/api/v1/recommendations/upload",
                mode="post-multipart",
                file_path=recommendations_path,
                query_params={
                    "source_id": source_id,
                    "source_version_id": source_version_id,
                    "pack_id": pack_id,
                    "pack_version_id": pack_version_id,
                },
            )
            if response.status_code == 200:
                logger.success("Recommendations pushed")
            else:
                logger.error(f"Failed to push recommendations: {response.text}")
        
        # Upload schemas
        schemas_path = os.path.join(run_path, "schemas.json")
        if os.path.exists(schemas_path):
            logger.info("Uploading schemas...")
            response = send_request(
                request=f"{api_url}/api/v1/schemas/upload",
                mode="post-multipart",
                file_path=schemas_path,
                query_params={
                    "source_id": source_id,
                    "source_version_id": source_version_id,
                    "pack_id": pack_id,
                    "pack_version_id": pack_version_id,
                },
            )
            if response.status_code == 200:
                logger.success("Schemas pushed")
            else:
                logger.error(f"Failed to push schemas: {response.text}")
        
        return logs_id
    
    async def _shutdown(self) -> None:
        """Gracefully shutdown the worker."""
        logger.info("Shutting down worker...")
        self._running = False
        
        if self.grpc_client:
            # Send offline status
            if self.worker_id:
                await self.grpc_client.send_worker_status(self.worker_id, "offline")
            
            await self.grpc_client.stop_stream()
            await self.grpc_client.disconnect()
        
        logger.info("Worker shutdown complete")


async def run_worker_grpc(config, name: str, mode: str, token: str, url: str) -> None:
    """
    Entry point for running the worker in gRPC mode.
    
    Args:
        config: CLI config object
        name: Worker name
        mode: Worker mode (worker/job)
        token: Authentication token
        url: Backend URL
    """
    runner = GrpcWorkerRunner(config, name, mode, token, url)
    
    if not await runner.authenticate():
        sys.exit(1)
    
    await runner.run()
