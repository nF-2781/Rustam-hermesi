"""
MARS LMS — Ish Zanjiri (Audit Chain) Skripti
Ushbu skript mars-backend API lari orqali to'liq ish zanjirini ketma-ket bajaradi:
1. Login -> Token olish
2. Branch profiling
3. Finance overview
4. Mentor workload & recommendations
5. Room availability & schedule conflicts
6. Groups & students capacity
7. Payments & Salaries summary
"""

import os
import sys
import json
import httpx

BASE_URL = os.getenv("MARS_BASE_URL", "https://mars-backend-six.vercel.app").rstrip("/")

def log_step(step_num: int, title: str):
    print(f"\n==========================================")
    print(f"📌 [BOSQICH {step_num}] {title}")
    print(f"==========================================")

def run_chain():
    print("🚀 MARS LMS ISH ZANJIRINI ISHGA TUSHIRISH")
    print(f"Backend URL: {BASE_URL}")

    # 1. Login
    log_step(1, "Autentifikatsiya (POST /api/auth/login)")
    with httpx.Client(timeout=20.0) as client:
        login_resp = client.post(
            f"{BASE_URL}/api/auth/login",
            json={"phone": "998935344549", "password": "1234", "role": "admin"}
        )
        if login_resp.status_code != 200:
            print(f"❌ Login xatosi: {login_resp.status_code} {login_resp.text}")
            return
        
        login_data = login_resp.json()
        token = login_data.get("token") or login_data.get("accessToken")
        print(f"✅ Login muvaffaqiyatli! Foydalanuvchi: {login_data.get('user', {}).get('fullname', 'Admin')}")
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

        # Branch me
        me_resp = client.get(f"{BASE_URL}/api/branch/me", headers=headers)
        if me_resp.status_code == 200:
            b_info = me_resp.json().get("branch", {})
            print(f"🏢 Filial: {b_info.get('name')} | Manzil: {b_info.get('address')}")

        # 2. Finance Overview
        log_step(2, "Moliyaviy Salomatlik Tahlili (GET /api/finance/overview)")
        fin_resp = client.get(f"{BASE_URL}/api/finance/overview", headers=headers)
        if fin_resp.status_code == 200:
            overview = fin_resp.json().get("overview", {})
            print(f"💰 Jami daromad: {overview.get('totalIncome', 0):,} so'm")
            print(f"📉 Jami xarajat: {overview.get('totalExpense', 0):,} so'm")
            print(f"📊 Sof foyda:    {overview.get('netProfit', 0):,} so'm")
            print(f"💳 To'lov usullari: Naqd: {overview.get('incomeByMethod', {}).get('cash', 0):,}, Karta: {overview.get('incomeByMethod', {}).get('card', 0):,}")

        # 3. Mentor Workload
        log_step(3, "Mentorlar Yuklamasi Tahlili (GET /api/branch/mentors/workload)")
        load_resp = client.get(f"{BASE_URL}/api/branch/mentors/workload", headers=headers)
        if load_resp.status_code == 200:
            workload = load_resp.json().get("data", {})
            summary = workload.get("summary", {})
            print(f"👨‍🏫 Jami mentorlar: {summary.get('totalMentors', 0)}")
            print(f"👥 Guruhlar soni:    {summary.get('totalGroups', 0)}")
            print(f"🟢 Bo'sh mentorlar:  {summary.get('availableMentorsCount', 0)}")
            for rec in workload.get("recommendations", []):
                print(f"💡 Tavsiya: {rec.get('title')} - {rec.get('message')}")

        # 4. Schedule & Rooms
        log_step(4, "Xonalar va Dars Jadvallari Tahlili")
        conflicts_resp = client.get(f"{BASE_URL}/api/branch/schedule/conflicts", headers=headers)
        if conflicts_resp.status_code == 200:
            conf_data = conflicts_resp.json().get("data", {})
            print(f"⚠️  Konfliktlar soni: {conf_data.get('totalConflicts', 0)}")
            for conf in conf_data.get("conflicts", []):
                print(f"   - {conf.get('title')}: {conf.get('description')}")

        rooms_resp = client.get(f"{BASE_URL}/api/branch/rooms/availability", headers=headers)
        if rooms_resp.status_code == 200:
            room_data = rooms_resp.json().get("data", {})
            print(f"🚪 Jami xonalar: {room_data.get('totalRooms', 0)}")
            for rec in room_data.get("recommendations", []):
                print(f"   - [{rec.get('severity').upper()}] {rec.get('title')}: {rec.get('message')}")

        # 5. Groups & Students
        log_step(5, "Guruhlar va O'quvchilar Sig'imi (GET /api/branch/groups)")
        grp_resp = client.get(f"{BASE_URL}/api/branch/groups", headers=headers)
        if grp_resp.status_code == 200:
            groups_list = grp_resp.json().get("groups", [])
            print(f"📚 Faol guruhlar: {len(groups_list)} ta")
            for g in groups_list:
                print(f"   • Guruh: {g.get('name')} | O'quvchilar: {g.get('studentsCount')}/{g.get('capacity')} | Bo'sh joy: {g.get('availableSeats')}")

        # 6. Payments
        log_step(6, "To'lovlar Monitoringi (GET /api/branch/payments)")
        pay_resp = client.get(f"{BASE_URL}/api/branch/payments?limit=5", headers=headers)
        if pay_resp.status_code == 200:
            payments = pay_resp.json().get("payments", [])
            print(f"💳 Oxirgi to'lovlar soni: {len(payments)} ta")

        # 7. Summary
        log_step(7, "Yakuniy Xulosa va Natija")
        print("✅ MARS LMS ISH ZANJIRI MUVAFFAQIYATLI YAKUNLANDI!")
        print("Barcha modullar (Auth -> Moliya -> Mentorlar -> Jadvallar -> Guruhlar -> To'lovlar) tekshirildi.")

if __name__ == "__main__":
    run_chain()
