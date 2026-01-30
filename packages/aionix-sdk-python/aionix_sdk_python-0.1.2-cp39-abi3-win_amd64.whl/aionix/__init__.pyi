"""Type stubs for aionix Python SDK."""

from typing import Optional, Any, Dict, List, Awaitable

__version__: str

def connect(
    api_base: Optional[str] = None,
    tenant: Optional[str] = None,
    auth_token: Optional[str] = None,
    api_key: Optional[str] = None,
    profile: Optional[str] = None,
) -> Client: ...

def connect_sync(
    api_base: Optional[str] = None,
    tenant: Optional[str] = None,
    auth_token: Optional[str] = None,
    api_key: Optional[str] = None,
    profile: Optional[str] = None,
) -> Client: ...

class AionixError(Exception): ...
class NotFoundError(AionixError): ...
class ValidationError(AionixError): ...
class AuthenticationError(AionixError): ...
class AuthorizationError(AionixError): ...
class ConflictError(AionixError): ...
class RateLimitError(AionixError): ...
class TimeoutError(AionixError): ...
class UnavailableError(AionixError): ...
class TransientError(AionixError): ...
class ExecutionFailedError(AionixError): ...
class PaymentRequiredError(AionixError): ...
class ConfigurationError(AionixError): ...
class InternalError(AionixError): ...
class CancelledError(AionixError): ...

class Action:
    @staticmethod
    def parse(action: str) -> "Action": ...
    @property
    def canonical(self) -> str: ...
    @property
    def op(self) -> str: ...
    @property
    def trn(self) -> str: ...

class Client:
    @staticmethod
    def from_env() -> "Client": ...
    @staticmethod
    def from_profile(profile: str) -> "Client": ...
    @property
    def tenant(self) -> str: ...
    @property
    def aionixfn(self) -> AionixFnClient: ...
    @property
    def agent(self) -> AgentClient: ...
    @property
    def credvault(self) -> CredVaultClient: ...
    @property
    def paramstore(self) -> ParamStoreClient: ...
    @property
    def stepflow(self) -> StepflowClient: ...
    @property
    def igniter(self) -> IgniterClient: ...
    @property
    def openact(self) -> OpenActClient: ...
    @property
    def auth(self) -> AuthClient: ...
    @property
    def org(self) -> OrgClient: ...
    @property
    def discovery(self) -> DiscoveryClient: ...

    def run(
        self,
        action: Action,
        input: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def execute(
        self,
        action: Action,
        input: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def invoke(
        self,
        action: Action,
        input: Optional[Dict[str, Any]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

class AionixFnClient:
    def upsert_function(
        self,
        tenant: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_function(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_functions(
        self,
        tenant: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_function(
        self,
        trn: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_function(self, trn: str) -> Awaitable[None]: ...

    def register_version(
        self,
        trn: str,
        req: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_version(
        self,
        trn: str,
        version_id: str,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_versions(
        self,
        trn: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_version(
        self,
        trn: str,
        version_id: str,
        req: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_version(
        self,
        trn: str,
        version_id: str,
    ) -> Awaitable[Dict[str, Any]]: ...

    def point_alias(
        self,
        function_trn: str,
        alias_name: str,
        version_id: str,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_alias(
        self,
        function_trn: str,
        alias_name: str,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_aliases(
        self,
        function_trn: str,
        limit: int,
        offset: int,
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_alias(
        self,
        function_trn: str,
        alias_name: str,
    ) -> Awaitable[Dict[str, Any]]: ...

    def get_invocation_status(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_invocations(
        self,
        trn: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_logs(
        self,
        trn: str,
        invocation_id: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_metrics(
        self,
        trn: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def health_check(self) -> Awaitable[None]: ...
    def activate_version(
        self,
        trn: str,
        version_id: str,
    ) -> Awaitable[Dict[str, Any]]: ...
    def rollback(
        self,
        trn: str,
        target_version: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def configure_traffic(
        self,
        trn: str,
        alias_name: str,
        entries: List[Dict[str, Any]],
    ) -> Awaitable[Dict[str, Any]]: ...
    def set_routing_policy(
        self,
        trn: str,
        alias_name: str,
        policy: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...

    def invoke(
        self,
        trn: str,
        input: Optional[Any] = None,
        mode: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def invoke_version(
        self,
        trn: str,
        version_id: str,
        input: Optional[Any] = None,
        mode: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def invoke_alias(
        self,
        trn: str,
        alias_name: str,
        input: Optional[Any] = None,
        mode: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def cancel_invocation(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def warm_function(
        self,
        trn: str,
        warm_venv: bool = True,
        warm_artifacts: bool = True,
        warm_runtime: bool = True,
    ) -> Awaitable[Dict[str, Any]]: ...
    def warm_version(
        self,
        trn: str,
        version_id: str,
        warm_venv: bool = True,
        warm_artifacts: bool = True,
        warm_runtime: bool = True,
    ) -> Awaitable[Dict[str, Any]]: ...
    def clear_warm_cache(self, tenant: Optional[str] = None) -> Awaitable[Dict[str, Any]]: ...

    def create_layer(
        self,
        req: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_layer(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_layers(
        self,
        tenant: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_layer(
        self,
        trn: str,
        req: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_layer(self, trn: str) -> Awaitable[None]: ...
    def publish_layer_version(
        self,
        req: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_layer_version(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_layer_versions(
        self,
        layer_trn: str,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_layer_version(self, trn: str) -> Awaitable[None]: ...
    def find_or_create_layer_version(
        self,
        req: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def check_artifacts(
        self,
        hashes: List[str],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def upload_artifact(
        self,
        content: bytes,
        content_type: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_artifact_meta(
        self,
        hash: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def download_artifact(
        self,
        hash: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[bytes]: ...

    def get_warm_stats(self, tenant: Optional[str] = None) -> Awaitable[Dict[str, Any]]: ...

class AgentClient:
    def chat_completions(
        self,
        request: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

class CredVaultClient:
    def upsert_credential(
        self,
        resource: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_credential(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def get_by_name(
        self,
        name: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_credentials(
        self,
        tenant: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        enabled: Optional[bool] = None,
        search: Optional[str] = None,
        path_prefix: Optional[str] = None,
        oauth_provider: Optional[str] = None,
        oauth_status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_credential(
        self,
        trn: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_credential(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def delete_by_name(
        self,
        name: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[None]: ...
    def list_versions(
        self,
        trn: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Awaitable[Dict[str, Any]]: ...

    def upsert_provider(
        self,
        resource: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_provider(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_providers(
        self,
        tenant: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
        search: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_provider(
        self,
        trn: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_provider(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_accounts(
        self,
        tenant: Optional[str] = None,
        provider_name: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Awaitable[Dict[str, Any]]: ...

    def list_credential_audit(
        self,
        trn: str,
        event_type: Optional[str] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_admin_audit(
        self,
        event_type: Optional[str] = None,
        from_time: Optional[str] = None,
        to_time: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def reveal_credential(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def reveal_version(
        self,
        trn: str,
        version: int,
    ) -> Awaitable[Dict[str, Any]]: ...
    def rotate_credential(
        self,
        trn: str,
        req: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def activate_version(
        self,
        trn: str,
        version: int,
    ) -> Awaitable[Dict[str, Any]]: ...
    def retire_version(
        self,
        trn: str,
        version: int,
    ) -> Awaitable[Dict[str, Any]]: ...
    def oauth_authorize(
        self,
        req: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def oauth_callback(
        self,
        state: str,
        code: Optional[str] = None,
        error: Optional[str] = None,
        error_description: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def oauth_refresh_token(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def oauth_revoke_account(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def get_key_status(self) -> Awaitable[Dict[str, Any]]: ...
    def start_key_rotation(
        self,
        req: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_rotation_progress(self) -> Awaitable[Dict[str, Any]]: ...
    def device_code_request(
        self,
        req: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def device_token_poll(
        self,
        req: Dict[str, Any],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

class ParamStoreClient:
    def list_parameters(
        self,
        tenant: Optional[str] = None,
        path: Optional[str] = None,
        recursive: Optional[bool] = None,
        kind: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_parameter(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def get_by_name(
        self,
        name: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def upsert_parameter(
        self,
        trn: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_parameter(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def delete_by_name(
        self,
        name: str,
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_versions(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def get_version(
        self,
        trn: str,
        version: int,
    ) -> Awaitable[Dict[str, Any]]: ...

    def evaluate(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def batch_evaluate(
        self,
        paths: List[str],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def batch_set(
        self,
        parameters: List[Dict[str, Any]],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def batch_delete(
        self,
        paths: List[str],
        tenant: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

class StepflowClient:
    def upsert_workflow(
        self,
        tenant: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_workflow(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def delete_workflow(
        self,
        trn: str,
        force: bool = False,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_workflows(
        self,
        tenant: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Awaitable[Dict[str, Any]]: ...

    def get_execution(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_executions(
        self,
        tenant: Optional[str] = None,
        workflow_trn: Optional[str] = None,
        status: Optional[str] = None,
        q: Optional[str] = None,
        sort: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_workflow_details(
        self,
        trn: str,
        include_steps: bool = False,
        include_events: bool = False,
        include_tasks: bool = False,
    ) -> Awaitable[Dict[str, Any]]: ...

    def start_workflow(
        self,
        workflow_trn: str,
        input: Optional[Dict[str, Any]] = None,
        run_id: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def cancel_execution(
        self,
        trn: str,
        reason: Optional[str] = None,
    ) -> Awaitable[None]: ...
    def submit_execution_event(
        self,
        event: Dict[str, Any],
    ) -> Awaitable[None]: ...

    def dsl_validate(self, dsl: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...
    def dsl_lint(self, dsl: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...
    def dsl_normalize(self, dsl: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...
    def dsl_simulate(
        self,
        dsl: Dict[str, Any],
        input: Dict[str, Any],
        max_steps: Optional[int] = None,
        timeout_ms: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def preview_step_mapping(
        self,
        request: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...

    def get_step(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_steps(
        self,
        execution_trn: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Awaitable[Dict[str, Any]]: ...

    def get_activity_task(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_activity_tasks_by_run(
        self,
        execution_trn: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Awaitable[Dict[str, Any]]: ...
    def list_activity_tasks_by_status(
        self,
        status: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Awaitable[Dict[str, Any]]: ...
    def enqueue_task(
        self,
        request: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...

    def get_event(self, id: int) -> Awaitable[Dict[str, Any]]: ...
    def list_events(
        self,
        execution_trn: str,
        limit: int = 20,
        offset: int = 0,
        scope: Optional[str] = None,
        types: Optional[List[str]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def schedule_timer(self, request: Dict[str, Any]) -> Awaitable[None]: ...
    def cancel_timer(self, trn: str) -> Awaitable[None]: ...
    def reschedule_timer(
        self,
        trn: str,
        new_fire_at_ms: int,
    ) -> Awaitable[None]: ...

    def test_step(self, request: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...

class IgniterClient:
    def upsert_trigger(
        self,
        tenant: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_trigger(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_triggers(
        self,
        tenant: Optional[str] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        enabled: Optional[bool] = None,
        name: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_trigger(
        self,
        trn: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_trigger(self, trn: str) -> Awaitable[Dict[str, Any]]: ...

    def get_execution(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_executions(
        self,
        tenant: Optional[str] = None,
        trigger_trn: Optional[str] = None,
        status: Optional[str] = None,
        target_trn: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def get_dlq_entry(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_dlq_entries(
        self,
        tenant: Optional[str] = None,
        trigger_trn: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def enable_trigger(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def disable_trigger(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def execute_trigger(
        self,
        trn: str,
        request: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def validate_trigger(
        self,
        tenant: str,
        request: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_trigger_health(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def get_trigger_statistics(self, trn: str) -> Awaitable[Dict[str, Any]]: ...

    def retry_dlq_entry(
        self,
        trn: str,
        request: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def batch_retry_dlq(
        self,
        tenant: str,
        request: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_dlq_entry(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def purge_dlq(
        self,
        tenant: str,
        request: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...

class OpenActClient:
    def upsert_resource(
        self,
        tenant: str,
        resource: Dict[str, Any],
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_resource(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_resources(
        self,
        tenant: Optional[str] = None,
        kind: Optional[str] = None,
        search: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def delete_resource(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def get_resource_schema(self, trn: str) -> Awaitable[Dict[str, Any]]: ...

    def get_execution(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def list_executions(
        self,
        tenant: Optional[str] = None,
        action_trn: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...

    def list_connectors(
        self,
        tenant: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def get_connector(self, kind: str) -> Awaitable[Dict[str, Any]]: ...

    def execute_action(
        self,
        trn: str,
        request: Optional[Dict[str, Any]] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def test_connection(self, trn: str) -> Awaitable[Dict[str, Any]]: ...
    def cancel_execution(self, trn: str) -> Awaitable[Dict[str, Any]]: ...

class AuthClient:
    def create_api_key(self, request: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...
    def list_api_keys(self) -> Awaitable[List[Dict[str, Any]]]: ...
    def delete_api_key(self, key_id: str) -> Awaitable[Dict[str, Any]]: ...
    def enable_api_key(self, key_id: str) -> Awaitable[Dict[str, Any]]: ...
    def disable_api_key(self, key_id: str) -> Awaitable[Dict[str, Any]]: ...

    def list_roles(self) -> Awaitable[List[Dict[str, Any]]]: ...
    def list_policies(self) -> Awaitable[List[Dict[str, Any]]]: ...
    def create_policy(self, policy: Dict[str, Any]) -> Awaitable[Dict[str, Any]]: ...
    def delete_policy(self, policy_id: str) -> Awaitable[Dict[str, Any]]: ...

    def create_user_key(
        self,
        name: str,
        user_id: str,
        description: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def create_agent_key(
        self,
        name: str,
        agent_id: str,
        description: Optional[str] = None,
    ) -> Awaitable[Dict[str, Any]]: ...
    def create_allow_policy(
        self,
        id: str,
        principal_pattern: str,
        operations: List[str],
        targets: List[str],
    ) -> Awaitable[Dict[str, Any]]: ...
    def create_deny_policy(
        self,
        id: str,
        principal_pattern: str,
        operations: List[str],
        targets: List[str],
    ) -> Awaitable[Dict[str, Any]]: ...

    def me(self) -> Awaitable[Dict[str, Any]]: ...
    def list_sso_providers(self) -> Awaitable[Dict[str, Any]]: ...
    def oidc_login_url(
        self,
        provider: Optional[str] = None,
        redirect: Optional[str] = None,
    ) -> str: ...
    def oidc_callback(
        self,
        code: str,
        state: str,
    ) -> Awaitable[Dict[str, Any]]: ...

class OrgClient:
    def list_tenants(self) -> Awaitable[List[Dict[str, Any]]]: ...
    def list_members(
        self,
        tenant: Optional[str] = None,
    ) -> Awaitable[List[Dict[str, Any]]]: ...
    def add_member(
        self,
        tenant: Optional[str],
        user_id: str,
        role: str,
    ) -> Awaitable[Dict[str, Any]]: ...
    def update_member_role(
        self,
        tenant: Optional[str],
        user_id: str,
        role: str,
    ) -> Awaitable[Dict[str, Any]]: ...
    def remove_member(
        self,
        tenant: Optional[str],
        user_id: str,
    ) -> Awaitable[Dict[str, Any]]: ...

class DiscoveryClient:
    def list(
        self,
        include_internal: Optional[bool] = None,
    ) -> Awaitable[List[Dict[str, Any]]]: ...

    def find(
        self,
        action: Action,
    ) -> Awaitable[Optional[Dict[str, Any]]]: ...
