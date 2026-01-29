# Changelog

All notable changes to Voight will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-01-23

### Added

- **Core Framework**
  - `@scenario` decorator for probabilistic test execution
  - `ScenarioResult` and `RunResult` dataclasses for detailed test results
  - Configurable `runs` and `threshold` parameters

- **Generators**
  - `SimpleGenerator`: Template-based input generation (no API key required)
  - `AdversarialGenerator`: LLM-powered adversarial input generation

- **Judges**
  - `SimpleLLMJudge`: LLM-based semantic evaluation with OpenAI
  - `DeterministicJudge`: Rule-based evaluation with required/forbidden phrases
  - `FileExistsJudge`: Side-effect verification for file creation

- **Sandbox**
  - `Sandbox` context manager for isolated file system operations
  - Automatic cleanup and directory restoration
  - File inspection utilities (`file_exists`, `get_file_content`, `list_files`)

- **CLI**
  - `voight init`: Project scaffolding with sample tests
  - `voight run`: Scenario discovery and execution
  - Verbose mode and pattern filtering

- **Utilities**
  - `check()` helper function for fluent assertions
  - `EvalResult` Pydantic model for evaluation results

### Documentation

- Comprehensive README with quickstart guide
- `llms.txt` for AI agent discoverability
- Example recipes for common use cases
