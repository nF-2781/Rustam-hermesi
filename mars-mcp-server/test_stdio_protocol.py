import subprocess
import json
import sys
import os

def main():
    server_path = "server.py" if os.path.exists("server.py") else "mars-mcp-server/server.py"
    proc = subprocess.Popen(
        [sys.executable, server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=0
    )

    def send_recv(req):
        line = json.dumps(req) + "\n"
        proc.stdin.write(line)
        proc.stdin.flush()
        res_line = proc.stdout.readline()
        if not res_line:
            err = proc.stderr.read()
            raise RuntimeError(f"Server terminated prematurely. Stderr: {err}")
        return json.loads(res_line)

    print("--- 1. Initialize ---")
    init_res = send_recv({
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "test-client", "version": "1.0"}
        }
    })
    print("Init response serverInfo:", init_res.get("result", {}).get("serverInfo"))

    # Initialized notification
    proc.stdin.write(json.dumps({
        "jsonrpc": "2.0",
        "method": "notifications/initialized"
    }) + "\n")
    proc.stdin.flush()

    print("\n--- 2. tools/list ---")
    tools_res = send_recv({
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    })
    tool_list = tools_res.get("result", {}).get("tools", [])
    print(f"Total tools registered: {len(tool_list)}")
    for t in tool_list:
        print(f" - {t['name']}: {t.get('description', '')[:50]}...")

    print("\n--- 3. tools/call -> login ---")
    login_call = send_recv({
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {
            "name": "login",
            "arguments": {
                "phone": "998935344549",
                "password": "1234",
                "role": "admin"
            }
        }
    })
    print("Login result content:")
    for c in login_call.get("result", {}).get("content", []):
        print(c.get("text", ""))

    print("\n--- 4. tools/call -> branch_me ---")
    branch_call = send_recv({
        "jsonrpc": "2.0",
        "id": 4,
        "method": "tools/call",
        "params": {
            "name": "branch_me",
            "arguments": {}
        }
    })
    print("branch_me result preview:")
    for c in branch_call.get("result", {}).get("content", []):
        print(c.get("text", "")[:250] + "...")

    proc.terminate()
    print("\n--- STDIO PROTOKOL TESTI MUVAFFAQIYATLI YAKUNLANDI! ---")

if __name__ == "__main__":
    main()
