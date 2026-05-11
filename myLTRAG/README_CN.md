# LTRAG

**语言版本 / Language**: [中文](README_CN.md) | [English](README.md)

LTRAG (Logic-enhanced Text Retrieval Augmented Generation) 是一个基于逻辑推理的文本检索增强生成框架，专门用于处理复杂的逻辑推理任务。

## 📋 目录

- [LTRAG](#ltrag)
  - [📋 目录](#-目录)
  - [🎯 项目简介](#-项目简介)
  - [📊 数据集](#-数据集)
  - [🔧 框架源代码](#-框架源代码)
    - [FOLIO框架](#folio框架)
    - [AR-LSAT框架](#ar-lsat框架)
  - [🚀 安装说明](#-安装说明)
    - [环境要求](#环境要求)
    - [安装步骤](#安装步骤)
  - [⚙️ 配置说明](#️-配置说明)
    - [1. FastGPT知识库配置](#1-fastgpt知识库配置)
    - [2. 模型API配置](#2-模型api配置)
    - [3. 知识库ID配置](#3-知识库id配置)
  - [🎮 使用方法](#-使用方法)
    - [FOLIO框架使用](#folio框架使用)
    - [LSAT框架使用](#lsat框架使用)
  - [📁 项目结构](#-项目结构)
  - [📄 许可证](#-许可证)

## 🎯 项目简介

LTRAG框架结合了检索增强生成(RAG)技术和逻辑推理能力，旨在提高大语言模型在复杂逻辑推理任务上的表现。该框架支持两个主要的逻辑推理数据集：

- **FOLIO**: 一阶逻辑推理数据集
- **AR-LSAT**: 法学院入学考试逻辑推理题

## 📊 数据集

AR-LSAT和FOLIO的知识库数据存储在`dataset_example`文件夹中：

- `FOLIO-fix.csv`: FOLIO数据集的修复版本
- `FOLIO-translation.csv`: FOLIO数据集的翻译版本
- `LSAT-fix.csv`: LSAT数据集的修复版本
- `LSAT-translation.csv`: LSAT数据集的翻译版本

## 🔧 框架源代码

> **注意**: 由于历史原因，两个框架并没有完全统一

### FOLIO框架

**环境要求**: Python 3.12

**代码位置**: `FOLIO_framework`文件夹

**主要功能**:
- 符号逻辑推理
- 错误修复机制
- 多种推理模式支持

**核心文件**:
- `run_symbol.py`: 符号逻辑推理（不包含修复）
- `run_errfix.py`: 在符号推理基础上进行错误修复
- `run_cot.py`: 思维链推理
- `run_standard.py`: 标准推理模式

### AR-LSAT框架

- `run_symbol.py`: 符号逻辑推理（通过控制参数`FIX_FLAG`决定是否修复）
- `run_cot.py`: 思维链推理（通过在修改思维链提示词的部分语句区分思维链推理和标准推理）

## 🚀 安装说明

### 环境要求

- Python 3.12+
- 依赖包见 `FOLIO_framework/requirements.txt` 和 `LSAT_framework/requirements.txt`

### 安装步骤

1. 克隆项目：
```bash
git clone <repository-url>
cd LTRAG
```

2. 安装依赖：
```bash
cd FOLIO_framework
pip install -r requirements.txt
```

LSAT_framework类似。

## ⚙️ 配置说明

### 1. FastGPT知识库配置

首先需要构造FastGPT知识库，然后在`FOLIO_framework/config/config.yaml`中配置：

```yaml
fastgpt:
  url: "https://your-fastgpt-url"
  key: "fastgpt-your-api-key"
```

### 2. 模型API配置

在`config.yaml`中配置各种模型的API密钥：

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

### 3. 知识库ID配置

在agent配置中设置对应的知识库ID：

```yaml
agent:
  symbol:
    kb_id: "your-knowledge-base-id"
```

对于 LSAT，以上操作在`config.ini`进行。

## 🎮 使用方法

### FOLIO框架使用

1. **符号逻辑推理**（不包含修复）：
```bash
cd FOLIO_framework
python run_symbol.py
```

2. **带错误修复的推理**：
```bash
cd FOLIO_framework
python run_errfix.py
```

3. **思维链推理**：
```bash
cd FOLIO_framework
python run_cot.py
```

4. **标准推理模式**：
```bash
cd FOLIO_framework
python run_standard.py
```

### LSAT 框架使用

1. **符号逻辑推理**（通过设定`FIX_FLAG`的值决定是否修复，`True`为修复）：
```bash
cd LSAT_framework
python run_symbol.py
```

2. **思维链推理**（通过`llm/agent/cot.py`中设定思维链提示词实现思维链推理，去除思维链部分提示词实现标准推理）：
```bash
cd LSAT_framework
python run_cot.py
```

## 📁 项目结构

```
LTRAG/
├── FOLIO_framework/           # FOLIO框架主目录
│   ├── config/               # 配置文件
│   │   ├── config.yaml      # 主配置文件
│   │   └── Settings.py      # 配置加载器
│   ├── data/                # 数据目录
│   ├── llm/                 # 大语言模型相关
│   │   ├── agent/          # 智能体实现
│   │   └── prompt/         # 提示词模板
│   ├── utils/              # 工具函数
│   ├── validator/          # 验证器模块
│   ├── requirements.txt    # Python依赖
│   └── run_*.py           # 运行脚本
├── LSAT_framework/           # LSAT框架主目录
│   ├── data/                # 数据目录
│   ├── llm/                 # 大语言模型相关
│   │   ├── agent/          # 智能体实现
│   │   ├── base.py/          # 模型基础配置
│   │   └── AgentBase.py         # 通用模型配置
│   ├── utils/              # 工具函数，其中包含求解程序
│   ├── config.ini               # 配置文件
│   ├── requirements.txt    # Python依赖
│   └── run_*.py           # 运行脚本
├── dataset_example/        # 示例数据集
├── README.md              # 英文说明文档
├── README_CN.md          # 中文说明文档
└── LICENSE               # 许可证文件
```

## 📄 许可证

本项目采用相应的开源许可证，详见 [LICENSE](LICENSE) 文件。
