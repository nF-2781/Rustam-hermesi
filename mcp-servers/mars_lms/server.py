"""MARS LMS uchun MCP server (stdio).

Hermes ichida ishlaydi: `config.yaml` dagi `mcp_servers.mars_lms` yozuvi shu faylni
stdio orqali ishga tushiradi. Server 10 ta workflow-agent toolini va ular uchun
ma'lumot beruvchi yordamchi tool'larni taqdim etadi.

Muhim qoidalar:
- `stdout` faqat JSON-RPC uchun; barcha loglar `stderr` ga yoziladi.
- Token xotirada saqlanadi, diskka chiqmaydi.
- Har bir tool yagona konvert qaytaradi: error/status_code/message/endpoint/details.
"""

from __future__ import annotations

import functools
import logging
import re
import sys
from datetime import date, datetime, timedelta
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

from lms_client import ENDPOINTS, LMSError, LMSClient, envelope
from profile_tools import register_profile_tools

logging.basicConfig(level=logging.INFO, stream=sys.stderr, format="%(asctime)s %(levelname)s %(name)s %(message)s")
logger = logging.getLogger("mars_lms.server")

CLIENT = LMSClient()

mcp = FastMCP(
    "mars-lms",
    instructions=(
        "MARS IT LMS filiali ma'lumotlari bilan ishlaydigan tool'lar. Avval `lms_login` "
        "chaqiring. Hisobot agentlari (`src` bilan boshlanmaydigan workflow tool'lari) "
        "login, ma'lumot yig'ish va tahlilni o'zi bajaradi va tayyor hisobot hamda "
        "yuborishga tayyor xabar matnlarini qaytaradi."
    ),
)

# ---------------------------------------------------------------------------
# Umumiy yordamchilar
# ---------------------------------------------------------------------------


def tool_guard(func):
    """Har qanday kutilmagan xatoni ham yagona konvertga aylantiradi."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except LMSError as exc:
            return exc.as_envelope()
        except ValueError as exc:
            return envelope(error=str(exc), status_code=400, message=str(exc), endpoint="local")
        except Exception as exc:  # noqa: BLE001 - agentga aniq xabar qaytarish muhim
            logger.exception("tool xatosi: %s", func.__name__)
            return envelope(
                error=f"Kutilmagan server xatosi: {type(exc).__name__}: {exc}",
                status_code=500,
                message="Tool ichida kutilmagan xato. Parametrlarni tekshirib qayta urinib ko'ring.",
                endpoint="local",
            )

    return wrapper


_NO_PHONE = "telefon yo'q"


def _money(value: Any) -> str:
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        return "0 UZS"
    return f"{amount:,.0f}".replace(",", " ") + " UZS"


def _month_or_default(month: Optional[str]) -> str:
    if not month:
        return date.today().strftime("%Y-%m")
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", month):
        raise ValueError("`month` YYYY-MM formatida bo'lishi kerak (masalan 2026-11).")
    return month


def _previous_month(month: str) -> str:
    year, mon = (int(part) for part in month.split("-"))
    return f"{year - 1}-12" if mon == 1 else f"{year}-{mon - 1:02d}"


def _slice(rows: list, limit: int, offset: int = 0) -> tuple[list, dict]:
    total = len(rows)
    limit = max(1, min(int(limit or 20), 100))
    offset = max(0, int(offset or 0))
    page = rows[offset: offset + limit]
    return page, {
        "total": total,
        "returned": len(page),
        "offset": offset,
        "limit": limit,
        "has_more": offset + len(page) < total,
        "next_offset": offset + len(page) if offset + len(page) < total else None,
    }


def _norm(text: Any) -> str:
    return str(text or "").strip().lower()


def _groups() -> list:
    return list(CLIENT.get(ENDPOINTS["groups"]).get("groups") or [])


def _students() -> list:
    return list(CLIENT.get(ENDPOINTS["students"]).get("students") or [])


def _debtors(month: Optional[str] = None, status: Optional[str] = None, search: Optional[str] = None) -> dict:
    params: dict = {}
    if month:
        params["month"] = month
    if status:
        params["status"] = status
    if search:
        params["search"] = search
    return CLIENT.get(ENDPOINTS["debtors"], params or None)


def _attendance(
    group_id: Optional[str] = None,
    student_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    limit: int = 90,
) -> list:
    params: dict = {"page": max(1, int(page)), "limit": max(1, min(int(limit), 100))}
    if group_id:
        params["groupId"] = group_id
    if student_id:
        params["studentId"] = student_id
    if date_from:
        params["from"] = date_from
    if date_to:
        params["to"] = date_to
    return list(CLIENT.get(ENDPOINTS["attendance"], params).get("attendance") or [])


def _homework(group_id: Optional[str] = None) -> list:
    rows = list(CLIENT.get(ENDPOINTS["homework"]).get("homework") or [])
    if group_id:
        rows = [hw for hw in rows if str((hw.get("group") or {}).get("_id")) == str(group_id)]
    return rows


def _branch_overview(month: Optional[str] = None) -> dict:
    params = {"month": month} if month else None
    return CLIENT.get(ENDPOINTS["overview"], params).get("overview") or {}


def _finance_overview() -> dict:
    return CLIENT.get(ENDPOINTS["finance_overview"]).get("overview") or {}


def _planning(max_groups_per_mentor: int = 3) -> dict:
    return CLIENT.get(ENDPOINTS["workload"], {"maxGroupsPerMentor": max_groups_per_mentor}).get("planning") or {}


def _status_requests(status: Optional[str] = "pending") -> list:
    params: dict = {"page": 1, "limit": 100}
    if status:
        params["status"] = status
    return list(CLIENT.get(ENDPOINTS["status_requests"], params).get("requests") or [])


def _waitlist(status: Optional[str] = None) -> list:
    params = {"status": status} if status else None
    return list(CLIENT.get(ENDPOINTS["waitlist"], params).get("items") or [])


def _inactive_students(threshold: int = 7) -> list:
    return list(CLIENT.get(ENDPOINTS["inactive_students"], {"threshold": threshold}).get("students") or [])


def _mentor_name(mentor: Any) -> str:
    if isinstance(mentor, dict):
        full = " ".join(part for part in (mentor.get("firstname"), mentor.get("lastname")) if part).strip()
        return full or mentor.get("fullname") or "Mentor"
    return "Mentor"


def _student_group(student: dict) -> str:
    group = student.get("group")
    if isinstance(group, dict):
        return group.get("name") or "Guruhsiz"
    return "Guruhsiz"


def _active_students(students: list) -> list:
    return [s for s in students if _norm(s.get("status")) == "active"]


def _attendance_stats(records: list) -> dict:
    """Har bir o'quvchi bo'yicha davomat statistikasi va ketma-ket qoldirilgan darslar."""
    stats: dict[str, dict] = {}
    ordered = sorted(records, key=lambda row: str(row.get("date") or ""), reverse=True)
    for record in ordered:
        group = record.get("group") or {}
        when = str(record.get("date") or "")[:10]
        for mark in record.get("records") or []:
            student = mark.get("student") or {}
            sid = str(student.get("_id") or "")
            if not sid:
                continue
            row = stats.setdefault(
                sid,
                {
                    "student_id": sid,
                    "fullname": student.get("fullname") or "—",
                    "phone": student.get("phone") or "",
                    "group": group.get("name") or "—",
                    "group_id": str(group.get("_id") or ""),
                    "lessons": 0,
                    "present": 0,
                    "absent": 0,
                    "consecutive_absent": 0,
                    "streak_open": True,
                    "last_present": None,
                    "last_absent": None,
                },
            )
            present = bool(mark.get("present"))
            row["lessons"] += 1
            if present:
                row["present"] += 1
                row["streak_open"] = False
                row["last_present"] = row["last_present"] or when
            else:
                row["absent"] += 1
                row["last_absent"] = row["last_absent"] or when
                if row["streak_open"]:
                    row["consecutive_absent"] += 1
    for row in stats.values():
        row["attendance_rate"] = round(row["present"] / row["lessons"] * 100) if row["lessons"] else None
        row.pop("streak_open", None)
    return stats


_WEEKDAY_RE = re.compile(
    r"(yakshanba|payshanba|chorshanba|seshanba|dushanba|shanba|juma|yak|chor|pay|shan|jum|ju|se|du)",
    re.IGNORECASE,
)
_DAY_CODE = {
    "du": "Du",
    "dushanba": "Du",
    "se": "Se",
    "seshanba": "Se",
    "chor": "Chor",
    "chorshanba": "Chor",
    "pay": "Pay",
    "payshanba": "Pay",
    "ju": "Ju",
    "jum": "Ju",
    "juma": "Ju",
    "shan": "Shan",
    "shanba": "Shan",
    "yak": "Yak",
    "yakshanba": "Yak",
}
_TIME_RE = re.compile(r"(\d{1,2})[:.](\d{2})")


def _parse_schedule(text: Any) -> list[dict]:
    """`Se-Pay-Shanba 18:00` kabi matndan kunlar va vaqt oralig'ini ajratadi."""
    raw = str(text or "")
    if not raw.strip():
        return []
    times = [(int(h), int(m)) for h, m in _TIME_RE.findall(raw)]
    if not times:
        return []
    start = times[0]
    end = times[1] if len(times) > 1 else ((start[0] + 2) % 24, start[1])
    days = []
    for match in _WEEKDAY_RE.finditer(raw):
        code = _DAY_CODE.get(match.group(0).lower())
        if code and code not in days:
            days.append(code)
    if not days:
        return []
    return [
        {
            "day": day,
            "start": f"{start[0]:02d}:{start[1]:02d}",
            "end": f"{end[0]:02d}:{end[1]:02d}",
        }
        for day in days
    ]


def _is_overdue(due: Any) -> bool:
    if not due:
        return False
    try:
        parsed = datetime.fromisoformat(str(due).replace("Z", "+00:00"))
    except ValueError:
        return False
    now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
    return parsed < now


# ---------------------------------------------------------------------------
# Sessiya va ma'lumot tool'lari
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def lms_login(phone: str = "", password: str = "", role: str = "", force: bool = False) -> dict:
    """MARS LMS backend'ga login qiladi va sessiya tokenini xotirada saqlaydi.

    Har qanday boshqa tool'dan oldin chaqiriladi. Parametrlar berilmasa
    MARS_PHONE / MARS_PASSWORD / MARS_ROLE muhit o'zgaruvchilari ishlatiladi.
    Token faqat xotirada turadi; jarayon qayta ishga tushsa qayta login kerak.

    Args:
        phone: Telefon raqami (masalan 998990000001). Bo'sh bo'lsa env ishlatiladi.
        password: Parol. Bo'sh bo'lsa env ishlatiladi.
        role: Akkaunt roli (admin, bm, owner, mentor...). Bo'sh bo'lsa env yoki admin.
        force: True bo'lsa mavjud sessiyani tashlab, qaytadan login qiladi.

    Returns:
        envelope: details ichida authenticated, role, user, branch, branch_id, base_url.
    """
    if phone:
        CLIENT.phone = phone
    if password:
        CLIENT.password = password
    if role:
        CLIENT.role = role
    if force:
        CLIENT.token = None
    summary = CLIENT.login(force=force)
    return envelope(message=f"Sessiya tayyor: {summary.get('user') or summary.get('role')}", endpoint=ENDPOINTS["login"], details=summary)


@mcp.tool()
@tool_guard
def lms_context() -> dict:
    """Joriy sessiya holatini va filial bo'yicha umumiy ko'rsatkichlarni qaytaradi.

    Agent ish boshlashdan oldin "kim sifatida ishlayapman va filialda nima bor"
    savoliga javob oladi. Sessiya yo'q bo'lsa avtomatik login qilinadi.
    """
    if not CLIENT.is_authenticated:
        CLIENT.login()
    overview = _branch_overview()
    groups = _groups()
    return envelope(
        endpoint=ENDPOINTS["overview"],
        details={
            "session": CLIENT.session_summary(),
            "counts": {
                "groups": len(groups),
                "active_students": overview.get("activeStudents"),
                "unpaid_students": overview.get("unpaidStudents"),
                "receivable": overview.get("receivable"),
            },
            "overview": overview,
        },
    )


@mcp.tool()
@tool_guard
def list_groups(search: str = "", limit: int = 20, offset: int = 0) -> dict:
    """Filial guruhlari ro'yxati (mentor, jadval, sig'im, o'quvchilar soni bilan).

    Args:
        search: Guruh nomi, yo'nalish yoki mentor bo'yicha matnli filtr.
        limit: Bir javobda qaytariladigan guruhlar soni (1-100, standart 20).
        offset: Sahifalash uchun boshlang'ich indeks.

    Returns:
        envelope: details.groups, details.pagination, details.schedule_hint.
    """
    groups = _groups()
    term = _norm(search)
    if term:
        def match(group: dict) -> bool:
            haystack = " ".join(
                str(value or "")
                for value in (
                    group.get("name"),
                    group.get("direction"),
                    group.get("schedule"),
                    _mentor_name(group.get("mentor")),
                    (group.get("course") or {}).get("title") if isinstance(group.get("course"), dict) else "",
                )
            ).lower()
            return term in haystack

        groups = [group for group in groups if match(group)]
    page, pagination = _slice(groups, limit, offset)
    return envelope(
        endpoint=ENDPOINTS["groups"],
        details={"groups": page, "pagination": pagination},
    )


@mcp.tool()
@tool_guard
def list_students(
    search: str = "",
    group_id: str = "",
    only_debtors: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Filial o'quvchilari ro'yxati (guruh, qarz holati, nofaollik kunlari bilan).

    Args:
        search: Ism, telefon yoki guruh nomi bo'yicha filtr.
        group_id: Faqat shu guruh o'quvchilari (ID `list_groups` dan olinadi).
        only_debtors: True bo'lsa faqat joriy oy uchun qarzi bor o'quvchilar.
        limit: Bir javobdagi yozuvlar soni (1-100).
        offset: Sahifalash uchun boshlang'ich indeks.
    """
    students = _students()
    term = _norm(search)
    if group_id:
        students = [s for s in students if str((s.get("group") or {}).get("_id") or "") == str(group_id)]
    if term:
        students = [
            s
            for s in students
            if term
            in " ".join(
                str(value or "")
                for value in (s.get("fullname"), s.get("phone"), _student_group(s), s.get("direction"))
            ).lower()
        ]
    if only_debtors:
        students = [s for s in students if float((s.get("billing") or {}).get("remaining") or 0) > 0]
    rows = [
        {
            "student_id": str(s.get("_id")),
            "fullname": s.get("fullname"),
            "phone": s.get("phone"),
            "group": _student_group(s),
            "group_id": str((s.get("group") or {}).get("_id") or "") or None,
            "status": s.get("status"),
            "monthly_fee": s.get("monthlyFee"),
            "remaining": (s.get("billing") or {}).get("remaining"),
            "payment_status": (s.get("billing") or {}).get("status"),
            "days_inactive": s.get("daysInactive"),
        }
        for s in students
    ]
    page, pagination = _slice(rows, limit, offset)
    return envelope(endpoint=ENDPOINTS["students"], details={"students": page, "pagination": pagination})


@mcp.tool()
@tool_guard
def get_debts(month: str = "", status: str = "", search: str = "", limit: int = 50) -> dict:
    """Joriy oy uchun qarzdorlar ro'yxati (summa, kechikish kunlari, guruh).

    Args:
        month: Oy `YYYY-MM`. Bo'sh bo'lsa joriy oy.
        status: `overdue` (muddati o'tgan) yoki `unpaid` (muddati o'tmagan).
        search: Ism, telefon yoki guruh bo'yicha filtr.
        limit: Maksimal yozuvlar soni.
    """
    month = _month_or_default(month or None)
    payload = _debtors(month=month, status=status or None, search=search or None)
    debtors = sorted(
        (
            {
                "student_id": str(row.get("_id")),
                "fullname": row.get("fullname"),
                "phone": row.get("phone"),
                "group": _student_group(row),
                "direction": row.get("direction"),
                "remaining": (row.get("billing") or {}).get("remaining"),
                "paid": (row.get("billing") or {}).get("paid"),
                "due": (row.get("billing") or {}).get("due"),
                "days_overdue": (row.get("billing") or {}).get("daysOverdue"),
                "is_overdue": (row.get("billing") or {}).get("isOverdue"),
            }
            for row in payload.get("debtors") or []
        ),
        key=lambda item: (-float(item.get("remaining") or 0), -float(item.get("days_overdue") or 0)),
    )
    page, pagination = _slice(debtors, limit, 0)
    return envelope(
        endpoint=ENDPOINTS["debtors"],
        details={
            "month": payload.get("month") or month,
            "total_remaining": payload.get("totalRemaining"),
            "counts": payload.get("counts"),
            "debtors": page,
            "pagination": pagination,
        },
    )


@mcp.tool()
@tool_guard
def get_attendance(
    group_id: str = "",
    student_id: str = "",
    date_from: str = "",
    date_to: str = "",
    page: int = 1,
    limit: int = 30,
) -> dict:
    """Davomat yozuvlari: guruh, o'quvchi va sana oralig'i bo'yicha.

    Args:
        group_id: Guruh ID (ixtiyoriy).
        student_id: O'quvchi ID (ixtiyoriy).
        date_from: Boshlanish sanasi `YYYY-MM-DD`.
        date_to: Tugash sanasi `YYYY-MM-DD`.
        page: Sahifa raqami (1 dan boshlanadi).
        limit: Bir sahifadagi dars yozuvlari soni (1-100).
    """
    records = _attendance(group_id or None, student_id or None, date_from or None, date_to or None, page, limit)
    lessons = [
        {
            "attendance_id": str(row.get("_id")),
            "date": str(row.get("date") or "")[:10],
            "group": (row.get("group") or {}).get("name"),
            "records": [
                {
                    "student_id": str((mark.get("student") or {}).get("_id") or ""),
                    "fullname": (mark.get("student") or {}).get("fullname"),
                    "present": bool(mark.get("present")),
                    "confirmation": mark.get("confirmation"),
                }
                for mark in row.get("records") or []
            ],
        }
        for row in records
    ]
    return envelope(endpoint=ENDPOINTS["attendance"], details={"lessons": lessons, "page": page, "limit": limit})


@mcp.tool()
@tool_guard
def get_homework(group_id: str = "", limit: int = 30) -> dict:
    """Uy vazifalari: muddat, topshirganlar soni, tekshirilmagan ishlar.

    Args:
        group_id: Guruh ID (ixtiyoriy) — faqat shu guruh vazifalari.
        limit: Maksimal vazifalar soni.
    """
    students = _students()
    homework = _homework(group_id or None)
    by_group: dict[str, list] = {}
    for student in students:
        if _norm(student.get("status")) != "active":
            continue
        by_group.setdefault(str((student.get("group") or {}).get("_id") or ""), []).append(student)
    rows = []
    for hw in homework:
        group = hw.get("group") or {}
        gid = str(group.get("_id") or "")
        active = by_group.get(gid, [])
        submissions = hw.get("submissions") or []
        submitted_ids = {str((sub.get("student") or sub.get("studentId") or "")) for sub in submissions}
        missing = [s.get("fullname") for s in active if str(s.get("_id")) not in submitted_ids]
        rows.append(
            {
                "homework_id": str(hw.get("_id")),
                "title": hw.get("title"),
                "group": group.get("name"),
                "group_id": gid,
                "due_date": str(hw.get("dueDate") or "")[:10] or None,
                "is_overdue": _is_overdue(hw.get("dueDate")),
                "active_students": len(active),
                "submitted": len(submitted_ids & {str(s.get("_id")) for s in active}),
                "missing_count": len(missing),
                "missing_students": missing,
            }
        )
    rows.sort(key=lambda item: (not item["is_overdue"], -item["missing_count"]))
    page, pagination = _slice(rows, limit, 0)
    return envelope(endpoint=ENDPOINTS["homework"], details={"homework": page, "pagination": pagination})


@mcp.tool()
@tool_guard
def get_finance_report(month: str = "") -> dict:
    """Filial moliyasi: tushum, xarajat, qoldiq, qarzdorlik va to'lov usullari.

    Args:
        month: Oy `YYYY-MM`. Bo'sh bo'lsa joriy oy.
    """
    month_value = _month_or_default(month or None)
    branch = _branch_overview(month_value)
    finance = _finance_overview()
    return envelope(
        endpoint=ENDPOINTS["overview"],
        details={"month": month_value, "branch": branch, "finance": finance},
    )


@mcp.tool()
@tool_guard
def get_payments(page: int = 1, limit: int = 20, month: str = "") -> dict:
    """Filial to'lovlari ro'yxati (o'quvchi, summa, usul, holat, sana).

    Args:
        page: Sahifa raqami.
        limit: Sahifadagi yozuvlar soni (1-100).
        month: Oy `YYYY-MM` (ixtiyoriy filtr).
    """
    params: dict = {"page": max(1, int(page)), "limit": max(1, min(int(limit), 100))}
    if month:
        params["month"] = _month_or_default(month)
    payload = CLIENT.get(ENDPOINTS["payments"], params)
    return envelope(
        endpoint=ENDPOINTS["payments"],
        details={
            "payments": payload.get("payments") or [],
            "pagination": {key: payload.get(key) for key in ("total", "page", "pages") if key in payload},
        },
    )


@mcp.tool()
@tool_guard
def get_pending_approvals() -> dict:
    """Tasdiq kutayotgan so'rovlar: o'quvchi holati so'rovlari va kutish ro'yxati.

    Filialda tasdiq kutayotgan barcha so'rovlarni bitta joyda beradi.
    """
    requests_raw = _status_requests("pending")
    waiting = _waitlist("waiting")
    requests = [
        {
            "request_id": str(row.get("_id")),
            "type": row.get("type") or "status_change",
            "status": row.get("status"),
            "student": (row.get("student") or {}).get("fullname") if isinstance(row.get("student"), dict) else row.get("student"),
            "student_id": str((row.get("student") or {}).get("_id") or "") if isinstance(row.get("student"), dict) else "",
            "requested_status": row.get("requestedStatus") or row.get("targetStatus"),
            "reason": row.get("reason") or row.get("note") or "",
            "created_at": row.get("createdAt"),
        }
        for row in requests_raw
    ]
    waitlist = [
        {
            "request_id": str(row.get("_id")),
            "type": "waitlist",
            "fullname": row.get("fullname"),
            "phone": row.get("phone"),
            "direction": row.get("direction"),
            "created_at": row.get("createdAt"),
        }
        for row in waiting
    ]
    return envelope(
        endpoint=ENDPOINTS["status_requests"],
        details={"requests": requests, "waitlist": waitlist, "counts": {"requests": len(requests), "waitlist": len(waitlist)}},
    )


@mcp.tool()
@tool_guard
def get_room_plan(max_groups_per_mentor: int = 3) -> dict:
    """Xonalar, vaqt slotlari va mentor yuklamasi bo'yicha rejalashtirish ma'lumoti.

    Args:
        max_groups_per_mentor: Bitta mentorga tavsiya etilgan maksimal guruhlar soni.
    """
    planning = _planning(max_groups_per_mentor)
    groups = _groups()
    schedule_rows = [
        {
            "group": group.get("name"),
            "group_id": str(group.get("_id")),
            "mentor": _mentor_name(group.get("mentor")),
            "mentor_id": str((group.get("mentor") or {}).get("_id") or ""),
            "room_id": str(group.get("room") or "") or None,
            "schedule_raw": group.get("schedule"),
            "slots": _parse_schedule(group.get("schedule")),
        }
        for group in groups
    ]
    return envelope(
        endpoint=ENDPOINTS["workload"],
        details={"planning": planning, "groups": schedule_rows},
    )


@mcp.tool()
@tool_guard
def get_student_progress(student_id: str = "", days: int = 60) -> dict:
    """Bitta o'quvchi bo'yicha davomat, uy vazifasi va to'lov ko'rsatkichlari.

    Args:
        student_id: O'quvchi ID (`list_students` dan).
        days: Necha kunlik davomat tarixini hisoblash (1-180).
    """
    if not student_id:
        raise ValueError("`student_id` majburiy. ID ni `list_students` toolidan oling.")
    students = _students()
    student = next((row for row in students if str(row.get("_id")) == str(student_id)), None)
    if student is None:
        raise ValueError(f"O'quvchi topilmadi: {student_id}. `list_students` bilan ID ni tekshiring.")
    date_from = (date.today() - timedelta(days=max(1, min(int(days), 180)))).isoformat()
    records = _attendance(student_id=student_id, date_from=date_from, page=1, limit=100)
    stats = _attendance_stats(records).get(str(student_id), {})
    group_id = str((student.get("group") or {}).get("_id") or "")
    homework = _homework(group_id or None)
    submitted_titles = set()
    for hw in homework:
        for sub in hw.get("submissions") or []:
            if str(sub.get("student") or sub.get("studentId") or "") == str(student_id):
                submitted_titles.add(str(hw.get("_id")))
    overdue_missing = [
        {
            "homework_id": str(hw.get("_id")),
            "title": hw.get("title"),
            "due_date": str(hw.get("dueDate") or "")[:10] or None,
        }
        for hw in homework
        if _is_overdue(hw.get("dueDate")) and str(hw.get("_id")) not in submitted_titles
    ]
    return envelope(
        endpoint=ENDPOINTS["attendance"],
        details={
            "student": {
                "student_id": str(student.get("_id")),
                "fullname": student.get("fullname"),
                "phone": student.get("phone"),
                "group": _student_group(student),
                "status": student.get("status"),
                "days_inactive": student.get("daysInactive"),
                "billing": student.get("billing"),
            },
            "attendance": stats,
            "homework": {"overdue_missing": overdue_missing, "missing_count": len(overdue_missing)},
        },
    )


# ---------------------------------------------------------------------------
# 1. Qarzdorlik nazoratchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def debt_control_agent(month: str = "", min_days_overdue: int = 0, limit: int = 50) -> dict:
    """Qarzdorlik nazoratchisi: qarzdorlarni saralaydi va eslatma matnlarini tayyorlaydi.

    Ish zanjiri: login -> `/api/branch/debtors` -> qarz miqdori va kechikish kuniga
    qarab saralash -> filial administratori uchun hisobot va yuborishga tayyor
    eslatma matnlari.

    Args:
        month: Oy `YYYY-MM`. Bo'sh bo'lsa joriy oy.
        min_days_overdue: Faqat shu kundan ko'p kechikkanlar (0 = barchasi).
        limit: Hisobotga kiradigan maksimal qarzdorlar soni.
    """
    month_value = _month_or_default(month or None)
    payload = _debtors(month=month_value)
    branch = _branch_overview(month_value)
    debtors = []
    for row in payload.get("debtors") or []:
        billing = row.get("billing") or {}
        days_overdue = int(billing.get("daysOverdue") or 0)
        if days_overdue < int(min_days_overdue or 0):
            continue
        remaining = float(billing.get("remaining") or 0)
        debtors.append(
            {
                "student_id": str(row.get("_id")),
                "fullname": row.get("fullname"),
                "phone": row.get("phone"),
                "group": _student_group(row),
                "direction": row.get("direction"),
                "remaining": remaining,
                "remaining_text": _money(remaining),
                "paid": billing.get("paid"),
                "due": billing.get("due"),
                "days_overdue": days_overdue,
                "due_date": billing.get("dueDate"),
                "severity": "critical" if days_overdue >= 14 else ("warning" if days_overdue > 0 else "info"),
                "group_id": str((row.get("group") or {}).get("_id") or "") or None,
            }
        )
    debtors.sort(key=lambda item: (-item["days_overdue"], -item["remaining"]))
    page, pagination = _slice(debtors, limit, 0)
    total = sum(item["remaining"] for item in page)
    critical = [item for item in page if item["severity"] == "critical"]
    messages = [
        {
            "student_id": item["student_id"],
            "fullname": item["fullname"],
            "phone": item["phone"],
            "channel": "telefon / Telegram",
            "text": (
                f"Assalomu alaykum, {item['fullname']}! MARS IT LMS filialidan yozmoqdamiz. "
                f"{month_value} oyi uchun to'lov qarzi {item['remaining_text']} "
                f"({item['days_overdue']} kun kechikkan). Iltimos, to'lovni {item['due_date'] or 'tez orada'} "
                "gacha amalga oshiring yoki sababini biz bilan bo'lishingizni so'raymiz."
            ),
        }
        for item in page
    ]
    report_lines = [
        f"# Qarzdorlik hisoboti — {month_value}",
        "",
        f"- Jami qarzdor: **{len(debtors)}**",
        f"- Jami qarz: **{_money(payload.get('totalRemaining') or total)}**",
        f"- Muddati o'tgan (14+ kun): **{len(critical)}**",
        f"- Filial oylik tushumi: {_money(branch.get('income'))}",
        "",
        "## Saralangan ro'yxat",
    ]
    for index, item in enumerate(page, start=1):
        report_lines.append(
            f"{index}. {item['fullname']} — {item['remaining_text']}, {item['days_overdue']} kun, "
            f"{item['group']}, {item['phone'] or _NO_PHONE}"
        )
    return envelope(
        message=f"{len(debtors)} ta qarzdor aniqlandi",
        endpoint=ENDPOINTS["debtors"],
        details={
            "month": month_value,
            "summary": {
                "debtors": len(debtors),
                "total_remaining": payload.get("totalRemaining"),
                "critical": len(critical),
                "branch_income": branch.get("income"),
                "branch_receivable": branch.get("receivable"),
            },
            "debtors": page,
            "pagination": pagination,
            "message_drafts": messages,
            "report_markdown": "\n".join(report_lines),
            "next_actions": [
                "Eslatmalarni tasdiqlangandan keyin yuborish (yuborish integratsiyasi alohida ulanadi).",
                "14+ kun kechikkanlar uchun filial administratoriga qo'ng'iroq ro'yxatini bering.",
            ],
        },
    )


# ---------------------------------------------------------------------------
# 2. Davomat nazoratchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def attendance_control_agent(consecutive_misses: int = 2, group_id: str = "", lookback_days: int = 30) -> dict:
    """Davomat nazoratchisi: ketma-ket dars qoldirgan o'quvchilarni aniqlaydi.

    Ish zanjiri: login -> guruhlar -> davomat tarixi -> ketma-ket qoldirilgan
    darslar soni -> mentor va administrator uchun ogohlantirish matni.

    Args:
        consecutive_misses: Nechta ketma-ket qoldirilgan dars xavf hisoblanadi (standart 2).
        group_id: Faqat shu guruh (ixtiyoriy).
        lookback_days: Necha kunlik tarix tekshiriladi (1-180).
    """
    threshold = max(1, int(consecutive_misses))
    date_from = (date.today() - timedelta(days=max(1, min(int(lookback_days), 180)))).isoformat()
    records = _attendance(group_id=group_id or None, date_from=date_from, page=1, limit=100)
    stats = _attendance_stats(records)
    students = {str(row.get("_id")): row for row in _students()}
    groups = {str(row.get("_id")): row for row in _groups()}
    at_risk = []
    for row in stats.values():
        if row["consecutive_absent"] < threshold:
            continue
        student = students.get(row["student_id"], {})
        group = groups.get(row["group_id"], {})
        at_risk.append(
            {
                **row,
                "mentor": _mentor_name(group.get("mentor")),
                "mentor_id": str((group.get("mentor") or {}).get("_id") or "") or None,
                "phone": student.get("phone") or row.get("phone"),
                "billing_status": (student.get("billing") or {}).get("status"),
                "risk": "high" if row["consecutive_absent"] >= 3 else "medium",
            }
        )
    at_risk.sort(key=lambda item: (-item["consecutive_absent"], item["attendance_rate"] or 0))
    mentor_warnings: dict[str, dict] = {}
    for row in at_risk:
        mentor = row["mentor"] or "Mentor biriktirilmagan"
        bucket = mentor_warnings.setdefault(mentor, {"mentor": mentor, "students": [], "text_lines": []})
        bucket["students"].append(row["fullname"])
        bucket["text_lines"].append(
            f"- {row['fullname']} ({row['group']}): {row['consecutive_absent']} ta dars ketma-ket qoldirilgan, "
            f"davomat {row['attendance_rate']}%, oxirgi dars {row['last_absent'] or '—'}"
        )
    warnings = [
        {
            "recipient": bucket["mentor"],
            "role": "mentor",
            "text": (
                "Assalomu alaykum! Quyidagi o'quvchilar ketma-ket darslarni qoldirmoqda, "
                "iltimos ular bilan bog'laning:\n" + "\n".join(bucket["text_lines"])
            ),
        }
        for bucket in mentor_warnings.values()
    ]
    admin_summary = (
        f"Davomat nazorati: {len(at_risk)} ta o'quvchi {threshold}+ dars ketma-ket qoldirgan "
        f"(oxirgi {lookback_days} kun). Guruhlar: "
        + ", ".join(sorted({row["group"] for row in at_risk})) or "—"
    )
    report_lines = [f"# Davomat ogohlantirishi ({date.today().isoformat()})", "", admin_summary, ""]
    for row in at_risk:
        report_lines.append(
            f"- **{row['fullname']}** · {row['group']} · {row['consecutive_absent']} dars ketma-ket · "
            f"davomat {row['attendance_rate']}% · mentor: {row['mentor']}"
        )
    if not at_risk:
        report_lines.append("Xavf ostidagi o'quvchi topilmadi — davomat me'yorda.")
    return envelope(
        message=f"{len(at_risk)} ta o'quvchi davomat xavfida",
        endpoint=ENDPOINTS["attendance"],
        details={
            "threshold": threshold,
            "lookback_days": lookback_days,
            "at_risk": at_risk,
            "mentor_warnings": warnings,
            "admin_summary": admin_summary,
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 3. Uy vazifasi nazoratchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def homework_control_agent(group_id: str = "", only_overdue: bool = True, limit: int = 40) -> dict:
    """Uy vazifasi nazoratchisi: topshirilmagan vazifalarni va eslatmalarni tayyorlaydi.

    Ish zanjiri: login -> guruhlar va uy vazifalari -> muddati o'tgan, ammo
    topshirilmagan vazifalarni ajratish -> o'quvchi uchun eslatma va mentor uchun
    umumiy ro'yxat.

    Args:
        group_id: Faqat shu guruh (ixtayoriy).
        only_overdue: True bo'lsa faqat muddati o'tgan vazifalar.
        limit: Hisobotdagi maksimal vazifa soni.
    """
    students = _active_students(_students())
    students_by_group: dict[str, list] = {}
    for student in students:
        students_by_group.setdefault(str((student.get("group") or {}).get("_id") or ""), []).append(student)
    homework = _homework(group_id or None)
    if only_overdue:
        homework = [hw for hw in homework if _is_overdue(hw.get("dueDate"))]
    per_student: dict[str, dict] = {}
    mentor_groups: dict[str, dict] = {}
    rows = []
    for hw in homework:
        group = hw.get("group") or {}
        gid = str(group.get("_id") or "")
        active = students_by_group.get(gid, [])
        submissions = hw.get("submissions") or []
        submitted = {str(sub.get("student") or sub.get("studentId") or "") for sub in submissions}
        missing = [s for s in active if str(s.get("_id")) not in submitted]
        mentor = _mentor_name(group.get("mentor")) if isinstance(group.get("mentor"), dict) else "Mentor"
        rows.append(
            {
                "homework_id": str(hw.get("_id")),
                "title": hw.get("title"),
                "group": group.get("name"),
                "group_id": gid,
                "mentor": mentor,
                "due_date": str(hw.get("dueDate") or "")[:10] or None,
                "active_students": len(active),
                "submitted": len(submitted),
                "missing_count": len(missing),
                "missing_students": [s.get("fullname") for s in missing],
            }
        )
        for student in missing:
            sid = str(student.get("_id"))
            bucket = per_student.setdefault(
                sid,
                {"student_id": sid, "fullname": student.get("fullname"), "phone": student.get("phone"), "group": group.get("name"), "missing": []},
            )
            bucket["missing"].append({"homework_id": str(hw.get("_id")), "title": hw.get("title"), "due_date": str(hw.get("dueDate") or "")[:10] or None})
        mentor_bucket = mentor_groups.setdefault(mentor, {"mentor": mentor, "rows": []})
        if missing:
            mentor_bucket["rows"].append(f"- {hw.get('title')} ({group.get('name')}): {len(missing)} o'quvchi topshirmagan")
    rows.sort(key=lambda item: -item["missing_count"])
    page, pagination = _slice(rows, limit, 0)
    reminders = [
        {
            "student_id": bucket["student_id"],
            "fullname": bucket["fullname"],
            "phone": bucket["phone"],
            "text": (
                f"Assalomu alaykum, {bucket['fullname']}! {bucket['group']} guruhida quyidagi uy vazifalari "
                "topshirilmagan: "
                + "; ".join(f"{item['title']} ({item['due_date']} gacha)" for item in bucket["missing"])
                + ". Iltimos, vazifani platformaga yuklang yoki mentor bilan bog'laning."
            ),
        }
        for bucket in per_student.values()
    ]
    mentor_reports = [
        {
            "recipient": bucket["mentor"],
            "text": "Topshirilmagan uy vazifalari bo'yicha jamlanma:\n" + "\n".join(bucket["rows"]),
        }
        for bucket in mentor_groups.values()
        if bucket["rows"]
    ]
    report_lines = [f"# Uy vazifasi nazorati ({date.today().isoformat()})", ""]
    if not page:
        report_lines.append("Topshirilmagan vazifa topilmadi.")
    for item in page:
        report_lines.append(
            f"- **{item['title']}** · {item['group']} · muddat {item['due_date'] or '—'} · "
            f"topshirmagan: {item['missing_count']}/{item['active_students']}"
        )
    return envelope(
        message=f"{sum(item['missing_count'] for item in rows)} ta topshirilmagan vazifa yozuvi",
        endpoint=ENDPOINTS["homework"],
        details={
            "homework": page,
            "pagination": pagination,
            "students_missing_total": len(per_student),
            "student_reminders": reminders,
            "mentor_reports": mentor_reports,
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 4. Moliya kundalik hisobotchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def daily_finance_report(month: str = "", compare: bool = True) -> dict:
    """Moliya kundalik hisobotchisi: tushum, xarajat, qoldiq va to'lovlar holati.

    Ish zanjiri: login -> filial overview + finance overview -> jamlash ->
    rahbarga qisqa hisobot -> oldingi davr bilan farq.

    Args:
        month: Oy `YYYY-MM`. Bo'sh bo'lsa joriy oy.
        compare: True bo'lsa oldingi oy bilan farqni hisoblaydi.
    """
    month_value = _month_or_default(month or None)
    branch = _branch_overview(month_value)
    finance = _finance_overview()
    previous = None
    if compare:
        prev_month = _previous_month(month_value)
        prev_branch = _branch_overview(prev_month)
        previous = {
            "month": prev_month,
            "income": prev_branch.get("income"),
            "expense": prev_branch.get("expense"),
            "receivable": prev_branch.get("receivable"),
            "active_students": prev_branch.get("activeStudents"),
            "delta": {
                "income": (branch.get("income") or 0) - (prev_branch.get("income") or 0),
                "expense": (branch.get("expense") or 0) - (prev_branch.get("expense") or 0),
                "receivable": (branch.get("receivable") or 0) - (prev_branch.get("receivable") or 0),
            },
        }
    balance = (branch.get("income") or 0) - (branch.get("expense") or 0)
    trend = finance.get("monthlyTrend") or []
    report_lines = [
        f"# Moliya hisoboti — {month_value}",
        "",
        f"- Tushum: **{_money(branch.get('income'))}**",
        f"- Xarajat: **{_money(branch.get('expense'))}**",
        f"- Qoldiq (tushum - xarajat): **{_money(balance)}**",
        f"- Kutilayotgan tushum (qarzdorlik): **{_money(branch.get('receivable'))}**",
        f"- Faol o'quvchilar: {branch.get('activeStudents')} · to'lagan: {branch.get('paidStudents')} · "
        f"qarzdor: {branch.get('unpaidStudents')}",
    ]
    if previous:
        report_lines += [
            "",
            f"## Oldingi oy bilan farq ({previous['month']})",
            f"- Tushum: {_money(previous['delta']['income'])}",
            f"- Xarajat: {_money(previous['delta']['expense'])}",
            f"- Qarzdorlik: {_money(previous['delta']['receivable'])}",
        ]
    report_lines += [
        "",
        "## Umumiy tizim ko'rsatkichlari",
        f"- Jami tushum: {_money(finance.get('totalIncome'))}",
        f"- Jami xarajat: {_money(finance.get('totalExpense'))}",
        f"- Sof foyda: {_money(finance.get('netProfit'))}",
    ]
    return envelope(
        message=f"Moliya hisoboti tayyor: {month_value}",
        endpoint=ENDPOINTS["overview"],
        details={
            "month": month_value,
            "branch": branch,
            "finance": finance,
            "previous_period": previous,
            "balance": balance,
            "trend": trend[:6] if isinstance(trend, list) else trend,
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 5. Yangi o'quvchi kuzatuvchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def new_student_followup(days: int = 14, limit: int = 40) -> dict:
    """Yangi o'quvchi kuzatuvchisi: ro'yxatdan o'tib, jarayoni tugallanmaganlar.

    Ish zanjiri: login -> o'quvchilar, guruhlar va to'lovlar -> qaysi bosqich
    tugallanmaganini aniqlash (guruhga biriktirilmagan / birinchi to'lov yo'q) ->
    reception xodimi uchun follow-up ro'yxati va xabar loyihasi.

    Args:
        days: Oxirgi necha kunda ro'yxatdan o'tganlar tekshiriladi (1-180).
        limit: Maksimal yozuvlar soni.
    """
    horizon = date.today() - timedelta(days=max(1, min(int(days), 180)))
    branches = _branch_overview()
    students = _students()
    fresh = []
    for student in students:
        created = str(student.get("createdAt") or "")[:10]
        if not created:
            continue
        try:
            created_date = date.fromisoformat(created)
        except ValueError:
            continue
        if created_date < horizon:
            continue
        billing = student.get("billing") or {}
        group = student.get("group") if isinstance(student.get("group"), dict) else None
        paid = float(billing.get("paid") or 0)
        steps = {
            "registered": True,
            "assigned_to_group": bool(group),
            "first_payment": paid > 0,
            "direction_selected": bool(student.get("direction")),
        }
        missing_steps = [name for name, done in steps.items() if not done and name != "registered"]
        if not missing_steps:
            continue
        fresh.append(
            {
                "student_id": str(student.get("_id")),
                "fullname": student.get("fullname"),
                "phone": student.get("phone"),
                "created_at": created,
                "direction": student.get("direction"),
                "group": _student_group(student) if group else "Guruhsiz",
                "monthly_fee": student.get("monthlyFee"),
                "paid": paid,
                "missing_steps": missing_steps,
                "stage_text": {
                    "assigned_to_group": "guruhga biriktirilmagan",
                    "first_payment": "birinchi to'lov qilinmagan",
                    "direction_selected": "yo'nalish tanlanmagan",
                },
            }
        )
    fresh.sort(key=lambda item: (-len(item["missing_steps"]), item["created_at"]))
    page, pagination = _slice(fresh, limit, 0)
    followups = [
        {
            "student_id": item["student_id"],
            "fullname": item["fullname"],
            "phone": item["phone"],
            "text": (
                f"Assalomu alaykum, {item['fullname']}! MARS IT LMS'da ro'yxatdan o'tganingiz uchun rahmat. "
                f"Ro'yxatdan o'tish jarayonida quyidagi qadam qolgan: {item['stage_text']}. "
                "Savollaringiz bo'lsa, biz bilan bog'laning — yordam berishga tayyormiz."
            ),
        }
        for item in page
    ]
    report_lines = [
        f"# Yangi o'quvchilar follow-up ({horizon.isoformat()} — {date.today().isoformat()})",
        "",
        f"- Jarayoni tugallanmagan: **{len(fresh)}**",
        f"- Faol o'quvchilar (filial): {branches.get('activeStudents')}",
        "",
    ]
    for item in page:
        report_lines.append(
            f"- **{item['fullname']}** · {item['created_at']} · {item['phone'] or _NO_PHONE} · "
            f"qolgan qadam: {', '.join(item['missing_steps'])}"
        )
    if not page:
        report_lines.append("Barcha yangi o'quvchilar jarayoni yakunlangan.")
    return envelope(
        message=f"{len(fresh)} ta yangi o'quvchi kuzatuvga olindi",
        endpoint=ENDPOINTS["students"],
        details={
            "window_days": days,
            "followups": page,
            "pagination": pagination,
            "message_drafts": followups,
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 6. Tasdiqlarni jamlovchi yordamchi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def pending_approvals_digest(limit: int = 50) -> dict:
    """Tasdiqlarni jamlovchi yordamchi: tasdiq kutayotgan so'rovlarni guruhlaydi.

    Ish zanjiri: login -> tasdiq kutayotgan so'rovlar -> tur, kutish vaqti va
    muhimlik bo'yicha guruhlash -> mas'ul rahbarga umumiy hisobot.

    Args:
        limit: Hisobotdagi maksimal so'rovlar soni.
    """
    pending = get_pending_approvals()
    if pending.get("error"):
        return pending
    details = pending.get("details") or {}
    requests = list(details.get("requests") or []) + list(details.get("waitlist") or [])
    now = datetime.now()
    for item in requests:
        created = item.get("created_at")
        waiting_days = 0
        if created:
            try:
                parsed = datetime.fromisoformat(str(created).replace("Z", "+00:00"))
                waiting_days = max(0, (now - parsed.replace(tzinfo=None)).days)
            except ValueError:
                waiting_days = 0
        item["waiting_days"] = waiting_days
        item["priority"] = "high" if waiting_days >= 3 else ("medium" if waiting_days >= 1 else "low")
    requests.sort(key=lambda item: (-item["waiting_days"], item.get("type") or ""))
    page, pagination = _slice(requests, limit, 0)
    grouped: dict[str, list] = {}
    for item in page:
        grouped.setdefault(item.get("type") or "other", []).append(item)
    report_lines = ["# Tasdiq kutayotgan so'rovlar", "", f"- Jami: **{len(requests)}**", ""]
    for kind, items in grouped.items():
        report_lines.append(f"## {kind} ({len(items)})")
        for item in items:
            who = item.get("fullname") or item.get("student") or "—"
            reason = f" · sabab: {item.get('reason')}" if item.get("reason") else ""
            report_lines.append(f"- {who} · {item['waiting_days']} kun kutmoqda · muhimlik: {item['priority']}{reason}")
        report_lines.append("")
    if not requests:
        report_lines.append("Tasdiq kutayotgan so'rov yo'q.")
    return envelope(
        message=f"{len(requests)} ta so'rov tasdiq kutmoqda",
        endpoint=ENDPOINTS["status_requests"],
        details={
            "requests": page,
            "grouped": {kind: len(items) for kind, items in grouped.items()},
            "pagination": pagination,
            "report_markdown": "\n".join(report_lines),
            "next_actions": ["Har bir guruh bo'yicha mas'ul rahbarga yuborish uchun hisobotdan foydalaning."],
        },
    )


# ---------------------------------------------------------------------------
# 7. Xona va jadval yordamchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def room_schedule_assistant(max_groups_per_mentor: int = 3) -> dict:
    """Xona va jadval yordamchisi: bandlik, to'qnashuvlar va bo'sh vaqtlar.

    Ish zanjiri: login -> guruhlar jadvali va rejalashtirish ma'lumoti -> bir
    mentor yoki xona bir vaqtda bir nechta darsga qo'yilganini tekshirish ->
    administratorga to'qnashuvlar va muqobil variantlar.

    Args:
        max_groups_per_mentor: Rejalashtirish uchun mentor sig'imi (ma'lumot uchun).
    """
    planning = _planning(max_groups_per_mentor)
    groups = _groups()
    slots_map: dict[tuple, list] = {}
    schedule_rows = []
    for group in groups:
        slots = _parse_schedule(group.get("schedule"))
        schedule_rows.append(
            {
                "group": group.get("name"),
                "group_id": str(group.get("_id")),
                "mentor": _mentor_name(group.get("mentor")),
                "room": group.get("room"),
                "schedule_raw": group.get("schedule"),
                "slots": slots,
            }
        )
        for slot in slots:
            slots_map.setdefault((slot["day"], slot["start"]), []).append(
                {
                    "group": group.get("name"),
                    "group_id": str(group.get("_id")),
                    "mentor": _mentor_name(group.get("mentor")),
                    "mentor_id": str((group.get("mentor") or {}).get("_id") or ""),
                    "room_id": str(group.get("room") or "") or None,
                }
            )
    conflicts = []
    for (day, start), items in sorted(slots_map.items()):
        if len(items) < 2:
            continue
        mentor_ids = [item["mentor_id"] for item in items if item["mentor_id"]]
        room_ids = [item["room_id"] for item in items if item["room_id"]]
        if len(set(mentor_ids)) < len(mentor_ids):
            conflicts.append(
                {
                    "type": "mentor_double_booking",
                    "day": day,
                    "start": start,
                    "groups": [item["group"] for item in items],
                    "mentor": items[0]["mentor"],
                    "suggestion": "Guruhlardan birini boshqa vaqt slotiga yoki boshqa mentorga ko'chiring.",
                }
            )
        if len(set(room_ids)) < len(room_ids):
            conflicts.append(
                {
                    "type": "room_double_booking",
                    "day": day,
                    "start": start,
                    "groups": [item["group"] for item in items],
                    "room_id": next(iter(set(room_ids))),
                    "suggestion": "Bir guruhni bo'sh xonaga yoki boshqa vaqtga o'tkazing.",
                }
            )
    rooms = planning.get("rooms") or []
    timeslots = planning.get("timeslots") or []
    empty_slots = [
        {"slot": item.get("slot"), "available_rooms": item.get("availableRooms"), "utilization": item.get("utilizationPercent")}
        for item in timeslots
        if not item.get("isOverCapacity")
    ]
    report_lines = ["# Xona va jadval holati", "", f"- Guruhlar: **{len(groups)}**", f"- To'qnashuvlar: **{len(conflicts)}**", ""]
    if conflicts:
        for item in conflicts:
            report_lines.append(
                f"- {item['type']}: {item['day']} {item['start']} — {', '.join(item['groups'])}. {item['suggestion']}"
            )
    else:
        report_lines.append("Jadval to'qnashuvi aniqlanmadi.")
    if not rooms:
        report_lines.append("\nDiqqat: filialda hali xona kiritilmagan — xona bandligi bo'yicha aniq xulosa cheklangan.")
    return envelope(
        message=f"{len(conflicts)} ta jadval to'qnashuvi aniqlandi",
        endpoint=ENDPOINTS["workload"],
        details={
            "groups": schedule_rows,
            "conflicts": conflicts,
            "rooms": rooms,
            "timeslots": timeslots,
            "free_timeslots": empty_slots,
            "planning_overview": planning.get("overview"),
            "recommendations": planning.get("recommendations") or [],
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 8. Mentor yuklamasi tahlilchisi
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def mentor_workload_analysis(max_groups_per_mentor: int = 3) -> dict:
    """Mentor yuklamasi tahlilchisi: yuklamani solishtiradi va tavsiya beradi.

    Ish zanjiri: login -> mentorlar va guruhlar -> guruhlar soni (va jadval
    ma'lumoti) -> yuklamasi yuqori/past mentorlar -> o'quv bo'limi rahbariga
    taqqoslash va tavsiya.

    Args:
        max_groups_per_mentor: Bitta mentorga me'yoriy guruhlar soni.
    """
    capacity = max(1, int(max_groups_per_mentor))
    planning = _planning(capacity)
    groups = _groups()
    mentors = CLIENT.get(ENDPOINTS["mentors"]).get("mentors") or []
    actual: dict[str, int] = {}
    for group in groups:
        mentor = group.get("mentor")
        if isinstance(mentor, dict) and mentor.get("_id"):
            actual[str(mentor["_id"])] = actual.get(str(mentor["_id"]), 0) + 1
    rows = []
    for mentor in mentors:
        mid = str(mentor.get("_id"))
        count = actual.get(mid, 0)
        load = round(count / capacity * 100)
        rows.append(
            {
                "mentor_id": mid,
                "mentor": _mentor_name(mentor),
                "grade": mentor.get("grade"),
                "groups": count,
                "load_percent": load,
                "status": "overloaded" if count > capacity else ("balanced" if count == capacity else "available"),
            }
        )
    missing_mentors = [row for row in rows if row["groups"] == 0]
    rows.sort(key=lambda item: (-item["groups"], item["mentor"]))
    best = min(rows, key=lambda item: (item["groups"], item["mentor"])) if rows else None
    report_lines = [
        f"# Mentor yuklamasi (me'yor: {capacity} guruh)",
        "",
        f"- Mentorlar: **{len(rows)}** · guruhlar: **{len(groups)}**",
        "",
    ]
    for row in rows:
        report_lines.append(f"- {row['mentor']} ({row['grade'] or '—'}): {row['groups']} guruh, yuklama {row['load_percent']}% — {row['status']}")
    if best:
        report_lines += ["", f"**Tavsiya:** yangi guruhni eng kam yuklamali mentorga — {best['mentor']} ({best['groups']} guruh) — biriktirish mumkin."]
    if missing_mentors:
        report_lines.append(
            "Bo'sh mentorlar: " + ", ".join(row["mentor"] for row in missing_mentors)
        )
    return envelope(
        message=f"{len(rows)} mentor yuklamasi tahlil qilindi",
        endpoint=ENDPOINTS["workload"],
        details={
            "capacity": capacity,
            "mentors": rows,
            "unassigned_mentors": [row["mentor"] for row in missing_mentors],
            "recommended_mentor": best,
            "planning_overview": planning.get("overview"),
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 9. O'quvchi progress auditori
# ---------------------------------------------------------------------------


@mcp.tool()
@tool_guard
def student_progress_audit(group_id: str = "", limit: int = 30, days: int = 60) -> dict:
    """O'quvchi progress auditori: ortda qolayotganlarni aniqlaydi va reja beradi.

    Ish zanjiri: login -> o'quvchilar, davomat va uy vazifasi -> mezonlar bilan
    solishtirish (davomat %, topshirilmagan vazifalar, to'lov, nofaollik) ->
    mentor uchun sabablar va tavsiya etilgan yordam rejasi.

    Args:
        group_id: Faqat shu guruh (ixtiyoriy).
        limit: Hisobotdagi maksimal o'quvchilar soni.
        days: Davomat tarixining chuqurligi (kunlarda).
    """
    date_from = (date.today() - timedelta(days=max(1, min(int(days), 180)))).isoformat()
    students = _active_students(_students())
    if group_id:
        students = [s for s in students if str((s.get("group") or {}).get("_id") or "") == str(group_id)]
    records = _attendance(group_id=group_id or None, date_from=date_from, page=1, limit=100)
    stats = _attendance_stats(records)
    homework = _homework(group_id or None)
    overdue_hw = [hw for hw in homework if _is_overdue(hw.get("dueDate"))]
    submitted_by_student: dict[str, set] = {}
    for hw in overdue_hw:
        for sub in hw.get("submissions") or []:
            sid = str(sub.get("student") or sub.get("studentId") or "")
            submitted_by_student.setdefault(sid, set()).add(str(hw.get("_id")))
    groups = {str(g.get("_id")): g for g in _groups()}
    lagging = []
    for student in students:
        sid = str(student.get("_id"))
        stat = stats.get(sid, {})
        attendance_rate = stat.get("attendance_rate")
        gid = str((student.get("group") or {}).get("_id") or "")
        group_homework = [hw for hw in overdue_hw if str((hw.get("group") or {}).get("_id") or "") == gid]
        missing = [hw for hw in group_homework if str(hw.get("_id")) not in submitted_by_student.get(sid, set())]
        billing = student.get("billing") or {}
        days_inactive = student.get("daysInactive")
        reasons = []
        score = 0
        if attendance_rate is not None and attendance_rate < 75:
            reasons.append(f"davomat past ({attendance_rate}%)")
            score += (75 - attendance_rate)
        if stat.get("consecutive_absent", 0) >= 2:
            reasons.append(f"{stat['consecutive_absent']} dars ketma-ket qoldirilgan")
            score += 15
        if len(missing) >= 2:
            reasons.append(f"{len(missing)} ta uy vazifasi topshirilmagan")
            score += 10 * len(missing)
        if float(billing.get("remaining") or 0) > 0:
            reasons.append("to'lov qarzi bor")
            score += 10
        if days_inactive and int(days_inactive) >= 14:
            reasons.append(f"{days_inactive} kundan beri platformaga kirmagan")
            score += 10
        if not reasons:
            continue
        group = groups.get(gid) or {}
        lagging.append(
            {
                "student_id": sid,
                "fullname": student.get("fullname"),
                "phone": student.get("phone"),
                "group": _student_group(student),
                "mentor": _mentor_name(group.get("mentor")),
                "attendance_rate": attendance_rate,
                "consecutive_absent": stat.get("consecutive_absent", 0),
                "missing_homework": len(missing),
                "remaining_debt": billing.get("remaining"),
                "days_inactive": days_inactive,
                "risk_score": round(score),
                "reasons": reasons,
                "support_plan": [
                    "Mentor bilan 15 daqiqalik individual suhbat o'tkazish.",
                    "Qoldirilgan mavzular bo'yicha qisqa takrorlash darsini belgilash.",
                    "Ota-onaga davomat va uy vazifasi holati bo'yicha xabar yuborish.",
                ],
            }
        )
    lagging.sort(key=lambda item: -item["risk_score"])
    page, pagination = _slice(lagging, limit, 0)
    report_lines = [f"# O'quvchi progress auditi ({date.today().isoformat()})", ""]
    if not page:
        report_lines.append("Barcha o'quvchilar mezonlar bo'yicha me'yorda.")
    for item in page:
        report_lines.append(
            f"- **{item['fullname']}** · {item['group']} · risk {item['risk_score']} · "
            f"sabablar: {', '.join(item['reasons'])} · mentor: {item['mentor']}"
        )
    return envelope(
        message=f"{len(lagging)} ta o'quvchi ortda qolmoqda",
        endpoint=ENDPOINTS["attendance"],
        details={
            "criteria": {"attendance_min": 75, "consecutive_misses": 2, "missing_homework": 2, "inactive_days": 14},
            "students": page,
            "pagination": pagination,
            "report_markdown": "\n".join(report_lines),
        },
    )


# ---------------------------------------------------------------------------
# 10. Reception so'rovlarini yo'naltiruvchi
# ---------------------------------------------------------------------------

_CATEGORY_RULES = (
    ("payment", ("to'lov", "tolov", "qarz", "pul", "chegirma", "payment", "invoice", "hisob")),
    ("schedule", ("jadval", "vaqt", "dars kuni", "kechik", "schedule", "time", "dars vaqti")),
    ("academic", ("dars", "mavzu", "uy vazifasi", "baholash", "o'qish", "kurs", "mentor", "homework", "grade")),
    ("technical", ("platforma", "ilova", "login", "parol", "xato", "ishlamayapti", "error", "bug", "video")),
)


def _categorize(text: str) -> tuple[str, str]:
    lowered = _norm(text)
    for category, keywords in _CATEGORY_RULES:
        if any(keyword in lowered for keyword in keywords):
            return category, {
                "payment": "moliya / buxgalteriya",
                "schedule": "o'quv bo'limi (jadval)",
                "academic": "mentor / metodist",
                "technical": "texnik yordam",
            }[category]
    return "other", "reception (aniqlashtirish kerak)"


@mcp.tool()
@tool_guard
def reception_router(limit: int = 50) -> dict:
    """Reception so'rovlarini yo'naltiruvchi: murojaatlarni toifalab, mas'ulga taqsimlaydi.

    Ish zanjiri: login -> yangi murojaatlar (kutish ro'yxati va holat so'rovlari)
    -> toifa (to'lov, jadval, ta'lim, texnik, boshqa) -> mas'ul xodim -> administrator
    uchun yo'naltirish ro'yxati va javob loyihasi; tushunarsizlar alohida.

    Args:
        limit: Hisobotdagi maksimal murojaatlar soni.
    """
    waiting = _waitlist()
    requests = _status_requests("pending")
    incoming = []
    for row in waiting:
        text = " ".join(str(row.get(key) or "") for key in ("direction", "note", "comment", "message", "fullname"))
        category, owner = _categorize(text)
        incoming.append(
            {
                "request_id": str(row.get("_id")),
                "source": "waitlist",
                "fullname": row.get("fullname"),
                "phone": row.get("phone"),
                "text": row.get("note") or row.get("comment") or row.get("direction") or "Kutish ro'yxatidan yozilgan",
                "category": category,
                "assignee": owner,
                "created_at": row.get("createdAt"),
            }
        )
    for row in requests:
        student = row.get("student") if isinstance(row.get("student"), dict) else {}
        text = " ".join(str(row.get(key) or "") for key in ("reason", "note", "requestedStatus", "targetStatus"))
        category, owner = _categorize(text)
        incoming.append(
            {
                "request_id": str(row.get("_id")),
                "source": "status_request",
                "fullname": student.get("fullname") or row.get("student"),
                "phone": student.get("phone"),
                "text": text or "O'quvchi holatini o'zgartirish so'rovi",
                "category": category,
                "assignee": owner,
                "created_at": row.get("createdAt"),
            }
        )
    page, pagination = _slice(incoming, limit, 0)
    unknown = [item for item in page if item["category"] == "other"]
    routed: dict[str, list] = {}
    for item in page:
        routed.setdefault(item["assignee"], []).append(item)
    drafts = [
        {
            "request_id": item["request_id"],
            "fullname": item["fullname"],
            "text": (
                f"Assalomu alaykum, {item['fullname'] or 'hurmatli mijoz'}! Murojaatingiz qabul qilindi va "
                f"\"{item['category']}\" yo'nalishi bo'yicha {item['assignee']} ga yuborildi. "
                "Tez orada siz bilan bog'lanamiz."
            ),
        }
        for item in page
    ]
    report_lines = ["# Reception murojaatlari", "", f"- Jami: **{len(incoming)}**", ""]
    for owner, items in routed.items():
        report_lines.append(f"## {owner} ({len(items)})")
        for item in items:
            report_lines.append(f"- {item['fullname'] or '—'} · {item['category']} · {item['text'][:120]}")
        report_lines.append("")
    if unknown:
        report_lines.append(f"**Aniqlashtirish kerak:** {len(unknown)} ta murojaat toifasini aniqlab bo'lmadi.")
    if not incoming:
        report_lines.append("Yangi murojaat yo'q.")
    return envelope(
        message=f"{len(incoming)} ta murojaat yo'naltirildi",
        endpoint=ENDPOINTS["waitlist"],
        details={
            "incoming": page,
            "pagination": pagination,
            "by_assignee": {owner: len(items) for owner, items in routed.items()},
            "unclear": unknown,
            "reply_drafts": drafts,
            "report_markdown": "\n".join(report_lines),
        },
    )


register_profile_tools(mcp)


if __name__ == "__main__":
    logger.info("MARS LMS MCP server ishga tushdi (stdio)")
    mcp.run(transport="stdio")
