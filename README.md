
# Jager FOMO Hunt - Automated Sniper Bot

![GitHub top language](https://img.shields.io/github/languages/top/Zisaac52/jager-fomo-sniper?style=flat-square) ![GitHub last commit](https://img.shields.io/github/last-commit/Zisaac52/jager-fomo-sniper?style=flat-square)

[中文说明](README.zh-CN.md)

This is an automated Python bot designed for the Jager FOMO Hunt game. It monitors the game countdown 24/7 and automatically executes purchase transactions at critical moments, aiming to be the last ticket buyer before the timer runs out.

<img width="297" height="112" alt="image" src="https://github.com/user-attachments/assets/7008c803-978e-4af8-b350-60820a33edc7" />

---

## Core Features

*   **Real-time Countdown Monitoring**: Utilizes Playwright with a headless browser to accurately scrape real-time countdown data from the official website.
*   **Intelligent Snipe Strategy**: Automatically triggers transactions within a preset time threshold (e.g., the last 11 seconds) to compete for the grand prize.
*   **Dynamic Gas Priority**: Detects the current Gas Price on the BSC network and submits transactions with a competitively higher price to ensure priority packing during "Gas Wars," maximizing snipe success rates.
*   **Ownership Check**: Before placing a bid, it queries the smart contract to check if the current leader is itself, avoiding redundant purchases and unnecessary fund expenditure.
*   **Real-time Telegram Notifications**: All critical bot statuses—startup, heartbeat, successful snipes, failed snipes, errors, and recoveries—are pushed to your designated Telegram channel in real-time.
*   **High Availability & Self-Healing**:
    *   **Guardian Process**: Even if the script crashes for any reason, an outer guardian process will automatically restart it after cleaning up the environment.
    *   **Memory Leak Protection**: Before each restart, it automatically cleans up residual browser processes, fundamentally preventing server freezes caused by memory leaks.
    *   **Page Recovery**: When the target webpage freezes or fails to load, the bot attempts to self-heal by creating a brand-new browser page instead of just refreshing.

## Telegram Notification Example

The bot provides clear, real-time updates on its status, keeping you informed of its every move:

<img width="404" height="897" alt="ScreenShot_2025-11-10_154420_950" src="https://github.com/user-attachments/assets/3d5bc74b-7c4f-4e6e-bd2a-40633d905525" />

---

## Deployment Guide

### 1. Server Requirements

To ensure stable bot operation, a Virtual Private Server (VPS) meeting the following minimum specifications is recommended:

*   **CPU**: 2 Cores
*   **Memory (RAM)**: 4 GB
*   **Operating System**: Ubuntu 20.04 LTS or later
*   **Network**: Stable outbound internet connection

### 2. Deployment Steps

#### 2.1 Clone the Repository
Log in to your server via SSH and clone this project repository. The `fomo_sniper.py` and `abi.json` files are included.

```bash
# First, install git (if not already installed)
sudo apt update
sudo apt install git -y

# Clone the repository
git clone https://github.com/Zisaac52/jager-fomo-sniper

# Navigate into the project directory
cd jager-fomo-sniper
```

#### 2.2 Install Environment Dependencies
Execute the following commands to install the Python environment, required libraries, and browser driver.

```bash
# Install pip and tmux
sudo apt install python3-pip tmux -y

# Install Python dependency libraries
pip install requests web3 playwright

# Install the Playwright browser driver
playwright install
```

#### 2.3 (Important) Configure the Script
All configuration parameters for this project are located at the top of the `fomo_sniper.py` script. You must edit this file and fill in your personal information before running.

```bash
# Open the script file with the nano editor
nano fomo_sniper.py
```

Use the arrow keys to navigate to the top of the file, locate the **first configuration section**, and **fill in your own credentials**:

```python
# ==============================================================================
# 1. Script Configuration
# ⚠️ Please fill in your credentials here
# ==============================================================================
# BSC RPC Node URL
BSC_RPC_URL = "https://bsc-dataseed.binance.org/" # Using a private node like QuickNode is recommended

# Your hot wallet private key (without the "0x" prefix)
BOT_PRIVATE_KEY = "your_hot_wallet_private_key" 

# Game contract address 
FOMO_CONTRACT_ADDRESS = "0x9d96D1CA764C902D65887B009c762e6c0329235a"

# Your Telegram bot token
TG_BOT_TOKEN = "your_telegram_bot_token"

# Your Telegram channel ID (a negative number, usually starting with -100)
TG_CHAT_ID = "your_telegram_channel_id"
```
After filling everything out, press `Ctrl + X` -> `Y` -> **Enter** to save and exit.

### 3. Launch the Bot

We use `tmux` to ensure the bot runs persistently in the background.

```bash
# 1. Create a new tmux session named "sniper"
tmux new -s sniper

# 2. Inside the tmux session, run the script
python3 fomo_sniper.py
```

At this point, you should see the bot's startup logs, and you will receive a launch notification on Telegram.

#### 4. Detach Safely
Once you confirm the script is running correctly, press `Ctrl + B`, then `D` to safely detach from the tmux session. The bot will continue to run in the background.

### 5. Daily Management

*   **View real-time logs**: `tmux attach -t sniper`
*   **Stop the bot**: Enter the session and press `Ctrl + C`

---

## Disclaimer

This project is for technical research purposes only. All interactions with the blockchain involve real funds (Gas Fees) and may result in financial loss due to various factors (network congestion, strategic errors, etc.). Always use a "hot wallet" with a limited amount of funds to run this bot and assume all risks yourself.

---

## Support & Appreciation

If you find this project helpful, if it has saved you time, or if you simply want to support my work, feel free to send a tip! Your support is a huge motivation for me to continue improving and sharing.

**BEP20 / ERC20 (BSC, ETH, Polygon, etc.)**
```
0x8ab29bd19e26176d39a40d1575a2056ea7fa001b
```


---

