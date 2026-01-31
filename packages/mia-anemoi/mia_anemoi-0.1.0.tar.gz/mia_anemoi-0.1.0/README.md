# mia-anemoi: Agent-to-Agent Communication System

**mia-anemoi** is Mia's fork of [Coral-Protocol/Anemoi](https://github.com/Coral-Protocol/Anemoi) — a semi-centralized multi-agent system (MAS) built on **Agent-to-Agent (A2A) communication** via MCP.

This fork is adapted for **terminal-based agent orchestration** and **SimExp integration**.

<p align="center">
  <img src="Anemoi/images/Anemoi_semi.png" alt="Anemoi Concept" width="70%">
</p>

---

## 🚀 Key Features

* **Semi-Centralized Architecture**: Reduces dependency on a single planner agent
* **Direct Agent-to-Agent Collaboration**: Real-time monitoring, assessment, and refinement
* **Efficient Context Management**: Minimizes redundant prompt concatenation
* **Benchmark Performance**: 52.73% accuracy on GAIA benchmark (+9.09% over OWL)
* **SimExp Integration**: Terminal-to-AI session continuations with A2A communication

---

## 📦 Package Components

| Component | Description | Location |
|-----------|-------------|----------|
| **Python Client** | Lightweight A2A communication library | `mia_anemoi/` |
| **CAMEL Agents** | Specialized AI agents (planning, web, coding) | `Anemoi/agents/` |
| **Kotlin MCP Server** | SSE-based thread messaging | `src/main/kotlin/` |

---

## 🔧 Installation

### Python Client (Lightweight)

```bash
pip install mia-anemoi
```

### With CAMEL Agents (Full)

```bash
pip install mia-anemoi[agents]
```

### From Source

```bash
git clone https://github.com/miadisabelle/mia-anemoi.git
cd mia-anemoi
pip install -e .
```

---

## 🚀 Quick Start

### 1. Start MCP Server

```bash
# Using Docker
docker run -p 5555:5555 ghcr.io/miadisabelle/mia-anemoi-server:latest

# Or build and run locally
./gradlew build
java -jar build/libs/mia-anemoi-server-1.0-SNAPSHOT.jar
```

### 2. Use Python Client

```python
from mia_anemoi import AnemoiClient, AnemoiClientConfig

# Initialize client
config = AnemoiClientConfig(transport="file", base_path="~/.anemoi")
client = AnemoiClient("session-123", config)

# Fork session with context inheritance
child_id = client.fork_session(parent_state)

# Send update to siblings
client.send_update("Task completed", {"files": ["main.py"]})

# Wait for messages
msg = client.wait_for_mentions(timeout=30)
```

### 3. Run CAMEL Agents

```bash
export CORAL_CONNECTION_URL="http://localhost:5555/devmode/gaia/public/session1/sse"
export OPENAI_API_KEY="sk-..."

python -m Anemoi.agents.planning_agent
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         mia-anemoi Package                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────┐      ┌────────────────────────────────────┐ │
│  │    Python Client   │ SSE  │         Kotlin MCP Server          │ │
│  │   (mia_anemoi/)    │──────│   (src/main/kotlin/coralserver/)   │ │
│  │                    │      │                                    │ │
│  │  - AnemoiClient    │      │  - list_agents                     │ │
│  │  - FileTransport   │      │  - create_thread                   │ │
│  │  - MCPTransport    │      │  - send_message                    │ │
│  └────────────────────┘      │  - wait_for_mentions               │ │
│           │                  │  - close_thread                    │ │
│           │                  └────────────────────────────────────┘ │
│           ▼                                                         │
│  ┌────────────────────┐                                             │
│  │   CAMEL Agents     │                                             │
│  │   (Anemoi/agents/) │                                             │
│  │                    │                                             │
│  │  - planning_agent  │                                             │
│  │  - web_agent       │                                             │
│  │  - coding_agent    │                                             │
│  │  - critique_agent  │                                             │
│  └────────────────────┘                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📄 Documentation

See the [rispecs/](./rispecs/) directory for RISE specifications:

- **[app.spec.md](./rispecs/app.spec.md)** - Package overview and Python client API
- **[server.spec.md](./rispecs/server.spec.md)** - Kotlin MCP server documentation
- **[agents.spec.md](./rispecs/agents.spec.md)** - CAMEL agent specifications

---

## 📄 Original Publication

This is a fork of the original Anemoi project. Please cite the original work:

```bibtex
@article{ren2025anemoi,
  title={Anemoi: A Semi-Centralized Multi-agent Systems Based on Agent-to-Agent Communication MCP server from Coral Protocol},
  author={Ren, Xinxing and Forder, Caelum and Zang, Qianbo and Tahir, Ahsen and Georgio, Roman J. and Deb, Suman and Carroll, Peter and G\"{u}rcan, \"{O}nder and Guo, Zekun},
  journal={arXiv preprint arXiv:2508.17068},
  year={2025},
  url={https://arxiv.org/abs/2508.17068}
}
```

---

## 🔗 Links

- **Original Repository**: [Coral-Protocol/Anemoi](https://github.com/Coral-Protocol/Anemoi)
- **arXiv Paper**: [arXiv:2508.17068](https://arxiv.org/abs/2508.17068)
- **SimExp Integration**: [miadisabelle/simexp](https://github.com/miadisabelle/simexp)

---

## 📜 License

MIT License - See [LICENSE](./LICENSE) for details.




