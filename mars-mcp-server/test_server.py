import os
import sys
import json

# server.py dan barcha tool larni import qilamiz
from server import (
    login,
    branch_me,
    groups,
    students,
    mentors,
    payments,
    finance_overview,
    finance_salaries,
    rooms_availability,
    schedule_conflicts,
    mentor_workload
)

print("=" * 60)
print("MARS LMS MCP SERVER - AVTOMATIK TEST")
print("=" * 60)

# 1. Tokensi holda chaqirish tekshiruvi (xato qaytarishi kerak)
print("\n[TEST 1] Tokensi holatda branch_me() chaqirish:")
res_no_token = branch_me()
print(res_no_token)
assert "HTTP 401" in res_no_token or "Token topilmadi" in res_no_token
print("-> TEST 1 MUVAFFAQISHLI: Token yo'qligi xatosi to'g'ri qaytarildi.")

# 2. Noto'g'ri login ma'lumotlari bilan login() chaqirish (backend xatosi)
print("\n[TEST 2] Noto'g'ri login ma'lumotlari bilan tekshirish:")
res_wrong_login = login(phone="998900000000", password="wrong_password_xyz", role="admin")
print(res_wrong_login)
assert "HTTP 401" in res_wrong_login or "XATO" in res_wrong_login
print("-> TEST 2 MUVAFFAQISHLI: Backend HTTP 401 xatosi jim yutilmadi va foydalanuvchiga qaytarildi.")

# 3. To'g'ri demo admin ma'lumotlari bilan login() chaqirish
print("\n[TEST 3] To'g'ri demo hisob (998935344549 / 1234) bilan login():")
res_login = login()
print(res_login)
assert "MUVAFFAQIYATLI" in res_login
print("-> TEST 3 MUVAFFAQISHLI: Token muvaffaqiyatli xotirada saqlandi.")

# 4. branch_me() chaqirish (saqlangan token bilan)
print("\n[TEST 4] branch_me() chaqirish:")
res_branch = branch_me()
print(res_branch[:300] + "..." if len(res_branch) > 300 else res_branch)
assert "Demo Admin" in res_branch or "success" in res_branch
print("-> TEST 4 MUVAFFAQISHLI: Filial admini va filial ma'lumotlari olindi.")

# 5. groups() chaqirish
print("\n[TEST 5] groups() chaqirish:")
res_groups = groups()
print(res_groups[:300] + "..." if len(res_groups) > 300 else res_groups)
assert "groups" in res_groups or "success" in res_groups
print("-> TEST 5 MUVAFFAQISHLI: Filial guruhlari olindi.")

# 6. students() chaqirish
print("\n[TEST 6] students() chaqirish:")
res_students = students(limit=3)
print(res_students[:300] + "..." if len(res_students) > 300 else res_students)
assert "students" in res_students or "success" in res_students
print("-> TEST 6 MUVAFFAQISHLI: Talabalar ro'yxati olindi.")

# 7. mentors() chaqirish
print("\n[TEST 7] mentors() chaqirish:")
res_mentors = mentors()
print(res_mentors[:300] + "..." if len(res_mentors) > 300 else res_mentors)
assert "mentors" in res_mentors or "success" in res_mentors
print("-> TEST 7 MUVAFFAQISHLI: Mentorlar ro'yxati olindi.")

# 8. payments() chaqirish
print("\n[TEST 8] payments() chaqirish:")
res_payments = payments(limit=3)
print(res_payments[:300] + "..." if len(res_payments) > 300 else res_payments)
assert "payments" in res_payments or "success" in res_payments
print("-> TEST 8 MUVAFFAQISHLI: To'lovlar ro'yxati olindi.")

# 9. finance_overview() chaqirish
print("\n[TEST 9] finance_overview() chaqirish:")
res_fin_overview = finance_overview()
print(res_fin_overview[:300] + "..." if len(res_fin_overview) > 300 else res_fin_overview)
assert "overview" in res_fin_overview or "success" in res_fin_overview
print("-> TEST 9 MUVAFFAQISHLI: Moliya xulosasi olindi.")

# 10. finance_salaries() chaqirish
print("\n[TEST 10] finance_salaries() chaqirish:")
res_fin_salaries = finance_salaries(limit=3)
print(res_fin_salaries[:300] + "..." if len(res_fin_salaries) > 300 else res_fin_salaries)
assert "salaries" in res_fin_salaries or "success" in res_fin_salaries
print("-> TEST 10 MUVAFFAQISHLI: Xodimlar oylik maoshlari ma'lumotlari olindi.")

# 11. rooms_availability() chaqirish (7-topshiriq)
print("\n[TEST 11] rooms_availability() chaqirish (7-topshiriq):")
res_rooms = rooms_availability()
print(res_rooms[:300] + "..." if len(res_rooms) > 300 else res_rooms)
assert "totalRooms" in res_rooms or "success" in res_rooms or "availableRooms" in res_rooms
print("-> TEST 11 MUVAFFAQISHLI: Xonalar bo'shligi va vaqt slotlari olindi.")

# 12. schedule_conflicts() chaqirish (7-topshiriq)
print("\n[TEST 12] schedule_conflicts() chaqirish (7-topshiriq):")
res_conflicts = schedule_conflicts()
print(res_conflicts[:300] + "..." if len(res_conflicts) > 300 else res_conflicts)
assert "conflicts" in res_conflicts or "hasConflicts" in res_conflicts or "success" in res_conflicts
print("-> TEST 12 MUVAFFAQISHLI: Dars jadvallari va xonalar to'qnashuvi tahlili olindi.")

# 13. mentor_workload() chaqirish (8-topshiriq)
print("\n[TEST 13] mentor_workload() chaqirish (8-topshiriq):")
res_workload = mentor_workload()
print(res_workload[:300] + "..." if len(res_workload) > 300 else res_workload)
assert "canTakeNewGroup" in res_workload or "availableMentorsCount" in res_workload or "success" in res_workload
print("-> TEST 13 MUVAFFAQISHLI: Mentorlar yuklama balansi va tavsiyalar olindi.")

print("\n" + "=" * 60)
print("BARCHA 13 TA TEST MUVAFFAQIYATLI O'TDI!")
print("=" * 60)
