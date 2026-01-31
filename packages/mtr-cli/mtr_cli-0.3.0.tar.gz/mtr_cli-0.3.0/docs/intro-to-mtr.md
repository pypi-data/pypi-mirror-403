# mtr-cli：远程训练框架开发的工作流优化

## 背景与问题

在训练框架开发过程中，我们面临一个结构性矛盾：代码开发在本地进行，但功能验证必须在远程 GPU/NPU 集群上完成。这种"本地-远程"的割裂带来了三个核心问题。

### 网络与环境隔离

训练集群通常部署在内网或隔离环境中，无法直接访问外部网络。这导致依赖安装困难，而训练框架的依赖链本身就很复杂（PyTorch、DeepSpeed、Megatron 等）。环境配置耗时较长，一旦集群环境需要重建，成本很高。

### 多集群切换成本高

框架开发需要在 GPU 集群和 NPU 集群之间频繁切换验证。每次切换涉及代码同步、路径检查、环境确认等重复性操作。虽然启动方式统一使用 torchrun，但不同集群的节点地址、Python 环境路径等配置存在差异，需要反复适配。

### AI Agent 集成受限

训练任务在远程集群执行时，代码报错和异常堆栈输出在远程终端。AI Agent 无法直接访问这些信息，开发者需要手动复制粘贴错误内容，打断开发流程。Agent 无法实时感知执行状态，失去了即时辅助调试的能力。

## 解决方案：mtr-cli

mtr-cli 采用"本地开发，远程执行"的架构，在保持本地开发体验的同时，实现与远程集群的无缝集成。

### 核心功能

**智能代码同步**

支持 rsync（增量同步，速度快）和 SFTP（兼容性好）两种引擎。自动过滤 .git、__pycache__ 等无需同步的文件，避免大数据集误传。

**多集群配置管理**

通过配置文件集中管理多个训练集群：

```yaml
servers:
  gpu-cluster:
    host: "gpu-node-01"
    user: "dev"
    remote_dir: "/data/train-project"
    
  npu-cluster:
    host: "npu-node-01"
    user: "dev"
    remote_dir: "/home/dev/project"
```

集群切换通过命令行参数完成：

```bash
# GPU 集群执行
mtr -s gpu-cluster torchrun --nproc_per_node=8 train.py

# NPU 集群执行
mtr -s npu-cluster torchrun --nproc_per_node=8 train.py
```

**实时流式输出**

远程训练日志实时回显至本地终端，包括 loss 曲线、吞吐量、显存占用等关键指标。代码异常时，堆栈信息直接显示在本地，AI Agent 可即时获取并分析。支持交互式命令（vim、ipython 等）。

## 应用场景

**分布式训练框架开发**

在本地完成数据并行或模型并行逻辑的实现后，需要上多卡环境验证。传统流程涉及打包代码、scp 传输、ssh 登录、路径定位、执行运行等多个步骤。使用 mtr-cli 可简化为：

```bash
mtr torchrun --nproc_per_node=8 train.py
```

代码自动同步，远程执行，日志实时回传。

**跨硬件平台验证**

框架在 GPU 环境验证通过后，需要在 NPU 环境测试兼容性。传统方式需要重复环境配置和代码同步流程。使用 mtr-cli 只需切换服务器参数：

```bash
mtr -s npu-cluster torchrun --nproc_per_node=8 train.py
```

**即时调试**

训练脚本执行过程中发生异常，报错信息和堆栈直接输出在本地终端。AI Agent 实时获取错误内容，可立即进行分析和建议，无需手动复制粘贴。

## 收益分析

- **时间效率**：消除手动 scp/rsync 和反复 ssh 登录的操作 overhead
- **认知负担**：本地维护单一的代码库和配置，远程仅作为计算资源
- **AI 辅助能力**：Agent 可获取完整执行日志，恢复实时调试辅助
- **流程一致性**：屏蔽 GPU/NPU 后端差异，提供统一的开发体验

## 快速开始

### 安装

推荐使用 uv 安装（更快、更可靠）：

```bash
uv pip install mtr-cli
```

或使用 pip：

```bash
pip install mtr-cli
```

### 初始化配置

在项目目录下运行初始化命令，生成默认配置文件：

```bash
mtr --init
```

这会创建 `.mtr/config.yaml` 文件，包含默认配置模板。根据你的集群信息编辑该文件：

```yaml
servers:
  dev-gpu:
    host: "192.168.1.10"
    user: "dev"
    key_filename: "~/.ssh/id_rsa"
    remote_dir: "/data/project"
    sync: "rsync"
```

### 执行命令

配置完成后，在项目根目录执行：

```bash
# 使用默认服务器
mtr python train.py

# 指定服务器
mtr -s dev-gpu torchrun --nproc_per_node=8 train.py
```

完整 workflow：

```bash
# 1. 安装
uv pip install mtr-cli

# 2. 进入项目目录
cd my-project

# 3. 初始化配置
mtr --init
# 编辑 .mtr/config.yaml 添加服务器信息

# 4. 运行
mtr python train.py
```

### 常用参数

```bash
# 指定服务器
mtr -s gpu-cluster python train.py

# 跳过代码同步（仅执行命令）
mtr --no-sync python train.py

# 预览将要执行的命令（不实际运行）
mtr --dry-run python train.py

# 强制禁用 TTY（用于日志记录场景）
mtr --no-tty python train.py

# 启用日志记录
mtr --enable-log python train.py

# 从远程下载文件
mtr --get /remote/path/to/file.txt --to ./local/file.txt
```

---

mtr-cli 的目标是将远程训练的日常操作自动化，使开发者能够专注于框架本身，而非环境切换的繁琐流程。
