"""
Synchronous HTTP client for ProcessCube® Engine API.

This client provides a high-level, synchronous interface to all ProcessCube® Engine
features. It is designed for Robot Framework and other synchronous contexts.
"""

import logging
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from dataclasses import dataclass, field
from dataclasses_json import dataclass_json, LetterCase

from .helpers.application_info import ApplicationInfo, ApplicationInfoHandler
from .helpers.data_object_instances import (
    DataObjectInstanceHandler,
    DataObjectInstancesQuery,
    DataObjectInstanceResponse,
)
from .helpers.empty_tasks import EmptyTaskHandler, EmptyTaskQuery, EmptyTaskResponse
from .helpers.events import EventsHandler, MessageTriggerRequest
from .helpers.external_tasks import (
    ExtendLockRequest,
    FetchAndLockRequestPayload,
    ExternalTask,
    ExternalTaskHandler,
    FinishExternalTaskRequestPayload,
    BpmnErrorRequest,
    ServiceErrorRequest,
)
from .helpers.flow_node_instances import (
    FlowNodeInstanceHandler,
    FlowNodeInstanceResponse,
    FlowNodeInstancesQuery,
)
from .helpers.manual_tasks import ManualTaskHandler, ManualTaskQuery, ManualTaskResponse
from .helpers.process_definitions import (
    ProcessDefinitionUploadPayload,
    ProcessDefinitionHandler,
)
from .helpers.process_instances import (
    ProcessInstanceHandler,
    ProcessInstanceQueryRequest,
    ProcessInstanceQueryResponse,
)
from .helpers.process_models import (
    ProcessStartRequest,
    ProcessStartResponse,
    ProcessModelHandler,
)
from .helpers.user_tasks import (
    UserTaskHandler,
    UserTaskQuery,
    UserTaskResponse,
    ReserveUserTaskRequest,
)


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class DeployResult:
    """
    Result of a single process model deployment.

    Attributes:
        filename: Path to the deployed file
        deployed: Whether deployment was successful
    """

    filename: str
    deployed: bool = True


@dataclass_json(letter_case=LetterCase.CAMEL)
@dataclass
class DeployResults:
    """
    Collection of deployment results.

    Attributes:
        deployed_files: List of individual deployment results
    """

    deployed_files: List[DeployResult] = field(default_factory=list)


class Client:
    """
    Synchronous client for ProcessCube® Engine API.

    This client provides a high-level interface to all ProcessCube® Engine features
    using synchronous HTTP requests. It is designed for use with Robot Framework
    and other synchronous contexts.

    The client automatically handles the ProcessCube API base path:
    - Default: /atlas_engine/api/v1

    Args:
        url: Base URL of the ProcessCube® Engine (e.g., "http://localhost:56100")
        identity: Optional callable that returns identity dict with 'token' key.
                 If None, uses default dummy token: ZHVtbXlfdG9rZW4=
        api_version: API version to use (default: "v1")

    Example:
        >>> # Simple usage with default identity
        >>> client = Client("http://localhost:56100")
        >>> info = client.info()
        >>>
        >>> # With custom identity provider
        >>> def get_identity():
        ...     return {"token": "my_token"}
        >>> client = Client("http://localhost:56100", identity=get_identity)
        >>>
        >>> # Start a process
        >>> result = client.process_model_start(
        ...     "MyProcess",
        ...     ProcessStartRequest(start_event_id="StartEvent_1")
        ... )
    """

    def __init__(
        self,
        url: str,
        identity: Optional[Callable[[], Dict[str, str]]] = None,
        api_version: str = "v1",
    ):
        """
        Initialize the Client.

        Args:
            url: Base URL of the ProcessCube® Engine (e.g., "http://localhost:56100")
            identity: Optional callable returning dict with 'token' key
            api_version: API version to use (default: "v1")
        """
        self._url = url
        self._identity = identity
        self._api_version = api_version
        self.logger = logging.getLogger(__name__)

    # =========================================================================
    # Application Info
    # =========================================================================

    def info(self) -> ApplicationInfo:
        """
        Get application information from the ProcessCube® Engine.

        API Endpoint: GET /info

        Returns:
            Application information including version, name, etc.

        Example:
            >>> client = Client("http://localhost:56100")
            >>> info = client.info()
            >>> print(f"Engine version: {info.version}")
        """
        handler = ApplicationInfoHandler(self._url, self._identity, self._api_version)
        return handler.info()

    def authority(self) -> str:
        """
        Get the authority/identity service URL.

        API Endpoint: GET /authority

        Returns:
            Authority service URL

        Example:
            >>> client = Client("http://localhost:56100")
            >>> authority = client.authority()
        """
        handler = ApplicationInfoHandler(self._url, self._identity, self._api_version)
        return handler.authority()

    # =========================================================================
    # Process Definitions
    # =========================================================================

    def process_definition_upload(
        self, payload: ProcessDefinitionUploadPayload
    ) -> None:
        """
        Upload a process definition to the ProcessCube® Engine.

        API Endpoint: POST /process_definitions

        Args:
            payload: Upload payload containing BPMN XML

        Example:
            >>> from processcube_client.core.api.helpers.process_definitions import (
            ...     ProcessDefinitionUploadPayload
            ... )
            >>>
            >>> payload = ProcessDefinitionUploadPayload(
            ...     xml="<bpmn:definitions>...</bpmn:definitions>",
            ...     overwrite_existing=True
            ... )
            >>> client.process_definition_upload(payload)
        """
        handler = ProcessDefinitionHandler(self._url, self._identity, self._api_version)
        handler.upload(payload)

    def process_definition_delete(
        self, process_definition_id: str, delete_all_related_data: bool = False
    ) -> None:
        """
        Delete a process definition from the ProcessCube® Engine.

        API Endpoint: DELETE /process_definitions/{processDefinitionId}

        Args:
            process_definition_id: ID of the process definition to delete
            delete_all_related_data: Whether to delete all related data

        Example:
            >>> client.process_definition_delete("myProcess_12345678")
        """
        handler = ProcessDefinitionHandler(self._url, self._identity, self._api_version)
        handler.delete(process_definition_id, delete_all_related_data)

    # =========================================================================
    # Process Models
    # =========================================================================

    def process_model_start(
        self, process_model_id: str, payload: ProcessStartRequest
    ) -> ProcessStartResponse:
        """
        Start a new process instance.

        API Endpoint: POST /process_models/{processModelId}/start

        Args:
            process_model_id: ID of the process model to start
            payload: Start request payload

        Returns:
            Process start response with instance ID

        Example:
            >>> from processcube_client.core.api.helpers.process_models import (
            ...     ProcessStartRequest,
            ...     StartCallbackType
            ... )
            >>>
            >>> request = ProcessStartRequest(
            ...     start_event_id="StartEvent_1",
            ...     return_on=StartCallbackType.CALLBACK_ON_PROCESS_INSTANCE_FINISHED
            ... )
            >>> result = client.process_model_start("MyProcess", request)
            >>> print(f"Started process: {result.process_instance_id}")
        """
        handler = ProcessModelHandler(self._url, self._identity, self._api_version)
        return handler.start(process_model_id, payload)

    # =========================================================================
    # Process Instances
    # =========================================================================

    def process_instance_query(
        self, request: ProcessInstanceQueryRequest
    ) -> List[ProcessInstanceQueryResponse]:
        """
        Query process instances.

        API Endpoint: GET /process_instances/query

        Args:
            request: Query parameters

        Returns:
            List of query responses with matching process instances

        Example:
            >>> from processcube_client.core.api.helpers.process_instances import (
            ...     ProcessInstanceQueryRequest
            ... )
            >>>
            >>> query = ProcessInstanceQueryRequest(
            ...     process_model_id="MyProcess",
            ...     limit=10
            ... )
            >>> response = client.process_instance_query(query)
            >>> print(f"Found {response.total_count} instances")
        """
        handler = ProcessInstanceHandler(self._url, self._identity, self._api_version)
        return handler.query(request)

    def process_instance_terminate(self, process_instance_id: str) -> bool:
        """
        Terminate a running process instance.

        API Endpoint: PUT /process_instances/{processInstanceId}/terminate

        Args:
            process_instance_id: ID of the process instance to terminate

        Returns:
            True if successful

        Example:
            >>> client.process_instance_terminate("myProcessInstance_12345678")
        """
        handler = ProcessInstanceHandler(self._url, self._identity, self._api_version)
        return handler.terminate(process_instance_id)

    # =========================================================================
    # User Tasks
    # =========================================================================

    def user_task_query(self, query: UserTaskQuery) -> List[UserTaskResponse]:
        """
        Query user tasks.

        API Endpoint: GET /user_tasks (with query parameters)

        Args:
            query: Query parameters

        Returns:
            List of responses with matching user tasks

        Example:
            >>> from processcube_client.core.api.helpers.user_tasks import UserTaskQuery
            >>>
            >>> query = UserTaskQuery(process_instance_id="myProcessInstance_12345678")
            >>> response = client.user_task_query(query)
            >>> print(f"Found {response.total_count} user tasks")
        """
        handler = UserTaskHandler(self._url, self._identity, self._api_version)
        return handler.query(query)

    def user_task_finish(
        self, user_task_instance_id: str, result: Dict[str, Any]
    ) -> bool:
        """
        Finish a user task.

        API Endpoint: PUT /user_tasks/{userTaskInstanceId}/finish

        Args:
            user_task_instance_id: ID of the user task instance
            result: Result payload

        Returns:
            True if successful

        Example:
            >>> client.user_task_finish(
            ...     "myUserTask_12345678",
            ...     {"approved": True, "comment": "Looks good"}
            ... )
        """
        handler = UserTaskHandler(self._url, self._identity, self._api_version)
        return handler.finish(user_task_instance_id, result)

    def user_task_reserve(
        self, user_task_instance_id: str, request: ReserveUserTaskRequest
    ) -> bool:
        """
        Reserve a user task.

        API Endpoint: PUT /user_tasks/{userTaskInstanceId}/reserve

        Args:
            user_task_instance_id: ID of the user task instance
            request: Reserve request with actual owner ID

        Returns:
            True if successful

        Example:
            >>> from processcube_client.core.api.helpers.user_tasks import (
            ...     ReserveUserTaskRequest
            ... )
            >>>
            >>> request = ReserveUserTaskRequest(actual_owner_id="user123")
            >>> client.user_task_reserve("myUserTask_12345678", request)
        """
        handler = UserTaskHandler(self._url, self._identity, self._api_version)
        return handler.reserve(user_task_instance_id, request)

    def user_task_cancel_reservation(self, user_task_instance_id: str) -> bool:
        """
        Cancel a user task reservation.

        API Endpoint: DELETE /user_tasks/{userTaskInstanceId}/cancel-reservation

        Args:
            user_task_instance_id: ID of the user task instance

        Returns:
            True if successful

        Example:
            >>> client.user_task_cancel_reservation("myUserTask_12345678")
        """
        handler = UserTaskHandler(self._url, self._identity, self._api_version)
        return handler.cancel_reservation(user_task_instance_id)

    # =========================================================================
    # Manual Tasks
    # =========================================================================

    def manual_task_query(self, query: ManualTaskQuery) -> List[ManualTaskResponse]:
        """
        Query manual tasks.

        Args:
            query: Query parameters

        Returns:
            List of responses with matching manual tasks

        Example:
            >>> from processcube_client.core.api.helpers.manual_tasks import ManualTaskQuery
            >>>
            >>> query = ManualTaskQuery(process_instance_id="myProcessInstance_12345678")
            >>> response = client.manual_task_query(query)
        """
        handler = ManualTaskHandler(self._url, self._identity, self._api_version)
        return handler.query(query)

    def manual_task_finish(self, manual_task_instance_id: str) -> bool:
        """
        Finish a manual task.

        API Endpoint: PUT /manual_tasks/{manualTaskInstanceId}/finish

        Args:
            manual_task_instance_id: ID of the manual task instance

        Returns:
            True if successful

        Example:
            >>> client.manual_task_finish("myManualTask_12345678")
        """
        handler = ManualTaskHandler(self._url, self._identity, self._api_version)
        return handler.finish(manual_task_instance_id)

    # =========================================================================
    # Empty Tasks (deprecated - use Untyped Tasks)
    # =========================================================================

    def empty_task_query(self, query: EmptyTaskQuery) -> List[EmptyTaskResponse]:
        """
        Query empty tasks (deprecated - use untyped_task_query).

        Args:
            query: Query parameters

        Returns:
            List of responses with matching empty tasks
        """
        handler = EmptyTaskHandler(self._url, self._identity, self._api_version)
        return handler.query(query)

    def empty_task_finish(self, empty_activity_instance_id: str) -> bool:
        """
        Finish an empty task (deprecated - use untyped_task_finish).

        Args:
            empty_activity_instance_id: ID of the empty task instance

        Returns:
            True if successful
        """
        handler = EmptyTaskHandler(self._url, self._identity, self._api_version)
        return handler.finish(empty_activity_instance_id)

    # =========================================================================
    # External Tasks
    # =========================================================================

    def external_task_fetch_and_lock(
        self, payload: FetchAndLockRequestPayload
    ) -> List[ExternalTask]:
        """
        Fetch and lock external tasks.

        API Endpoint: POST /external_tasks/fetch_and_lock

        Args:
            payload: Fetch and lock request payload

        Returns:
            List of locked external tasks

        Example:
            >>> from processcube_client.core.api.helpers.external_tasks import (
            ...     FetchAndLockRequestPayload
            ... )
            >>>
            >>> payload = FetchAndLockRequestPayload(
            ...     worker_id="myWorker",
            ...     topic_name="myTopic",
            ...     max_tasks=5,
            ...     long_polling_timeout=10000,
            ...     lock_duration=30000
            ... )
            >>> tasks = client.external_task_fetch_and_lock(payload)
        """
        handler = ExternalTaskHandler(self._url, self._identity, self._api_version)
        return handler.fetch_and_lock(payload)

    def external_task_extend_lock(
        self, external_task_id: str, request: ExtendLockRequest
    ) -> bool:
        """
        Extend the lock of an external task.

        API Endpoint: PUT /external_tasks/{externalTaskId}/extend_lock

        Args:
            external_task_id: ID of the external task
            request: Extend lock request with duration

        Returns:
            True if successful

        Example:
            >>> from processcube_client.core.api.helpers.external_tasks import (
            ...     ExtendLockRequest
            ... )
            >>>
            >>> request = ExtendLockRequest(
            ...     worker_id="myWorker",
            ...     additional_duration=30000
            ... )
            >>> client.external_task_extend_lock("myTask_12345678", request)
        """
        handler = ExternalTaskHandler(self._url, self._identity, self._api_version)
        return handler.extend_lock(external_task_id, request)

    def external_task_finish(
        self, external_task_id: str, payload: FinishExternalTaskRequestPayload
    ) -> bool:
        """
        Finish an external task.

        API Endpoint: PUT /external_tasks/{externalTaskId}/finish

        Args:
            external_task_id: ID of the external task
            payload: Finish request with result

        Returns:
            True if successful

        Example:
            >>> from processcube_client.core.api.helpers.external_tasks import (
            ...     FinishExternalTaskRequestPayload
            ... )
            >>>
            >>> payload = FinishExternalTaskRequestPayload(
            ...     worker_id="myWorker",
            ...     result={"status": "completed"}
            ... )
            >>> client.external_task_finish("myTask_12345678", payload)
        """
        handler = ExternalTaskHandler(self._url, self._identity, self._api_version)
        return handler.finish(external_task_id, payload)

    def external_task_handle_bpmn_error(
        self, external_task_id: str, request: BpmnErrorRequest
    ) -> bool:
        """
        Report a BPMN error for an external task.

        API Endpoint: PUT /external_tasks/{externalTaskId}/error

        Args:
            external_task_id: ID of the external task
            request: BPMN error request

        Returns:
            True if successful

        Example:
            >>> from processcube_client.core.api.helpers.external_tasks import (
            ...     BpmnErrorRequest
            ... )
            >>>
            >>> error = BpmnErrorRequest(
            ...     worker_id="myWorker",
            ...     error_code="ValidationError",
            ...     error_message="Invalid data"
            ... )
            >>> client.external_task_handle_bpmn_error("myTask_12345678", error)
        """
        handler = ExternalTaskHandler(self._url, self._identity, self._api_version)
        return handler.handle_bpmn_error(external_task_id, request)

    def external_task_handle_service_error(
        self, external_task_id: str, request: ServiceErrorRequest
    ) -> bool:
        """
        Report a service error for an external task.

        API Endpoint: PUT /external_tasks/{externalTaskId}/error

        Args:
            external_task_id: ID of the external task
            request: Service error request

        Returns:
            True if successful

        Example:
            >>> from processcube_client.core.api.helpers.external_tasks import (
            ...     ServiceErrorRequest
            ... )
            >>>
            >>> error = ServiceErrorRequest(
            ...     worker_id="myWorker",
            ...     error_message="Service unavailable",
            ...     error_details={"service": "payment-api"}
            ... )
            >>> client.external_task_handle_service_error("myTask_12345678", error)
        """
        handler = ExternalTaskHandler(self._url, self._identity, self._api_version)
        return handler.handle_service_error(external_task_id, request)

    # =========================================================================
    # Events
    # =========================================================================

    def trigger_message(
        self, message_name: str, request: MessageTriggerRequest
    ) -> bool:
        """
        Trigger a message event.

        API Endpoint: POST /messages/{eventName}/trigger

        Args:
            message_name: Name of the message event
            request: Message trigger request

        Returns:
            True if successful

        Example:
            >>> from processcube_client.core.api.helpers.events import (
            ...     MessageTriggerRequest
            ... )
            >>>
            >>> request = MessageTriggerRequest(
            ...     process_instance_id="myProcessInstance_12345678",
            ...     payload={"data": "value"}
            ... )
            >>> client.event_trigger_message_event("OrderReceived", request)
        """
        handler = EventsHandler(self._url, self._identity, self._api_version)
        return handler.trigger_message(message_name, request)

    def trigger_signal(self, signal_name: str) -> bool:
        """
        Trigger a signal event.

        API Endpoint: POST /signals/{eventName}/trigger

        Args:
            signal_name: Name of the signal event

        Returns:
            True if successful

        Example:
            >>> client.event_trigger_signal_event("EmergencyShutdown")
        """
        handler = EventsHandler(self._url, self._identity, self._api_version)
        return handler.trigger_signal(signal_name)

    # =========================================================================
    # Flow Node Instances
    # =========================================================================

    def flow_node_instance_query(
        self, query: FlowNodeInstancesQuery
    ) -> List[FlowNodeInstanceResponse]:
        """
        Query flow node instances.

        API Endpoint: GET /flow_node_instances

        Args:
            query: Query parameters

        Returns:
            List of responses with matching flow node instances

        Example:
            >>> from processcube_client.core.api.helpers.flow_node_instances import (
            ...     FlowNodeInstancesQuery
            ... )
            >>>
            >>> query = FlowNodeInstancesQuery(
            ...     process_instance_id="myProcessInstance_12345678"
            ... )
            >>> response = client.flow_node_instance_query(query)
        """
        handler = FlowNodeInstanceHandler(self._url, self._identity, self._api_version)
        return handler.query(query)

    # =========================================================================
    # Data Object Instances
    # =========================================================================

    def data_object_instance_query(
        self, query: DataObjectInstancesQuery
    ) -> List[DataObjectInstanceResponse]:
        """
        Query data object instances.

        API Endpoint: GET /data_object_instances/query

        Args:
            query: Query parameters

        Returns:
            List of responses with matching data object instances

        Example:
            >>> from processcube_client.core.api.helpers.data_object_instances import (
            ...     DataObjectInstancesQuery
            ... )
            >>>
            >>> query = DataObjectInstancesQuery(
            ...     process_instance_id="myProcessInstance_12345678"
            ... )
            >>> response = client.data_object_instance_query(query)
        """
        handler = DataObjectInstanceHandler(
            self._url, self._identity, self._api_version
        )
        return handler.query(query)

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    def deploy_bpmn_from_path(self, path: str | Path) -> DeployResults:
        """
        Deploy BPMN file(s) from a path.

        Args:
            path: Path to BPMN file or directory containing BPMN files

        Returns:
            Deployment results

        Example:
            >>> # Deploy single file
            >>> result = client.deploy_bpmn_from_path("process.bpmn")
            >>>
            >>> # Deploy directory
            >>> result = client.deploy_bpmn_from_path("processes/")
            >>> for deployed in result.deployed_files:
            ...     print(f"{deployed.filename}: {deployed.deployed}")
        """
        path_obj = Path(path)
        results = DeployResults()

        if path_obj.is_file():
            # Deploy single file
            with open(path_obj, "r", encoding="utf-8") as f:
                xml = f.read()

            payload = ProcessDefinitionUploadPayload(xml=xml, overwrite_existing=True)

            try:
                self.process_definition_upload(payload)
                results.deployed_files.append(
                    DeployResult(filename=str(path_obj), deployed=True)
                )
            except Exception as e:
                self.logger.error(f"Failed to deploy {path_obj}: {e}")
                results.deployed_files.append(
                    DeployResult(filename=str(path_obj), deployed=False)
                )

        elif path_obj.is_dir():
            # Deploy all BPMN files in directory
            for bpmn_file in path_obj.glob("**/*.bpmn"):
                with open(bpmn_file, "r", encoding="utf-8") as f:
                    xml = f.read()

                payload = ProcessDefinitionUploadPayload(
                    xml=xml, overwrite_existing=True
                )

                try:
                    self.process_definition_upload(payload)
                    results.deployed_files.append(
                        DeployResult(filename=str(bpmn_file), deployed=True)
                    )
                except Exception as e:
                    self.logger.error(f"Failed to deploy {bpmn_file}: {e}")
                    results.deployed_files.append(
                        DeployResult(filename=str(bpmn_file), deployed=False)
                    )

        return results

    def __repr__(self) -> str:
        """String representation of the client."""
        return f"Client(url='{self._url}', api_version='{self._api_version}')"


__all__ = ["Client", "DeployResult", "DeployResults"]
