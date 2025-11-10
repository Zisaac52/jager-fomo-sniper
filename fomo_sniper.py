import os
import json
import time
import traceback
from typing import Optional

import requests
from playwright.sync_api import sync_playwright
from web3 import Web3
import re

# ==============================================================================
# 1. 脚本配置
# ⚠️ 请务必在此处填入你的真实信息
# ==============================================================================
# BSC RPC 节点地址
BSC_RPC_URL = "https://bsc-dataseed.binance.org/"  # 使用私有RPC节点可以增加速度 这里推荐QuickNode的节点可以创建免费的

# 你的热钱包私钥 (请确保去掉开头的 "0x")
BOT_PRIVATE_KEY = "" 

# 游戏合约地址 
FOMO_CONTRACT_ADDRESS = "0x9d96D1CA764C902D65887B009c762e6c0329235a"

# 你的 Telegram 机器人 Token
TG_BOT_TOKEN = ""

# 你的 Telegram 频道 ID (以 -100 开头的负数)
TG_CHAT_ID = ""

# ==============================================================================
# 2. 策略配置
# ==============================================================================
# 倒计时低于多少秒时，触发狙击检查 会存在一点延迟 不要太极限
SNIPE_THRESHOLD_SECONDS = 11

# 每多少秒检查一次网页倒计时
CHECK_INTERVAL = 3

# 每多少小时发送一次心跳通知
HEARTBEAT_INTERVAL = 6 * 3600

# 动态 Gas 价格的倍数 (1.2 = 比当前市场价高20%，确保优先打包)
GAS_PRICE_MULTIPLIER = 1.2 

# Gas Limit: 基于实战测试，设置一个安全的上限
GAS_LIMIT = 600000

# ==============================================================================
# 脚本启动前的配置检查
# ==============================================================================
if "你的" in BOT_PRIVATE_KEY:
    raise ValueError("错误：请先在脚本顶部的配置区域填写你的真实信息！")

# ==============================================================================
# 3. 合约 ABI 及 Web3 初始化
# ==============================================================================
try:
    with open('abi.json', 'r') as f:
        CONTRACT_ABI = json.load(f)
except FileNotFoundError:
    raise FileNotFoundError("错误: abi.json 文件未找到。请确保它和本脚本在同一个目录下。")

w3 = Web3(Web3.HTTPProvider(BSC_RPC_URL))
if not w3.is_connected():
    raise ConnectionError(f"无法连接到 BSC RPC 节点: {BSC_RPC_URL}")

bot_account = w3.eth.account.from_key(BOT_PRIVATE_KEY)
MY_WALLET_ADDRESS = bot_account.address
print(f"✅ 机器人钱包地址: {MY_WALLET_ADDRESS}")

# 注意：与实现合约交互，需要用实现合约的ABI，但地址用代理合约的
fomo_contract = w3.eth.contract(address=FOMO_CONTRACT_ADDRESS, abi=CONTRACT_ABI)

# ==============================================================================
# 4. 核心合约交互函数
# ==============================================================================
def get_last_buyer() -> Optional[str]:
    """读取最后一个购买者 (增加重试机制)"""
    # 尝试最多3次
    for i in range(3):
        try:
            current_round_id = fomo_contract.functions.currentRound().call()
            last_records = fomo_contract.functions.getRoundLastRecords(current_round_id).call()
            if last_records:
                return last_records[0]
            return None # 如果列表为空，直接返回None，不需要重试
        except Exception as e:
            print(f"❌ (尝试 {i+1}/3) 读取最后购买者地址失败: {e}")
            # 如果不是最后一次尝试，则等待一小会儿再重试
            if i < 2:
                time.sleep(0.5) # 等待500毫秒
    # 如果3次都失败了，才最终返回 None
    return None

def buy_ticket():
    """使用动态 Gas Price 策略来购买门票"""
    try:
        print("🚀 正在构造狙击交易 (使用动态优先 Gas)...")
        current_gas_price = w3.eth.gas_price
        priority_gas_price = int(current_gas_price * GAS_PRICE_MULTIPLIER)
        
        print(f"   - 当前市场 Gas Price: {w3.from_wei(current_gas_price, 'gwei'):.2f} Gwei")
        print(f"   - 我们的优先 Gas Price: {w3.from_wei(priority_gas_price, 'gwei'):.2f} Gwei")

        transaction = fomo_contract.functions.buyTicket().build_transaction({
            'from': MY_WALLET_ADDRESS,
            'nonce': w3.eth.get_transaction_count(MY_WALLET_ADDRESS),
            'gasPrice': priority_gas_price,
            'gas': GAS_LIMIT,
        })

        signed_txn = w3.eth.account.sign_transaction(transaction, private_key=BOT_PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        print(f"🧾 交易已发送! Hash: {w3.to_hex(tx_hash)}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        
        if receipt['status'] == 1:
            print("✅ 交易成功确认!")
            return True, w3.to_hex(tx_hash)
        else:
            print("❌ 交易失败 (reverted)!")
            return False, w3.to_hex(tx_hash)
    except Exception as e:
        print(f"🔥 购买门票时发生严重错误: {e}")
        return False, str(e)

# ==============================================================================
# 5. 辅助函数
# ==============================================================================
def send_telegram(text: str):
    try:
        requests.get(
            f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage",
            params={"chat_id": TG_CHAT_ID, "text": text, "disable_web_page_preview": "true"},
            timeout=10,
        )
    except Exception:
        pass

def parse_countdown(text: str) -> int:
    raw = text.strip()
    m = re.search(r"(\d+:\d+(?::\d+)?)", raw)
    if not m: raise ValueError(f"无法在字符串中找到时间格式: {raw}")
    t = m.group(1)
    parts = t.split(":")
    if len(parts) == 3: h, m_, s = map(int, parts); return h * 3600 + m_ * 60 + s
    elif len(parts) == 2: m_, s = map(int, parts); return m_ * 60 + s
    else: raise ValueError(f"无法解析倒计时字符串: {t}")

# ==============================================================================
# 6. 主监控与狙击逻辑
# ==============================================================================
def monitor_and_snipe():
    last_heartbeat = 0
    # --- 新增：用于跟踪上一次页面刷新的时间戳 ---
    last_reload_time = time.time() 
    # --- 新增：设置刷新间隔为60秒 ---
    RELOAD_INTERVAL_SECONDS = 60

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("https://www.bnb100k.com/", wait_until="domcontentloaded", timeout=60000)

        send_telegram("✅ Jager FOMO 狙击机器人已启动 (V-Final-OptimizedReload)！")

        while True:
            current_time = time.time()
            if current_time - last_heartbeat >= HEARTBEAT_INTERVAL:
                send_telegram("🟢 狙击机器人正常运行中...")
                last_heartbeat = current_time

            try:
                # 定位并读取倒计时 (这部分逻辑不变)
                countdown_locator = page.locator(
                    "xpath=//div[@id='module-fomomint']//div[contains(text(), ':')]"
                ).first
                countdown_text = countdown_locator.inner_text(timeout=20000).strip()
                seconds_left = parse_countdown(countdown_text)
                
                print(f"⏱️  当前倒计时: {seconds_left}s")

                # 狙击逻辑 (这部分逻辑不变)
                if 0 < seconds_left <= SNIPE_THRESHOLD_SECONDS:
                    print(f"🚨 倒计时 {seconds_left}s, 进入狙击窗口!")
                    
                    last_buyer = get_last_buyer()
                    if last_buyer and last_buyer.lower() == MY_WALLET_ADDRESS.lower():
                        print("😎 我已是最后购买者，本次跳过。")
                    else:
                        print(f"⚔️ 最后购买者是 {last_buyer}，不是我。执行狙击！")
                        
                        success, tx_info = buy_ticket()

                        if success:
                            msg = (f"🎉 狙击成功! 门票已购买!\n\n"
                                   f"倒计时: {countdown_text}\n"
                                   f"交易 Hash: https://bscscan.com/tx/{tx_info}")
                            send_telegram(msg)
                            print("🎯 狙击完成，进入 10 秒智能冷却期...")
                            time.sleep(10)
                        else:
                            msg = (f"🔥 狙击失败!\n\n"
                                   f"原因: {tx_info}")
                            send_telegram(msg)
                            print("❌ 狙击失败，暂停15秒...")
                            time.sleep(15)
                
                # --- 优化后的刷新逻辑 ---
                # 检查是否需要执行例行刷新
                if time.time() - last_reload_time > RELOAD_INTERVAL_SECONDS:
                   print(f"🔄 距离上次刷新已超过 {RELOAD_INTERVAL_SECONDS} 秒，执行例行页面刷新...")
                   page.reload(wait_until="domcontentloaded", timeout=60000)
                   # 更新刷新时间戳，以便下一次计时
                   last_reload_time = time.time()
                # -------------------------

            except Exception as e:
                print(f"❌ 监控循环严重出错: {e}")
                send_telegram(f"❗ 机器人监控严重异常: {str(e)[:100]}")
                
                # 异常恢复逻辑 (这部分逻辑不变)
                try:
                    print("🔥 页面可能已卡死，正在尝试创建全新页面...")
                    page.close()
                    page = browser.new_page()
                    page.goto("https://www.bnb100k.com/", wait_until="domcontentloaded", timeout=60000)
                    print("✅ 全新页面已创建并加载成功！")
                    send_telegram("✅ 机器人已通过重启页面恢复！")
                    # 重置刷新计时器
                    last_reload_time = time.time()
                except Exception as e2:
                    print(f"☠️ 创建全新页面失败，浏览器实例可能已损坏: {e2}")
                    raise

            time.sleep(CHECK_INTERVAL)

# ==============================================================================
# 7. 守护进程 (已增强“防卡死”清理功能)
# ==============================================================================
if __name__ == "__main__":
    while True:
        try:
            monitor_and_snipe()
        except Exception as e:
            error_details = f"❗ 机器人主进程崩溃: {e}\n{traceback.format_exc()}"
            print(error_details)
            send_telegram(f"☠️ 机器人崩溃，正在准备重启... Error: {str(e)[:100]}")
            
            # --- 核心优化：在重启前，强力清理所有残留的浏览器进程 ---
            try:
                print("🧹 正在清理任何残留的 Playwright/Chromium 浏览器进程...")
                # 这个命令会找到所有包含 "chromium" 字符的进程并强制杀死它们
                # 能够有效地防止内存泄漏导致的系统卡死
                os.system("pkill -f chromium")
                print("✅ 清理完成。")
            except Exception as kill_e:
                print(f"🔥 清理进程时出错: {kill_e}")
            # -----------------------------------------------------------

            print("⏳ 15秒后将重启脚本...")
            time.sleep(15)
