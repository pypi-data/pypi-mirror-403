# AI Skill Manager

[![PyPI version](https://badge.fury.io/py/ai-skill-manager.svg)](https://badge.fury.io/py/ai-skill-manager)
[![npm version](https://badge.fury.io/js/ai-skill-manager.svg)](https://badge.fury.io/js/ai-skill-manager)
[![Crates.io](https://img.shields.io/crates/v/ai-skill-manager.svg)](https://crates.io/crates/ai-skill-manager)
[![Python Tests](https://github.com/binzhango/agent-skills-util/workflows/CI/badge.svg)](https://github.com/binzhango/agent-skills-util/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Node.js 14+](https://img.shields.io/badge/node.js-14+-green.svg)](https://nodejs.org/)
[![Rust 1.75+](https://img.shields.io/badge/rust-1.75+-orange.svg)](https://www.rust-lang.org/)

A lightweight utility to download and manage skills for different AI coding assistants. Available in Python, Node.js, and Rust with full feature parity.

> **Status**: ✅ **Production Ready** - Version 1.0.1 released with complete selective download functionality, comprehensive test suite, and multi-language support (Python, Node.js, and Rust).

## 🎯 Choose Your Implementation

AI Skill Manager is available in three languages, each optimized for different use cases:

| Implementation | Best For | Installation |
|---------------|----------|--------------|
| **🦀 Rust** | Performance, CLI usage, cross-platform binaries | `cargo install ai-skill-manager` |
| **🐍 Python** | Python projects, scripting, data science workflows | `pip install ai-skill-manager` |
| **📦 Node.js** | JavaScript/TypeScript projects, web development | `npm install -g ai-skill-manager` |

All implementations provide the same core features with language-specific optimizations.

## ✨ Features

- **🤖 Multi-AI Support**: Works with GitHub Copilot, Claude, Cursor, Codeium, and more
- **🎯 Selective Downloads**: Download specific skills using git sparse-checkout
- **📦 Batch Operations**: Download multiple skills with configuration files
- **🔍 Repository Exploration**: Browse available skills in repositories
- **🔄 Cross-Model Copying**: Share skills between different AI assistants
- **📋 Dependency Management**: Automatic Python/Node.js dependency installation
- **🌐 Cross-Platform**: Available for both Python and Node.js ecosystems
- **⚡ Performance Optimized**: Uses uv for fast Python package management

## 🆕 What's New in v1.0.1

- ✅ **Repository URL Fixes**: Corrected repository URLs for proper npm provenance verification
- ✅ **Complete Selective Download Implementation**: Full sparse-checkout support for efficient skill downloads
- ✅ **Dual Package Support**: Both Python (PyPI) and Node.js (npm) packages with feature parity
- ✅ **Property-Based Testing**: Comprehensive test suite with 45+ tests including property-based tests
- ✅ **Enhanced CLI**: Rich command-line interface with batch operations and repository exploration
- ✅ **Type Safety**: Full TypeScript support with comprehensive type definitions
- ✅ **Modern Tooling**: Uses uv for Python package management and modern build tools
- ✅ **CI/CD Pipeline**: Automated testing and publishing via GitHub Actions
- ✅ **Documentation**: Complete API documentation and usage examples

## Supported AI Models

- **GitHub Copilot**: `.github/skills/`
- **Claude**: `.claude/skills/`
- **Antigravity**: `.agent/skills/`
- **Codex**: `.codex/skills/`
- **Cursor**: `.cursor/skills/`
- **Codeium**: `.codeium/skills/`
- **TabNine**: `.tabnine/skills/`
- **Kite**: `.kite/skills/`

## 📋 Requirements

### System Requirements
- **Git**: Version 2.25.0 or higher (required for sparse-checkout support)
- **Python**: 3.11+ (for Python package)
- **Node.js**: 14.0+ (for Node.js package)

### Optional Dependencies
- **uv**: Recommended for faster Python package management
- **SSH keys**: For private repository access

## 📦 Installation

### 🦀 Rust (Recommended for CLI)

Fast, standalone binary with no runtime dependencies:

```bash
# Install from crates.io
cargo install ai-skill-manager

# Or build from source
git clone https://github.com/binzhango/agent-skills-util
cd agent-skills-util/rust
cargo install --path .
```

**Why Rust?**
- ⚡ Blazing fast performance
- 📦 Single binary, no runtime required
- 🔒 Memory safe and reliable
- 🌐 True cross-platform support

### 🐍 Python Package (PyPI)

```bash
# Using pip
pip install ai-skill-manager

# Using uv (recommended for faster installation)
uv add ai-skill-manager
```

### 📦 Node.js Package (npm)

```bash
# Global installation
npm install -g ai-skill-manager

# Local installation
npm install ai-skill-manager

# Using yarn
yarn global add ai-skill-manager
```

## 🚀 Quick Start

> **Note**: The examples below use the Rust CLI syntax. Python and Node.js have similar commands with slight variations. See language-specific documentation for details.

### Rust CLI

```bash
# Detect installed AI assistants
ai-skill-manager detect

# Download a single skill
ai-skill-manager download \
  --repo https://github.com/example/skills \
  --path skills/code-review \
  --assistant copilot

# Batch download from config file
ai-skill-manager batch skills.yaml

# List installed skills
ai-skill-manager list

# Copy skills between assistants
ai-skill-manager copy copilot cursor

# Remove a skill
ai-skill-manager remove copilot old-skill
```

### Python CLI
### Python CLI

```bash
# Auto-detect AI Model
ai-skill detect
```

### Download Skills

From any URL:
```bash
ai-skill download https://example.com/skill.py --name my-skill
```

From GitHub repository:
```bash
ai-skill github owner/repo path/to/skill.py --name custom-name
```

### 🎯 Selective Download (Recommended!)

Download specific skills from git repositories using sparse-checkout for efficient, targeted downloads:

```bash
# Download a specific skill folder from a repository
ai-skill download-selective https://github.com/user/skills-repo skills/data-analysis --name data-analyzer

# Download with custom options
ai-skill download-selective https://github.com/user/skills-repo skills/web-scraper \
  --name scraper --no-deps --timeout 600 --retries 5

# Download multiple skills from a batch configuration
ai-skill download-batch batch-config.json
```

### 🔍 Repository Exploration

Explore repositories to see available skills:

```bash
# List all available skills in a repository
ai-skill explore https://github.com/user/skills-repo

# Explore a specific branch
ai-skill explore https://github.com/user/skills-repo --branch develop
```

### 📋 Skill Management

List skills:
```bash
# For current/detected model
ai-skill list

# For all models
ai-skill list --all
```

Copy skills between models:
```bash
ai-skill copy skill-name --from claude --to github-copilot
```

Remove skills:
```bash
ai-skill remove skill-name
```

List supported models:
```bash
ai-skill models
```

Specify model manually:
```bash
ai-skill --model claude download https://example.com/skill.py
```

## 💻 Programmatic Usage

### 🦀 Rust Library

The Rust implementation provides a library for embedding in Rust applications:

```rust
use ai_skill_manager::{detect_assistants, commands};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    // Detect installed assistants
    let assistants = detect_assistants()?;
    for assistant in assistants {
        println!("{}: {:?}", assistant.name, assistant.config_dir);
    }
    
    // Download a skill
    commands::download_skill(
        "https://github.com/example/skills",
        "skills/code-review",
        "copilot",
    )?;
    
    // Batch download
    commands::download_batch("skills.yaml").await?;
    
    // List skills
    commands::list_skills()?;
    
    // Copy skills between assistants
    commands::copy_skills("copilot", "cursor")?;
    
    Ok(())
}
```

**Rust Features:**
- 🔒 Type-safe API with comprehensive error handling
- ⚡ Async/await support with Tokio
- 📝 Full documentation with examples
- 🧪 Property-based testing with Proptest
- 🎯 Zero-cost abstractions

See the [Rust documentation](rust/README.md) for complete API reference.

### 🐍 Python

```python
from ai_skill_manager import SkillManager

manager = SkillManager()

# Auto-detect model
model = manager.detect_model()
print(f"Detected model: {model}")

# Download a skill
manager.download_skill_from_url(
    "https://example.com/skill.py", 
    "claude", 
    "my-skill"
)

# Selective download with options
result = manager.download_skill_selective(
    "https://github.com/user/skills-repo",
    "python/data-analysis",
    "claude",
    {
        'skillName': 'data-analyzer',
        'installDependencies': True,
        'useShallowClone': True,
        'timeout': 600
    }
)

# Batch download
requests = [
    {
        'repoUrl': 'https://github.com/user/skills-repo',
        'skillPath': 'python/skill1',
        'model': 'claude',
        'options': {'skillName': 'skill1'}
    },
    {
        'repoUrl': 'https://github.com/user/skills-repo', 
        'skillPath': 'python/skill2',
        'model': 'claude',
        'options': {'skillName': 'skill2'}
    }
]
results = manager.download_multiple_skills(requests)

# Explore repository
skills = manager.list_repository_skills("https://github.com/user/skills-repo")
print(f"Available skills: {skills}")

# List skills
skills = manager.list_skills("claude")
print(f"Skills: {skills}")
```

### Node.js

```javascript
const { SkillManager } = require('ai-skill-manager');

const manager = new SkillManager();

// Auto-detect model
const model = await manager.detectModel();
console.log(`Detected model: ${model}`);

// Download a skill
await manager.downloadSkillFromUrl(
    "https://example.com/skill.py", 
    "claude", 
    "my-skill"
);

// Selective download with options
const result = await manager.downloadSkillSelective(
    "https://github.com/user/skills-repo",
    "javascript/web-scraper", 
    "claude",
    {
        skillName: 'scraper',
        installDependencies: true,
        useShallowClone: true,
        timeout: 600
    }
);

// Batch download
const requests = [
    {
        repoUrl: 'https://github.com/user/skills-repo',
        skillPath: 'javascript/skill1',
        model: 'claude',
        options: { skillName: 'skill1' }
    },
    {
        repoUrl: 'https://github.com/user/skills-repo',
        skillPath: 'javascript/skill2', 
        model: 'claude',
        options: { skillName: 'skill2' }
    }
];
const results = await manager.downloadMultipleSkills(requests);

// Explore repository
const skills = await manager.listRepositorySkills("https://github.com/user/skills-repo");
console.log(`Available skills: ${skills}`);

// List skills
const skills = await manager.listSkills("claude");
console.log(`Skills: ${skills}`);
```

## 📚 TypeScript API Documentation

### Core Interfaces

#### SelectiveDownloadOptions
```typescript
interface SelectiveDownloadOptions {
  skillName?: string;              // Custom name for the downloaded skill
  useShallowClone?: boolean;       // Use shallow git clone (default: true)
  installDependencies?: boolean;   // Install Python/Node.js dependencies (default: true)
  dependencyManager?: 'uv' | 'pip' | 'auto';  // Python package manager preference
  timeout?: number;                // Timeout in seconds (default: 300)
  retryAttempts?: number;          // Number of retry attempts (default: 3)
}
```

#### SkillDownloadRequest
```typescript
interface SkillDownloadRequest {
  repoUrl: string;                 // Git repository URL
  skillPath: string;               // Path to skill within repository
  model: ModelType;                // Target AI model
  options?: SelectiveDownloadOptions;
}
```

#### DownloadResult
```typescript
interface DownloadResult {
  success: boolean;                // Whether download succeeded
  skillName: string;               // Name of the downloaded skill
  model: ModelType;                // Target AI model
  error?: string;                  // Error message if failed
  downloadedFiles: string[];       // List of downloaded files
  installedDependencies?: string[]; // List of installed dependencies
}
```

#### RepositoryInfo
```typescript
interface RepositoryInfo {
  url: string;                     // Repository URL
  defaultBranch: string;           // Default branch name
  availableSkills: string[];       // List of available skill paths
  lastUpdated: Date;               // Last update timestamp
  size: number;                    // Repository size in bytes
}
```

### SkillManager Methods

#### Selective Download Methods
```typescript
// Download a specific skill using sparse-checkout
downloadSkillSelective(
  repoUrl: string, 
  skillPath: string, 
  model: ModelType, 
  options?: SelectiveDownloadOptions
): Promise<DownloadResult>

// Download multiple skills in batch
downloadMultipleSkills(
  requests: SkillDownloadRequest[]
): Promise<DownloadResult[]>

// List available skills in a repository
listRepositorySkills(
  repoUrl: string, 
  branch?: string
): Promise<string[]>

// Update an existing skill from its source repository
updateSkillFromRepository(
  skillName: string, 
  model: ModelType
): Promise<void>
```

#### Traditional Download Methods
```typescript
// Download skill from any URL
downloadSkillFromUrl(
  url: string, 
  model: ModelType, 
  skillName?: string
): Promise<void>

// Download skill from GitHub repository
downloadGithubSkill(
  repo: string, 
  path: string, 
  model: ModelType, 
  skillName?: string
): Promise<void>
```

#### Skill Management Methods
```typescript
// List skills for a model
listSkills(model: ModelType): Promise<string[]>

// Remove a skill
removeSkill(model: ModelType, skillName: string): Promise<boolean>

// Copy skill between models
copySkill(
  sourceModel: ModelType, 
  targetModel: ModelType, 
  skillName: string
): Promise<boolean>

// Auto-detect current AI model
detectModel(): Promise<ModelType | null>

// Get list of supported models
getSupportedModels(): ModelType[]
```

### Error Handling

The TypeScript implementation provides comprehensive error handling with typed exceptions:

```typescript
try {
  const result = await manager.downloadSkillSelective(
    'https://github.com/user/skills-repo',
    'typescript/web-scraper',
    'claude',
    { timeout: 600, retryAttempts: 5 }
  );
  
  if (result.success) {
    console.log(`Downloaded ${result.downloadedFiles.length} files`);
  } else {
    console.error(`Download failed: ${result.error}`);
  }
} catch (error) {
  if (error instanceof GitError) {
    console.error(`Git operation failed: ${error.message}`);
  } else if (error instanceof NetworkError) {
    console.error(`Network error: ${error.message}`);
  } else {
    console.error(`Unexpected error: ${error.message}`);
  }
}
```

### Advanced Usage Examples

#### Custom Configuration
```typescript
import { SkillManager } from 'ai-skill-manager';

const manager = new SkillManager({
  projectRoot: '/custom/project/path'
});

// Set environment variables for configuration
process.env.AI_SKILL_MANAGER_TIMEOUT = '600';
process.env.AI_SKILL_MANAGER_RETRIES = '5';
process.env.AI_SKILL_MANAGER_USE_UV = 'true';
```

#### Progress Monitoring
```typescript
// Monitor download progress with custom logging
const result = await manager.downloadSkillSelective(
  repoUrl,
  skillPath,
  model,
  {
    timeout: 600,
    onProgress: (stage: string, progress: number) => {
      console.log(`${stage}: ${progress}%`);
    }
  }
);
```

#### Batch Operations with Error Handling
```typescript
const requests: SkillDownloadRequest[] = [
  {
    repoUrl: 'https://github.com/user/skills-repo',
    skillPath: 'typescript/skill1',
    model: 'claude',
    options: { skillName: 'skill1', timeout: 300 }
  },
  {
    repoUrl: 'https://github.com/user/skills-repo',
    skillPath: 'typescript/skill2',
    model: 'claude',
    options: { skillName: 'skill2', timeout: 300 }
  }
];

const results = await manager.downloadMultipleSkills(requests);

// Process results
const successful = results.filter(r => r.success);
const failed = results.filter(r => !r.success);

console.log(`✓ ${successful.length} skills downloaded successfully`);
if (failed.length > 0) {
  console.log(`✗ ${failed.length} skills failed:`);
  failed.forEach(result => {
    console.log(`  - ${result.skillName}: ${result.error}`);
  });
}
```

## 📖 Examples

```bash
# Download a Python skill for Claude
ai-skill --model claude download https://raw.githubusercontent.com/user/repo/main/skills/data-analysis.py

# Download from GitHub for auto-detected model
ai-skill github anthropic/claude-skills skills/code-review.md

# Selective download - download only specific skill folders
ai-skill download-selective https://github.com/awesome-ai/skills-collection python-tools/data-processor

# Batch download multiple skills
ai-skill download-batch my-skills-config.json

# Explore repository structure
ai-skill explore https://github.com/awesome-ai/skills-collection

# Copy a skill from Claude to GitHub Copilot
ai-skill copy code-review.md --from claude --to github-copilot

# List all skills across all models
ai-skill list --all
```

### Batch Configuration Example

Create a `batch-config.json` file for downloading multiple skills:

```json
{
  "skills": [
    {
      "repoUrl": "https://github.com/user/skills-repo",
      "skillPath": "python/data-analysis",
      "options": {
        "skillName": "data-analyzer",
        "installDependencies": true,
        "useShallowClone": true
      }
    },
    {
      "repoUrl": "https://github.com/user/skills-repo", 
      "skillPath": "javascript/web-scraper",
      "options": {
        "skillName": "scraper",
        "timeout": 600
      }
    }
  ]
}
```

## Features

- **Auto-detection**: Automatically detects which AI model you're using
- **Multi-format support**: Handles Python, JavaScript, JSON, YAML, and Markdown files
- **GitHub integration**: Easy downloading from GitHub repositories
- **Selective downloads**: Download specific skill folders using git sparse-checkout
- **Batch operations**: Download multiple skills with configuration files
- **Repository exploration**: Browse available skills in repositories
- **Cross-model copying**: Share skills between different AI assistants
- **Clean organization**: Maintains proper directory structure for each model
- **Dependency management**: Automatic Python dependency installation with uv/pip
- **Cross-platform**: Available for both Python and Node.js ecosystems

## ⚙️ Configuration

### Environment Variables

- `AI_SKILL_MANAGER_TIMEOUT`: Default timeout for git operations (seconds, default: 300)
- `AI_SKILL_MANAGER_RETRIES`: Default number of retry attempts (default: 3)
- `AI_SKILL_MANAGER_USE_UV`: Force use of uv for Python dependencies (true/false)

### Configuration File

Create `.ai-skill-manager.json` in your project root:

```json
{
  "defaultTimeout": 600,
  "defaultRetries": 5,
  "preferUv": true,
  "tempDirectory": "/tmp/ai-skills",
  "gitOptions": {
    "depth": 1,
    "singleBranch": true
  }
}
```

## 🔧 Troubleshooting

### Common Issues

**Git not found**
```bash
# Install git on your system
# macOS: brew install git
# Ubuntu: sudo apt-get install git
# Windows: Download from https://git-scm.com/
```

**Authentication failures for private repositories**
```bash
# Set up SSH key authentication
ssh-keygen -t ed25519 -C "your_email@example.com"
# Add the public key to your Git provider

# Or use personal access tokens for HTTPS
git config --global credential.helper store
```

**Dependency installation failures**
```bash
# Install uv for faster Python package management
pip install uv

# Or ensure pip is up to date
python -m pip install --upgrade pip
```

**Permission errors**
```bash
# Ensure you have write permissions to the skill directories
chmod -R 755 ~/.github/skills/  # Example for GitHub Copilot
```

### Debug Mode

Enable verbose logging:
```bash
export AI_SKILL_MANAGER_DEBUG=1
ai-skill download-selective https://github.com/user/repo skill-path
```

## 📦 Publishing

### Python Package
```bash
# Build and publish to PyPI
uv build
uv publish
```

### Node.js Package
```bash
# Build and publish to npm
npm run build
npm publish
```

## 🛠️ Development

### Prerequisites

- **Rust 1.75+** with Cargo (for Rust implementation)
- **Python 3.11+** with [uv](https://docs.astral.sh/uv/) package manager (recommended)
- **Node.js 16+** with npm
- **Git 2.25+** (for sparse-checkout support)

### Setup

```bash
# Clone the repository
git clone https://github.com/binzhango/agent-skills-util.git
cd agent-skills-util

# Rust setup
cd rust
cargo build
cargo test

# Python setup
cd ..
uv sync --dev
# Or with pip
pip install -e ".[dev]"

# Node.js setup
npm install
```

### 🔧 Development Workflow

```bash
# Rust development
cd rust
cargo build                     # Build Rust project
cargo test                      # Run tests (45+ tests including property-based)
cargo clippy                    # Lint Rust code
cargo fmt                       # Format Rust code
cargo doc --open               # Generate and view documentation
cargo run -- detect            # Test CLI

# Python development
uv run pytest                    # Run Python tests
uv run ruff check .             # Lint Python code  
uv run ruff format .            # Format Python code
uv run mypy ai_skill_manager/   # Type check Python code
uv run ai-skill --help          # Test CLI

# Node.js development
npm test                        # Run TypeScript tests
npm run lint                    # Lint TypeScript code
npm run type-check             # Type check TypeScript code
npm run build                  # Build TypeScript
node bin/ai-skill.js --help    # Test CLI

# Build packages
cargo build --release          # Build Rust binary
uv build                       # Build Python package (wheel + sdist)
npm run build                  # Build TypeScript package
```

### 🧪 Testing

```bash
# Rust tests
cd rust
cargo test                      # Run all tests (unit + property-based + doc tests)
cargo test --lib               # Run library tests only
cargo test prop_               # Run property-based tests only
cargo test --doc               # Run documentation tests

# Python tests
uv run pytest tests/ -v        # Python tests (45+ tests including property-based)
npm test                       # TypeScript tests (31+ tests)

# Run specific test types
uv run pytest tests/test_*_properties.py  # Property-based tests only
npm run test:watch                         # Watch mode for TypeScript tests

# Run integration tests
uv run pytest tests/ -m integration

# Test coverage
cargo tarpaulin --out Html     # Rust coverage
uv run pytest --cov=ai_skill_manager tests/
npm run test -- --coverage
```

### 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `uv run pytest && npm test`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### 🚀 Release Process

Releases are automated via GitHub Actions:

1. Update version numbers in:
   - `rust/Cargo.toml` (Rust)
   - `pyproject.toml` (Python)
   - `package.json` (Node.js)
2. Update `CHANGELOG.md` with new features and changes
3. Create a git tag: `git tag v1.0.1`
4. Push the tag: `git push origin v1.0.1`
5. GitHub Actions will automatically build and publish to:
   - crates.io (Rust)
   - PyPI (Python)
   - npm (Node.js)

## 📚 Documentation

- **Rust**: See [rust/README.md](rust/README.md) for complete Rust documentation
  - [Quick Reference](rust/examples/QUICK_REFERENCE.md)
  - [Usage Examples](rust/examples/USAGE.md)
  - [Creating Skills Repositories](rust/examples/creating-skills-repo.md)
  - [Contributing Guide](rust/examples/CONTRIBUTING.md)
- **Python**: API documentation available in docstrings
- **Node.js**: TypeScript definitions included in package

## 🆚 Implementation Comparison

| Feature | Rust | Python | Node.js |
|---------|------|--------|---------|
| **Performance** | ⚡⚡⚡ Fastest | ⚡⚡ Fast | ⚡⚡ Fast |
| **Binary Size** | ~5MB standalone | Requires Python runtime | Requires Node.js runtime |
| **Startup Time** | Instant | Fast | Fast |
| **Memory Usage** | Minimal | Moderate | Moderate |
| **Concurrency** | Native async (Tokio) | asyncio | Native async |
| **Type Safety** | Compile-time | Runtime (with type hints) | Compile-time (TypeScript) |
| **Package Manager** | Cargo | pip/uv | npm/yarn |
| **Cross-compilation** | ✅ Easy | ❌ Platform-specific | ❌ Platform-specific |
| **Dependency Management** | Cargo.lock | requirements.txt | package-lock.json |
| **Best Use Case** | CLI tools, performance-critical | Scripting, data science | Web apps, JS projects |

## 🌟 Why Three Implementations?

- **Rust**: Maximum performance and reliability for production CLI usage
- **Python**: Perfect for data science workflows and Python-centric projects
- **Node.js**: Ideal for JavaScript/TypeScript projects and web development

Choose the implementation that best fits your ecosystem!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.