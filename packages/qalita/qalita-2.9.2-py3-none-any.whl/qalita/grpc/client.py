"""
# QALITA (c) COPYRIGHT 2025 - ALL RIGHTS RESERVED -
gRPC client for Worker-Backend communication with automatic reconnection
"""

import asyncio
from typing import Optional, AsyncIterator, Callable, Any
from datetime import datetime, timezone
from urllib.parse import urlparse

import grpc
import grpc.aio
from google.protobuf.timestamp_pb2 import Timestamp
from google.protobuf import empty_pb2

from qalita.internal.utils import logger
from qalita.grpc.protos import qalita_pb2, qalita_pb2_grpc


class GrpcClient:
    """
    gRPC client for communicating with the QALITA backend.
    
    Features:
    - Automatic reconnection with exponential backoff
    - Keep-alive management
    - Bidirectional streaming support
    - Thread-safe connection state
    """
    
    def __init__(
        self,
        url: str,
        token: str,
        worker_id: Optional[int] = None,
        max_reconnect_attempts: int = 10,
        initial_reconnect_delay: float = 1.0,
        max_reconnect_delay: float = 60.0,
    ):
        """
        Initialize the gRPC client.
        
        Args:
            url: Backend URL (e.g., "http://localhost:3080" or "grpc://localhost:50051")
            token: Authentication token
            worker_id: Optional worker ID for keep-alive
            max_reconnect_attempts: Maximum reconnection attempts (0 = unlimited)
            initial_reconnect_delay: Initial delay between reconnection attempts
            max_reconnect_delay: Maximum delay between reconnection attempts
        """
        self._url = url
        self._token = token
        self._worker_id = worker_id
        self._max_reconnect_attempts = max_reconnect_attempts
        self._initial_reconnect_delay = initial_reconnect_delay
        self._max_reconnect_delay = max_reconnect_delay
        
        # Connection state - set before parsing URL
        self._use_secure_channel = False
        
        # Parse URL to get gRPC endpoint (may update _use_secure_channel)
        self._grpc_target = self._parse_grpc_target(url)
        
        # Connection state
        self._channel: Optional[grpc.aio.Channel] = None
        self._stub: Optional[qalita_pb2_grpc.WorkerServiceStub] = None
        self._connected = False
        self._reconnect_attempts = 0
        
        # Stream state
        self._stream_call = None
        self._outgoing_queue: asyncio.Queue = asyncio.Queue()
        self._stream_active = False
        
        # Callbacks
        self._on_job_received: Optional[Callable] = None
        self._on_routine_received: Optional[Callable] = None
        self._on_data_preview_request: Optional[Callable] = None
        self._on_add_source_request: Optional[Callable] = None
        self._on_agent_action_request: Optional[Callable] = None
        self._on_disconnect: Optional[Callable] = None
    
    def _parse_grpc_target(self, url: str) -> str:
        """
        Parse the backend URL to get the gRPC target.
        
        For production deployments with ingress:
        - https://api.domain.com -> grpc.domain.com:443 (secure)
        - http://api.domain.com -> grpc.domain.com:443 (secure, assumes TLS termination)
        
        For local development:
        - http://localhost:3080 -> localhost:50051 (insecure)
        - grpc://host:port -> host:port (as-is)
        """
        parsed = urlparse(url)
        
        if parsed.scheme in ('grpc', 'grpcs'):
            # Already a gRPC URL
            self._use_secure_channel = parsed.scheme == 'grpcs'
            return f"{parsed.hostname}:{parsed.port or 50051}"
        
        host = parsed.hostname or 'localhost'
        
        # For localhost/development, use insecure channel on port 50051
        if host in ('localhost', '127.0.0.1', '0.0.0.0'):
            self._use_secure_channel = False
            return f"{host}:50051"
        
        # For production URLs (e.g., https://api.app.platform.qalita.io)
        # Convert to gRPC endpoint (e.g., grpc.app.platform.qalita.io:443)
        self._use_secure_channel = True
        
        # Replace 'api.' prefix with 'grpc.' if present
        if host.startswith('api.'):
            host = 'grpc.' + host[4:]
        else:
            # If no api. prefix, just prepend grpc.
            host = 'grpc.' + host
        
        # Use port 443 for HTTPS/TLS ingress
        return f"{host}:443"
    
    @property
    def metadata(self) -> list[tuple[str, str]]:
        """Get gRPC call metadata with authentication."""
        return [('authorization', f'Bearer {self._token}')]
    
    async def connect(self) -> bool:
        """
        Establish connection to the gRPC server.
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            # Channel options for long-running streams
            channel_options = [
                ('grpc.keepalive_time_ms', 30000),
                ('grpc.keepalive_timeout_ms', 10000),
                ('grpc.keepalive_permit_without_calls', True),
                ('grpc.http2.min_recv_ping_interval_without_data_ms', 10000),
                ('grpc.http2.max_pings_without_data', 0),
                ('grpc.max_receive_message_length', 50 * 1024 * 1024),
                ('grpc.max_send_message_length', 50 * 1024 * 1024),
            ]
            
            # Create channel - secure for production, insecure for local dev
            if self._use_secure_channel:
                # Use system root certificates for TLS
                self._channel = grpc.aio.secure_channel(
                    self._grpc_target,
                    grpc.ssl_channel_credentials(),
                    options=channel_options,
                )
            else:
                self._channel = grpc.aio.insecure_channel(
                    self._grpc_target,
                    options=channel_options,
                )
            
            self._stub = qalita_pb2_grpc.WorkerServiceStub(self._channel)
            self._connected = True
            self._reconnect_attempts = 0
            
            logger.info(f"Connected to gRPC server at {self._grpc_target}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to gRPC server: {e}")
            self._connected = False
            return False
    
    async def disconnect(self) -> None:
        """Close the gRPC connection gracefully."""
        self._stream_active = False
        
        if self._stream_call:
            try:
                self._stream_call.cancel()
            except Exception as e:
                logger.debug(f"Error cancelling stream during disconnect: {e}")
            self._stream_call = None
        
        if self._channel:
            await self._channel.close()
            self._channel = None
        
        self._stub = None
        self._connected = False
        
        if self._on_disconnect:
            await self._on_disconnect()
        
        logger.info("Disconnected from gRPC server")
    
    async def _reconnect(self) -> bool:
        """
        Attempt to reconnect with exponential backoff.
        
        Returns:
            True if reconnection successful, False if max attempts exceeded
        """
        delay = self._initial_reconnect_delay
        
        while (self._max_reconnect_attempts == 0 or 
               self._reconnect_attempts < self._max_reconnect_attempts):
            
            self._reconnect_attempts += 1
            logger.warning(
                f"Reconnection attempt {self._reconnect_attempts}"
                f"{f'/{self._max_reconnect_attempts}' if self._max_reconnect_attempts > 0 else ''}"
            )
            
            await asyncio.sleep(delay)
            
            if await self.connect():
                return True
            
            # Exponential backoff
            delay = min(delay * 2, self._max_reconnect_delay)
        
        logger.error("Max reconnection attempts exceeded")
        return False
    
    # =========================================================================
    # Unary RPCs
    # =========================================================================
    
    async def authenticate(self) -> Optional[qalita_pb2.AuthResponse]:
        """
        Authenticate with the backend.
        
        Returns:
            AuthResponse if successful, None otherwise
        """
        if not self._connected:
            if not await self.connect():
                return None
        
        try:
            request = qalita_pb2.AuthRequest(token=self._token)
            response = await self._stub.Authenticate(request)
            return response
        except grpc.aio.AioRpcError as e:
            logger.error(f"Authentication failed: {e.code()} - {e.details()}")
            return None
    
    async def register_worker(
        self,
        name: str,
        mode: str,
        status: str = "online",
        is_active: bool = True,
    ) -> Optional[qalita_pb2.Worker]:
        """
        Register or update a worker.
        
        Returns:
            Worker object if successful, None otherwise
        """
        if not self._connected:
            if not await self.connect():
                return None
        
        try:
            request = qalita_pb2.RegisterWorkerRequest(
                name=name,
                mode=mode,
                status=status,
                is_active=is_active,
            )
            response = await self._stub.RegisterWorker(
                request,
                metadata=self.metadata,
            )
            self._worker_id = response.id
            return response
        except grpc.aio.AioRpcError as e:
            logger.error(f"Worker registration failed: {e.code()} - {e.details()}")
            return None
    
    async def get_worker(self, worker_id: int) -> Optional[qalita_pb2.Worker]:
        """Get worker by ID."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.GetWorkerRequest(worker_id=worker_id)
            return await self._stub.GetWorker(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Get worker failed: {e.code()} - {e.details()}")
            return None
    
    async def get_pack(self, pack_id: int) -> Optional[qalita_pb2.Pack]:
        """Get pack by ID with versions."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.GetPackRequest(pack_id=pack_id)
            return await self._stub.GetPack(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Get pack failed: {e.code()} - {e.details()}")
            return None
    
    async def get_source(self, source_id: int) -> Optional[qalita_pb2.Source]:
        """Get source by ID with versions."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.GetSourceRequest(source_id=source_id)
            return await self._stub.GetSource(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Get source failed: {e.code()} - {e.details()}")
            return None
    
    async def get_asset_url(self, asset_id: int) -> Optional[qalita_pb2.AssetUrl]:
        """Get asset URL by ID."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.GetAssetUrlRequest(asset_id=asset_id)
            return await self._stub.GetAssetUrl(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Get asset URL failed: {e.code()} - {e.details()}")
            return None
    
    async def get_registries(self) -> list[qalita_pb2.Registry]:
        """Get all registries."""
        if not self._connected:
            return []
        
        try:
            response = await self._stub.GetRegistries(
                empty_pb2.Empty(),
                metadata=self.metadata,
            )
            return list(response.registries)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Get registries failed: {e.code()} - {e.details()}")
            return []
    
    async def create_job(
        self,
        source_id: int,
        pack_id: int,
        source_version_id: Optional[int] = None,
        target_id: Optional[int] = None,
        target_version_id: Optional[int] = None,
        pack_version_id: Optional[int] = None,
        routine_id: Optional[int] = None,
        pack_config_override: Optional[str] = None,
        job_type: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Optional[qalita_pb2.Job]:
        """Create a new job."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.CreateJobRequest(
                source_id=source_id,
                pack_id=pack_id,
            )
            if source_version_id:
                request.source_version_id = source_version_id
            if target_id:
                request.target_id = target_id
            if target_version_id:
                request.target_version_id = target_version_id
            if pack_version_id:
                request.pack_version_id = pack_version_id
            if routine_id:
                request.routine_id = routine_id
            if pack_config_override:
                request.pack_config_override = pack_config_override
            if job_type:
                request.type = job_type
            if name:
                request.name = name
            
            return await self._stub.CreateJob(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Create job failed: {e.code()} - {e.details()}")
            return None
    
    async def update_job(
        self,
        job_id: int,
        agent_id: Optional[int] = None,
        status: Optional[str] = None,
        name: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        logs_id: Optional[int] = None,
    ) -> Optional[qalita_pb2.Job]:
        """Update an existing job."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.UpdateJobRequest(job_id=job_id)
            if agent_id is not None:
                request.agent_id = agent_id
            if status:
                request.status = status
            if name:
                request.name = name
            if start_date:
                ts = Timestamp()
                ts.FromDatetime(start_date if start_date.tzinfo else start_date.replace(tzinfo=timezone.utc))
                request.start_date.CopyFrom(ts)
            if end_date:
                ts = Timestamp()
                ts.FromDatetime(end_date if end_date.tzinfo else end_date.replace(tzinfo=timezone.utc))
                request.end_date.CopyFrom(ts)
            if logs_id is not None:
                request.logs_id = logs_id
            
            return await self._stub.UpdateJob(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Update job failed: {e.code()} - {e.details()}")
            return None
    
    async def claim_job(self, job_id: int, worker_id: int) -> Optional[qalita_pb2.Job]:
        """Claim a job for a worker."""
        if not self._connected:
            return None
        
        try:
            request = qalita_pb2.ClaimJobRequest(job_id=job_id, worker_id=worker_id)
            return await self._stub.ClaimJob(request, metadata=self.metadata)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Claim job failed: {e.code()} - {e.details()}")
            return None
    
    async def get_routines(self) -> list[qalita_pb2.Routine]:
        """Get all routines."""
        if not self._connected:
            return []
        
        try:
            response = await self._stub.GetRoutines(
                empty_pb2.Empty(),
                metadata=self.metadata,
            )
            return list(response.routines)
        except grpc.aio.AioRpcError as e:
            logger.error(f"Get routines failed: {e.code()} - {e.details()}")
            return []
    
    # =========================================================================
    # Bidirectional Streaming
    # =========================================================================
    
    def on_job_received(self, callback: Callable[[qalita_pb2.Job], Any]) -> None:
        """Set callback for when a job is received via stream."""
        self._on_job_received = callback
    
    def on_routine_received(self, callback: Callable[[qalita_pb2.Routine], Any]) -> None:
        """Set callback for when a routine is triggered via stream."""
        self._on_routine_received = callback
    
    def on_data_preview_request(self, callback: Callable[[qalita_pb2.DataPreviewRequest], Any]) -> None:
        """Set callback for when a data preview request is received via stream."""
        self._on_data_preview_request = callback
    
    def on_add_source_request(self, callback: Callable[[qalita_pb2.AddSourceRequest], Any]) -> None:
        """Set callback for when an add source request is received via stream."""
        self._on_add_source_request = callback
    
    def on_agent_action_request(self, callback: Callable[[qalita_pb2.AgentActionRequest], Any]) -> None:
        """Set callback for when an agent action request is received via stream."""
        self._on_agent_action_request = callback
    
    def on_disconnect(self, callback: Callable[[], Any]) -> None:
        """Set callback for when connection is lost."""
        self._on_disconnect = callback
    
    async def send_keep_alive(self) -> None:
        """Send a keep-alive message through the stream."""
        if not self._worker_id:
            logger.warning("Cannot send keep-alive: worker_id not set")
            return
        
        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))
        
        msg = qalita_pb2.WorkerMessage(
            keep_alive=qalita_pb2.KeepAlive(
                worker_id=self._worker_id,
                timestamp=ts,
            )
        )
        await self._outgoing_queue.put(msg)
    
    async def send_job_status(
        self,
        job_id: int,
        status: str,
        error_message: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        logs_id: Optional[int] = None,
    ) -> None:
        """Send a job status update through the stream."""
        job_status = qalita_pb2.JobStatusUpdate(
            job_id=job_id,
            status=status,
        )
        if error_message:
            job_status.error_message = error_message
        if start_date:
            ts = Timestamp()
            ts.FromDatetime(start_date if start_date.tzinfo else start_date.replace(tzinfo=timezone.utc))
            job_status.start_date.CopyFrom(ts)
        if end_date:
            ts = Timestamp()
            ts.FromDatetime(end_date if end_date.tzinfo else end_date.replace(tzinfo=timezone.utc))
            job_status.end_date.CopyFrom(ts)
        if logs_id is not None:
            job_status.logs_id = logs_id
        
        msg = qalita_pb2.WorkerMessage(job_status=job_status)
        await self._outgoing_queue.put(msg)
    
    async def send_worker_status(self, worker_id: int, status: str) -> None:
        """Send a worker status update through the stream."""
        msg = qalita_pb2.WorkerMessage(
            worker_status=qalita_pb2.WorkerStatusUpdate(
                worker_id=worker_id,
                status=status,
            )
        )
        await self._outgoing_queue.put(msg)
    
    async def send_log_line(self, job_id: int, line: str, level: str = "INFO") -> None:
        """Send a log line through the stream for live log streaming."""
        ts = Timestamp()
        ts.FromDatetime(datetime.now(timezone.utc))
        
        msg = qalita_pb2.WorkerMessage(
            log_line=qalita_pb2.JobLogLine(
                job_id=job_id,
                line=line,
                level=level,
                timestamp=ts,
            )
        )
        await self._outgoing_queue.put(msg)
    
    async def send_data_preview_response(
        self,
        request_id: str,
        ok: bool,
        data_type: str,
        error: Optional[str] = None,
        headers: Optional[list[str]] = None,
        rows: Optional[list[list[str]]] = None,
        total_rows: Optional[int] = None,
        content: Optional[str] = None,
        binary_base64: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> None:
        """Send a data preview response through the stream."""
        response = qalita_pb2.DataPreviewResponse(
            request_id=request_id,
            ok=ok,
            data_type=data_type,
        )
        
        if error:
            response.error = error
        if headers:
            response.headers.extend(headers)
        if rows:
            for row in rows:
                data_row = qalita_pb2.DataRow(values=row)
                response.rows.append(data_row)
        if total_rows is not None:
            response.total_rows = total_rows
        if content:
            response.content = content
        if binary_base64:
            response.binary_base64 = binary_base64
        if mime_type:
            response.mime_type = mime_type
        
        msg = qalita_pb2.WorkerMessage(data_preview_response=response)
        await self._outgoing_queue.put(msg)
    
    async def send_add_source_response(
        self,
        request_id: str,
        ok: bool,
        source_id: Optional[int] = None,
        connectivity_verified: bool = False,
        error: Optional[str] = None,
    ) -> None:
        """Send an add source response through the stream."""
        response = qalita_pb2.AddSourceResponse(
            request_id=request_id,
            ok=ok,
            connectivity_verified=connectivity_verified,
        )
        
        if error:
            response.error = error
        if source_id is not None:
            response.source_id = source_id
        
        msg = qalita_pb2.WorkerMessage(add_source_response=response)
        await self._outgoing_queue.put(msg)
    
    async def send_agent_action_response(
        self,
        request_id: str,
        ok: bool,
        action_type: str,
        error: Optional[str] = None,
        result_json: Optional[str] = None,
        data: Optional[qalita_pb2.DataPreviewResponse] = None,
        execution_time_ms: Optional[int] = None,
    ) -> None:
        """Send an agent action response through the stream."""
        response = qalita_pb2.AgentActionResponse(
            request_id=request_id,
            ok=ok,
            action_type=action_type,
        )
        
        if error:
            response.error = error
        if result_json:
            response.result_json = result_json
        if data:
            response.data.CopyFrom(data)
        if execution_time_ms is not None:
            response.execution_time_ms = execution_time_ms
        
        msg = qalita_pb2.WorkerMessage(agent_action_response=response)
        await self._outgoing_queue.put(msg)
    
    async def _outgoing_messages(self) -> AsyncIterator[qalita_pb2.WorkerMessage]:
        """Generator for outgoing stream messages."""
        logger.info("Outgoing messages generator started")
        while self._stream_active:
            try:
                # Use get_nowait in a loop with sleep to avoid blocking gRPC
                try:
                    msg = self._outgoing_queue.get_nowait()
                    logger.debug(f"Yielding message type: {msg.WhichOneof('payload')}")
                    yield msg
                except asyncio.QueueEmpty:
                    # No message available, yield control briefly
                    await asyncio.sleep(0.05)
            except asyncio.CancelledError:
                logger.info("Outgoing messages generator cancelled")
                break
            except Exception as e:
                logger.error(f"Error in outgoing generator: {e}")
                await asyncio.sleep(0.1)
        logger.info("Outgoing messages generator stopped")
    
    async def start_stream(self) -> None:
        """
        Start the bidirectional stream for real-time communication.
        
        This method runs indefinitely, handling:
        - Keep-alive signals (sent every 10 seconds)
        - Incoming job assignments
        - Incoming routine triggers
        - Automatic reconnection on failure
        """
        if not self._connected:
            if not await self.connect():
                raise ConnectionError("Failed to connect to gRPC server")
        
        # Recreate queue in async context to ensure proper event loop binding
        self._outgoing_queue = asyncio.Queue()
        self._stream_active = True
        
        async def keep_alive_loop():
            """Send keep-alive every 10 seconds."""
            logger.info(f"Keep-alive loop started, worker_id={self._worker_id}")
            while self._stream_active:
                try:
                    logger.debug(f"Sending keep-alive for worker {self._worker_id}")
                    await self.send_keep_alive()
                    await asyncio.sleep(10)
                except asyncio.CancelledError:
                    logger.info("Keep-alive loop cancelled")
                    break
                except Exception as e:
                    logger.error(f"Keep-alive error: {e}")
        
        async def process_stream():
            """Process incoming stream messages."""
            try:
                self._stream_call = self._stub.Connect(
                    self._outgoing_messages(),
                    metadata=self.metadata,
                )
                
                async for msg in self._stream_call:
                    if msg.HasField('job_assignment'):
                        job = msg.job_assignment.job
                        logger.info(f"Received job assignment: {job.id}")
                        if self._on_job_received:
                            await self._on_job_received(job)
                    
                    elif msg.HasField('routine_triggered'):
                        routine = msg.routine_triggered.routine
                        logger.info(f"Received routine trigger: {routine.id}")
                        if self._on_routine_received:
                            await self._on_routine_received(routine)
                    
                    elif msg.HasField('data_preview_request'):
                        request = msg.data_preview_request
                        logger.info(f"Received data preview request: {request.request_id} for source {request.source_id}")
                        if self._on_data_preview_request:
                            await self._on_data_preview_request(request)
                    
                    elif msg.HasField('add_source_request'):
                        request = msg.add_source_request
                        logger.info(f"Received add source request: {request.request_id} for '{request.name}'")
                        if self._on_add_source_request:
                            await self._on_add_source_request(request)
                    
                    elif msg.HasField('agent_action_request'):
                        request = msg.agent_action_request
                        logger.info(f"Received agent action request: {request.request_id} type={request.action_type}")
                        if self._on_agent_action_request:
                            await self._on_agent_action_request(request)
                    
                    elif msg.HasField('ack'):
                        logger.debug(f"Received ack: {msg.ack.message_type}")
                    
                    elif msg.HasField('error'):
                        logger.error(f"Server error: {msg.error.code} - {msg.error.message}")
            
            except grpc.aio.AioRpcError as e:
                if e.code() == grpc.StatusCode.CANCELLED:
                    logger.info("Stream cancelled")
                else:
                    logger.error(f"Stream error: {e.code()} - {e.details()}")
                    # Attempt reconnection
                    if self._stream_active and await self._reconnect():
                        await process_stream()
        
        # Run keep-alive and stream processing concurrently
        keep_alive_task = asyncio.create_task(keep_alive_loop())
        
        try:
            await process_stream()
        finally:
            self._stream_active = False
            keep_alive_task.cancel()
            try:
                await keep_alive_task
            except asyncio.CancelledError:
                pass
    
    async def stop_stream(self) -> None:
        """Stop the bidirectional stream."""
        self._stream_active = False
        if self._stream_call:
            try:
                self._stream_call.cancel()
            except Exception as e:
                logger.debug(f"Error cancelling stream during stop: {e}")
