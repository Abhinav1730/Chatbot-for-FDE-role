import pytest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.schemas import BookingMode, BookingStatus, LeadSlots
from app.services.booking import simulate_booking
from app.services.llm import merge_extracted_slots, should_attempt_booking
from app.services.slot_extractor import extract_slots_heuristic

client = TestClient(app)


class TestBookingSimulator:
    def test_booking_success(self):
        result = simulate_booking(BookingMode.SUCCESS, "Saturday 11 AM")
        assert result.success is True
        assert result.status == BookingStatus.CONFIRMED

    def test_booking_fail(self):
        result = simulate_booking(BookingMode.FAIL, "Sunday 10 AM")
        assert result.success is False
        assert result.status == BookingStatus.FAILED

    def test_booking_random(self):
        results = {simulate_booking(BookingMode.RANDOM, "Monday 3 PM").success for _ in range(20)}
        assert len(results) >= 1


class TestSlotMerging:
    def test_merge_configuration(self):
        slots = LeadSlots()
        updated = merge_extracted_slots(
            slots,
            {"configuration": "3 BHK", "interest_level": "high"},
        )
        assert updated.configuration == "3 BHK"
        assert updated.interest_level.value == "high"

    def test_merge_opt_out(self):
        slots = LeadSlots()
        updated = merge_extracted_slots(slots, {"opt_out": True})
        assert updated.opt_out is True

    def test_merge_objections(self):
        slots = LeadSlots(objections=["price"])
        updated = merge_extracted_slots(slots, {"objections": ["location"]})
        assert "price" in updated.objections
        assert "location" in updated.objections


class TestHeuristicExtraction:
    def test_configuration_3bhk(self):
        slots = extract_slots_heuristic(LeadSlots(), "I'm interested in a 3 BHK apartment")
        assert slots.configuration == "3 BHK"
        assert slots.interest_level.value == "medium"

    def test_price_objection_hinglish(self):
        slots = extract_slots_heuristic(LeadSlots(), "Bahut expensive lag raha hai, costly hai")
        assert "price" in slots.objections

    def test_opt_out(self):
        slots = extract_slots_heuristic(LeadSlots(), "Don't contact me again please")
        assert slots.opt_out is True
        assert slots.interest_level.value == "not_interested"

    def test_site_visit_request(self):
        slots = extract_slots_heuristic(LeadSlots(), "Book site visit Saturday 11 AM")
        assert slots.site_visit_status == BookingStatus.REQUESTED
        assert slots.site_visit_details.date == "Saturday"
        assert slots.site_visit_details.time == "11 AM"

    def test_hinglish_language(self):
        slots = extract_slots_heuristic(LeadSlots(), "2BHK ka price kya hai?")
        assert slots.preferred_language == "hinglish"

    def test_escalation(self):
        slots = extract_slots_heuristic(LeadSlots(), "Manager se baat karni hai")
        assert slots.escalated_to_human is True


class TestShouldAttemptBooking:
    def test_no_booking_when_opt_out(self):
        slots = LeadSlots(opt_out=True, site_visit_status=BookingStatus.REQUESTED)
        assert should_attempt_booking(slots) is False

    def test_booking_when_requested(self):
        slots = LeadSlots(site_visit_status=BookingStatus.REQUESTED)
        assert should_attempt_booking(slots) is True

    def test_no_booking_when_already_confirmed(self):
        slots = LeadSlots(site_visit_status=BookingStatus.CONFIRMED)
        assert should_attempt_booking(slots) is False


class TestAPIEndpoints:
    @patch("app.services.llm._chat_completion")
    def test_create_session(self, mock_chat):
        mock_chat.return_value = "Hello greeting"
        response = client.post("/api/sessions")
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "greeting" in data

    @patch("app.services.llm._chat_completion")
    def test_chat_flow(self, mock_chat):
        mock_chat.return_value = (
            "2 BHK starts at ₹1.35 crore onwards. Are you looking for 2 or 3 BHK?"
        )
        session = client.post("/api/sessions").json()
        response = client.post(
            "/api/chat",
            json={"session_id": session["session_id"], "message": "2BHK ka price kya hai?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "reply" in data
        assert "slots" in data
        assert mock_chat.call_count == 1

    @patch("app.services.llm._chat_completion")
    def test_opt_out_scenario(self, mock_chat):
        mock_chat.return_value = (
            "Understood — I won't contact you further. Thank you for your time."
        )
        session = client.post("/api/sessions").json()
        response = client.post(
            "/api/chat",
            json={
                "session_id": session["session_id"],
                "message": "Don't contact me again please",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["slots"]["opt_out"] is True
        assert mock_chat.call_count == 1

    @patch("app.services.llm._chat_completion")
    def test_booking_success_flow(self, mock_chat):
        mock_chat.side_effect = [
            "I'll book Saturday 11 AM for you.",
            "Your site visit is confirmed for Saturday at 11 AM!",
        ]
        session = client.post("/api/sessions").json()
        client.patch(
            f"/api/sessions/{session['session_id']}/booking-mode",
            json={"mode": "success"},
        )
        response = client.post(
            "/api/chat",
            json={
                "session_id": session["session_id"],
                "message": "Book site visit Saturday 11 AM",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["booking"] is not None
        assert data["booking"]["success"] is True
        assert mock_chat.call_count == 2

    @patch("app.services.llm._chat_completion")
    def test_booking_fail_flow(self, mock_chat):
        mock_chat.side_effect = [
            "Let me book Sunday 10 AM for you.",
            "I'm sorry, I couldn't confirm Sunday 10 AM. Would Sunday 12 PM work instead?",
        ]
        session = client.post("/api/sessions").json()
        client.patch(
            f"/api/sessions/{session['session_id']}/booking-mode",
            json={"mode": "fail"},
        )
        response = client.post(
            "/api/chat",
            json={
                "session_id": session["session_id"],
                "message": "Book Sunday 10 AM visit",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["booking"] is not None
        assert data["booking"]["success"] is False
        assert mock_chat.call_count == 2

    @patch("app.services.llm._chat_completion")
    def test_end_session_analytics(self, mock_chat):
        mock_chat.return_value = (
            '{"lead_summary": "Interested in 3 BHK", "interest_level": "high", '
            '"site_visit_status": "not_discussed", "objections_raised": [], '
            '"follow_up_required": false, "opt_out": false, "escalated_to_human": false, '
            '"conversation_outcome": "information_gathered"}'
        )
        session = client.post("/api/sessions").json()
        response = client.post(f"/api/sessions/{session['session_id']}/end")
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
        assert data["analytics"]["lead_summary"]

    def test_health(self):
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
