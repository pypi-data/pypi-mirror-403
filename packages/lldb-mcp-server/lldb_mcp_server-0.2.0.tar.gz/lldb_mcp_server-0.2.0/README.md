# LLDB MCP Server

语言: [中文](README.md) | [English](docs/README.en.md)

[![Version](https://img.shields.io/badge/version-0.2.0-blue.svg)](https://github.com/yourusername/lldb-mcp-server)
[![Python](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## 目录

- [概述](#概述)
- [核心特性](#核心特性)
- [环境要求](#环境要求)
- [安装与配置](#安装与配置)
- [MCP 配置](#mcp-配置)
- [运行服务器](#运行服务器)
- [工具列表](#工具列表)
- [使用示例](#使用示例)
- [测试](#测试)
- [故障排除](#故障排除)
- [开发](#开发)
- [文档](#文档)

## 概述

LLDB MCP Server 是一个基于 [Model Context Protocol (MCP)](https://modelcontextprotocol.io) 的调试服务器，通过 40 个 MCP 工具暴露 LLDB 调试功能，支持 AI 驱动的 C/C++ 应用程序交互式调试。

**核心架构：** 多会话设计，每个调试会话拥有独立的 `SBDebugger`、`SBTarget` 和 `SBProcess` 实例，支持并发调试。

**适用场景：**
- Claude Code / Claude Desktop 的 AI 辅助调试
- 自动化调试脚本
- 崩溃分析和安全漏洞检测
- 远程调试和核心转储分析

## 核心特性

### 🔧 40 个调试工具

| 类别 | 工具数 | 功能 |
|------|--------|------|
| **会话管理** | 3 | 创建、终止、列出调试会话 |
| **目标控制** | 6 | 加载二进制、启动/附加进程、重启、发送信号、加载核心转储 |
| **断点** | 4 | 设置、删除、列出、更新断点（支持符号、文件:行号、地址、条件） |
| **执行控制** | 5 | 继续、暂停、单步进入/跨越/跳出 |
| **检查** | 6 | 线程、栈帧、堆栈跟踪、表达式求值 |
| **内存操作** | 2 | 内存读/写（支持十六进制和 ASCII 视图） |
| **观察点** | 3 | 设置、删除、列出内存观察点 |
| **寄存器** | 2 | 读取、写入寄存器 |
| **符号与模块** | 2 | 符号搜索、已加载模块列表 |
| **高级工具** | 4 | 事件轮询、原始 LLDB 命令、反汇编、会话记录 |
| **安全分析** | 2 | 崩溃可利用性分析、可疑函数检测 |
| **核心转储** | 2 | 加载/创建核心转储 |

### ✨ 关键能力

- **多会话调试**：并发运行多个独立调试会话，每个会话隔离状态
- **事件驱动架构**：后台事件收集，非阻塞轮询（状态变化、断点命中、stdout/stderr）
- **安全分析**：崩溃可利用性分类、危险函数检测（strcpy、sprintf 等）
- **会话记录**：自动记录所有命令和输出，带时间戳，可通过 `lldb_getTranscript` 检索
- **灵活断点**：支持符号、文件:行号、地址断点，条件断点，启用/禁用
- **内存调试**：内存读/写、观察点监控（读/写访问）

## 环境要求

### ✅ 推荐配置（Homebrew LLVM + Python 3.13）

**关键问题：** LLDB 与 FastMCP 的 Python 版本冲突
- **Xcode LLDB**: 仅支持 Python 3.9.6
- **FastMCP**: 需要 Python ≥3.10

**解决方案：** 使用 Homebrew LLVM，其 LLDB 支持现代 Python 版本（3.10+）

**系统要求：**
- macOS（任何版本）
- Homebrew（`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`）
- `uv` 包管理器：`brew install uv`（可选，推荐）

## 安装与配置

### 步骤 1：安装 LLVM 和 Python 3.13

```bash
# 安装 LLVM（包含支持现代 Python 的 LLDB）
brew install llvm

# 安装 Python 3.13
brew install python@3.13

# 验证安装
/usr/local/opt/python@3.13/bin/python3.13 -V
# 期望输出: Python 3.13.x

$(brew --prefix llvm)/bin/lldb --version
# 期望输出: lldb version ...
```

### 步骤 2：配置 Shell 环境

在 `~/.zshrc`（或 `~/.bashrc`）中添加：

```bash
# 将 Homebrew LLVM 添加到 PATH（优先于系统 LLDB）
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

重新加载配置：

```bash
source ~/.zshrc  # 或 source ~/.bashrc
hash -r          # 清除命令缓存
```

验证 LLDB 来自 Homebrew：

```bash
which lldb
# 期望输出: /usr/local/opt/llvm/bin/lldb（不是 /usr/bin/lldb）

lldb --version
lldb -P  # 查看 LLDB Python 路径
```

### 步骤 3：创建 Python 3.13 虚拟环境

```bash
# 删除旧的 venv（如果存在）
deactivate 2>/dev/null || true
rm -rf .venv

# 使用 Python 3.13 创建 venv
/usr/local/opt/python@3.13/bin/python3.13 -m venv .venv
source .venv/bin/activate

# 验证 Python 版本
python -c "import sys; print(sys.version)"
# 期望输出: Python 3.13.x
```

### 步骤 4：将 LLDB Python 路径添加到虚拟环境

此步骤使 LLDB 模块永久可用，无需 PYTHONPATH：

```bash
# 获取 LLDB Python 模块路径
LLDB_PY_PATH="$(lldb -P)"
echo "LLDB Python 路径: $LLDB_PY_PATH"

# 获取 venv 的 site-packages 目录
SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
echo "Site packages: $SITE_PKGS"

# 将 LLDB 路径写入 .pth 文件（永久 Python 路径配置）
echo "$LLDB_PY_PATH" > "$SITE_PKGS/lldb.pth"
```

### 步骤 5：验证 LLDB 导入（无需 PYTHONPATH）

```bash
python - <<'PY'
import lldb
print("lldb 模块:", lldb.__file__)
print("lldb 版本:", lldb.SBDebugger.GetVersionString())

# 验证内部模块
import lldb._lldb as m
print("lldb._lldb:", m.__file__)
PY
```

期望输出：

```
lldb 模块: /usr/local/opt/llvm/lib/python3.13/site-packages/lldb/__init__.py
lldb 版本: lldb-<版本>
lldb._lldb: /usr/local/opt/llvm/lib/python3.13/site-packages/lldb/_lldb.cpython-313-darwin.so
```

### 步骤 6：安装项目依赖

```bash
# 使用 uv 安装（推荐，速度更快）
uv pip install -e ".[dev]"

# 或使用 pip
pip install -e ".[dev]"

# 验证 FastMCP 已安装
python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"
```

### 步骤 7：最终验证

```bash
# 测试所有导入
python -c "
import lldb
import fastmcp
print('✅ LLDB 版本:', lldb.SBDebugger.GetVersionString())
print('✅ FastMCP 版本:', fastmcp.__version__)
print('✅ 环境配置完成！')
"
```

### 完整验证检查清单

**1. 验证 LLDB 来自 Homebrew**

```bash
which lldb
# 期望输出: /usr/local/opt/llvm/bin/lldb

lldb --version
# 期望输出: lldb version ...
```

**2. 验证 Python 版本**

```bash
python --version
# 期望输出: Python 3.13.x
```

**3. 验证 LLDB 导入**

```bash
python -c "import lldb; print(lldb.SBDebugger.GetVersionString())"
# 期望输出: lldb-<版本>
```

**4. 验证 FastMCP 安装**

```bash
python -c "import fastmcp; print('FastMCP:', fastmcp.__version__)"
# 期望输出: FastMCP: <版本号>
```

## MCP 配置

### 方式一：uvx（推荐 ⭐）

**uvx** 是最简单的安装方式，无需手动配置 Python 环境。

**前置条件：**
```bash
# 安装 Homebrew LLVM（提供 LLDB）
brew install llvm

# 安装 uv（提供 uvx 命令）
brew install uv

# 将 LLVM 添加到 PATH（添加到 ~/.zshrc）
export PATH="$(brew --prefix llvm)/bin:$PATH"
```

**配置文件位置：**
- **Claude Code**: 项目根目录下的 `.mcp.json`
- **Claude Desktop**: `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）

**配置内容：**

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**优点：**
- 无需手动创建虚拟环境
- 无需手动安装 Python 依赖
- uvx 自动管理包和环境

**如果 LLDB 自动检测失败，可设置 LLDB_PYTHON_PATH：**

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "uvx",
      "args": ["lldb-mcp-server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1",
        "LLDB_PYTHON_PATH": "/opt/homebrew/opt/llvm/lib/python3.13/site-packages"
      }
    }
  }
}
```

### 方式二：本地开发（使用虚拟环境）

适用于本地开发或需要自定义配置的场景。

**配置内容：**

```json
{
  "mcpServers": {
    "lldb-debugger": {
      "command": "/absolute/path/to/project/.venv/bin/python",
      "args": ["-m", "lldb_mcp_server.fastmcp_server"],
      "env": {
        "LLDB_MCP_ALLOW_LAUNCH": "1",
        "LLDB_MCP_ALLOW_ATTACH": "1"
      }
    }
  }
}
```

**⚠️ 重要说明：**
- **必须使用绝对路径**：`command` 字段必须是虚拟环境中 Python 的绝对路径
- **不要使用 `python3`**：系统 Python 无法访问虚拟环境的包
- **示例绝对路径**：`/Users/yourname/Projects/lldb-mcp-server/.venv/bin/python`

**快速获取绝对路径：**

```bash
# 在项目目录下运行
source .venv/bin/activate
which python
# 复制输出的路径到 .mcp.json 的 command 字段
```

### 安全配置（环境变量）

| 环境变量 | 作用 | 默认值 |
|---------|------|--------|
| `LLDB_MCP_ALLOW_LAUNCH=1` | 允许启动新进程 | 禁用 |
| `LLDB_MCP_ALLOW_ATTACH=1` | 允许附加到现有进程 | 禁用 |

## 运行服务器

### Stdio 模式（Claude Code/Claude Desktop）

```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server
```

### HTTP 模式（测试和开发）

```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765
```

### 开发模式（自动重载）

```bash
LLDB_MCP_ALLOW_LAUNCH=1 \
  fastmcp dev src/lldb_mcp_server/fastmcp_server.py
```

## 工具列表

完整的 40 个 MCP 工具：

### 会话管理（3 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_initialize` | 创建新调试会话 | - |
| `lldb_terminate` | 终止调试会话 | `sessionId` |
| `lldb_listSessions` | 列出所有活动会话 | - |

### 目标控制（6 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_createTarget` | 加载可执行文件 | `sessionId`, `file` |
| `lldb_launch` | 启动进程 | `sessionId`, `args`, `env` |
| `lldb_attach` | 附加到进程 | `sessionId`, `pid`/`name` |
| `lldb_restart` | 重启进程 | `sessionId` |
| `lldb_signal` | 发送信号 | `sessionId`, `signal` |
| `lldb_loadCore` | 加载核心转储 | `sessionId`, `corePath`, `executablePath` |

### 断点（4 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_setBreakpoint` | 设置断点 | `sessionId`, `symbol`/`file:line`/`address` |
| `lldb_deleteBreakpoint` | 删除断点 | `sessionId`, `breakpointId` |
| `lldb_listBreakpoints` | 列出断点 | `sessionId` |
| `lldb_updateBreakpoint` | 修改断点 | `sessionId`, `breakpointId`, `enabled`, `condition` |

### 执行控制（5 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_continue` | 继续执行 | `sessionId` |
| `lldb_pause` | 暂停执行 | `sessionId` |
| `lldb_stepIn` | 单步进入函数 | `sessionId` |
| `lldb_stepOver` | 单步跨越函数 | `sessionId` |
| `lldb_stepOut` | 单步跳出函数 | `sessionId` |

### 检查（6 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_threads` | 列出线程 | `sessionId` |
| `lldb_frames` | 列出栈帧 | `sessionId`, `threadId`（可选） |
| `lldb_stackTrace` | 获取堆栈跟踪 | `sessionId`, `threadId`（可选） |
| `lldb_selectThread` | 选择线程 | `sessionId`, `threadId` |
| `lldb_selectFrame` | 选择栈帧 | `sessionId`, `frameIndex` |
| `lldb_evaluate` | 求值表达式 | `sessionId`, `expression`, `frameIndex`（可选） |

### 内存操作（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_readMemory` | 读取内存 | `sessionId`, `address`, `size` |
| `lldb_writeMemory` | 写入内存 | `sessionId`, `address`, `data` |

### 观察点（3 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_setWatchpoint` | 设置观察点 | `sessionId`, `address`, `size`, `read`, `write` |
| `lldb_deleteWatchpoint` | 删除观察点 | `sessionId`, `watchpointId` |
| `lldb_listWatchpoints` | 列出观察点 | `sessionId` |

### 寄存器操作（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_readRegisters` | 读取寄存器 | `sessionId`, `threadId`（可选） |
| `lldb_writeRegister` | 写入寄存器 | `sessionId`, `name`, `value` |

### 符号与模块（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_searchSymbol` | 搜索符号 | `sessionId`, `pattern`, `module`（可选） |
| `lldb_listModules` | 列出已加载模块 | `sessionId` |

### 高级工具（4 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_pollEvents` | 轮询调试事件 | `sessionId`, `limit` |
| `lldb_command` | 执行原始 LLDB 命令 | `sessionId`, `command` |
| `lldb_getTranscript` | 获取会话记录 | `sessionId` |
| `lldb_disassemble` | 反汇编代码 | `sessionId`, `address`, `count` |

### 安全分析（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_analyzeCrash` | 分析崩溃 | `sessionId` |
| `lldb_getSuspiciousFunctions` | 查找可疑函数 | `sessionId` |

### 核心转储（2 个工具）

| 工具 | 描述 | 参数 |
|------|------|------|
| `lldb_loadCore` | 加载核心转储 | `sessionId`, `corePath`, `executablePath` |
| `lldb_createCoredump` | 创建核心转储 | `sessionId`, `path` |

**详细工具文档：** 参见 [dev_docs/FEATURES.md](dev_docs/FEATURES.md)

## 使用示例

### 示例 1：基本调试流程（Claude Code）

在 Claude Code 中，配置好 MCP 后，可以直接使用自然语言调试：

```
User: "调试 examples/client/c_test/hello/hello 程序"

Claude 会自动：
1. 调用 lldb_initialize 创建会话
2. 调用 lldb_createTarget 加载二进制
3. 调用 lldb_setBreakpoint 在 main 设置断点
4. 调用 lldb_launch 启动进程
5. 调用 lldb_pollEvents 检查断点命中
6. 调用 lldb_stackTrace 显示堆栈
```

### 示例 2：崩溃分析

```
User: "这个程序崩溃了，帮我分析原因"

Claude 会：
1. 调用 lldb_pollEvents 获取崩溃事件
2. 调用 lldb_analyzeCrash 分析崩溃类型
3. 调用 lldb_stackTrace 显示崩溃时堆栈
4. 调用 lldb_readRegisters 查看寄存器状态
5. 调用 lldb_getSuspiciousFunctions 检测危险函数
6. 提供修复建议
```

### 示例 3：HTTP 模式测试（手动调用）

**启动服务器（终端 1）：**

```bash
LLDB_MCP_ALLOW_LAUNCH=1 LLDB_MCP_ALLOW_ATTACH=1 \
  .venv/bin/python -m lldb_mcp_server.fastmcp_server \
  --transport http --host 127.0.0.1 --port 8765
```

**准备测试程序：**

```bash
cd examples/client/c_test/hello
cc -g -O0 -Wall -Wextra -o hello hello.c
cd ../../../..
```

**运行示例客户端（终端 2）：**

```bash
TARGET_BIN=$(pwd)/examples/client/c_test/hello/hello \
MCP_HOST=127.0.0.1 \
MCP_PORT=8765 \
  .venv/bin/python examples/client/run_debug_flow.py
```

**或使用 curl 手动调用：**

```bash
# 创建会话
curl -X POST http://127.0.0.1:8765/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"lldb_initialize","arguments":{}}'

# 创建目标（替换 <SESSION_ID>）
curl -X POST http://127.0.0.1:8765/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"lldb_createTarget","arguments":{"sessionId":"<SESSION_ID>","file":"./examples/client/c_test/hello/hello"}}'

# 启动进程
curl -X POST http://127.0.0.1:8765/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"lldb_launch","arguments":{"sessionId":"<SESSION_ID>","args":[]}}'

# 轮询事件
curl -X POST http://127.0.0.1:8765/tools/call \
  -H "Content-Type: application/json" \
  -d '{"name":"lldb_pollEvents","arguments":{"sessionId":"<SESSION_ID>","limit":10}}'
```

### 事件类型

通过 `lldb_pollEvents` 可获取的事件类型：

| 事件类型 | 描述 |
|---------|------|
| `targetCreated` | 目标已创建 |
| `processLaunched` | 进程已启动 |
| `processAttached` | 已附加到进程 |
| `processStateChanged` | 进程状态变化（running/stopped/exited 等） |
| `breakpointSet` | 断点已设置 |
| `breakpointHit` | 断点命中（包含线程/栈帧信息） |
| `stdout` | 进程标准输出 |
| `stderr` | 进程标准错误输出 |

## 测试

### 运行所有测试

```bash
# 运行所有单元测试
pytest tests/ -v

# 运行端到端测试
pytest tests/e2e/ -v

# 运行带覆盖率的测试
pytest tests/ --cov=src/lldb_mcp_server --cov-report=html
```

### 编译测试程序

```bash
# 编译所有测试程序（8 种 bug 类型）
cd examples/client/c_test
./build_all.sh

# 或单独编译
cd hello
cc -g -O0 -Wall -Wextra -o hello hello.c
```

**可用测试程序：**
- `hello/` - 基本 Hello World
- `segfault/` - 段错误（空指针解引用）
- `buffer_overflow/` - 缓冲区溢出
- `use_after_free/` - 释放后使用
- `double_free/` - 双重释放
- `stack_overflow/` - 栈溢出
- `integer_overflow/` - 整数溢出
- `format_string/` - 格式化字符串漏洞

## 故障排除

### 问题 1：`ModuleNotFoundError: No module named 'lldb_mcp_server'`

**原因：** `.mcp.json` 使用了系统 Python 而不是虚拟环境的 Python。

**解决方案：** 更新 `.mcp.json` 的 `command` 字段为虚拟环境 Python 的绝对路径：

```bash
# 获取绝对路径
source .venv/bin/activate
which python
# 复制输出路径到 .mcp.json 的 command 字段
```

### 问题 2：`No module named lldb`

**原因：** LLDB Python 绑定未正确配置。

**解决方案：**

```bash
# 1. 验证 LLDB 来自 Homebrew
which lldb
# 应该是: /usr/local/opt/llvm/bin/lldb

# 2. 检查 .pth 文件
SITE_PKGS="$(python -c 'import site; print(site.getsitepackages()[0])')"
cat "$SITE_PKGS/lldb.pth"
# 应该输出 LLDB Python 路径

# 3. 如果不存在，重新创建
LLDB_PY_PATH="$(lldb -P)"
echo "$LLDB_PY_PATH" > "$SITE_PKGS/lldb.pth"

# 4. 验证导入
python -c "import lldb; print(lldb.SBDebugger.GetVersionString())"
```

### 问题 3：LLDB 仍来自 Xcode（`/usr/bin/lldb`）

**原因：** PATH 配置未生效。

**解决方案：**

```bash
# 1. 检查 ~/.zshrc 或 ~/.bashrc 是否添加了 PATH
cat ~/.zshrc | grep llvm

# 2. 如果没有，添加
echo 'export PATH="$(brew --prefix llvm)/bin:$PATH"' >> ~/.zshrc

# 3. 重新加载并清除缓存
source ~/.zshrc
hash -r

# 4. 重新打开终端验证
which lldb
```

### 问题 4：FastMCP 导入失败

**解决方案：**

```bash
# 重新安装依赖
uv pip install -e ".[dev]"

# 验证 Python 版本 ≥3.10
python --version
```

**更多故障排除：** 参见 [dev_docs/TROUBLESHOOTING.md](dev_docs/TROUBLESHOOTING.md)

## 开发

### 代码规范

```bash
# 运行 linting
ruff check src/

# 格式化代码
ruff format src/

# 类型检查
mypy src/
```

### 项目结构

```
lldb-mcp-server/
├── src/lldb_mcp_server/
│   ├── fastmcp_server.py      # MCP 入口点
│   ├── session/
│   │   └── manager.py          # SessionManager（核心）
│   ├── tools/                  # 9 个工具模块
│   │   ├── session.py          # 会话管理
│   │   ├── target.py           # 目标控制
│   │   ├── breakpoints.py      # 断点
│   │   ├── execution.py        # 执行控制
│   │   ├── inspection.py       # 检查
│   │   ├── memory.py           # 内存操作
│   │   ├── watchpoints.py      # 观察点
│   │   ├── registers.py        # 寄存器
│   │   └── advanced.py         # 高级工具
│   └── analysis/
│       └── exploitability.py   # 崩溃分析
├── examples/client/
│   ├── c_test/                 # 8 种 bug 类型的测试程序
│   └── run_debug_flow.py       # HTTP 客户端示例
├── tests/                      # 单元测试
├── tests/e2e/                  # 端到端测试
├── skills/lldb-debugger/       # Claude Code skill（包含交互式调试指南）
├── dev_docs/                   # 设计和功能文档
├── .mcp.json                   # Stdio 配置（生产）
├── .mcp.json.http              # HTTP 配置（开发）
└── README.md                   # 本文件
```

### 添加新功能

在添加新功能时：

1. 更新 `dev_docs/FEATURES.md` 添加工具摘要
2. 在 `dev_docs/features/<category>.md` 添加详细文档
3. 在 `tests/` 添加单元测试
4. 在 `tests/e2e/` 添加端到端测试（如适用）

**详细设计文档：** 参见 [dev_docs/DESIGN.md](dev_docs/DESIGN.md)

## 文档

| 文档 | 描述 |
|------|------|
| [FEATURES.md](dev_docs/FEATURES.md) | 40 个工具的完整列表和参数 |
| [DESIGN.md](dev_docs/DESIGN.md) | 架构设计和实现细节 |
| [TROUBLESHOOTING.md](dev_docs/TROUBLESHOOTING.md) | 常见问题和解决方案 |
| [INTERACTIVE_DEBUGGING.md](skills/lldb-debugger/INTERACTIVE_DEBUGGING.md) | 交互式调试工作流程和决策树 |
| [TESTING_GUIDE.md](examples/client/c_test/TESTING_GUIDE.md) | 测试程序使用指南 |

**功能详细文档**（`dev_docs/features/`）：
- [01-session-management.md](dev_docs/features/01-session-management.md)
- [02-target-control.md](dev_docs/features/02-target-control.md)
- [03-breakpoints.md](dev_docs/features/03-breakpoints.md)
- [04-execution-control.md](dev_docs/features/04-execution-control.md)
- [05-inspection.md](dev_docs/features/05-inspection.md)
- [06-memory-operations.md](dev_docs/features/06-memory-operations.md)
- [07-watchpoints.md](dev_docs/features/07-watchpoints.md)
- [08-advanced-tools.md](dev_docs/features/08-advanced-tools.md)
- [09-security-analysis.md](dev_docs/features/09-security-analysis.md)
- [10-register-operations.md](dev_docs/features/10-register-operations.md)
- [11-symbol-search.md](dev_docs/features/11-symbol-search.md)
- [12-module-management.md](dev_docs/features/12-module-management.md)
- [13-core-dump-support.md](dev_docs/features/13-core-dump-support.md)

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 贡献

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 致谢

- [LLDB](https://lldb.llvm.org/) - 强大的调试器
- [FastMCP](https://github.com/jlowin/fastmcp) - MCP 框架
- [Anthropic](https://www.anthropic.com/) - Model Context Protocol
- [Homebrew](https://brew.sh/) - macOS 包管理器

## 联系方式

- Issues: [GitHub Issues](https://github.com/yourusername/lldb-mcp-server/issues)
- Discussions: [GitHub Discussions](https://github.com/yourusername/lldb-mcp-server/discussions)

---

**版本：** 0.2.0
**最后更新：** 2026-01-25
