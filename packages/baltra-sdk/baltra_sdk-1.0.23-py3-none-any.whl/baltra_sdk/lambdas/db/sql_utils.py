from datetime import datetime, timedelta, timezone
import logging
from sqlalchemy.orm import Session

from baltra_sdk.backend.db.screening_models import (
    ScreeningMessages,
    Candidates,
    ResponseTiming,
    Roles,  
    CandidateFunnelLog,
    BusinessUnits,
    Locations
)

def store_message(session: Session, message_id, candidate_data, sent_by, message_body, whatsapp_msg_id):
    """Store a message in the ScreeningMessages table."""
    try:
        candidate_id = candidate_data.get('candidate_id')
        print(
            f"Attempting to store message for candidate "
            f"{candidate_id} in thread {candidate_data.get('thread_id')}"
        )
        
        # Get business_unit_id from candidate_data if available, otherwise fetch from candidate
        business_unit_id = candidate_data.get("business_unit_id")
        if business_unit_id is None and candidate_id:
            candidate = session.query(Candidates).filter_by(candidate_id=candidate_id).first()
            if candidate:
                business_unit_id = candidate.business_unit_id
        
        message = ScreeningMessages(
            message_id=message_id,
            wa_id=candidate_data.get("wa_id"),
            business_unit_id=business_unit_id,
            candidate_id=candidate_id,
            thread_id=candidate_data.get("thread_id"),
            time_stamp=datetime.now(),
            sent_by=sent_by,
            message_body=message_body,
            conversation_type="screening",
            whatsapp_msg_id=whatsapp_msg_id,
            set_id=candidate_data.get("set_id"),
            question_id=candidate_data.get("question_id"),
        )
        print(
            f"Message object created for candidate {candidate_id} "
            f"with message ID {message_id}"
        )

        session.add(message)
        session.commit()
        print(
            f"Message stored successfully in the database for candidate "
            f"{candidate_id}"
        )

        return message
    except Exception as e:
        session.rollback()
        print(
            f"Error storing message for candidate {candidate_data.get('candidate_id')}: {e}"
        )
        return None


def get_company_wa_id(session: Session, business_unit_id):
    """Get the WhatsApp ID of the business unit by business unit ID."""
    try:
        print(f"Attempting to retrieve WA ID for business unit ID: {business_unit_id}")

        business_unit = (
            session.query(BusinessUnits)
            .filter(BusinessUnits.business_unit_id == business_unit_id)
            .first()
        )

        if business_unit and business_unit.wa_id:
            print(f"Found WA ID {business_unit.wa_id} for business unit ID: {business_unit_id}")
            return business_unit.wa_id
        else:
            print(f"No WA ID found for business unit ID: {business_unit_id}")
            return None
    except Exception as e:
        print(f"Error retrieving WA ID for business unit ID {business_unit_id}: {e}")
        return None


def get_candidates_to_remind_application(session: Session):
    """Get candidates that need application reminders."""
    now = datetime.now()
    cutoff_time = now - timedelta(hours=23)

    return (
        session.query(Candidates)
        .filter(
            Candidates.funnel_state == "screening_in_progress",
            Candidates.application_reminder_sent.is_(False),
            Candidates.created_at <= cutoff_time,
            Candidates.phone.isnot(None),
        )
        .all()
    )


def log_response_time(
    session: Session,
    candidate_data,
    start_time,
    end_time,
    time_delta,
    assistant_id,
    model,
    prompt_tokens,
    completion_tokens,
    total_tokens,
):
    """Log time it takes for an assistant to generate a response including token and model info using SQLAlchemy"""
    try:
        # Get business_unit_id from candidate_data if available, otherwise fetch from candidate
        business_unit_id = candidate_data.get("business_unit_id")
        candidate_id = candidate_data.get("candidate_id", 99999)
        if business_unit_id is None and candidate_id != 99999:
            candidate = session.query(Candidates).filter_by(candidate_id=candidate_id).first()
            if candidate:
                business_unit_id = candidate.business_unit_id
        
        record = ResponseTiming(
            employee_id=candidate_id,
            business_unit_id=business_unit_id or 99999,
            start_time=start_time,
            end_time=end_time,
            time_delta=time_delta,
            assistant_id=assistant_id,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )
        session.add(record)
        session.commit()
    except Exception as e:
        session.rollback()
        logging.error(f"An error occurred while logging response time: {e}")


def get_company_screening_data(session: Session, business_unit_id, role_id=None):
    """
    Get screening data for a business unit by business unit ID.
    
    Location priority:
    1. Role's interview location -> role's work location
    2. business_unit.default_location_id
    3. Any location for the business unit
    """
    business_unit = (
        session.query(BusinessUnits)
        .filter_by(business_unit_id=business_unit_id)
        .first()
    )
    if not business_unit:
        return None
    
    # Get location info from Locations table
    location = None
    address = None
    maps_link_json = {}
    interview_address_json = {}
    
    # Try to get location from specific role
    if role_id:
        role = session.query(Roles).filter_by(role_id=role_id).first()
        if role:
            if role.location_id_interview:
                location = session.query(Locations).filter_by(location_id=role.location_id_interview).first()
            if not location and role.location_id:
                location = session.query(Locations).filter_by(location_id=role.location_id).first()
    
    # Fall back to business unit's default_location_id
    if not location and business_unit.default_location_id:
        location = session.query(Locations).filter_by(location_id=business_unit.default_location_id).first()
    
    # Fall back to any location for the business unit
    if not location:
        location = session.query(Locations).filter_by(business_unit_id=business_unit_id).first()
    
    if location:
        address = location.address
        if location.url:
            maps_link_json = {"location_link_1": location.url}
        if location.address:
            interview_address_json = {"location_1": location.address}
    
    return {
        "address": address,
        "unavailable_dates": business_unit.interview_excluded_dates or [],
        "interview_days": business_unit.interview_days or [],
        "interview_hours": business_unit.interview_hours or [],
        "interview_location": {
            "address": address,
            "url": location.url if location else None,
            "latitude": location.latitude if location else None,
            "longitude": location.longitude if location else None,
        } if location else {},
        # Keep these for backward compatibility, but they now come from Locations
        "interview_address_json": interview_address_json,
        "maps_link_json": maps_link_json,
    }


def get_active_roles_text(session: Session, business_unit_id):
    """Get formatted text list of active roles for a business unit."""
    roles = (
        session.query(Roles)
        .filter_by(business_unit_id=business_unit_id, is_active=True)
        .order_by(Roles.role_name)
        .all()
    )

    if not roles:
        return "No hay puestos activos para esta empresa."

    lines = []
    for idx, role in enumerate(roles, start=1):
        lines.append(f"{idx}️⃣ {role.role_name}")

    return "\n".join(lines)


def get_active_roles_for_company(session: Session, business_unit_id):
    """Fetch active roles for a given business_unit_id and return as a list of dictionaries."""
    roles = (
        session.query(Roles)
        .filter_by(business_unit_id=business_unit_id, is_active=True)
        .with_entities(Roles.role_id, Roles.role_name, Roles.role_list_subtitle)
        .all()
    )

    return [
        {"role_id": r.role_id, "role_name": r.role_name, "role_list_subtitle": r.role_list_subtitle} for r in roles
    ]


def mark_end_flow_rejected(session: Session, candidate_id):
    """Mark a candidate's end flow as rejected."""
    candidate = session.query(Candidates).filter_by(candidate_id=candidate_id).first()
    if candidate:
        candidate.end_flow_rejected = True
        session.commit()
        return True
    return False


def get_candidate_eligible_roles(session: Session, candidate_id: int):
    """Fetch eligible roles for a given candidate_id and return as a list of role names."""
    try:
        candidate = (
            session.query(Candidates)
            .filter_by(candidate_id=candidate_id)
            .first()
        )
        if not candidate:
            logging.warning(f"No candidate found with ID {candidate_id}")
            return []

        return candidate.eligible_roles or []

    except Exception as e:
        logging.error(
            f"Error retrieving eligible_roles for candidate {candidate_id}: {e}"
        )
        return []


def get_candidate_eligible_companies(session: Session, candidate_id: int):
    """Fetch eligible business units for a given candidate_id and return as a list of dicts with truncated name and address."""
    try:
        candidate = (
            session.query(Candidates)
            .filter_by(candidate_id=candidate_id)
            .first()
        )
        if not candidate:
            logging.warning(f"No candidate found with ID {candidate_id}")
            return []

        eligible_ids = candidate.eligible_companies or []
        if not eligible_ids:
            return []

        business_units = (
            session.query(
                BusinessUnits.business_unit_id,
                BusinessUnits.name,
                BusinessUnits.address,
            )
            .filter(BusinessUnits.business_unit_id.in_(eligible_ids))
            .all()
        )

        result = []
        for bu in business_units:
            name = bu.name or ""
            address = bu.address or ""

            try:
                import unicodedata

                name = unicodedata.normalize("NFC", name)
                address = unicodedata.normalize("NFC", address)
            except Exception:
                pass

            if len(name) > 24:
                visible_limit = 24
                head = name[:visible_limit]
                truncated_name = head.rsplit(" ", 1)[0] if " " in head else head
                truncated_name = truncated_name.rstrip() + "…"
            else:
                truncated_name = name

            if len(address) > 72:
                visible_desc_limit = 72
                head_addr = address[:visible_desc_limit]
                truncated_address = (
                    head_addr.rsplit(" ", 1)[0] if " " in head_addr else head_addr
                )
                truncated_address = truncated_address.rstrip() + "…"
            else:
                truncated_address = address

            result.append(
                {
                    "business_unit_id": bu.business_unit_id,
                    "name": truncated_name,
                    "address": truncated_address,
                }
            )

        logging.info(
            f"Found {len(result)} eligible business units for candidate {candidate_id}"
        )
        return result

    except Exception as e:
        logging.error(
            f"Error fetching eligible business units for candidate {candidate_id}: {e}"
        )
        return []


# ---- Availability helpers (mirrored from backend for Flow hours) ----
def count_bookings_for_slot(session: Session, business_unit_id: int, date: str, hour: str) -> int:
    """Count how many candidates are scheduled in a given slot."""
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d").date()
        hour_obj = datetime.strptime(hour, "%H:%M").time()
        target_dt = datetime.combine(date_obj, hour_obj).replace(tzinfo=timezone.utc)

        return (
            session.query(Candidates)
            .filter(
                Candidates.business_unit_id == business_unit_id,
                Candidates.interview_date_time == target_dt,
                Candidates.funnel_state.in_(["scheduled_interview", "screening_in_progress"]),
            )
            .count()
        )
    except Exception as err:
        logging.error(f"Error counting bookings for slot ({business_unit_id}, {date} {hour}): {err}")
        return 0


def is_slot_available(session: Session, business_unit_id: int, date: str, hour: str, max_capacity) -> bool:
    """Check if a time slot is available given max_capacity."""
    if max_capacity is None:
        return True
    current_bookings = count_bookings_for_slot(session, business_unit_id, date, hour)
    return current_bookings < max_capacity


def _weekday_to_short_name(weekday_num: int) -> str:
    """Convert Python weekday number (0=Monday) to 3-letter format."""
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    return days[weekday_num]


def get_available_dates_and_hours(
    session: Session,
    business_unit_id: int,
    start_date: str,
    end_date: str,
    all_hours: list,
    max_capacity,
    interview_days: list,
    unavailable_dates: list = None,
    max_days: int = 4,
):
    """Return up to max_days dates with per-date hour availability (enabled flags) for WhatsApp Flow."""
    all_hours = sorted(all_hours)
    unavailable_dates = unavailable_dates or []

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()

    available_dates = []
    current_date = start

    while current_date <= end and len(available_dates) < max_days:
        weekday_name = _weekday_to_short_name(current_date.weekday())
        if interview_days and weekday_name not in interview_days:
            current_date += timedelta(days=1)
            continue

        date_str = current_date.strftime("%Y-%m-%d")
        if date_str in unavailable_dates:
            current_date += timedelta(days=1)
            continue

        hours = []
        for i, hour in enumerate(all_hours):
            available = is_slot_available(session, business_unit_id, date_str, hour, max_capacity)
            hours.append(
                {
                    "id": str(i + 1),
                    "title": hour,
                    "enabled": available,
                    "on-select-action": {
                        "name": "update_data",
                        "payload": {"selected_hour": hour},
                    },
                }
            )

        available_dates.append({"date": date_str, "hours": hours})
        current_date += timedelta(days=1)

    return available_dates


def log_funnel_state_change(session: Session, candidate_id: int, previous_state: str, new_state: str):
    """Log a funnel state change in the CandidateFunnelLog table."""
    try:
        new_log = CandidateFunnelLog(
            candidate_id=candidate_id,
            previous_funnel_state=previous_state,
            new_funnel_state=new_state,
            changed_at=datetime.now(timezone.utc)
        )
        session.add(new_log)
        session.commit()
        logging.info(f"Logged funnel state change for candidate {candidate_id}: {previous_state} -> {new_state}")
        return True
    except Exception as e:
        session.rollback()
        logging.error(f"Error logging funnel state change for candidate {candidate_id}: {e}")
        return False
