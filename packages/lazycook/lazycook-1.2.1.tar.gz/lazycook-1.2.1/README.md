# 🧠 LazyCook — Multi-Agent AI Assistant

### Version: 1.2.0
### Author: **Hitarth Trivedi and Harsh Bhatt**
### Language: **Python 3.10+**  
### Powered by: **Google Gemini 2.5 Flash**

---

## 📘 Overview

**LazyCook** is an **autonomous multi-agent conversational assistant** that intelligently processes user queries, manages documents, tracks tasks, and maintains context across sessions.  
It leverages **Google Gemini API** and a **four-agent architecture** — *Generator*, *Analyzer*, *Optimizer*, and *Validator* — to deliver accurate, coherent, and high-quality responses through iterative reasoning.

LazyCook is ideal for developers, researchers, and productivity users who want an intelligent assistant capable of local storage, contextual memory, and automated document analysis — all inside a single Python app.

---

## ⚙️ Core Features

| Feature                          | Description                                                                                              |
|----------------------------------|----------------------------------------------------------------------------------------------------------|
| 🤖 **Multi-Agent System**        | Four specialized AI agents collaborate to generate, analyze, optimize, and validate every response.      |
| 🧠 **Smart Context Management**  | Maintains conversation context from current and past sessions (default 70, configurable). |
| 📄 **Document Processing**       | Supports `.pdf`, `.docx`, `.txt`, `.md`, and `.csv` files (default 50 docs, configurable). |
| 📊 **Smart Visualization**       | Automatically generates insightful graphs and plots for data-heavy queries.                               |
| 🎯 **Intelligent Query Routing** | Adjusts API usage automatically based on query complexity (Simple / Medium / Complex).                   |
| 📊 **Quality Metrics**           | Evaluates completeness, accuracy, and polish with weighted scoring.                                      |
| 💾 **Persistent Storage**        | Stores all data — chats, tasks, documents — as JSON files for easy access.                               |
| 📦 **Export Options**            | Export past conversations in `.txt`, `.md`, or `.json` formats.                                          |
| 🔧 **Maintenance Tools**         | Clear old chats, documents, and caches for optimal performance.                                          |
| 🧮 **Real-Time Logging**         | Colorful terminal output and progress visualization using `rich`.                                        |

---

## 🧩 System Architecture

```
User Query
    ↓
AutonomousMultiAgentAssistant
├── TextFileManager         # File & context storage
├── MultiAgentSystem        # Core orchestrator
│     ├── Generator Agent   # Draft creation
│     ├── Analyzer Agent    # Error detection
│     ├── Optimizer Agent   # Refinement
│     └── Validator Agent   # Final verification
├── QueryComplexityAnalyzer # Routing logic
└── QualityMetrics          # Evaluation engine
```

---

## 🚀 Installation & Setup

### 1. Prerequisites
- Python **3.10+**
- Google Gemini API key
- Internet connection

### 2. Install Dependencies
```bash
pip install google-generativeai rich PyPDF2 python-docx matplotlib pandas seaborn numpy
```

### 3. Run the Application

```bash
export GEMINI_API_KEY="your-api-key"
python -m lazycook
```

---

## 💬 Example Usage

```python
import lazycook
import asyncio

config = lazycook.create_assistant("your-api-key", conversation_limit=9, document_limit=1)

# Run CLI
asyncio.run(config.run_cli())
```

---

## 📂 Directory Structure

```
project/
├── lazycook.py                    # Main application
├── multi_agent_data/              # Stored data
│   ├── conversations.json
│   ├── tasks.json
│   ├── documents.json
│   └── new_convo.json
├── exported_chats/                # Exported chat files
└── multi_agent_assistant.log      # Application logs
```

---

## 🧠 Multi-Agent Roles

| Agent         | Role       | Purpose                                                   |
|---------------|------------|-----------------------------------------------------------|
| **Generator** | Creative   | Drafts the initial solution using context and user query. |
| **Analyzer**  | Critical   | Detects logical or factual errors and missing details.    |
| **Optimizer** | Refinement | Enhances clarity, formatting, and completeness.           |
| **Validator** | Assurance  | Final accuracy and factual verification.                  |

---

## ⚡ Quality Scoring System

| Metric                 | Weight | Description                                     |
|------------------------|--------|-------------------------------------------------|
| **Completeness**       | 40%    | Ensures all query points are addressed.         |
| **Accuracy**           | 40%    | Checks factual and logical correctness.         |
| **Length**             | 20%    | Evaluates concise vs. detailed balance.         |
| **Structure & Polish** | —      | Considers clarity, readability, and formatting. |

**Tiers:**

* 🔥 **Excellent:** ≥ 0.95
* ✅ **Very Good:** 0.90–0.94
* 📈 **Good:** 0.85–0.89
* ⚠️ **Acceptable:** 0.75–0.84

---

## 🛠 Maintenance Commands

| Command       | Function                              |
|---------------|---------------------------------------|
| `maintenance` | Access cleanup, reset tools, and **upload documents** (via Manage Documents) |
| `docs`        | View current uploaded documents       |
| `download`    | Export chat history                   |
| `quality`     | View session quality metrics          |
| `stats`       | View performance statistics           |
| `context`     | Preview current conversation context  |
| `quit`        | Exit application safely               |

---

## 🧾 Logging Example

```
2025-10-31 13:22:51 - INFO - Query classified as: complex
2025-10-31 13:22:52 - INFO - Iteration 1: Objective=0.913, Subjective=0.867, Combined=0.890
2025-10-31 13:22:52 - INFO - ✓ Quality threshold met: 0.890 >= 0.880
```

---

## 🧱 Future Enhancements

* VERSION THAT CAN BE DOWNLOADED AND USED WITHOUT API-KEY(using gemma2.0)
* Multi-model fusion (Gemini + LLaMA)
* Long-term vector memory
* Web-based dashboard and analytics
* Speech-to-text and voice integration

---

## 🧰 Troubleshooting

| Issue                 | Possible Fix                                    |
|-----------------------|-------------------------------------------------|
| API Connection Failed | Verify `GEMINI_API_KEY` and internet access.    |
| Context Not Loading   | Check user ID consistency and clear cache.      |
| Document Upload Error | Ensure file < 5MB and supported format.         |
| Low Quality Scores    | Add context or documents for deeper responses.  |
| Slow Responses        | Reduce context size or clean old conversations. |

---

## 📜 License

Copyright (c) 2025 Harsh Bhatt, Hitarth Trivedi. All Rights Reserved.

This software and associated documentation files (the "Software") may not be
copied, modified, merged, published, distributed, sublicensed, and/or sold
without explicit written permission from the copyright holder.

---

## 💡 Credits

* **AI Framework:** Google Gemini API
* **Terminal UI:** `rich`
* **PDF Handling:** `PyPDF2`
* **DOCX Handling:** `python-docx`
* **Visualization:** `matplotlib`, `seaborn`, `pandas`
* **Developer:** Hitarth Trivedi, Harsh Bhatt

> *Let it cook 🔥*