# 負責整個流程控制的主程式
import subprocess # 引入用來執行 ADB 指令的內建套件
import time     # 引入時間模組以便使用 sleep 等功能
import os       # 引入作業系統模組以便處理檔案路徑
from datetime import datetime # 引入日期時間模組
from open_package import start_app  # 引入啟動 App 的模組
from setting_google_1_1_v5 import run_setting_task # 引入設定頁面模組
import openpyxl # 引入 openpyxl 以便寫入 Excel

# 測試清單： package 名稱
apps_to_test = [
    "com.mvbcast.crosswalk", # Airsync
    "com.viewsonic.droid", # myViewBoard
    "com.android.settings" # gSettings
]

# 定義一個函式來強行關閉 App
def force_stop(package):
    """強行關閉 App"""
    subprocess.run(f"adb shell am force-stop {package.strip()}", shell=True) # am force-stop 強制停止 App
    print(f"🛑 已強制停止: {package}")

# 新增函式：檢查 app 是否在前台運行
def is_app_in_foreground(package):
    """檢查 app 是否在前台（mResumedActivity）"""
    result = subprocess.run("adb shell dumpsys activity activities | findstr mResumedActivity", shell=True, capture_output=True, text=True)
    return package in result.stdout

# 新增函式：檢查 app 的 UI 是否加載完成（通過 UI hierarchy），返回 (成功?, 失敗原因)
def is_app_ui_loaded(package):
    """檢查 app UI 是否真正加載，使用以下指標：
    返回: (True, None) 或 (False, 失敗原因)
    1. 窗口是否有實際尺寸（不是 0x0）
    2. UI hierarchy 中是否有元素（不是空或只有黑屏）
    3. 焦點應用是否就是該 package
    """
    try:
        # 1. 檢查焦點應用
        result = subprocess.run("adb shell dumpsys window windows | findstr mCurrentFocus", 
                              shell=True, capture_output=True, text=True, timeout=5)
        if package not in result.stdout:
            reason = "焦點應用不符"
            print(f"   ⚠️  {reason}")
            return False, reason
        print(f"   ✓ 焦點應用正確")
        
        # 2. 檢查窗口尺寸（排除黑屏情況）
        result = subprocess.run(f"adb shell dumpsys window windows | findstr {package}", 
                              shell=True, capture_output=True, text=True, timeout=5)
        if "0x0" in result.stdout or result.stdout.count(package) == 0:
            reason = "窗口尺寸異常（0x0 或黑屏）"
            print(f"   ⚠️  {reason}")
            return False, reason
        print(f"   ✓ 窗口尺寸正常")
        
        # 3. 檢查 UI hierarchy 是否有內容（通過 uiautomator dump）
        subprocess.run("adb shell uiautomator dump /sdcard/ui_dump.xml", 
                      shell=True, capture_output=True, timeout=5)
        result = subprocess.run("adb shell cat /sdcard/ui_dump.xml | findstr hierarchy", 
                              shell=True, capture_output=True, text=True, timeout=5)
        if "hierarchy" not in result.stdout or len(result.stdout) < 50:
            reason = "UI 層級結構為空或過小"
            print(f"   ⚠️  {reason}")
            return False, reason
        print(f"   ✓ UI hierarchy 已加載")
        
        return True, None
    except subprocess.TimeoutExpired:
        reason = "檢查 UI 加載時超時"
        print(f"   ⚠️  {reason}")
        return False, reason
    except Exception as e:
        reason = f"檢查 UI 加載出錯: {str(e)}"
        print(f"   ⚠️  {reason}")
        return False, reason

# 新增函式：等待 app loading 成功（最多 30 秒），返回 (成功?, 失敗原因)
def wait_for_app_ready(package, timeout=30):
    """等待 app 前台運行 & UI 加載完成，返回 (True, None) 或 (False, 失敗原因)
    使用漸進式檢查：
    1. 前 5 秒：檢查應用是否在前台
    2. 5-30 秒：檢查應用是否在前台 + UI 是否加載
    """
    start_time = time.time()
    foreground_check_passed = False
    
    while time.time() - start_time < timeout:
        elapsed = time.time() - start_time
        
        # 檢查前台狀態
        if not is_app_in_foreground(package):
            print(f"   ⏳ 應用未進入前台 ({elapsed:.0f}s)")
            time.sleep(1)
            continue
        
        foreground_check_passed = True
        print(f"✅ {package} 已在前台運行")
        
        # 若應用已在前台，繼續檢查 UI 加載（最多再等 10 秒）
        ui_check_start = time.time()
        while time.time() - ui_check_start < 10:
            print(f"   檢查 UI 加載狀態...")
            is_loaded, reason = is_app_ui_loaded(package)
            if is_loaded:
                print(f"✅ {package} UI 已完全加載！")
                return True, None
            time.sleep(1)
        
        # UI 檢查超時，視為失敗
        reason = "UI 加載超時（應用前台但 UI 未就緒）"
        print(f"⚠️  {package} {reason}")
        return False, reason
    
    if foreground_check_passed:
        reason = "等待 UI 加載超時"
        print(f"⚠️ {package} {reason}")
    else:
        reason = "應用未在前台（未成功啟動）"
        print(f"⚠️ {package} {reason}")
    return False, reason

# 新增函式：截圖並儲存
def take_screenshot(package, folder="checkOpen"):
    """截圖並儲存到指定資料夾，檔名為 APP名稱_日期時間.png"""
    if not os.path.exists(folder):
        os.makedirs(folder)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{package}_{timestamp}.png"
    filepath = os.path.join(folder, filename)
    # ADB 截圖到裝置
    subprocess.run("adb shell screencap -p /sdcard/screenshot.png", shell=True)
    # 拉取到本地
    subprocess.run(f"adb pull /sdcard/screenshot.png {filepath}", shell=True)
    print(f"📸 截圖已儲存: {filepath}")
    return filepath

# 新增函式：寫入 Excel
def write_to_excel(results, folder="checkOpen"):
    """將結果寫入 Excel 檔案"""
    if not os.path.exists(folder):
        os.makedirs(folder)
    filepath = os.path.join(folder, "app_results.xlsx")
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["App Name", "Result", "失敗原因"])
    for app, result, reason in results:
        ws.append([app, result, reason if reason else ""])
    wb.save(filepath)
    print(f"📊 Excel 已儲存: {filepath}")

# --- 主循環 ---
results = []  # 儲存結果列表
for package in apps_to_test: # 逐一處理清單中的每個 App
    print(f"\n--- 正在處理: {package} ---")
    
    # 1. 啟動 App
    start_app(package) 
    
    # 2. 等待 app loading 成功並截圖
    is_ready, failure_reason = wait_for_app_ready(package)
    take_screenshot(package)  # 無論成功與否都截圖
    
    # 3. 記錄結果
    result = "Pass" if is_ready else "Fail"
    results.append((package, result, failure_reason))
    
    if not is_ready:
        print(f"跳過 {package} 的額外任務")
        force_stop(package)
        continue
    
    # 4. 根據 package_name 決定是否執行額外任務
    package_name = package.strip()
    match package_name:
        case "com.mvbcast.crosswalk":
            # 這裡可以放入 Airsync 的自動化任務函式
            pass # 目前沒有額外任務
        case "com.viewsonic.droid":
            # 這裡可以放入 myViewBoard 的自動化任務函式
            pass # 目前沒有額外任務
        case "com.android.settings":
            run_setting_task() # 執行 Appium 邏輯
        case _: # 預設：無額外任務
            pass
    
    # 5. 總是關閉 App（任務執行完後）
    force_stop(package)
    
    # 6. 執行完後固定等 1 秒再換下一個
    print("⏳ 等待 1 秒切換...")
    time.sleep(1)

# 寫入 Excel
write_to_excel(results)

print("\n🏁 所有任務已完成！")