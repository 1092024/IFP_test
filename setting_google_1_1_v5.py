import os
import time
from datetime import datetime
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options

# --------------------------
# 1️⃣ 基礎工具
# --------------------------
def run_adb(cmd):
    return os.popen(cmd).read()

def open_settings():
    print("📱 開啟系統設定...")
    run_adb("adb shell am start -a android.settings.SETTINGS")
    time.sleep(3)

def create_screenshot_folder():
    folder_name = datetime.now().strftime("Screenshots_%Y%m%d_%H%M%S")
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

# --------------------------
# 2️⃣ 獲取左側清單
# --------------------------
def get_left_pane_list(driver):
    print("\n🔄 [第一階段] 獲取左側清單順序...")
    window_size = driver.get_window_size()
    left_pane_boundary = window_size['width'] * 0.3
    ordered_items = []
    
    # 確保回到頂部 (限定在左側容器內操作)
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
        'new UiScrollable(new UiSelector().resourceId("com.android.settings:id/recycler_view")).scrollToBeginning(10)')

    for _ in range(8):
        titles = driver.find_elements(AppiumBy.XPATH, "//androidx.recyclerview.widget.RecyclerView[@resource-id='com.android.settings:id/recycler_view']//android.widget.TextView[@resource-id='android:id/title']")
        for t in titles:
            try:
                if t.text and t.location['x'] < left_pane_boundary:
                    if t.text not in ordered_items:
                        ordered_items.append(t.text)
            except: continue
        # 手動在左側滑動
        driver.swipe(start_x=200, start_y=1000, end_x=200, end_y=400, duration=800)
        time.sleep(1)
    
    print(f"✅ 獲取完成，共 {len(ordered_items)} 項。")
    return ordered_items

# --------------------------
# 3️⃣ 核心：點擊與截圖 (精準限定區域)
# --------------------------
def click_and_screenshot_all(driver, item_list, folder):
    print(f"\n📸 [第二階段] 開始逐項點擊並截圖")
    
    # 確保先回到頂部
    driver.find_element(AppiumBy.ANDROID_UIAUTOMATOR, 
        'new UiScrollable(new UiSelector().resourceId("com.android.settings:id/recycler_view")).scrollToBeginning(5)')

    for index, name in enumerate(item_list):
        print(f"👉 [{index+1}/{len(item_list)}] 處理中: {name}")
        success = False
        
        # 嘗試最多 3 次尋找（包含小幅度捲動）
        for attempt in range(3):
            try:
                # 只找目前畫面看的見的元素，不使用會噴錯的 scrollIntoView
                target_el = driver.find_element(AppiumBy.XPATH, 
                    f"//android.widget.TextView[@resource-id='android:id/title' and @text='{name}']")
                
                # 取得中心座標點擊，這比只拿 y 座標穩
                rect = target_el.rect
                center_x = rect['x'] + (rect['width'] / 2)
                center_y = rect['y'] + (rect['height'] / 2)
                
                driver.tap([(center_x, center_y)], 100)
                time.sleep(2) # 等待右側反應
                
                # 截圖
                safe_name = "".join([c for c in name if c.isalnum() or c in (' ', '_')]).strip().replace(' ', '_')
                file_name = f"{index+1:02d}_{safe_name}.png"
                driver.get_screenshot_as_file(os.path.join(folder, file_name))
                print(f"   🖼️ 已存檔: {file_name}")
                
                success = True
                break # 成功就跳出 attempt 迴圈
                
            except:
                # 找不到就稍微往下滑一點點再找一次
                driver.swipe(start_x=200, start_y=800, end_x=200, end_y=500, duration=500)
                time.sleep(0.5)

        if not success:
            print(f"   ⚠️ 無法定位 {name}，已跳過。")
# --------------------------
# 4️⃣ 執行
# --------------------------
# ... 前面你的 import 和工具函式保持不變 ...

def run_setting_task(already_open=True):
    """
    already_open: 如果主程式已經開好了，就不再執行 adb 指令
    """
    if not already_open:
        open_settings()
    else:
        print("⚡ 偵測到設定頁面已由主程式開啟，直接啟動 Appium 進行操作...")
    options = UiAutomator2Options()
    options.platform_name = "Android"
    options.automation_name = "UiAutomator2"
    options.set_capability("appium:enableMultiWindows", True)
    options.set_capability("appium:ignoreUnimportantViews", False)
    options.no_reset = True

    # 建議加上 error handling 以防 Appium 沒開
    try:
        driver = webdriver.Remote("http://127.0.0.1:4725", options=options)
        save_path = create_screenshot_folder()
        full_list = get_left_pane_list(driver)
        
        if full_list:
            click_and_screenshot_all(driver, full_list, save_path)
            print(f"\n✨ 任務結束，照片存放在: {save_path}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Appium 執行失敗: {e}")
        return False

# 保留這個，讓你單獨執行此檔時也能動
if __name__ == "__main__":
    run_setting_task()