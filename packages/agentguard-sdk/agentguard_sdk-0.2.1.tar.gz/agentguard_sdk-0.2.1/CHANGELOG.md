# Changelog

All notable changes to the AgentGuard Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-01-30

### Added
- **Client-Side Guardrails** - Offline security protection without server dependency
  - `GuardrailEngine` for parallel/sequential guardrail execution
  - `PIIDetectionGuardrail` - Detect and redact PII (emails, phones, SSNs, credit cards)
  - `ContentModerationGuardrail` - Detect harmful content (hate, violence, harassment)
  - `PromptInjectionGuardrail` - Detect jailbreak and injection attempts
  - Configurable actions: block, allow, redact, mask, transform
  - Timeout protection and error handling with asyncio
  - Pydantic models for type safety
- Comprehensive test suite for guardrails (50 tests passing)
- Guardrails demo example with real-world scenarios
- Full async/await support for all guardrail operations

### Features
- **Offline Capability**: Run guardrails without network calls
- **Parallel Execution**: Execute multiple guardrails simultaneously with asyncio
- **Flexible Actions**: Block, redact, mask, or transform risky content
- **Risk Scoring**: Quantify security risks (0-100 scale)
- **Pattern Detection**: Regex-based detection with high accuracy
- **OpenAI Integration**: Optional OpenAI Moderation API support
- **Type Safety**: Full Pydantic models for all guardrail results

### Performance
- < 50ms guardrail execution (parallel mode)
- Configurable timeouts per guardrail
- Efficient pattern matching with compiled regex
- Async-first design for high concurrency

### Documentation
- Added guardrails usage examples
- Updated README with guardrails showcase
- Added inline documentation for all guardrail classes

## [0.1.1] - 2026-01-29

### Fixed
- Package name changed to `agentguard-sdk` (from `agentguard`) due to PyPI name conflict
- Updated all imports and documentation

### Added
- Published to PyPI as `agentguard-sdk`
- GitHub repository: https://github.com/agentguard-ai/agentguard-python

## [0.1.0] - 2026-01-28

### Added
- Initial release of AgentGuard Python SDK
- Core security evaluation functionality
- Tool execution with security decisions (allow/deny/transform)
- Security Sidecar Agent (SSA) HTTP client
- Configuration management with validation
- Comprehensive error handling with custom exceptions
- Audit trail functionality
- Policy validation and management
- Full async/await support
- Type hints throughout the codebase
- Comprehensive test suite with pytest
- Examples for basic and advanced usage
- Complete API documentation

### Features
- **Security Evaluation**: Evaluate tool calls before execution
- **Policy Enforcement**: Automatic policy-based decision making
- **Request Transformation**: Safe transformation of risky operations
- **Audit Trail**: Complete audit logging for compliance
- **Performance**: < 100ms security evaluation overhead
- **Type Safety**: Full type hints with Pydantic models
- **Async Support**: Built-in async/await for modern Python

### Security
- API key authentication with SSA
- Input validation and sanitization
- Secure HTTP communication with httpx
- Error handling that doesn't leak sensitive information

### Developer Experience
- Comprehensive documentation with examples
- Type hints for better IDE support
- Pytest test suite with 100% core functionality coverage
- Examples for common integration patterns
- Poetry and pip support

[Unreleased]: https://github.com/agentguard-ai/agentguard-python/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/agentguard-ai/agentguard-python/releases/tag/v0.2.0
[0.1.1]: https://github.com/agentguard-ai/agentguard-python/releases/tag/v0.1.1
[0.1.0]: https://github.com/agentguard-ai/agentguard-python/releases/tag/v0.1.0
