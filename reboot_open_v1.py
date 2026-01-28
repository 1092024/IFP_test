import subprocess
import time

def adb_command(command):
    """執行 ADB 指令並回傳結果"""
    result = subprocess.run(f"adb {command}", shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def unlock_phone(pin):
    print("🚀 正在重新開機...")
    adb_command("reboot")
    
    # 1. 等待設備重新連線
    print("⏳ 等待裝置重新連線...")
    subprocess.run("adb wait-for-device", shell=True)
    
    # 2. 等待系統 UI 完全載入 (開機後通常需要較長時間)
    # 根據手機效能，建議 30-45 秒
    time.sleep(40) 
    
    # 3. 點亮螢幕
    print("💡 點亮螢幕...")
    adb_command("shell input keyevent 26")
    time.sleep(1)
    
    # 4. 向上滑動喚起 PIN 輸入頁面 (從螢幕下方往上滑)
    # 座標參考：x=500, y=1800 滑到 x=500, y=500
    print("👆 執行向上滑動...")
    adb_command("shell input swipe 500 1800 500 500 300")
    time.sleep(2) # 等待 Gboard 彈出
    
    # 5. 輸入 PIN 碼
    # 使用 keyevent 是最穩定的方式，Gboard 會自動接收這些數字
    print(f"⌨️  正在輸入 PIN: {pin}")
    key_map = {
        '0': 7, '1': 8, '2': 9, '3': 10, '4': 11,
        '5': 12, '6': 13, '7': 14, '8': 15, '9': 16
    }
    
    for digit in pin:
        if digit in key_map:
            adb_command(f"shell input keyevent {key_map[digit]}")
            time.sleep(0.2) # 模擬真實輸入間隔
            
    # 6. 按下 Enter (Done) 確認
    print("✅ 按下確認鍵...")
    adb_command("shell input keyevent 66")
    print("🎉 解鎖流程執行完畢！")

if __name__ == "__main__":
    # 在這裡設定你的 PIN 碼
    MY_PIN = "0000" 
    unlock_phone(MY_PIN)