"""
NC1709 - AI Coding Assistant with Fine-Tuned Tool Calling
Version 3.0.2 - Lightweight Install
"""

from setuptools import setup, find_packages
from setuptools.command.install import install
import os
import subprocess
import sys


class PostInstallCommand(install):
    """Custom post-installation command"""
    
    def run(self):
        install.run(self)
        
        # Run post-install setup only for user installs
        if '--user' in sys.argv or os.environ.get('PIP_USER'):
            try:
                # Import and run post-install script
                from nc1709.post_install import main
                main()
            except ImportError:
                # Fallback: run as subprocess
                post_install_script = os.path.join(
                    os.path.dirname(__file__), 
                    'nc1709', 
                    'post_install.py'
                )
                if os.path.exists(post_install_script):
                    subprocess.run([sys.executable, post_install_script])


long_description = """
# NC1709 - AI Coding Assistant

**99% Tool-Calling Accuracy** | Outperforms Claude Sonnet 3.5

---

## ⚡ INSTALLATION

```bash
# Install (Ubuntu/Debian/macOS):
pipx install nc1709

# Upgrade to latest version:
pipx upgrade nc1709

# Alternative install method:
pip install --user nc1709
```

> **Note:** On Ubuntu 23.04+, Debian 12+, use `pipx` (NOT `pip install nc1709`)

## 🔑 SETUP API KEY

```bash
# Request your API key: asif90988@gmail.com
export NC1709_API_KEY="your-api-key-here"

# Add to ~/.bashrc for persistence:
echo 'export NC1709_API_KEY="your-key"' >> ~/.bashrc
```

## 🚀 START USING

```bash
nc1709 "create a FastAPI server with authentication"
```

---

## What Makes NC1709 Special

- **99% Tool-Calling Accuracy**: Outperforms Claude Sonnet 3.5 (80.5%)
- **Zero Setup Required**: No local models, no GPU needed
- **Server-Side Intelligence**: Fine-tuned Qwen2.5-Coder-7B via API
- **Enterprise Monitoring**: Prometheus metrics, health checks

## Features

- **File Operations**: Read, Write, Edit, Glob with 99% accuracy
- **Code Search**: Advanced regex and context-aware search
- **Git Integration**: Natural language git commands
- **Bash Execution**: Safe command execution with smart permissions
- **Web Tools**: Fetch and analyze web content
- **Task Management**: Intelligent todo tracking

## Quick Start

```bash
# Start coding with 99% accuracy AI
nc1709

# Example commands
nc1709 "Find all Python functions with TODO comments"  
nc1709 "Create a FastAPI endpoint for user auth"
nc1709 "Debug the TypeError in main.py line 42"
```

## Why Choose NC1709?

| Feature | NC1709 | Claude Sonnet 3.5 | Local Models |
|---------|--------|--------------------|--------------|
| **Tool Accuracy** | 99% | 80.5% | Variable |
| **Setup Time** | 0 minutes | API key setup | Hours |
| **Hardware Needed** | None | None | RTX 3090+ |
| **Storage Required** | 0GB | 0GB | 15GB+ |

## New in Version 3.0.0 - Unified Enhanced Architecture

### 🏗️ Architecture Improvements
- **Unified Codebase**: Single enhanced package replacing legacy dual-package structure
- **5-Layer Cognitive System**: Router → Context → Council → Learning → Anticipation
- **Dependency Injection**: Full IoC container with service locator pattern
- **OpenTelemetry Tracing**: Distributed tracing with W3C context propagation
- **Rate Limiting**: Token bucket algorithm with configurable strategies
- **JSON Schema Validation**: Full draft-07 validation with type coercion
- **Input Sanitization**: NC1709-SAN algorithm for command/path injection prevention
- **API Key Masking**: NC1709-CAI (Color-Animal Identifier) for privacy

### 🏭 Production-Ready Features
- **Multi-Worker Scaling**: Automatic worker count optimization
- **Connection Pooling**: Efficient resource management with retry logic
- **Circuit Breaker**: Automatic failure detection and recovery
- **Prometheus Metrics**: 15+ monitoring metrics for performance tracking
- **Health Monitoring**: Comprehensive system health checks
- **Load Balancing**: Nginx configuration with rate limiting
- **Graceful Shutdown**: Clean resource cleanup on shutdown
- **Auto-deployment**: One-command production deployment script

### 📊 Monitoring Endpoints
- `/health` - Basic health status
- `/health/detailed` - Comprehensive system health
- `/metrics` - Prometheus metrics endpoint
- `/status/connections` - Connection pool statistics
- `/status/circuit-breaker` - Circuit breaker status

## Behind the Scenes

**Our Training**: 800K examples on DeepFabric infrastructure  
**Our Model**: Fine-tuned Qwen2.5-Coder-7B optimized for tool-calling  
**Our Infrastructure**: Enterprise-grade servers with monitoring & auto-scaling
**Your Benefit**: 99% accuracy with production-grade reliability

## Links

- Documentation: https://docs.lafzusa.com/nc1709
- GitHub: https://github.com/lafzusa/nc1709
- PyPI: https://pypi.org/project/nc1709/
- Support: support@lafzusa.com
"""

install_requires = [
    # Core - lightweight deps for remote mode (most users)
    "rich>=13.0.0",
    "prompt_toolkit>=3.0.0",
    "click>=8.1.0",
    "pydantic>=2.0.0",
    "python-dotenv>=0.20.0",
    "httpx>=0.24.0",
    "aiofiles>=23.0.0",
    "psutil>=5.9.0",

    # Search
    "ddgs>=9.0.0",
]

extras_require = {
    "local": [
        # ML dependencies for local model inference
        "litellm>=1.0.0",
        "huggingface_hub>=0.20.0",
        "transformers>=4.36.0",
        "torch>=2.0.0",
        "accelerate>=0.25.0",
        "bitsandbytes>=0.41.0",
        "peft>=0.7.0",
    ],
    "server": [
        # Dependencies for running production server
        "prometheus-client>=0.17.0",
        "litellm>=1.0.0",
    ],
    "memory": [
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
    ],
    "dev": [
        "pytest>=7.0.0",
        "pytest-asyncio>=0.21.0",
        "black>=23.0.0",
        "mypy>=1.0.0",
    ],
    "full": [
        # Everything
        "litellm>=1.0.0",
        "huggingface_hub>=0.20.0",
        "transformers>=4.36.0",
        "torch>=2.0.0",
        "accelerate>=0.25.0",
        "bitsandbytes>=0.41.0",
        "peft>=0.7.0",
        "prometheus-client>=0.17.0",
        "chromadb>=0.4.0",
        "sentence-transformers>=2.2.0",
    ],
}

setup(
    name="nc1709",
    version="3.0.31",
    author="Lafzusa Corp",
    author_email="asif90988@gmail.com",
    description="AI coding assistant with fine-tuned tool calling - Your code comes to life",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lafzusa/nc1709",
    packages=find_packages(),
    cmdclass={
        'install': PostInstallCommand,
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: Other/Proprietary License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=install_requires,
    extras_require=extras_require,
    entry_points={
        "console_scripts": [
            "nc1709=nc1709.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "nc1709": [
            "prompts/*.txt",
            "prompts/*.md",
            "config/*.json",
        ],
    },
    data_files=[
        ('', ['install.sh']),
    ],
)
