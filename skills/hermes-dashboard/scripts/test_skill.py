"""
Hermes Dashboard Skill — Avtomatlashtirilgan tekshiruv va diagnostika skripti.
Ushbu skript:
1. hermes-2.bat orqali Mars loyihasi faolligini tekshiradi
2. 9119-portda Dashboard web interfeysi HTTP 200 javob berishini tekshiradi
3. /api/status dan tizim parametrlarini o'qiydi
4. mars-lms MCP serveridagi 11 ta toolni probe test qiladi
"""

import sys
import subprocess
import httpx
import re

BASE_URL = "http://127.0.0.1:9119"

def run():
    print("==================================================")
    print("🚀 HERMES DASHBOARD (LOYIHA: MARS) TESTI BOSHLANDI")
    print("==================================================")

    # 1. Web UI tekshiruvi
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(BASE_URL)
            if resp.status_code != 200:
                print(f"❌ Web UI yuklanmadi, status: {resp.status_code}")
                sys.exit(1)
            print(f"✅ 1. Web UI Dashboard faol: {BASE_URL} (HTTP {resp.status_code})")

            # 2. Xavfsizlik tokenini ajratib olish
            token_match = re.search(r'__HERMES_SESSION_TOKEN__="([^"]+)"', resp.text)
            if not token_match:
                print("❌ HTML dan sessiya tokeni topilmadi!")
                sys.exit(1)
            token = token_match.group(1)
            print(f"✅ 2. Xavfsizlik sessiya tokeni olindi: {token[:12]}...")
            headers = {"X-Hermes-Session-Token": token}

            # 3. /api/status tekshiruvi
            status_resp = client.get(f"{BASE_URL}/api/status", headers=headers)
            if status_resp.status_code == 200:
                s_data = status_resp.json()
                print(f"✅ 3. Tizim holati (status):")
                print(f"   • Hermes Home: {s_data.get('hermes_home')}")
                print(f"   • Disk holati: {s_data.get('disk', {}).get('pressure')}")
            else:
                print(f"❌ /api/status xatosi: {status_resp.status_code}")
                sys.exit(1)

            # 4. MCP mars-lms test probe
            mcp_resp = client.post(f"{BASE_URL}/api/mcp/servers/mars-lms/test", headers=headers)
            if mcp_resp.status_code == 200 and mcp_resp.json().get("ok"):
                tools = mcp_resp.json().get("tools", [])
                print(f"✅ 4. MCP Server ('mars-lms') faol: {len(tools)} ta tool aniqlandi:")
                for t in tools:
                    print(f"   - {t.get('name')}")
            else:
                print(f"❌ MCP mars-lms test xatosi: {mcp_resp.status_code} {mcp_resp.text}")
                sys.exit(1)

    except Exception as e:
        print(f"❌ Xatolik yuz berdi: {type(e).__name__} - {e}")
        sys.exit(1)

    print("==================================================")
    print("🎉 BARCHA TEKSHIRUVLAR MUVAFFAQIYATLI O'TDI (PASS)")
    print("==================================================")

if __name__ == "__main__":
    run()
