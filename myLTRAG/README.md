# LTRAG

**Language Version**: [English](README.md) | [Chinese](README_CN.md)

LTRAG (Logic-enhanced Text Retrieval Augmented Generation) is a logic reasoning-based text retrieval augmented generation framework specifically designed for handling complex logical reasoning tasks.

## 📋 Table of Contents

- [LTRAG](#ltrag)
  - [📋 Table of Contents](#-table-of-contents)
  - [🎯 Project Overview](#-project-overview)
  - [📊 Datasets](#-datasets)
  - [🔧 Framework Source Code](#-framework-source-code)
    - [FOLIO Framework](#folio-framework)
    - [AR-LSAT Framework](#ar-lsat-framework)
  - [🚀 Installation](#-installation)
    - [Requirements](#requirements)
    - [Installation Steps](#installation-steps)
  - [⚙️ Configuration](#️-configuration)
    - [1. FastGPT Knowledge Base Configuration](#1-fastgpt-knowledge-base-configuration)
    - [2. Model API Configuration](#2-model-api-configuration)
    - [3. Knowledge Base ID Configuration](#3-knowledge-base-id-configuration)
  - [🎮 Usage](#-usage)
    - [FOLIO Framework Usage](#folio-framework-usage)
    - [LSAT Framework Usage](#lsat-framework-usage)
  - [📁 Project Structure](#-project-structure)
  - [📄 License](#-license)

## 🎯 Project Overview

The LTRAG framework combines Retrieval Augmented Generation (RAG) technology with logical reasoning capabilities, aiming to improve the performance of large language models on complex logical reasoning tasks. The framework supports two main logical reasoning datasets:

- **FOLIO**: First-Order Logic reasoning dataset
- **AR-LSAT**: Law School Admission Test logical reasoning questions

## 📊 Datasets

Knowledge base data for AR-LSAT and FOLIO are stored in the `dataset_example` folder:

- `FOLIO-fix.csv`: Fixed version of the FOLIO dataset
- `FOLIO-translation.csv`: Translated version of the FOLIO dataset
- `LSAT-fix.csv`: Fixed version of the LSAT dataset
- `LSAT-translation.csv`: Translated version of the LSAT dataset

## 🔧 Framework Source Code

> **Note**: Due to historical reasons, the two frameworks are not completely unified

### FOLIO Framework

**Environment Requirements**: Python 3.12

**Code Location**: `FOLIO_framework` folder

**Main Features**:
- Symbolic logic reasoning
- Error correction mechanism
- Multiple reasoning mode support

**Core Files**:
- `run_symbol.py`: Symbolic logic reasoning (without correction)
- `run_errfix.py`: Error correction based on symbolic reasoning
- `run_cot.py`: Chain-of-thought reasoning
- `run_standard.py`: Standard reasoning mode

### AR-LSAT Framework

**Environment Requirements**: Python 3.12

**Code Location**: `LSAT_framework` folder

- `run_symbol.py`: Symbolic logical reasoning (controls whether to apply fixes via the parameter `FIX_FLAG`)
- `run_cot.py`: Chain-of-thought reasoning (distinguishes between CoT and standard reasoning by modifying parts of the CoT prompt)


## 🚀 Installation

### Requirements

- Python 3.12+
- Dependencies listed in `FOLIO_framework/requirements.txt` and `LSAT_framework/requirements.txt`

### Installation Steps

1. Clone the repository:
```bash
git clone <repository-url>
cd LTRAG
```

2. Install dependencies:
```bash
cd FOLIO_framework
pip install -r requirements.txt
```

LSAT_framework is similar to the above.

## ⚙️ Configuration

### 1. FastGPT Knowledge Base Configuration

First, you need to construct a FastGPT knowledge base, then configure it in `FOLIO_framework/config/config.yaml`:

```yaml
fastgpt:
  url: "https://your-fastgpt-url"
  key: "fastgpt-your-api-key"
```

### 2. Model API Configuration

Configure various model API keys in `config.yaml`:

```yaml
sf:  # SiliconFlow
  api_key: "sk-your-api-key"
  base_url: "https://api.siliconflow.cn/v1"

qdd:  # QDD
  api_key: "sk-your-api-key"
  base_url: "https://35.aigcbest.top/v1"

deepseek:  # DeepSeek
  api_key: "sk-your-api-key"
  base_url: "https://api.deepseek.com"
```

### 3. Knowledge Base ID Configuration

Set the corresponding knowledge base ID in the agent configuration:

```yaml
agent:
  symbol:
    kb_id: "your-knowledge-base-id"
```

For LSAT, the above operations are performed in `config.ini`.

## 🎮 Usage

### FOLIO Framework Usage

1. **Symbolic Logic Reasoning** (without correction):
```bash
cd FOLIO_framework
python run_symbol.py
```

2. **Reasoning with Error Correction**:
```bash
cd FOLIO_framework
python run_errfix.py
```

3. **Chain-of-Thought Reasoning**:
```bash
cd FOLIO_framework
python run_cot.py
```

4. **Standard Reasoning Mode**:
```bash
cd FOLIO_framework
python run_standard.py
```

### LSAT Framework Usage

1. **Symbolic Reasoning** (controlled by setting the value of `FIX_FLAG`; set to `True` to apply fixes):

```bash
cd LSAT_framework
python run_symbol.py
```

2. **Chain-of-Thought Reasoning** (set the CoT prompt in `llm/agent/cot.py` to enable CoT reasoning; removing the CoT portion results in standard reasoning):

```bash
cd LSAT_framework
python run_cot.py
```

## 📁 Project Structure

```
LTRAG/
├── FOLIO_framework/           # FOLIO framework main directory
│   ├── config/               # Configuration files
│   │   ├── config.yaml      # Main configuration file
│   │   └── Settings.py      # Configuration loader
│   ├── data/                # Data directory
│   ├── llm/                 # Large language model related
│   │   ├── agent/          # Agent implementations
│   │   └── prompt/         # Prompt templates
│   ├── utils/              # Utility functions
│   ├── validator/          # Validator modules
│   ├── requirements.txt    # Python dependencies
│   └── run_*.py           # Run scripts
├── LSAT_framework/          # Main directory of the LSAT framework
│   ├── data/                # Data directory
│   ├── llm/                 # Related to large language models
│   │   ├── agent/           # Agent implementation
│   │   ├── base/        # Base model configuration
│   │   └── AgentBase.py # General model configuration
│   ├── utils/               # Utility functions, including solvers
│   ├── config.ini           # Configuration file
│   ├── requirements.txt     # Python dependencies
│   └── run_*.py             # Execution scripts
├── dataset_example/        # Example datasets
├── README.md              # English documentation
├── README_CN.md          # Chinese documentation
└── LICENSE               # License file
```

## 📄 License

This project is licensed under the corresponding open source license. See the [LICENSE](LICENSE) file for details.
