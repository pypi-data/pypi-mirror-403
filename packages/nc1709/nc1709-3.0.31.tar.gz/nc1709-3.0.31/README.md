# NC1709 - AI Coding Assistant

**Version:** 3.0.17 (Fine-tuned)
**Created by:** Lafzusa Corp

NC1709 is an advanced AI coding assistant with 99% tool-calling accuracy, built on a custom fine-tuned Qwen2.5-Coder model.

## Quick Start

```bash
# SSH to server
ssh fas@100.90.213.50

# Check status
/home/fas/start_nc1709.sh status

# Health check
curl http://100.90.213.50:8000/health
```

## API Usage

```bash
curl -X POST http://100.90.213.50:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer nc1709_production_key" \
  -d '{"model": "nc1709:latest", "messages": [{"role": "user", "content": "Hello"}]}'
```

## Server Management

| Command | Description |
|---------|-------------|
| `start_nc1709.sh status` | Check server status |
| `start_nc1709.sh start` | Start server |
| `start_nc1709.sh stop` | Stop server |
| `start_nc1709.sh restart` | Restart server |
| `start_nc1709.sh logs` | View logs |

## Documentation

**[NC1709_COMPLETE_DOCUMENTATION.md](NC1709_COMPLETE_DOCUMENTATION.md)** - Full documentation including:
- System Architecture
- Model Architecture & Fine-Tuning Details
- Code Architecture
- API Reference
- Troubleshooting Guide
- Maintenance Procedures

## Architecture Overview

```
Production Server (fas@100.90.213.50)
├── FastAPI Server (Port 8000)
│   └── production_server.py
└── Ollama (Port 11434)
    └── nc1709:latest (Fine-tuned 7B, 15GB F16)
```

## Key Files

| File | Location |
|------|----------|
| Management Script | `/home/fas/start_nc1709.sh` |
| Server Logs | `/home/fas/nc1709.log` |
| Model File | `/home/fas/nc1709-finetuned-f16.gguf` |
| Model Weights | `/home/fas/nc1709_merged_fp16/` |

## Archived Documentation

Previous documentation versions are in `docs_archive/` for reference.
