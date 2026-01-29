from __future__ import annotations

import uuid
from contextlib import asynccontextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, Any, Self, TypedDict, cast

from cedarpy import (
    AuthzResult,
    Decision,
    format_policies,
    is_authorized,
)
from fastapi import HTTPException
from pydantic import BaseModel

from planar.human.models import Assignment, HumanTask, TaskScope
from planar.logging import get_logger
from planar.security.auth_context import get_current_principal
from planar.utils import flatmap

if TYPE_CHECKING:
    from planar.security.models import Principal
    from planar.user.models import IDPGroup, IDPUser

logger = get_logger(__name__)

# Context variable for the current authorization service
policy_service_var: ContextVar["PolicyService | None"] = ContextVar(
    "policy_service", default=None
)


def get_policy_service() -> "PolicyService | None":
    """
    Get the current authorization service from context.

    Returns:
        The current PolicyService or None if not set.
    """
    return policy_service_var.get()


def set_policy_service(policy_service: "PolicyService | None") -> Any:
    """
    Set the current authorization service in context.

    Args:
        policy_service: The authorization service to set.

    Returns:
        A token that can be used to reset the context.
    """
    return policy_service_var.set(policy_service)


@asynccontextmanager
async def policy_service_context(policy_service: "PolicyService | None"):
    """Context manager for setting up and tearing down authorization service context"""
    token = set_policy_service(policy_service)
    try:
        yield policy_service
    finally:
        policy_service_var.reset(token)


class WorkflowAction(str, Enum):
    """Actions that can be performed on a workflow."""

    WORKFLOW_LIST = "Workflow::List"
    WORKFLOW_VIEW_DETAILS = "Workflow::ViewDetails"
    WORKFLOW_RUN = "Workflow::Run"
    WORKFLOW_CANCEL = "Workflow::Cancel"


class AgentAction(str, Enum):
    """Actions that can be performed on an agent."""

    AGENT_LIST = "Agent::List"
    AGENT_VIEW_DETAILS = "Agent::ViewDetails"
    AGENT_RUN = "Agent::Run"
    AGENT_UPDATE = "Agent::Update"
    AGENT_SIMULATE = "Agent::Simulate"


class RuleAction(str, Enum):
    """Actions that can be performed on rules."""

    RULE_LIST = "Rule::List"
    RULE_VIEW_DETAILS = "Rule::ViewDetails"
    RULE_UPDATE = "Rule::Update"
    RULE_SIMULATE = "Rule::Simulate"


class DatasetAction(str, Enum):
    """Actions that can be performed on datasets."""

    DATASET_LIST_SCHEMAS = "Dataset::ListSchemas"
    DATASET_LIST = "Dataset::List"
    DATASET_VIEW_DETAILS = "Dataset::ViewDetails"
    DATASET_STREAM_CONTENT = "Dataset::StreamContent"
    DATASET_DOWNLOAD = "Dataset::Download"


class EvalAction(str, Enum):
    """Actions that can be performed on eval resources."""

    EVAL_SET_READ = "Eval::SetRead"
    EVAL_SET_WRITE = "Eval::SetWrite"
    EVAL_SUITE_READ = "Eval::SuiteRead"
    EVAL_SUITE_WRITE = "Eval::SuiteWrite"
    EVAL_RUN_READ = "Eval::RunRead"
    EVAL_RUN_CREATE = "Eval::RunCreate"


class UserAction(str, Enum):
    """Actions that can be performed on user resources."""

    USER_LIST = "User::List"
    USER_VIEW_DETAILS = "User::ViewDetails"


class GroupAction(str, Enum):
    """Actions that can be performed on group resources."""

    GROUP_LIST = "Group::List"
    GROUP_VIEW_DETAILS = "Group::ViewDetails"


class DirSyncAction(str, Enum):
    """Actions that can be performed on dir sync resources."""

    DIR_SYNC_TRIGGER_SYNC = "DirSync::TriggerSync"


class HumanTaskAction(str, Enum):
    TASK_ASSIGN = "HumanTask::Assign"
    TASK_VIEW = "HumanTask::View"


class ResourceType(str, Enum):
    PRINCIPAL = "Principal"
    WORKFLOW = "Workflow"
    ENTITY = "Entity"
    AGENT = "Agent"
    Rule = "Rule"
    DATASET = "Dataset"
    EVAL_SET = "EvalSet"
    EVAL_SUITE = "EvalSuite"
    USER = "User"
    GROUP = "Group"
    DIR_SYNC = "DirSync"
    HUMAN_TASK = "HumanTask"


class EntityIdentifier(TypedDict):
    type: str
    id: str


class EntityUid(TypedDict):
    __entity: EntityIdentifier


class EntityDict(TypedDict):
    uid: EntityUid
    attrs: dict
    parents: list[EntityIdentifier]


@dataclass(frozen=True, slots=True)
class AgentResource:
    """`id=None` means “any agent” (wild-card)."""

    id: str | None = None


@dataclass(frozen=True, slots=True)
class WorkflowResource:
    """`name=None` means “any workflow”."""

    function_name: str | None = None


@dataclass(frozen=True, slots=True)
class RuleResource:
    rule_name: str | None = None


@dataclass(frozen=True, slots=True)
class DatasetResource:
    dataset_name: str | None = None


@dataclass(frozen=True, slots=True)
class EvalSetResource:
    eval_set_id: str | None = None


@dataclass(frozen=True, slots=True)
class EvalSuiteResource:
    suite_id: str | None = None


@dataclass(frozen=True, slots=True)
class UserResource:
    user_id: str | None = None
    email: str | None = None
    first_name: str | None = None
    last_name: str | None = None

    group_names: list[str] | None = None

    @classmethod
    def from_user(cls, user: IDPUser) -> Self:
        return cls(
            user_id=str(user.id),
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            group_names=flatmap(user.groups, lambda groups: [g.name for g in groups]),
        )


@dataclass(frozen=True, slots=True)
class GroupResource:
    group_id: str | None = None
    group_name: str | None = None

    @classmethod
    def from_group(cls, group: IDPGroup) -> Self:
        return cls(
            group_id=str(group.id),
            group_name=group.name,
        )


@dataclass(frozen=True, slots=True)
class DirSyncResource:
    dir_sync_id: str | None = None


@dataclass(frozen=True, slots=True)
class TaskScopeResource:
    task_id: str | None = None
    user_emails: list[str] | None = None
    group_names: list[str] | None = None

    @classmethod
    def from_task_scope(cls, scope: TaskScope) -> Self:
        return cls(
            task_id=str(scope.task_id),
            user_emails=flatmap(scope.users, lambda users: [u.email for u in users]),
            group_names=flatmap(scope.groups, lambda groups: [g.name for g in groups]),
        )


@dataclass(frozen=True, slots=True)
class AssignmentResource:
    task_id: str | None = None
    assignee: UserResource | None = None
    assignor: UserResource | None = None

    @classmethod
    def from_assignment(cls, assignment: Assignment) -> Self:
        return cls(
            task_id=str(assignment.task_id),
            assignee=flatmap(assignment.assignee, UserResource.from_user),
            assignor=flatmap(assignment.assignor, UserResource.from_user),
        )


@dataclass(frozen=True, slots=True)
class HumanTaskResource:
    human_task_id: str | None = None
    assignment: AssignmentResource | None = None
    scope: TaskScopeResource | None = None

    # A proposed assignment that we wish to validate via Cedar policies
    proposed_assignment: AssignmentResource | None = None

    @classmethod
    def from_human_task(
        cls, task: HumanTask, proposed_assignment: AssignmentResource | None = None
    ) -> Self:
        # NB: because we're using async SQLA, all the relationships must be eagerly loaded via
        # `selectinload` or `joinedload` in the `HumanTask` query for `task` to avoid `greenlet_spawn` errors.
        return cls(
            human_task_id=str(task.id),
            assignment=flatmap(task.assignment, AssignmentResource.from_assignment),
            scope=flatmap(task.scope, TaskScopeResource.from_task_scope),
            proposed_assignment=proposed_assignment,
        )


ResourceDescriptor = (
    AgentResource
    | WorkflowResource
    | RuleResource
    | DatasetResource
    | EvalSetResource
    | EvalSuiteResource
    | UserResource
    | GroupResource
    | DirSyncResource
    | HumanTaskResource
)


def _filter_nones(data: Any) -> Any:
    """Recursively filter out None values from a dict, because Cedar doesn't support nulls."""
    if isinstance(data, dict):
        return {k: _filter_nones(v) for k, v in data.items() if v is not None}
    elif isinstance(data, list):
        return [_filter_nones(item) for item in data if item is not None]
    else:
        return data


class CedarEntity(BaseModel):
    resource_type: ResourceType
    resource_key: str
    resource_attributes: dict[str, Any] = {}

    def to_dict(self) -> EntityDict:
        role = self.resource_attributes.get("role", None)
        parents = []
        if role is not None:
            parents.append({"type": "Role", "id": role})

        return {
            "uid": {
                "__entity": {
                    "type": self.resource_type.value,
                    "id": str(self.resource_attributes[self.resource_key]),
                }
            },
            "attrs": {
                k: v for k, v in self.resource_attributes.items() if v is not None
            },
            "parents": parents,
        }

    @property
    def id(self) -> str:
        """
        Returns the identifier value for this CedarEntity, based on its resource_key.

        Sometimes, such as when authorizing on a list of resources, there is no id present
        for a given resource_key. In this case, we return the string "None".
        """
        return str(self.resource_attributes.get(self.resource_key))

    @staticmethod
    def from_principal(principal: Principal) -> "CedarEntity":
        """Create a CedarEntity instance from principal data.

        Args:
            principal: Principal instance

        Returns:
            CedarEntity: A new CedarEntity instance
        """
        return CedarEntity(
            resource_type=ResourceType.PRINCIPAL,
            resource_key="sub",
            resource_attributes=principal.model_dump(exclude={"idp_user_"}),
        )

    @staticmethod
    def from_workflow(function_name: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from workflow data."""
        return CedarEntity(
            resource_type=ResourceType.WORKFLOW,
            resource_key="function_name",
            resource_attributes={"function_name": function_name},
        )

    @staticmethod
    def from_agent(agent_id: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from agent data."""
        return CedarEntity(
            resource_type=ResourceType.AGENT,
            resource_key="agent_id",
            resource_attributes={"agent_id": agent_id},
        )

    @staticmethod
    def from_rule(rule_name: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from rule data"""
        return CedarEntity(
            resource_type=ResourceType.Rule,
            resource_key="rule_name",
            resource_attributes={"rule_name": rule_name},
        )

    @staticmethod
    def from_dataset(dataset_name: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from dataset data"""
        return CedarEntity(
            resource_type=ResourceType.DATASET,
            resource_key="dataset_name",
            resource_attributes={"dataset_name": dataset_name},
        )

    @staticmethod
    def from_eval_set(eval_set_id: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from eval set data"""
        return CedarEntity(
            resource_type=ResourceType.EVAL_SET,
            resource_key="eval_set_id",
            resource_attributes={"eval_set_id": eval_set_id},
        )

    @staticmethod
    def from_eval_suite(suite_id: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from eval suite data"""
        return CedarEntity(
            resource_type=ResourceType.EVAL_SUITE,
            resource_key="suite_id",
            resource_attributes={"suite_id": suite_id},
        )

    @staticmethod
    def from_user(user_id: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from user data"""
        return CedarEntity(
            resource_type=ResourceType.USER,
            resource_key="user_id",
            resource_attributes={"user_id": user_id},
        )

    @staticmethod
    def from_group(group_id: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from group data"""
        return CedarEntity(
            resource_type=ResourceType.GROUP,
            resource_key="group_id",
            resource_attributes={"group_id": group_id},
        )

    @staticmethod
    def from_dir_sync(dir_sync_id: str | None) -> "CedarEntity":
        """Create a CedarEntity instance from dir sync data"""
        return CedarEntity(
            resource_type=ResourceType.DIR_SYNC,
            resource_key="dir_sync_id",
            resource_attributes={"dir_sync_id": dir_sync_id},
        )

    @staticmethod
    def from_human_task(resource: HumanTaskResource) -> "CedarEntity":
        """Create a CedarEntity instance from human task data"""
        return CedarEntity(
            resource_type=ResourceType.HUMAN_TASK,
            resource_key="human_task_id",
            resource_attributes=_filter_nones(asdict(resource)),
        )


class PolicyService:
    """Service for managing and evaluating Authorization policies."""

    def __init__(self, policy_file_path: str | None = None) -> None:
        """Initialize the Cedar policy service.

        Args:
            policy_file_path: Path to the Cedar policy file. If not provided,
                            will look for 'policies.cedar' in the current directory.
        """
        self.policy_file_path = (
            policy_file_path or "planar/security/default_policies.cedar"
        )
        self.policies = self._load_policies()

    def _load_policies(self) -> str:
        """Load Cedar policies from the specified file."""
        try:
            policy = Path(self.policy_file_path).read_text()
            formatted_policy = format_policies(policy)
            return formatted_policy
        except FileNotFoundError:
            raise FileNotFoundError(f"Policy file not found: {self.policy_file_path}")

    def _get_relevant_role_entities(
        self, principal_entity: EntityDict
    ) -> list[EntityDict]:
        member_role_entity_id: EntityIdentifier = {
            "type": "Role",
            "id": "member",
        }

        member_role_entity: EntityDict = {
            "uid": {
                "__entity": member_role_entity_id,
            },
            "attrs": {},
            "parents": [],
        }

        admin_role_entity_id: EntityIdentifier = {
            "type": "Role",
            "id": "admin",
        }

        admin_role_entity: EntityDict = {
            "uid": {"__entity": admin_role_entity_id},
            "attrs": {},
            "parents": [member_role_entity_id],
        }

        for parent in principal_entity["parents"]:
            if parent["type"] == "Role" and parent["id"] == "admin":
                return [admin_role_entity, member_role_entity]
            elif parent["type"] == "Role" and parent["id"] == "member":
                return [member_role_entity]

        return []

    def is_allowed(
        self,
        principal: CedarEntity,
        action: str
        | WorkflowAction
        | AgentAction
        | RuleAction
        | DatasetAction
        | EvalAction
        | UserAction
        | GroupAction
        | DirSyncAction
        | HumanTaskAction,
        resource: CedarEntity,
    ) -> bool:
        """Check if the principal is permitted to perform the action on the resource.

        Args:
            principal: Dictionary containing principal data with all required fields
            action: The action to perform (e.g., "Workflow::Run")
            resource_type: Type of the resource (e.g., "Workflow", "DomainModel")
            resource_data: Dictionary containing resource data with all required fields

        Returns:
            bool: True if the action is permitted, False otherwise
        """
        # Create principal and resource entities
        principal_entity = principal.to_dict()
        resource_entity = resource.to_dict()

        if (
            isinstance(action, WorkflowAction)
            or isinstance(action, AgentAction)
            or isinstance(action, RuleAction)
            or isinstance(action, DatasetAction)
            or isinstance(action, EvalAction)
            or isinstance(action, UserAction)
            or isinstance(action, GroupAction)
            or isinstance(action, DirSyncAction)
            or isinstance(action, HumanTaskAction)
        ):
            action = f'Action::"{action.value}"'
        else:
            action = f'Action::"{action}"'

        # Create request with principal and resource entities
        request = {
            "principal": f'Principal::"{principal.id}"',
            "action": f"{action}",
            "resource": f'{resource.resource_type.value}::"{resource.id}"',
        }

        # Add entities for this request
        entities = [
            principal_entity,
            resource_entity,
            *self._get_relevant_role_entities(principal_entity),
        ]

        # Log the authorization request
        auth_request_uuid = str(uuid.uuid4())

        logger.info(
            "authorization request",
            uuid=auth_request_uuid,
            principal=principal.id,
            action=action,
            resource=resource.id,
        )

        authz_result = is_authorized(request, self.policies, cast(list[dict], entities))

        match authz_result:
            case AuthzResult(decision=Decision.Allow):
                logger.info("authorization decision: allow", uuid=auth_request_uuid)
                return True
            case _:
                logger.warning(
                    "authorization decision: deny",
                    uuid=auth_request_uuid,
                    reasons=authz_result.diagnostics.reasons,
                    errors=authz_result.diagnostics.errors,
                )
                return False

    def reload_policies(self) -> None:
        """Reload policies from the policy file."""
        self.policies = self._load_policies()


def validate_authorization_for(
    resource_descriptor: ResourceDescriptor,
    action: WorkflowAction
    | AgentAction
    | RuleAction
    | DatasetAction
    | EvalAction
    | UserAction
    | GroupAction
    | DirSyncAction
    | HumanTaskAction,
):
    authz_service = get_policy_service()

    if not authz_service:
        logger.warning("No authorization service configured, skipping authorization")
        return

    entity: CedarEntity | None = None

    match action:
        case WorkflowAction() if isinstance(resource_descriptor, WorkflowResource):
            entity = CedarEntity.from_workflow(resource_descriptor.function_name)
        case AgentAction() if isinstance(resource_descriptor, AgentResource):
            entity = CedarEntity.from_agent(resource_descriptor.id)
        case RuleAction() if isinstance(resource_descriptor, RuleResource):
            entity = CedarEntity.from_rule(resource_descriptor.rule_name)
        case DatasetAction() if isinstance(resource_descriptor, DatasetResource):
            entity = CedarEntity.from_dataset(resource_descriptor.dataset_name)
        case EvalAction() if isinstance(resource_descriptor, EvalSetResource):
            entity = CedarEntity.from_eval_set(resource_descriptor.eval_set_id)
        case EvalAction() if isinstance(resource_descriptor, EvalSuiteResource):
            entity = CedarEntity.from_eval_suite(resource_descriptor.suite_id)
        case UserAction() if isinstance(resource_descriptor, UserResource):
            entity = CedarEntity.from_user(resource_descriptor.user_id)
        case GroupAction() if isinstance(resource_descriptor, GroupResource):
            entity = CedarEntity.from_group(resource_descriptor.group_id)
        case DirSyncAction() if isinstance(resource_descriptor, DirSyncResource):
            entity = CedarEntity.from_dir_sync(resource_descriptor.dir_sync_id)
        case HumanTaskAction() if isinstance(resource_descriptor, HumanTaskResource):
            entity = CedarEntity.from_human_task(resource_descriptor)
        case _:
            raise ValueError(
                f"Invalid resource descriptor {type(resource_descriptor).__name__} for action {action}"
            )

    # Get current principal and check authorization on current resource
    principal: Principal | None = get_current_principal()
    if not principal:
        raise HTTPException(status_code=401, detail="Not authenticated")
    if not authz_service.is_allowed(
        CedarEntity.from_principal(principal),
        action,
        entity,
    ):
        raise HTTPException(
            status_code=403, detail="Not authorized to perform this action"
        )
