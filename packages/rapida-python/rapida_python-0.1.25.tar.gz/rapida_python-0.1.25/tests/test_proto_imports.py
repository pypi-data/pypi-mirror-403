"""
Test module to validate protobuf imports.

This test ensures all imports from generated protobuf files are valid.
When proto files are regenerated and classes change, these tests will fail
and show exactly which imports need to be updated.

Run with: pytest tests/test_proto_imports.py -v
"""
import pytest
import importlib
from typing import List, Tuple


class TestCommonPb2Imports:
    """Test imports from common_pb2 module."""
    
    MODULE = "rapida.clients.protos.common_pb2"
    
    EXPECTED_IMPORTS = [
        "FieldSelector",
        "Criteria",
        "Error",
        "Paginate",
        "Paginated",
        "Ordering",
        "User",
        "BaseResponse",
        "Metadata",
        "Argument",
        "Variable",
        "Tag",
        "Organization",
        "Metric",
        "Message",
        "ToolCall",
        "FunctionCall",
        "Knowledge",
        "TextPrompt",
        "TextChatCompletePrompt",
        "AssistantConversationMessage",
        "AssistantConversationContext",
        "AssistantConversation",
        "GetAllAssistantConversationRequest",
        "GetAllAssistantConversationResponse",
        "GetAllConversationMessageRequest",
        "GetAllConversationMessageResponse",
        "AssistantDefinition",
        "Source",  # Enum
    ]
    
    @pytest.fixture
    def module(self):
        """Load the protobuf module."""
        return importlib.import_module(self.MODULE)
    
    def test_module_loads(self, module):
        """Test that the module can be imported."""
        assert module is not None
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        """Test that each expected class can be imported from the module."""
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"The proto file may have changed. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )
    
    def test_list_available_exports(self, module):
        """Helper test to show all available exports from the module."""
        exports = [name for name in dir(module) if not name.startswith('_')]
        print(f"\nAvailable exports in {self.MODULE}:")
        for export in sorted(exports):
            print(f"  - {export}")


class TestAssistantKnowledgePb2Imports:
    """Test imports from assistant_knowledge_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_knowledge_pb2"
    
    EXPECTED_IMPORTS = [
        "AssistantKnowledge",
        "CreateAssistantKnowledgeRequest",
        "UpdateAssistantKnowledgeRequest",
        "GetAssistantKnowledgeRequest",
        "DeleteAssistantKnowledgeRequest",
        "GetAssistantKnowledgeResponse",
        "GetAllAssistantKnowledgeRequest",
        "GetAllAssistantKnowledgeResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestVaultApiPb2Imports:
    """Test imports from vault_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.vault_api_pb2"
    
    EXPECTED_IMPORTS = [
        "VaultCredential",
        "CreateProviderCredentialRequest",
        "DeleteCredentialRequest",
        "GetAllOrganizationCredentialResponse",
        "GetCredentialResponse",
        "GetAllOrganizationCredentialRequest",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestTalkApiPb2Imports:
    """Test imports from talk_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.talk_api_pb2"
    
    EXPECTED_IMPORTS = [
        "CreateMessageMetricRequest",
        "CreateMessageMetricResponse",
        "CreateConversationMetricRequest",
        "CreateConversationMetricResponse",
        "CreateBulkPhoneCallRequest",
        "CreateBulkPhoneCallResponse",
        "CreatePhoneCallRequest",
        "CreatePhoneCallResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestAssistantAnalysisPb2Imports:
    """Test imports from assistant_analysis_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_analysis_pb2"
    
    EXPECTED_IMPORTS = [
        "AssistantAnalysis",
        "CreateAssistantAnalysisRequest",
        "UpdateAssistantAnalysisRequest",
        "GetAssistantAnalysisRequest",
        "DeleteAssistantAnalysisRequest",
        "GetAssistantAnalysisResponse",
        "GetAllAssistantAnalysisRequest",
        "GetAllAssistantAnalysisResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestInvokerApiPb2Imports:
    """Test imports from invoker_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.invoker_api_pb2"
    
    EXPECTED_IMPORTS = [
        "EndpointDefinition",
        "InvokeRequest",
        "InvokeResponse",
        "UpdateRequest",
        "UpdateResponse",
        "ProbeRequest",
        "ProbeResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestWebApiPb2Imports:
    """Test imports from web_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.web_api_pb2"
    
    EXPECTED_IMPORTS = [
        "AuthenticateRequest",
        "RegisterUserRequest",
        "Token",
        "OrganizationRole",
        "ProjectRole",
        "FeaturePermission",
        "Authentication",
        "ScopedAuthentication",
        "AuthenticateResponse",
        "ForgotPasswordRequest",
        "ForgotPasswordResponse",
        "CreatePasswordRequest",
        "CreatePasswordResponse",
        "VerifyTokenRequest",
        "VerifyTokenResponse",
        "AuthorizeRequest",
        "ScopeAuthorizeRequest",
        "ScopedAuthenticationResponse",
        "GetUserRequest",
        "GetUserResponse",
        "UpdateUserRequest",
        "UpdateUserResponse",
        "SocialAuthenticationRequest",
        "GetAllUserRequest",
        "GetAllUserResponse",
        "CreateOrganizationRequest",
        "UpdateOrganizationRequest",
        "GetOrganizationRequest",
        "GetOrganizationResponse",
        "CreateOrganizationResponse",
        "UpdateOrganizationResponse",
        "UpdateBillingInformationRequest",
        "Project",
        "CreateProjectRequest",
        "CreateProjectResponse",
        "UpdateProjectRequest",
        "UpdateProjectResponse",
        "GetProjectRequest",
        "GetProjectResponse",
        "GetAllProjectRequest",
        "GetAllProjectResponse",
        "AddUsersToProjectRequest",
        "ArchiveProjectRequest",
        "ArchiveProjectResponse",
        "AddUsersToProjectResponse",
        "ProjectCredential",
        "CreateProjectCredentialRequest",
        "GetAllProjectCredentialRequest",
        "CreateProjectCredentialResponse",
        "GetAllProjectCredentialResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestAssistantWebhookPb2Imports:
    """Test imports from assistant_webhook_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_webhook_pb2"
    
    EXPECTED_IMPORTS = [
        "AssistantWebhook",
        "AssistantWebhookLog",
        "CreateAssistantWebhookRequest",
        "UpdateAssistantWebhookRequest",
        "GetAssistantWebhookRequest",
        "DeleteAssistantWebhookRequest",
        "GetAssistantWebhookResponse",
        "GetAllAssistantWebhookRequest",
        "GetAllAssistantWebhookResponse",
        "GetAllAssistantWebhookLogRequest",
        "GetAssistantWebhookLogRequest",
        "GetAssistantWebhookLogResponse",
        "GetAllAssistantWebhookLogResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestConnectApiPb2Imports:
    """Test imports from connect_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.connect_api_pb2"
    
    EXPECTED_IMPORTS = [
        "GeneralConnectRequest",
        "GeneralConnectResponse",
        "GetConnectorFilesRequest",
        "GetConnectorFilesResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestEndpointApiPb2Imports:
    """Test imports from endpoint_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.endpoint_api_pb2"
    
    EXPECTED_IMPORTS = [
        "EndpointAttribute",
        "EndpointProviderModelAttribute",
        "CreateEndpointRequest",
        "CreateEndpointResponse",
        "EndpointProviderModel",
        "AggregatedEndpointAnalytics",
        "Endpoint",
        "CreateEndpointProviderModelRequest",
        "CreateEndpointProviderModelResponse",
        "GetEndpointRequest",
        "GetEndpointResponse",
        "GetAllEndpointRequest",
        "GetAllEndpointResponse",
        "GetAllEndpointProviderModelRequest",
        "GetAllEndpointProviderModelResponse",
        "UpdateEndpointVersionRequest",
        "UpdateEndpointVersionResponse",
        "EndpointRetryConfiguration",
        "EndpointCacheConfiguration",
        "CreateEndpointRetryConfigurationRequest",
        "CreateEndpointRetryConfigurationResponse",
        "CreateEndpointCacheConfigurationRequest",
        "CreateEndpointCacheConfigurationResponse",
        "CreateEndpointTagRequest",
        "ForkEndpointRequest",
        "UpdateEndpointDetailRequest",
        "EndpointLog",
        "GetAllEndpointLogRequest",
        "GetAllEndpointLogResponse",
        "GetEndpointLogRequest",
        "GetEndpointLogResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestAssistantToolPb2Imports:
    """Test imports from assistant_tool_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_tool_pb2"
    
    EXPECTED_IMPORTS = [
        "AssistantTool",
        "CreateAssistantToolRequest",
        "UpdateAssistantToolRequest",
        "GetAssistantToolRequest",
        "DeleteAssistantToolRequest",
        "GetAssistantToolResponse",
        "GetAllAssistantToolRequest",
        "GetAllAssistantToolResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestIntegrationApiPb2Imports:
    """Test imports from integration_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.integration_api_pb2"
    
    EXPECTED_IMPORTS = [
        "Credential",
        "ToolDefinition",
        "FunctionDefinition",
        "FunctionParameter",
        "FunctionParameterProperty",
        "Embedding",
        "EmbeddingRequest",
        "EmbeddingResponse",
        "Reranking",
        "RerankingRequest",
        "RerankingResponse",
        "ChatResponse",
        "ChatRequest",
        "VerifyCredentialRequest",
        "VerifyCredentialResponse",
        "Moderation",
        "GetModerationRequest",
        "GetModerationResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestAssistantDeploymentPb2Imports:
    """Test imports from assistant_deployment_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_deployment_pb2"
    
    EXPECTED_IMPORTS = [
        "DeploymentAudioProvider",
        "AssistantWebpluginDeployment",
        "AssistantPhoneDeployment",
        "AssistantWhatsappDeployment",
        "AssistantDebuggerDeployment",
        "AssistantApiDeployment",
        "GetAssistantDeploymentRequest",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestKnowledgeApiPb2Imports:
    """Test imports from knowledge_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.knowledge_api_pb2"
    
    EXPECTED_IMPORTS = [
        "CreateKnowledgeRequest",
        "CreateKnowledgeResponse",
        "GetAllKnowledgeRequest",
        "GetAllKnowledgeResponse",
        "GetKnowledgeRequest",
        "GetKnowledgeResponse",
        "CreateKnowledgeTagRequest",
        "KnowledgeDocument",
        "GetAllKnowledgeDocumentRequest",
        "GetAllKnowledgeDocumentResponse",
        "CreateKnowledgeDocumentRequest",
        "CreateKnowledgeDocumentResponse",
        "KnowledgeDocumentSegment",
        "GetAllKnowledgeDocumentSegmentRequest",
        "GetAllKnowledgeDocumentSegmentResponse",
        "UpdateKnowledgeDetailRequest",
        "UpdateKnowledgeDocumentSegmentRequest",
        "DeleteKnowledgeDocumentSegmentRequest",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestAssistantApiPb2Imports:
    """Test imports from assistant_api_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_api_pb2"
    
    EXPECTED_IMPORTS = [
        "Assistant",
        "CreateAssistantRequest",
        "CreateAssistantTagRequest",
        "GetAssistantRequest",
        "DeleteAssistantRequest",
        "GetAssistantResponse",
        "GetAllAssistantRequest",
        "GetAllAssistantResponse",
        "GetAllAssistantMessageRequest",
        "GetAllAssistantMessageResponse",
        "GetAllMessageRequest",
        "GetAllMessageResponse",
        "UpdateAssistantDetailRequest",
        "GetAssistantConversationRequest",
        "GetAssistantConversationResponse",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


class TestAssistantProviderPb2Imports:
    """Test imports from assistant_provider_pb2 module."""
    
    MODULE = "rapida.clients.protos.assistant_provider_pb2"
    
    EXPECTED_IMPORTS = [
        "AssistantProviderModel",
    ]
    
    @pytest.fixture
    def module(self):
        return importlib.import_module(self.MODULE)
    
    @pytest.mark.parametrize("class_name", EXPECTED_IMPORTS)
    def test_import_exists(self, module, class_name):
        assert hasattr(module, class_name), (
            f"'{class_name}' not found in {self.MODULE}. "
            f"Available exports: {[name for name in dir(module) if not name.startswith('_')]}"
        )


# ============================================================================
# Utility functions to help discover available exports
# ============================================================================

def get_module_exports(module_path: str) -> List[str]:
    """
    Helper function to get all public exports from a module.
    
    Usage:
        exports = get_module_exports("rapida.clients.protos.common_pb2")
        print(exports)
    """
    try:
        module = importlib.import_module(module_path)
        return [name for name in dir(module) if not name.startswith('_')]
    except ImportError as e:
        return [f"ERROR: {e}"]


def validate_imports(module_path: str, expected_imports: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """
    Validate imports against a module and return valid, invalid, and extra exports.
    
    Returns:
        Tuple of (valid_imports, invalid_imports, extra_exports)
    """
    try:
        module = importlib.import_module(module_path)
        actual_exports = set(name for name in dir(module) if not name.startswith('_'))
        expected_set = set(expected_imports)
        
        valid = list(expected_set & actual_exports)
        invalid = list(expected_set - actual_exports)
        extra = list(actual_exports - expected_set)
        
        return sorted(valid), sorted(invalid), sorted(extra)
    except ImportError as e:
        return [], expected_imports, [f"ERROR: {e}"]


class TestRapidaPackageImport:
    """Test that the main rapida package can be imported without errors."""
    
    def test_rapida_import(self):
        """
        Test that 'import rapida' works without ImportError.
        
        If this test fails, it means there's a broken import in rapida/__init__.py
        """
        try:
            import rapida
            assert rapida is not None
        except ImportError as e:
            pytest.fail(
                f"Failed to import rapida package: {e}\n"
                f"This likely means a protobuf class is being imported that doesn't exist.\n"
                f"Check rapida/__init__.py and compare with the actual proto exports."
            )


# ============================================================================
# Summary test that reports all import issues at once
# ============================================================================

class TestProtoImportSummary:
    """Generate a summary report of all proto import issues."""
    
    PROTO_MODULES = {
        "rapida.clients.protos.common_pb2": TestCommonPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_knowledge_pb2": TestAssistantKnowledgePb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.vault_api_pb2": TestVaultApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.talk_api_pb2": TestTalkApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_analysis_pb2": TestAssistantAnalysisPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.invoker_api_pb2": TestInvokerApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.web_api_pb2": TestWebApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_webhook_pb2": TestAssistantWebhookPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.connect_api_pb2": TestConnectApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.endpoint_api_pb2": TestEndpointApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_tool_pb2": TestAssistantToolPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.integration_api_pb2": TestIntegrationApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_deployment_pb2": TestAssistantDeploymentPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.knowledge_api_pb2": TestKnowledgeApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_api_pb2": TestAssistantApiPb2Imports.EXPECTED_IMPORTS,
        "rapida.clients.protos.assistant_provider_pb2": TestAssistantProviderPb2Imports.EXPECTED_IMPORTS,
    }
    
    def test_generate_import_report(self):
        """
        Generate a comprehensive report of all import issues.
        
        This test always passes but prints a detailed report.
        """
        print("\n" + "=" * 80)
        print("PROTO IMPORT VALIDATION REPORT")
        print("=" * 80)
        
        all_issues = []
        
        for module_path, expected_imports in self.PROTO_MODULES.items():
            valid, invalid, extra = validate_imports(module_path, expected_imports)
            
            if invalid:
                all_issues.append((module_path, invalid))
                print(f"\n❌ {module_path}")
                print(f"   MISSING ({len(invalid)}): {invalid}")
                if extra:
                    print(f"   AVAILABLE ALTERNATIVES: {extra[:10]}{'...' if len(extra) > 10 else ''}")
            else:
                print(f"\n✅ {module_path} - All {len(valid)} imports valid")
        
        print("\n" + "=" * 80)
        
        if all_issues:
            print("\n⚠️  SUMMARY: Found import issues in the following modules:")
            for module_path, invalid in all_issues:
                print(f"   - {module_path}: {invalid}")
            print("\nTo fix: Update rapida/__init__.py to remove or replace these imports.")
        else:
            print("\n✅ SUMMARY: All proto imports are valid!")
        
        print("=" * 80)
