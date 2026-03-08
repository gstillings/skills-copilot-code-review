"""
Announcement endpoints for the High School Management System API
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


class AnnouncementPayload(BaseModel):
    """Payload for creating or updating an announcement."""

    title: str
    message: str
    expiration_date: str
    start_date: Optional[str] = None


def _parse_iso_date(date_text: str, field_name: str) -> str:
    """Parse and normalize incoming date strings to YYYY-MM-DD format."""
    try:
        return datetime.fromisoformat(date_text).date().isoformat()
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} must be a valid ISO date (YYYY-MM-DD)"
        ) from exc


def _to_response(doc: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": str(doc["_id"]),
        "title": doc["title"],
        "message": doc["message"],
        "start_date": doc.get("start_date"),
        "expiration_date": doc["expiration_date"],
        "created_by": doc.get("created_by")
    }


def _assert_teacher(teacher_username: Optional[str]) -> Dict[str, Any]:
    """Validate that the caller is a teacher user."""
    if not teacher_username:
        raise HTTPException(status_code=401, detail="Teacher authentication is required")

    teacher = teachers_collection.find_one({"_id": teacher_username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Invalid teacher credentials")

    if teacher.get("role") != "teacher":
        raise HTTPException(status_code=403, detail="Only teacher users can edit announcements")

    return teacher


@router.get("", response_model=List[Dict[str, Any]])
def get_announcements(include_expired: bool = Query(False)) -> List[Dict[str, Any]]:
    """Get announcements, defaulting to only currently active ones."""
    today = datetime.now(timezone.utc).date().isoformat()

    query: Dict[str, Any] = {}
    if not include_expired:
        query["expiration_date"] = {"$gte": today}
        query["$or"] = [
            {"start_date": {"$exists": False}},
            {"start_date": None},
            {"start_date": ""},
            {"start_date": {"$lte": today}}
        ]

    docs = announcements_collection.find(query).sort([("start_date", -1), ("expiration_date", 1), ("_id", 1)])
    return [_to_response(doc) for doc in docs]


@router.post("", response_model=Dict[str, Any])
def create_announcement(payload: AnnouncementPayload, teacher_username: Optional[str] = Query(None)) -> Dict[str, Any]:
    """Create a new announcement (teacher users only)."""
    teacher = _assert_teacher(teacher_username)

    if not payload.title.strip():
        raise HTTPException(status_code=422, detail="title is required")
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message is required")

    expiration_date = _parse_iso_date(payload.expiration_date, "expiration_date")
    start_date = _parse_iso_date(payload.start_date, "start_date") if payload.start_date else None

    if start_date and start_date > expiration_date:
        raise HTTPException(status_code=422, detail="start_date cannot be later than expiration_date")

    announcement_id = f"announcement-{int(datetime.now(timezone.utc).timestamp() * 1000)}"
    document = {
        "_id": announcement_id,
        "title": payload.title.strip(),
        "message": payload.message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_by": teacher["username"]
    }

    announcements_collection.insert_one(document)
    return _to_response(document)


@router.put("/{announcement_id}", response_model=Dict[str, Any])
def update_announcement(
    announcement_id: str,
    payload: AnnouncementPayload,
    teacher_username: Optional[str] = Query(None)
) -> Dict[str, Any]:
    """Update an existing announcement (teacher users only)."""
    _assert_teacher(teacher_username)

    existing = announcements_collection.find_one({"_id": announcement_id})
    if not existing:
        raise HTTPException(status_code=404, detail="Announcement not found")

    if not payload.title.strip():
        raise HTTPException(status_code=422, detail="title is required")
    if not payload.message.strip():
        raise HTTPException(status_code=422, detail="message is required")

    expiration_date = _parse_iso_date(payload.expiration_date, "expiration_date")
    start_date = _parse_iso_date(payload.start_date, "start_date") if payload.start_date else None

    if start_date and start_date > expiration_date:
        raise HTTPException(status_code=422, detail="start_date cannot be later than expiration_date")

    update_data = {
        "title": payload.title.strip(),
        "message": payload.message.strip(),
        "start_date": start_date,
        "expiration_date": expiration_date
    }

    announcements_collection.update_one({"_id": announcement_id}, {"$set": update_data})
    updated = announcements_collection.find_one({"_id": announcement_id})
    return _to_response(updated)


@router.delete("/{announcement_id}")
def delete_announcement(announcement_id: str, teacher_username: Optional[str] = Query(None)) -> Dict[str, str]:
    """Delete an announcement (teacher users only)."""
    _assert_teacher(teacher_username)

    result = announcements_collection.delete_one({"_id": announcement_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")

    return {"message": "Announcement deleted successfully"}
