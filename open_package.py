import subprocess # 引入"用來執行 ADB 指令的內建套件"

# 程式說明:
# 這個模組負責啟動指定的 App
# 它會根據不同的 Package Name 使用不同的啟動方式，這樣可以確保大部分的 App 都能被成功啟動
# 主要分成兩種情況：
# 如果目標是系統設定，就直接叫系統打開設定頁面；如果目標是其他 App，就叫 Monkey 去找出這個 App 的啟動圖示並點它一下。
# 如果之後有遇到其他 App 使用其指令打不開，可能也要為它寫一個專屬的 if 啟動指令！

def start_app(package_name): # 定義一個函式來啟動 App (接收的參數-想要開啟的 APP package name)
    clean_package = package_name.strip() # strip 去除字串前後空白
    try:
        if clean_package == "com.android.settings":
            cmd = "adb shell am start -a android.settings.SETTINGS"
        else:
            cmd = f"adb shell monkey -p {clean_package} -c android.intent.category.LAUNCHER 1" # f-string 格式化字串，可以把變數直接放進字串
        
        subprocess.run(cmd, shell=True, capture_output=True) # 執行 ADB 指令，shell 讓指令可以在命令列執行；capture_output 捕捉輸出結果
        print(f"✅ 成功發送啟動指令: {clean_package}")
        return True
    except Exception as e:
        print(f"⚠️ 啟動失敗: {e}")
        return False