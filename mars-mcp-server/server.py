import os
import sys
import json
import httpx
from typing import Optional, Dict, Any

try:
    from mcp.server.mcpserver import MCPServer
except ImportError:
    from mcp.server.fastmcp import FastMCP as MCPServer

# Backend URL sozlamasi
BASE_URL = os.getenv("MARS_BASE_URL", "https://mars-backend-six.vercel.app").rstrip("/")

# Xotirada tokenni saqlash (in-memory token)
AUTH_TOKEN: Optional[str] = os.getenv("MARS_AUTH_TOKEN", None)

mcp = MCPServer("mars-lms-server")


def _get_headers() -> Dict[str, str]:
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    if AUTH_TOKEN:
        headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    return headers


def _handle_response(resp: httpx.Response) -> str:
    try:
        data = resp.json()
        formatted = json.dumps(data, ensure_ascii=False, indent=2)
    except Exception:
        data = None
        formatted = resp.text

    if resp.status_code >= 400:
        error_msg = ""
        if isinstance(data, dict):
            error_msg = data.get("message") or data.get("error") or data.get("detail") or formatted
        else:
            error_msg = formatted
        return f"[XATO: HTTP {resp.status_code}] {error_msg}\nStatus: {resp.status_code}\nJavob:\n{formatted}"

    return formatted


def _make_get_request(path: str, params: Optional[Dict[str, Any]] = None) -> str:
    global AUTH_TOKEN
    if not AUTH_TOKEN:
        return (
            "[XATO: HTTP 401] Token topilmadi. Avval login(phone, password, role) toolini chaqiring!\n"
            "Demo hisob: phone='998935344549', password='1234', role='admin'"
        )

    clean_params = {k: v for k, v in params.items() if v is not None} if params else None
    url = f"{BASE_URL}{path}"
    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.get(url, headers=_get_headers(), params=clean_params)
            return _handle_response(resp)
    except httpx.TimeoutException:
        return f"[XATO: TIMEOUT] {url} ga so'rov 15 soniya ichida javob bermadi."
    except httpx.ConnectError as e:
        return f"[XATO: TARMOQ] Backend bilan bog'lanishda xatolik ({url}): {type(e).__name__} - {str(e)}"
    except Exception as e:
        return f"[XATO: KUTILMAGAN]: {type(e).__name__}: {str(e)}"


@mcp.tool()
def login(phone: str = "998935344549", password: str = "1234", role: str = "admin") -> str:
    """MARS LMS backendiga login qilish va JWT tokenni xotirada saqlash.

    Args:
        phone: Telefon raqami (masalan: 998935344549). Standart: demo admin
        password: Parol (masalan: 1234). Standart: demo admin
        role: Rol (admin, bm, mentor, financeManager, ceo, tutor va h.k.). Standart: admin
    """
    global AUTH_TOKEN
    url = f"{BASE_URL}/api/auth/login"
    payload = {
        "phone": phone,
        "password": password,
        "role": role
    }

    try:
        with httpx.Client(timeout=15.0) as client:
            resp = client.post(url, json=payload, headers={"Content-Type": "application/json", "Accept": "application/json"})
            if resp.status_code == 200:
                body = resp.json()
                token = body.get("token") or body.get("accessToken")
                if token:
                    AUTH_TOKEN = token
                    user_info = body.get("user") or body.get("admin") or {}
                    return (
                        f"[MUVAFFAQIYATLI] Login bajarildi! Token xotirada saqlandi.\n"
                        f"Foydalanuvchi: {user_info.get('fullname', 'Nomaʼlum')}\n"
                        f"Rol: {body.get('role', role)}\n"
                        f"Telefon: {user_info.get('phone', phone)}\n"
                        f"Filial ID: {user_info.get('branch', 'N/A')}\n"
                        f"Token prefiksi: {token[:15]}..."
                    )
                return f"[OGOHLANTIRISH: HTTP 200] 200 qaytdi, lekin javobda token topilmadi:\n{json.dumps(body, ensure_ascii=False, indent=2)}"
            return _handle_response(resp)
    except httpx.TimeoutException:
        return "[XATO: TIMEOUT] Login so'rovi 15 soniya ichida javob bermadi."
    except httpx.ConnectError as e:
        return f"[XATO: TARMOQ] Login so'rovida tarmoq xatosi: {e}"
    except Exception as e:
        return f"[XATO: KUTILMAGAN]: {type(e).__name__}: {str(e)}"


@mcp.tool()
def branch_me() -> str:
    """Joriy filial admini va uning filiali ma'lumotlarini olish (/api/branch/me)."""
    return _make_get_request("/api/branch/me")


@mcp.tool()
def groups(status: Optional[str] = None, search: Optional[str] = None) -> str:
    """Filialdagi guruhlar ro'yxatini olish (/api/branch/groups).

    Args:
        status: Guruh holati bo'yicha filter (active, finished, etc.)
        search: Guruh nomi bo'yicha qidiruv
    """
    return _make_get_request("/api/branch/groups", {"status": status, "search": search})


@mcp.tool()
def students(
    month: Optional[str] = None,
    search: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None
) -> str:
    """Filialdagi talabalar ro'yxatini olish (/api/branch/students).

    Args:
        month: Oy filtri (masalan: 2026-11)
        search: O'quvchi ismi yoki telefoni bo'yicha qidiruv
        page: Sahifa raqami
        limit: Sahifadagi talabalar soni
    """
    return _make_get_request("/api/branch/students", {
        "month": month,
        "search": search,
        "page": page,
        "limit": limit
    })


@mcp.tool()
def mentors(search: Optional[str] = None) -> str:
    """Filialdagi mentorlar ro'yxatini olish (/api/branch/mentors).

    Args:
        search: Mentor ismi yoki telefoni bo'yicha qidiruv
    """
    return _make_get_request("/api/branch/mentors", {"search": search})


@mcp.tool()
def payments(
    status: Optional[str] = None,
    method: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None
) -> str:
    """Filialdagi to'lovlar ro'yxatini olish (/api/branch/payments).

    Args:
        status: To'lov holati (paid, pending, cancelled)
        method: To'lov turi (cash, card, transfer)
        page: Sahifa raqami
        limit: Sahifadagi to'lovlar soni
    """
    return _make_get_request("/api/branch/payments", {
        "status": status,
        "method": method,
        "page": page,
        "limit": limit
    })


@mcp.tool()
def finance_overview(start_date: Optional[str] = None, end_date: Optional[str] = None) -> str:
    """Moliya umumiy holati va KPI ko'rsatkichlarini olish (/api/finance/overview).

    Args:
        start_date: Boshlang'ich sana (YYYY-MM-DD)
        end_date: Tugash sanasi (YYYY-MM-DD)
    """
    return _make_get_request("/api/finance/overview", {
        "startDate": start_date,
        "endDate": end_date
    })


@mcp.tool()
def finance_salaries(
    month: Optional[str] = None,
    page: Optional[int] = None,
    limit: Optional[int] = None
) -> str:
    """Xodimlar maoshlari va to'lovlari ro'yxatini olish (/api/finance/salaries).

    Args:
        month: Maosh oyi (YYYY-MM)
        page: Sahifa raqami
        limit: Sahifadagi xodimlar soni
    """
    return _make_get_request("/api/finance/salaries", {
        "month": month,
        "page": page,
        "limit": limit
    })


def _parse_schedule_slot(schedule_str: Optional[str]) -> Dict[str, Any]:
    if not schedule_str or not isinstance(schedule_str, str) or "jadvallanmagan" in schedule_str.lower():
        return {"is_valid": False, "days": "Jadvallanmagan", "time": "Noma’lum", "slot": "Jadvallanmagan"}

    s = schedule_str.lower().strip()
    days = "Boshqa kunlar"
    if any(k in s for k in ["du", "chor", "ju", "toq"]):
        days = "Du-Chor-Ju"
    elif any(k in s for k in ["se", "pay", "shan", "juft"]):
        days = "Se-Pay-Shanba"
    elif any(k in s for k in ["dam", "yakshanba"]):
        days = "Dam olish kunlari"

    import re
    match = re.search(r"([01]?\d|2[0-3]):([0-5]\d)", s)
    hour = int(match.group(1)) if match else 18
    minute = int(match.group(2)) if match else 0
    time_str = f"{hour:02d}:{minute:02d}"

    if hour < 11:
        slot_label = "09:00–11:00 (Ertalab)"
    elif hour < 14:
        slot_label = "11:30–13:30 (Tushki)"
    elif hour < 17:
        slot_label = "14:30–16:30 (Kunduzi)"
    else:
        slot_label = "18:00–20:00 (Kechki pik)"

    return {
        "is_valid": True,
        "days": days,
        "time": time_str,
        "slot": f"{days} {slot_label}"
    }


def _compute_rooms_availability_fallback(days: Optional[str] = None, time_slot: Optional[str] = None) -> str:
    wp_raw = _make_get_request("/api/branch/workload-planning")
    g_raw = _make_get_request("/api/branch/groups")
    try:
        wp_json = json.loads(wp_raw)
        g_json = json.loads(g_raw)
    except Exception:
        return f"[XATO] Backenddan yuklama yoki guruh ma'lumotlarini o'qib bo'lmadi."

    planning = wp_json.get("planning", {})
    overview = planning.get("overview", {})
    total_rooms = overview.get("totalRooms", 0)
    timeslots = planning.get("timeslots", [])
    groups = g_json.get("groups", [])

    if days:
        timeslots = [t for t in timeslots if days.lower() in t.get("slot", "").lower()]

    res = {
        "success": True,
        "message": "success",
        "data": {
            "totalRooms": total_rooms,
            "totalActiveGroups": len(groups),
            "timeslots": timeslots,
            "recommendations": planning.get("recommendations", [])
        }
    }
    return json.dumps(res, ensure_ascii=False, indent=2)


def _compute_schedule_conflicts_fallback() -> str:
    g_raw = _make_get_request("/api/branch/groups")
    try:
        g_json = json.loads(g_raw)
    except Exception:
        return f"[XATO] Backenddan guruh ma'lumotlarini o'qib bo'lmadi:\n{g_raw}"

    groups = g_json.get("groups", g_json if isinstance(g_json, list) else [])
    conflicts = []
    mentor_slots = {}
    unscheduled = []

    for g in groups:
        sched = g.get("schedule")
        slot_info = _parse_schedule_slot(sched)
        g_name = g.get("name", "Noma’lum")
        if not slot_info["is_valid"]:
            unscheduled.append({"name": g_name, "schedule": sched or "Jadvallanmagan"})
            continue

        m_info = g.get("mentor")
        if m_info and isinstance(m_info, dict):
            mid = str(m_info.get("_id"))
            mname = m_info.get("fullname") or "Mentor"
            key = f"{mid}_{slot_info['slot']}"
            if key not in mentor_slots:
                mentor_slots[key] = {"mentor": mname, "slot": slot_info["slot"], "groups": []}
            mentor_slots[key]["groups"].append(g_name)

    for item in mentor_slots.values():
        if len(item["groups"]) > 1:
            conflicts.append({
                "type": "mentor_conflict",
                "severity": "critical",
                "title": f"Mentor to'qnashuvi: {item['mentor']}",
                "description": f"Mentor {item['mentor']} bir vaqtning o'zida ({item['slot']}) bir nechta guruhda dars o'tishi belgilangan: {', '.join(item['groups'])}.",
                "solution": "Guruhlardan birining jadvalini yoki mentorini o'zgartiring."
            })

    if unscheduled:
        conflicts.append({
            "type": "unscheduled_group",
            "severity": "info",
            "title": f"Jadval belgilanmagan guruhlar ({len(unscheduled)} ta)",
            "description": f"Quyidagi guruhlarning dars jadvali belgilanmagan: {', '.join([u['name'] for u in unscheduled])}.",
            "solution": "Guruhlarga dars kunlari va soatini kiriting."
        })

    res = {
        "success": True,
        "message": "success",
        "data": {
            "hasConflicts": any(c["severity"] == "critical" for c in conflicts),
            "totalConflicts": len(conflicts),
            "conflicts": conflicts
        }
    }
    return json.dumps(res, ensure_ascii=False, indent=2)


def _compute_mentor_workload_fallback(max_groups: int = 3) -> str:
    m_raw = _make_get_request("/api/branch/mentors")
    g_raw = _make_get_request("/api/branch/groups")
    try:
        m_json = json.loads(m_raw)
        g_json = json.loads(g_raw)
    except Exception:
        return f"[XATO] Backenddan mentor yoki guruh ma'lumotlarini o'qib bo'lmadi.\nMentors: {m_raw}\nGroups: {g_raw}"

    mentors = m_json.get("mentors", m_json if isinstance(m_json, list) else [])
    groups = g_json.get("groups", g_json if isinstance(g_json, list) else [])

    mentor_map = {}
    for m in mentors:
        mid = str(m.get("_id"))
        fullname = f"{m.get('firstname', '')} {m.get('lastname', '')}".strip() or m.get("fullname") or "Mentor"
        mentor_map[mid] = {
            "_id": mid,
            "name": fullname,
            "grade": m.get("grade", "Mentor"),
            "groups": [],
            "groupsCount": 0,
            "studentsCount": 0,
            "maxCapacity": max_groups,
            "availableSlots": max_groups,
            "loadPercent": 0,
            "status": "free",
            "canTakeNewGroup": True
        }

    unassigned_groups = []
    for g in groups:
        m_info = g.get("mentor")
        st_count = g.get("studentsCount", 0)
        g_name = g.get("name", "Noma’lum")
        g_sched = g.get("schedule", "Jadvallanmagan")
        if m_info and isinstance(m_info, dict) and "_id" in m_info:
            mid = str(m_info["_id"])
            if mid in mentor_map:
                mentor_map[mid]["groups"].append({"name": g_name, "schedule": g_sched, "studentsCount": st_count})
                mentor_map[mid]["groupsCount"] += 1
                mentor_map[mid]["studentsCount"] += st_count
            else:
                unassigned_groups.append({"name": g_name, "schedule": g_sched})
        else:
            unassigned_groups.append({"name": g_name, "schedule": g_sched})

    for m in mentor_map.values():
        m["availableSlots"] = max(0, m["maxCapacity"] - m["groupsCount"])
        m["loadPercent"] = min(100, round((m["groupsCount"] / m["maxCapacity"]) * 100))
        if m["groupsCount"] == 0:
            m["status"] = "free"
            m["canTakeNewGroup"] = True
        elif m["groupsCount"] < m["maxCapacity"]:
            m["status"] = "available"
            m["canTakeNewGroup"] = True
        elif m["groupsCount"] == m["maxCapacity"]:
            m["status"] = "full"
            m["canTakeNewGroup"] = False
        else:
            m["status"] = "overloaded"
            m["canTakeNewGroup"] = False

    grade_order = {"Senior": 4, "Middle": 3, "Junior": 2, "intern": 1, "Mentor": 2}
    available_mentors = sorted(
        [m for m in mentor_map.values() if m["canTakeNewGroup"]],
        key=lambda x: (x["availableSlots"], grade_order.get(x["grade"], 2)),
        reverse=True
    )
    full_mentors = [m for m in mentor_map.values() if m["status"] == "full"]
    overloaded_mentors = [m for m in mentor_map.values() if m["status"] == "overloaded"]

    recommendations = []
    if available_mentors:
        top_m = available_mentors[0]
        recommendations.append({
            "type": "recommended_assignee",
            "title": f"Yangi guruh uchun eng munosib: {top_m['name']}",
            "message": f"{top_m['name']} ({top_m['grade']}) hozirda {top_m['groupsCount']} ta guruhga ega va yana {top_m['availableSlots']} ta guruh qabul qila oladi (yuklama: {top_m['loadPercent']}%)."
        })
    else:
        recommendations.append({
            "type": "no_available_mentors",
            "title": "Barcha mentorlar band!",
            "message": "Filialdagi barcha mentorlar to'liq yuklamada dars bermoqda. Yangi mentor jalb qilinishi lozim."
        })

    res = {
        "success": True,
        "message": "success",
        "data": {
            "summary": {
                "totalMentors": len(mentor_map),
                "totalGroups": len(groups),
                "availableMentorsCount": len(available_mentors),
                "fullMentorsCount": len(full_mentors),
                "overloadedMentorsCount": len(overloaded_mentors),
                "unassignedGroupsCount": len(unassigned_groups)
            },
            "canTakeNewGroup": [{
                "_id": m["_id"],
                "name": m["name"],
                "grade": m["grade"],
                "currentGroups": m["groupsCount"],
                "availableSlots": m["availableSlots"],
                "loadPercent": m["loadPercent"]
            } for m in available_mentors],
            "cannotTakeNewGroup": [{
                "_id": m["_id"],
                "name": m["name"],
                "grade": m["grade"],
                "currentGroups": m["groupsCount"],
                "status": m["status"],
                "reason": "Limitdan oshgan" if m["status"] == "overloaded" else "To'liq band (3/3 guruh)"
            } for m in (full_mentors + overloaded_mentors)],
            "unassignedGroups": unassigned_groups,
            "allMentors": list(mentor_map.values()),
            "recommendations": recommendations
        }
    }
    return json.dumps(res, ensure_ascii=False, indent=2)


@mcp.tool()
def rooms_availability(days: Optional[str] = None, time_slot: Optional[str] = None) -> str:
    """7. Xonalar bo'shligi va dars jadvallari bo'yicha bandlik tahlili (/api/branch/rooms/availability).
    Filialdagi qaysi xonalar bo'sh, qaysilari band ekanligini va qachon yangi dars qo'yish mumkinligini aniqlaydi.

    Args:
        days: Kun filtri (masalan: Du-Chor-Ju, Se-Pay-Shanba)
        time_slot: Vaqt filtri (masalan: 18:00, 09:00)
    """
    res = _make_get_request("/api/branch/rooms/availability", {"days": days, "time": time_slot})
    if "[XATO: HTTP 404]" not in res:
        return res
    return _compute_rooms_availability_fallback(days, time_slot)


@mcp.tool()
def schedule_conflicts() -> str:
    """7. Jadval va xonalar to'qnashuvini topish (/api/branch/schedule/conflicts).
    Bir xonaga bir vaqtda 2 ta guruh yoki bir mentorga bir vaqtda 2 ta dars tushib qolganini aniqlaydi.
    """
    res = _make_get_request("/api/branch/schedule/conflicts")
    if "[XATO: HTTP 404]" not in res:
        return res
    return _compute_schedule_conflicts_fallback()


@mcp.tool()
def mentor_workload(max_groups: int = 3) -> str:
    """8. Mentorlar yuklama balansi (/api/branch/mentors/workload yoki /api/branch/mentors + /api/branch/groups).
    Kim band, kim bo'sh, kimga yangi guruh berish mumkinligini aniqlaydi.

    Args:
        max_groups: Bitta mentorga tavsiya etilgan maksimal guruhlar soni (standart: 3)
    """
    res = _make_get_request("/api/branch/mentors/workload", {"maxGroups": max_groups})
    if "[XATO: HTTP 404]" not in res:
        return res
    return _compute_mentor_workload_fallback(max_groups)


if __name__ == "__main__":
    mcp.run(transport="stdio")
