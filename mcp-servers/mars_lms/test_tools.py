"""MCP server tool'lari uchun mock backend testlari.

Ishga tushirish:
    .venv/Scripts/python.exe -m unittest discover -s . -p "test_*.py" -v
"""

from __future__ import annotations

import json
import unittest
from datetime import date, datetime, timedelta

import httpx

import server
from lms_client import LMSClient, LMSError

TODAY = date.today()
MONTH = TODAY.strftime("%Y-%m")


def _student(sid: str, name: str, phone: str, group_id: str, group_name: str, remaining: float = 0, paid: float = 0, created: str = "", inactive: int = 0) -> dict:
    return {
        "_id": sid,
        "fullname": name,
        "phone": phone,
        "status": "active",
        "direction": "Backend",
        "group": {"_id": group_id, "name": group_name} if group_id else None,
        "monthlyFee": 800000,
        "daysInactive": inactive,
        "createdAt": created,
        "billing": {
            "due": 800000,
            "paid": paid,
            "remaining": remaining,
            "status": "unpaid" if remaining > 0 else "paid",
            "daysOverdue": 14 if remaining > 0 else 0,
            "isOverdue": remaining > 0,
            "dueDate": f"{MONTH}-05",
        },
    }


class MockBackend:
    """Kichik fixture backend: kerakli endpointlarni taqlid qiladi."""

    def __init__(self, fail_login: bool = False, expire_after_login: bool = False):
        self.fail_login = fail_login
        self.expire_after_login = expire_after_login
        self.login_calls = 0
        self.today = TODAY

    def handler(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/api/auth/login":
            self.login_calls += 1
            if self.fail_login:
                return httpx.Response(401, json={"success": False, "message": "Login ma'lumotlari noto'g'ri"})
            token = "token-new" if self.login_calls > 1 else "token-1"
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "accessToken": token,
                    "refreshToken": "refresh",
                    "role": "admin",
                    "user": {"_id": "admin1", "fullname": "Mars Filial Admin", "branch": "branch1"},
                    "branch": {"_id": "branch1", "name": "Test Branch"},
                },
            )
        if self.expire_after_login and self.login_calls == 1:
            return httpx.Response(401, json={"success": False, "message": "token expired"})
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return httpx.Response(401, json={"success": False, "message": "Avtorizatsiya talab qilinadi"})
        if path == "/api/branch/me":
            return httpx.Response(200, json={"success": True, "admin": {"fullname": "Mars Filial Admin"}, "branch": {"_id": "branch1", "name": "Test Branch"}})
        if path == "/api/branch/groups":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "groups": [
                        {"_id": "g1", "name": "Backend-1", "direction": "Backend", "schedule": "Se-Pay-Shanba 18:00-20:00", "capacity": 15, "studentsCount": 3, "mentor": {"_id": "m1", "fullname": "Ali Valiyev"}, "course": None, "room": None},
                        {"_id": "g2", "name": "Frontend-1", "direction": "Frontend", "schedule": "Se-Pay 18:00", "capacity": 12, "studentsCount": 2, "mentor": {"_id": "m1", "fullname": "Ali Valiyev"}, "course": None, "room": None},
                    ],
                },
            )
        if path == "/api/branch/students":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "month": MONTH,
                    "students": [
                        _student("s1", "Aziz Karimov", "998901112233", "g1", "Backend-1", remaining=1000000),
                        _student("s2", "Bekzod Tosh", "998902223344", "g1", "Backend-1", paid=800000),
                        _student("s3", "Dilnoza Yusupova", "998903334455", "", "", remaining=500000, created=(TODAY - timedelta(days=3)).isoformat()),
                    ],
                },
            )
        if path == "/api/branch/debtors":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "month": MONTH,
                    "totalRemaining": 1500000,
                    "counts": {"total": 2, "overdue": 2, "unpaid": 0},
                    "debtors": [
                        {"_id": "s3", "fullname": "Dilnoza Yusupova", "phone": "998903334455", "direction": "Backend", "billing": {"remaining": 500000, "paid": 0, "due": 800000, "daysOverdue": 7, "isOverdue": True, "dueDate": f"{MONTH}-05"}},
                        {"_id": "s1", "fullname": "Aziz Karimov", "phone": "998901112233", "group": {"_id": "g1", "name": "Backend-1"}, "direction": "Backend", "billing": {"remaining": 1000000, "paid": 0, "due": 800000, "daysOverdue": 14, "isOverdue": True, "dueDate": f"{MONTH}-05"}},
                    ],
                },
            )
        if path == "/api/branch/attendance":
            lessons = [
                {"_id": "a1", "date": f"{TODAY.isoformat()}T10:00:00.000Z", "group": {"_id": "g1", "name": "Backend-1"}, "records": [
                    {"student": {"_id": "s1", "fullname": "Aziz Karimov", "phone": "998901112233"}, "present": False},
                    {"student": {"_id": "s2", "fullname": "Bekzod Tosh"}, "present": True},
                ]},
                {"_id": "a2", "date": f"{(TODAY - timedelta(days=2)).isoformat()}T10:00:00.000Z", "group": {"_id": "g1", "name": "Backend-1"}, "records": [
                    {"student": {"_id": "s1", "fullname": "Aziz Karimov", "phone": "998901112233"}, "present": False},
                    {"student": {"_id": "s2", "fullname": "Bekzod Tosh"}, "present": True},
                ]},
                {"_id": "a3", "date": f"{(TODAY - timedelta(days=4)).isoformat()}T10:00:00.000Z", "group": {"_id": "g1", "name": "Backend-1"}, "records": [
                    {"student": {"_id": "s1", "fullname": "Aziz Karimov", "phone": "998901112233"}, "present": True},
                ]},
            ]
            return httpx.Response(200, json={"success": True, "attendance": lessons, "pagination": {"page": 1, "limit": 100, "total": 3}})
        if path == "/homework":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "homework": [
                        {"_id": "hw1", "title": "Kalkulyator", "dueDate": f"{(TODAY - timedelta(days=5)).isoformat()}T00:00:00.000Z", "group": {"_id": "g1", "name": "Backend-1", "mentor": {"firstname": "Ali", "lastname": "Valiyev"}}, "submissions": []},
                        {"_id": "hw2", "title": "Layout", "dueDate": f"{(TODAY + timedelta(days=3)).isoformat()}T00:00:00.000Z", "group": {"_id": "g1", "name": "Backend-1"}, "submissions": [{"student": "s2"}]},
                        {"_id": "hw3", "title": "API test", "dueDate": f"{(TODAY - timedelta(days=2)).isoformat()}T00:00:00.000Z", "group": {"_id": "g1", "name": "Backend-1"}, "submissions": [{"student": "s1"}]},
                    ],
                },
            )
        if path == "/api/branch/overview":
            month = request.url.params.get("month") or MONTH
            income = 2203106 if month == MONTH else 500000
            return httpx.Response(200, json={"success": True, "overview": {"month": month, "activeStudents": 3, "paidStudents": 1, "partialStudents": 0, "unpaidStudents": 2, "receivable": 1500000, "income": income, "expense": 100000, "incomeByMethod": {"cash": income}}})
        if path == "/api/finance/overview":
            return httpx.Response(200, json={"success": True, "overview": {"totalIncome": 5753106, "totalExpense": 49101150, "netProfit": -43348044, "monthlyTrend": [{"month": MONTH, "income": 2203106}]}})
        if path == "/api/branch/mentors":
            return httpx.Response(200, json={"success": True, "mentors": [{"_id": "m1", "firstname": "Ali", "lastname": "Valiyev", "grade": "Senior"}, {"_id": "m2", "firstname": "Bekzod", "lastname": "Rahimov", "grade": "Junior"}]})
        if path == "/api/branch/workload-planning":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "planning": {
                        "overview": {"currentActiveGroupsCount": 2, "totalMentors": 2, "totalRooms": 0},
                        "mentors": [],
                        "rooms": [],
                        "timeslots": [{"slot": "Se-Pay-Shanba 18:00-20:00 (Kechki pik)", "activeGroupsCount": 2, "availableRooms": 0, "isOverCapacity": False, "utilizationPercent": 100}],
                        "recommendations": [],
                    },
                },
            )
        if path == "/api/branch/status-requests":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "requests": [
                        {"_id": "r1", "status": "pending", "student": {"_id": "s1", "fullname": "Aziz Karimov", "phone": "998901112233"}, "requestedStatus": "frozen", "reason": "To'lov qilolmayman, muzlatish so'rayman", "createdAt": (datetime.now() - timedelta(days=4)).isoformat()},
                    ],
                    "pagination": {"page": 1, "limit": 100, "total": 1},
                },
            )
        if path == "/api/branch/waitlist":
            return httpx.Response(
                200,
                json={
                    "success": True,
                    "count": 1,
                    "items": [{"_id": "w1", "fullname": "Jasur Aliyev", "phone": "998905556677", "direction": "Frontend", "note": "Platformaga login qilolmayapman, parolim ishlamayapti", "createdAt": datetime.now().isoformat()}],
                },
            )
        if path == "/api/branch/inactive-students":
            return httpx.Response(200, json={"success": True, "count": 0, "students": []})
        if path == "/api/branch/payments":
            return httpx.Response(200, json={"success": True, "payments": [{"_id": "p1", "amount": 800000}], "total": 1, "page": 1, "pages": 1})
        return httpx.Response(404, json={"success": False, "message": f"endpoint topilmadi: {path}"})


class ToolTestBase(unittest.TestCase):
    backend: MockBackend

    def setUp(self) -> None:
        self.backend = MockBackend()
        self.client = LMSClient(
            base_url="https://mock.local",
            phone="998990000001",
            password="Admin123!",
            role="admin",
            transport=httpx.MockTransport(self.backend.handler),
        )
        self._original = server.CLIENT
        server.CLIENT = self.client

    def tearDown(self) -> None:
        server.CLIENT = self._original

    def login(self) -> None:
        result = server.lms_login(force=True)
        self.assertIsNone(result["error"], result)


class SessionTests(ToolTestBase):
    def test_login_returns_session_summary(self) -> None:
        self.login()
        result = server.lms_context()
        self.assertIsNone(result["error"], result)
        session = result["details"]["session"]
        self.assertTrue(session["authenticated"])
        self.assertEqual(session["branch"], "Test Branch")
        self.assertEqual(result["details"]["counts"]["groups"], 2)

    def test_missing_credentials_is_actionable(self) -> None:
        client = LMSClient(base_url="https://mock.local", phone="", password="", role="admin", transport=httpx.MockTransport(self.backend.handler))
        server.CLIENT = client
        result = server.get_debts()
        self.assertIsNotNone(result["error"])
        self.assertIn("MARS_PHONE", result["message"])
        self.assertEqual(result["status_code"], 0)

    def test_wrong_password_surfaces_backend_message(self) -> None:
        self.backend.fail_login = True
        result = server.lms_login(force=True)
        self.assertEqual(result["status_code"], 401)
        self.assertIn("lms_login", result["message"])
        self.assertIn("Login ma'lumotlari", result["message"])

    def test_expired_token_triggers_single_relogin(self) -> None:
        self.backend.expire_after_login = True
        self.login()
        result = server.get_debts()
        self.assertIsNone(result["error"], result)
        self.assertEqual(self.backend.login_calls, 2)

    def test_forbidden_is_explained(self) -> None:
        original = self.backend.handler

        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == "/api/finance/overview":
                return httpx.Response(403, json={"success": False, "message": "Bu amal uchun ruxsat yoq"})
            return original(request)

        server.CLIENT = LMSClient(base_url="https://mock.local", phone="1", password="2", transport=httpx.MockTransport(handler))
        result = server.get_finance_report()
        self.assertEqual(result["status_code"], 403)
        self.assertIn("Ruxsat yo'q", result["message"])

    def test_bad_month_is_rejected_locally(self) -> None:
        self.login()
        result = server.get_debts(month="noyabr")
        self.assertEqual(result["status_code"], 400)
        self.assertIn("YYYY-MM", result["message"])


class DataToolTests(ToolTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.login()

    def test_get_debts_sorted_by_amount(self) -> None:
        result = server.get_debts()
        self.assertIsNone(result["error"], result)
        names = [row["fullname"] for row in result["details"]["debtors"]]
        self.assertEqual(names[0], "Aziz Karimov")

    def test_list_students_pagination(self) -> None:
        result = server.list_students(limit=2)
        self.assertEqual(len(result["details"]["students"]), 2)
        self.assertTrue(result["details"]["pagination"]["has_more"])
        self.assertEqual(result["details"]["pagination"]["next_offset"], 2)

    def test_homework_missing_counts(self) -> None:
        self.client.token = self.client.token  # sessiya saqlanadi
        result = server.get_homework()
        overdue = [row for row in result["details"]["homework"] if row["is_overdue"]]
        self.assertEqual(len(overdue), 2)
        titles = {row["title"]: row for row in overdue}
        self.assertEqual(titles["Kalkulyator"]["missing_count"], 2)
        self.assertEqual(titles["API test"]["missing_count"], 1)

    def test_pending_approvals_collects_both_sources(self) -> None:
        result = server.get_pending_approvals()
        self.assertEqual(result["details"]["counts"]["requests"], 1)
        self.assertEqual(result["details"]["counts"]["waitlist"], 1)


class WorkflowAgentTests(ToolTestBase):
    def setUp(self) -> None:
        super().setUp()
        self.login()

    def test_debt_control_agent_builds_drafts(self) -> None:
        result = server.debt_control_agent()
        self.assertIsNone(result["error"], result)
        details = result["details"]
        self.assertEqual(details["summary"]["debtors"], 2)
        self.assertEqual(details["debtors"][0]["fullname"], "Aziz Karimov")
        self.assertEqual(len(details["message_drafts"]), 2)
        self.assertIn("14 kun", details["message_drafts"][0]["text"])

    def test_debt_control_agent_filters_by_overdue_days(self) -> None:
        result = server.debt_control_agent(min_days_overdue=10)
        self.assertEqual(len(result["details"]["debtors"]), 1)
        self.assertEqual(result["details"]["debtors"][0]["fullname"], "Aziz Karimov")

    def test_attendance_control_agent_detects_streak(self) -> None:
        result = server.attendance_control_agent(consecutive_misses=2)
        at_risk = result["details"]["at_risk"]
        self.assertEqual(len(at_risk), 1)
        self.assertEqual(at_risk[0]["student_id"], "s1")
        self.assertEqual(at_risk[0]["consecutive_absent"], 2)
        self.assertEqual(result["details"]["mentor_warnings"][0]["recipient"], "Ali Valiyev")

    def test_attendance_control_agent_respects_threshold(self) -> None:
        result = server.attendance_control_agent(consecutive_misses=3)
        self.assertEqual(result["details"]["at_risk"], [])

    def test_homework_control_agent_collects_missing(self) -> None:
        result = server.homework_control_agent()
        details = result["details"]
        self.assertEqual(details["students_missing_total"], 2)
        titles = {row["title"]: row for row in details["homework"]}
        self.assertEqual(titles["Kalkulyator"]["missing_count"], 2)
        self.assertNotIn("Layout", titles)
        self.assertTrue(details["mentor_reports"])

    def test_daily_finance_report_compares_previous_month(self) -> None:
        result = server.daily_finance_report()
        details = result["details"]
        self.assertEqual(details["balance"], 2203106 - 100000)
        self.assertIsNotNone(details["previous_period"])
        self.assertEqual(details["previous_period"]["delta"]["income"], 2203106 - 500000)
        self.assertIn("Oldingi oy bilan farq", details["report_markdown"])

    def test_new_student_followup_finds_missing_steps(self) -> None:
        result = server.new_student_followup(days=7)
        followups = result["details"]["followups"]
        self.assertEqual(len(followups), 1)
        self.assertEqual(followups[0]["student_id"], "s3")
        self.assertIn("assigned_to_group", followups[0]["missing_steps"])
        self.assertIn("Assalomu alaykum", result["details"]["message_drafts"][0]["text"])

    def test_pending_approvals_digest_prioritises(self) -> None:
        result = server.pending_approvals_digest()
        details = result["details"]
        self.assertEqual(len(details["requests"]), 2)
        self.assertEqual(details["requests"][0]["priority"], "high")
        self.assertIn("Tasdiq kutayotgan so'rovlar", details["report_markdown"])

    def test_room_schedule_assistant_detects_mentor_conflict(self) -> None:
        result = server.room_schedule_assistant()
        conflicts = result["details"]["conflicts"]
        self.assertTrue(any(item["type"] == "mentor_double_booking" for item in conflicts))
        self.assertEqual(len(result["details"]["free_timeslots"]), 1)

    def test_mentor_workload_analysis_recommends_least_loaded(self) -> None:
        result = server.mentor_workload_analysis(max_groups_per_mentor=2)
        details = result["details"]
        workloads = {row["mentor"]: row for row in details["mentors"]}
        self.assertEqual(workloads["Ali Valiyev"]["groups"], 2)
        self.assertEqual(workloads["Ali Valiyev"]["status"], "balanced")
        self.assertEqual(details["recommended_mentor"]["mentor"], "Bekzod Rahimov")

    def test_student_progress_audit_scores_reasons(self) -> None:
        result = server.student_progress_audit()
        students = result["details"]["students"]
        ids = {item["student_id"] for item in students}
        self.assertEqual(ids, {"s1", "s2", "s3"})
        row = next(item for item in students if item["student_id"] == "s1")
        self.assertGreater(row["risk_score"], 0)
        self.assertIn("davomat past (33%)", row["reasons"])
        self.assertIn("to'lov qarzi bor", row["reasons"])
        self.assertTrue(row["support_plan"])

    def test_reception_router_categorises_requests(self) -> None:
        result = server.reception_router()
        details = result["details"]
        categories = {item["request_id"]: item["category"] for item in details["incoming"]}
        self.assertEqual(categories["w1"], "technical")
        self.assertEqual(categories["r1"], "payment")
        self.assertEqual(details["by_assignee"]["texnik yordam"], 1)
        self.assertEqual(len(details["reply_drafts"]), 2)


class EnvelopeTests(unittest.TestCase):
    def test_envelope_shape_is_stable(self) -> None:
        from lms_client import envelope

        result = envelope(error="x", status_code=400, message="m", endpoint="/e", details={"a": 1})
        self.assertEqual(set(result), {"error", "status_code", "message", "endpoint", "details"})

    def test_lms_error_envelope(self) -> None:
        error = LMSError("boom", status_code=500, endpoint="/x", details={"k": "v"})
        result = error.as_envelope()
        self.assertEqual(result["error"], "boom")
        self.assertEqual(result["status_code"], 500)
        self.assertEqual(json.loads(json.dumps(result))["details"], {"k": "v"})


if __name__ == "__main__":
    unittest.main()
