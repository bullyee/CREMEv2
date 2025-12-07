# msf_live_poll.py
# Run: python3 msf_live_poll.py
from pymetasploit3.msfrpc import MsfRpcClient
import time, pprint, sys

# adjust port/ssl to match how you started msfrpcd
RPC_PASSWORD = 'kali'
RPC_USERNAME = 'kali'
RPC_PORT = 55553   # change if msfrpcd uses other port
USE_SSL = True     # True if msfrpcd started with -S

pp = pprint.PrettyPrinter(indent=2)

def main():
    client = MsfRpcClient(password=RPC_PASSWORD, username=RPC_USERNAME, ssl=USE_SSL, port=RPC_PORT)
    print("[*] connected to msfrpcd (port {})".format(RPC_PORT))
    last_jobs = {}
    try:
        while True:
            # 1) Jobs list + info for new jobs
            try:
                jobs = client.jobs.list()   # returns dict jobid -> info (or {})
            except Exception as e:
                print("[!] jobs.list() error:", e)
                jobs = {}

            # Print jobs and show details when job appears/disappears
            if jobs != last_jobs:
                pp.pprint({"jobs": jobs})
                # try to fetch detailed info for each job id
                for jid in list(jobs.keys()):
                    try:
                        info = client.jobs.info(jid)
                        pp.pprint({f"job_{jid}_info": info})
                    except Exception as e:
                        print(f"[!] job info error for {jid}:", e)
                last_jobs = jobs

            # 2) Consoles: list & read outputs
            try:
                consoles = client.consoles.list()
            except Exception as e:
                consoles = {}
                print("[!] consoles.list() error:", e)

            if consoles:
                pp.pprint({"consoles": consoles})
                for cid in consoles:
                    try:
                        out = client.consoles.read(cid)
                        if out and (out.get('data') or out.get('busy')):
                            pp.pprint({f"console_{cid}_out": out})
                    except Exception as e:
                        print(f"[!] consoles.read({cid}) error:", e)

            # 3) DB checks (hosts, services, creds) - useful for scanner modules
            try:
                hosts = client.db.hosts()
                services = client.db.services()
                creds = client.db.creds()
                # only print when something exists
                if hosts: pp.pprint({"hosts_count": len(hosts)})
                if services: pp.pprint({"services_count": len(services)})
                if creds: pp.pprint({"creds_count": len(creds)})
            except Exception as e:
                print("[!] db.* read error:", e)

            time.sleep(2)  # poll interval; lower for faster updates, higher to reduce noise
    except KeyboardInterrupt:
        print("\n[+] exiting poller")
        sys.exit(0)

if __name__ == '__main__':
    main()
