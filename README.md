# Jager FOMO Hunt - 自动化狙击机器人

![GitHub top language](https://img.shields.io/github/languages/top/YourUsername/YourRepoName?style=flat-square) ![GitHub last commit](https://img.shields.io/github/last-commit/YourUsername/YourRepoName?style=flat-square)

这是一个专为 Jager FOMO Hunt 游戏设计的自动化 Python 机器人。它能够 7x24 小时不间断地监控游戏倒计时，并在最关键的时刻自动执行购买操作，旨在成为倒计时结束前的最后一位购票者。

<img width="297" height="112" alt="image" src="https://github.com/user-attachments/assets/7008c803-978e-4af8-b350-60820a33edc7" />



---

## 核心功能

*   **实时倒计时监控**: 使用 Playwright 驱动无头浏览器，精准抓取官网的实时倒计时数据。
*   **智能狙击策略**: 在预设的时间阈值内（例如最后11秒），自动触发交易，争夺最终大奖。
*   **动态 Gas 优先权**: 自动检测当前 BSC 网络的 Gas Price，并以一个有竞争力的更高价格提交交易，确保在“Gas 战争”中获得优先打包权，最大化狙击成功率。
*   **所有权检查**: 在出价前，会先通过智能合约查询当前的第一名是否是自己，避免重复购买和不必要的资金浪费。
*   **Telegram 实时通知**: 机器人的所有关键状态——启动、心跳、狙击成功、狙击失败、异常和恢复——都会通过 Telegram Bot 实时推送到您的指定频道。
*   **高可用性与自愈能力**:
    *   **守护进程**: 即使脚本因任何原因崩溃，外层的守护进程也会在清理现场后自动重启脚本。
    *   **内存泄漏防护**: 在每次重启前，会自动清理残留的浏览器进程，从根本上防止因内存泄漏导致的服务器卡死。
    *   **页面恢复**: 当目标网页卡死或加载失败时，机器人会尝试创建全新的浏览器页面进行自愈，而不是简单地刷新。

## Telegram 通知示例

机器人会为您提供清晰、实时的战况更新，让您对它的一举一动都了如指掌：

<img width="404" height="897" alt="ScreenShot_2025-11-10_154420_950" src="https://github.com/user-attachments/assets/3d5bc74b-7c4f-4e6e-bd2a-40633d905525" />


---

## 部署指南

### 1. 服务器要求

为保证机器人稳定运行，推荐使用满足以下最低配置的云服务器 (VPS)：

*   **CPU**: 2 核心
*   **内存 (RAM)**: 4 GB
*   **操作系统**: Ubuntu 20.04 LTS 或更高版本
*   **网络**: 稳定的出站网络连接

### 2. 部署步骤

#### 2.1 克隆仓库
通过 SSH 登录到您的服务器，并克隆此项目仓库。`fomo_sniper.py` 和 `abi.json` 文件都已包含在内。

```bash
# 首先安装 git (如果尚未安装)
sudo apt update
sudo apt install git -y

# 克隆您的仓库 (请替换为您的仓库URL)
git clone https://github.com/Zisaac52/jager-fomo-sniper

# 进入项目目录
cd jager-fomo-sniper
```

#### 2.2 安装环境依赖
执行以下命令安装 Python 环境、依赖库及浏览器驱动。

```bash
# 安装 pip 和 tmux
sudo apt install python3-pip tmux -y

# 安装 Python 依赖库
pip install requests web3 playwright

# 安装 Playwright 浏览器驱动
playwright install
```

#### 2.3 (重要) 配置脚本
本项目的所有配置项都集中在 `fomo_sniper.py` 脚本的顶部。在运行前，您必须手动编辑此文件并填入您的个人信息。

```bash
# 使用 nano 编辑器打开脚本文件
nano fomo_sniper.py
```

使用键盘方向键移动到文件顶部，找到**第一部分的配置区域**，并**填入您自己的真实信息**：

```python
# ==============================================================================
# 1. 脚本配置
# ⚠️ 请务必在此处填入你的真实信息
# ==============================================================================
# BSC RPC 节点地址
BSC_RPC_URL = "https://bsc-dataseed.binance.org/" # 推荐使用 QuickNode 等私有节点

# 你的热钱包私钥 (请确保去掉开头的 "0x")
BOT_PRIVATE_KEY = "你的热钱包私钥" 

# 游戏合约地址 
FOMO_CONTRACT_ADDRESS = "0x9d96D1CA764C902D65887B009c762e6c0329235a"

# 你的 Telegram 机器人 Token
TG_BOT_TOKEN = "你的Telegram机器人TOKEN"

# 你的 Telegram 频道 ID (以 -100 开头的负数)
TG_CHAT_ID = "你的Telegram频道ID"
```

填写完毕后，按 `Ctrl + X` -> `Y` -> **回车** 保存并退出。

### 3. 启动机器人

我们使用 `tmux` 来确保机器人在后台持久化运行。

```bash
# 1. 创建一个名为 "sniper" 的 tmux session
tmux new -s sniper

# 2. 在 tmux session 内部，运行脚本
python3 fomo_sniper.py
```

此时，您应该能看到脚本的启动日志，并且 Telegram 会收到启动成功的通知。

#### 4. 安全退出
确认脚本运行正常后，按 `Ctrl + B`，然后按 `D`，即可安全地从 tmux session 分离。机器人将在后台持续为您工作。

### 5. 日常管理

*   **查看实时日志**: `tmux attach -t sniper`
*   **停止机器人**: 进入 session 后按 `Ctrl + C`

---

## 免责声明

本项目仅为技术研究目的。所有与区块链交互的行为都会消耗真实的资金（Gas Fee），并可能因各种原因（网络拥堵、策略失误等）导致资金损失。请务必使用一个仅存放少量资金的“热钱包”来运行此机器人，并自行承担所有风险。

---

## 支持与赞赏 (Support & Appreciation)

如果您觉得这个项目对您有帮助，节省了您的时间，或者您只是单纯地想支持我的工作，欢迎通过以下地址给我“加个鸡腿”！您的支持是我持续改进和分享的巨大动力。

**BEP20 / ERC20 (BSC, ETH, Polygon, etc.)**
```
0x8ab29bd19e26176d39a40d1575a2056ea7fa001b
```

