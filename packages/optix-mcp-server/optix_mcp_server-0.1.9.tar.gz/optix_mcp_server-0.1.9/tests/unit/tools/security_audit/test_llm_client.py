"""Unit tests for LLM client abstraction."""

import pytest

from config.llm import LLMProviderConfig
from tools.security_audit.llm_client import (
    MockLLMClient,
    OpenAILLMClient,
    create_llm_client,
)


class TestLLMProviderConfig:
    """Tests for LLMProviderConfig (T061)."""

    def test_valid_openai_config(self):
        """Should accept valid OpenAI config."""
        config = LLMProviderConfig(provider="openai", api_key="sk-test123")
        assert config.provider == "openai"
        assert config.api_key == "sk-test123"

    def test_invalid_provider_raises_error(self):
        """Should reject invalid provider."""
        with pytest.raises(ValueError, match="Invalid provider"):
            LLMProviderConfig(provider="invalid", api_key="test")

    def test_empty_api_key_raises_error(self):
        """Should reject empty API key."""
        with pytest.raises(ValueError, match="API key must not be empty"):
            LLMProviderConfig(provider="openai", api_key="")

    def test_default_model_for_openai(self):
        """Should return default model for OpenAI."""
        config = LLMProviderConfig(provider="openai", api_key="test")
        assert config.default_model == "gpt-4o"

    def test_custom_model_override(self):
        """Should allow custom model override."""
        config = LLMProviderConfig(
            provider="openai", api_key="test", model="gpt-4-turbo"
        )
        assert config.default_model == "gpt-4-turbo"


class TestCreateLLMClient:
    """Tests for LLM client factory (T062)."""

    def test_creates_openai_client(self):
        """Should create OpenAI client for openai provider."""
        config = LLMProviderConfig(provider="openai", api_key="test")
        client = create_llm_client(config)
        assert isinstance(client, OpenAILLMClient)

    def test_returns_none_for_none_config(self):
        """Should return None when config is None."""
        client = create_llm_client(None)
        assert client is None


class TestMockLLMClient:
    """Tests for MockLLMClient (T063-T064)."""

    @pytest.fixture
    def mock_client(self):
        """Create mock client for testing."""
        config = LLMProviderConfig(provider="openai", api_key="test")
        return MockLLMClient(config)

    @pytest.fixture
    def sample_context(self):
        """Create sample analysis context."""
        return {
            "task": "validate_and_remediate",
            "summary": {"total_vulnerabilities": 2},
            "critical_findings": [
                {
                    "severity": "critical",
                    "category": "SQL Injection",
                    "description": "Direct query concatenation",
                }
            ],
            "high_findings": [
                {
                    "severity": "high",
                    "category": "Weak Auth",
                    "description": "No MFA",
                }
            ],
            "files_examined": ["app.py", "auth.py"],
            "confidence": "high",
        }

    @pytest.mark.asyncio
    async def test_mock_returns_validated_findings(self, mock_client, sample_context):
        """Mock should return validated findings."""
        result = await mock_client.analyze(sample_context)
        assert "validated_findings" in result
        assert len(result["validated_findings"]) == 2

    @pytest.mark.asyncio
    async def test_mock_returns_remediation_plan(self, mock_client, sample_context):
        """Mock should return remediation plan."""
        result = await mock_client.analyze(sample_context)
        assert "remediation_plan" in result
        assert len(result["remediation_plan"]) > 0

    @pytest.mark.asyncio
    async def test_mock_returns_overall_assessment(self, mock_client, sample_context):
        """Mock should return overall assessment."""
        result = await mock_client.analyze(sample_context)
        assert "overall_assessment" in result
        assert len(result["overall_assessment"]) > 0


class TestPromptBuilding:
    """Tests for prompt building (T065-T066)."""

    @pytest.fixture
    def client(self):
        """Create client for testing."""
        config = LLMProviderConfig(provider="openai", api_key="test")
        return MockLLMClient(config)

    def test_system_prompt_contains_security_context(self, client):
        """System prompt should mention security analysis."""
        prompt = client._build_system_prompt()
        assert "security" in prompt.lower()

    def test_system_prompt_requests_validation(self, client):
        """System prompt should request validation."""
        prompt = client._build_system_prompt()
        assert "validate" in prompt.lower() or "severity" in prompt.lower()

    def test_system_prompt_requests_remediation(self, client):
        """System prompt should request remediation."""
        prompt = client._build_system_prompt()
        assert "remediation" in prompt.lower()

    def test_user_prompt_includes_findings(self, client):
        """User prompt should include findings from context."""
        context = {
            "summary": {"total_vulnerabilities": 1},
            "critical_findings": [
                {"category": "XSS", "description": "Reflected XSS in search"}
            ],
            "high_findings": [],
            "files_examined": ["search.py"],
        }
        prompt = client._build_user_prompt(context)
        assert "XSS" in prompt

    def test_user_prompt_includes_file_count(self, client):
        """User prompt should mention files examined."""
        context = {
            "summary": {"total_vulnerabilities": 0},
            "critical_findings": [],
            "high_findings": [],
            "files_examined": ["a.py", "b.py", "c.py"],
        }
        prompt = client._build_user_prompt(context)
        assert "3" in prompt


class TestClientFallback:
    """Tests for client fallback behavior (T067-T069)."""

    def test_openai_has_fallback(self):
        """OpenAI client should have fallback method."""
        config = LLMProviderConfig(provider="openai", api_key="test")
        client = OpenAILLMClient(config)
        context = {"critical_findings": [], "high_findings": []}
        result = client._fallback_response(context)
        assert "overall_assessment" in result

    def test_fallback_includes_original_findings(self):
        """Fallback should include original findings."""
        config = LLMProviderConfig(provider="openai", api_key="test")
        client = OpenAILLMClient(config)
        context = {
            "critical_findings": [{"category": "Test"}],
            "high_findings": [],
        }
        result = client._fallback_response(context)
        assert len(result["validated_findings"]) == 1
