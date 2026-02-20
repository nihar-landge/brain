"""
Google Calendar integration service.
Creates/updates events in a dedicated "Brain Calendar".
"""

from datetime import datetime, timedelta
from typing import Optional
from urllib.parse import urlencode

import httpx
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REDIRECT_URI
from models.dopamine import CalendarIntegration
from models.user import User
from utils.logger import log


GOOGLE_CALENDAR_SCOPES = ["https://www.googleapis.com/auth/calendar"]
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"


class GoogleCalendarService:
    def is_configured(self) -> bool:
        return bool(GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REDIRECT_URI)

    def get_auth_url(self, user_id: int = 1) -> str:
        query = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(GOOGLE_CALENDAR_SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": str(user_id),
        }
        return f"{GOOGLE_AUTH_URL}?{urlencode(query)}"

    async def exchange_code(
        self, db, code: str, user_id: int = 1
    ) -> CalendarIntegration:
        payload = {
            "code": code,
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "redirect_uri": GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(GOOGLE_TOKEN_URL, data=payload)
            resp.raise_for_status()
            data = resp.json()

        integration = (
            db.query(CalendarIntegration)
            .filter(
                CalendarIntegration.user_id == user_id,
                CalendarIntegration.provider == "google",
            )
            .first()
        )
        if not integration:
            integration = CalendarIntegration(user_id=user_id, provider="google")
            db.add(integration)

        integration.access_token = data.get("access_token")
        integration.refresh_token = (
            data.get("refresh_token") or integration.refresh_token
        )
        integration.token_uri = GOOGLE_TOKEN_URL
        integration.client_id = GOOGLE_CLIENT_ID
        integration.client_secret = GOOGLE_CLIENT_SECRET
        integration.scopes = GOOGLE_CALENDAR_SCOPES
        integration.token_expiry = datetime.now(timezone.utc) + timedelta(
            seconds=data.get("expires_in", 3600)
        )
        integration.is_connected = True
        integration.updated_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(integration)

        await self.ensure_brain_calendar(db, user_id)
        return integration

    def _build_credentials(self, integration: CalendarIntegration) -> Credentials:
        creds = Credentials(
            token=integration.access_token,
            refresh_token=integration.refresh_token,
            token_uri=integration.token_uri or GOOGLE_TOKEN_URL,
            client_id=integration.client_id or GOOGLE_CLIENT_ID,
            client_secret=integration.client_secret or GOOGLE_CLIENT_SECRET,
            scopes=integration.scopes or GOOGLE_CALENDAR_SCOPES,
        )
        return creds

    def _get_integration(self, db, user_id: int = 1) -> Optional[CalendarIntegration]:
        return (
            db.query(CalendarIntegration)
            .filter(
                CalendarIntegration.user_id == user_id,
                CalendarIntegration.provider == "google",
                CalendarIntegration.is_connected.is_(True),
            )
            .first()
        )

    def _get_user_timezone(self, db, user_id: int = 1) -> str:
        user = db.query(User).filter(User.id == user_id).first()
        return user.timezone if user and user.timezone else "UTC"

    def _get_service(self, db, user_id: int = 1):
        integration = self._get_integration(db, user_id)
        if not integration:
            return None, None

        creds = self._build_credentials(integration)
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            integration.access_token = creds.token
            integration.token_expiry = creds.expiry
            integration.updated_at = datetime.now(timezone.utc)
            db.commit()

        service = build("calendar", "v3", credentials=creds, cache_discovery=False)
        return service, integration

    async def ensure_brain_calendar(self, db, user_id: int = 1) -> Optional[str]:
        service, integration = self._get_service(db, user_id)
        if not service or not integration:
            return None

        timezone = self._get_user_timezone(db, user_id)
        target_name = "Brain Calendar"

        # Reuse existing calendar if already set
        if integration.calendar_id:
            try:
                service.calendars().get(calendarId=integration.calendar_id).execute()
                return integration.calendar_id
            except Exception:
                integration.calendar_id = None
                db.commit()

        # Find by summary first
        cal_list = service.calendarList().list().execute()
        for item in cal_list.get("items", []):
            if item.get("summary") == target_name:
                integration.calendar_id = item.get("id")
                integration.updated_at = datetime.now(timezone.utc)
                db.commit()
                return integration.calendar_id

        created = (
            service.calendars()
            .insert(body={"summary": target_name, "timeZone": timezone})
            .execute()
        )
        integration.calendar_id = created.get("id")
        integration.updated_at = datetime.now(timezone.utc)
        db.commit()
        return integration.calendar_id

    async def disconnect(self, db, user_id: int = 1):
        integration = self._get_integration(db, user_id)
        if not integration:
            return

        integration.is_connected = False
        integration.access_token = None
        integration.refresh_token = None
        integration.calendar_id = None
        integration.updated_at = datetime.now(timezone.utc)
        db.commit()

    async def upsert_task_event(self, db, task, user_id: int = 1) -> Optional[str]:
        service, integration = self._get_service(db, user_id)
        if not service or not integration:
            return None

        calendar_id = await self.ensure_brain_calendar(db, user_id)
        if not calendar_id:
            return None

        timezone = self._get_user_timezone(db, user_id)
        title = f"Task: {task.title}"
        desc = task.description or ""

        body = {"summary": title, "description": desc}
        if task.scheduled_at:
            end_dt = task.scheduled_end or (task.scheduled_at + timedelta(minutes=30))
            body["start"] = {
                "dateTime": task.scheduled_at.isoformat(),
                "timeZone": timezone,
            }
            body["end"] = {"dateTime": end_dt.isoformat(), "timeZone": timezone}
        elif task.due_date:
            # all-day event
            next_day = task.due_date + timedelta(days=1)
            body["start"] = {"date": str(task.due_date)}
            body["end"] = {"date": str(next_day)}
        else:
            return None

        if task.google_event_id:
            try:
                event = (
                    service.events()
                    .update(
                        calendarId=calendar_id, eventId=task.google_event_id, body=body
                    )
                    .execute()
                )
            except Exception:
                event = (
                    service.events().insert(calendarId=calendar_id, body=body).execute()
                )
        else:
            event = service.events().insert(calendarId=calendar_id, body=body).execute()

        task.google_event_id = event.get("id")
        integration.last_sync_at = datetime.now(timezone.utc)
        db.commit()
        return task.google_event_id

    async def create_session_event(self, db, ctx, user_id: int = 1) -> Optional[str]:
        service, integration = self._get_service(db, user_id)
        if not service or not integration:
            return None
        if not ctx.ended_at:
            return None

        calendar_id = await self.ensure_brain_calendar(db, user_id)
        if not calendar_id:
            return None

        timezone = self._get_user_timezone(db, user_id)
        title = f"Focus: {ctx.context_name or 'Session'}"
        body = {
            "summary": title,
            "description": f"Type: {ctx.context_type or 'deep_work'}",
            "start": {"dateTime": ctx.started_at.isoformat(), "timeZone": timezone},
            "end": {"dateTime": ctx.ended_at.isoformat(), "timeZone": timezone},
        }

        event = service.events().insert(calendarId=calendar_id, body=body).execute()
        integration.last_sync_at = datetime.now(timezone.utc)
        db.commit()
        return event.get("id")

    async def sync_all(self, db, user_id: int = 1) -> dict:
        from models.dopamine import Task
        from models.context import ContextLog

        synced_tasks = 0
        synced_sessions = 0

        tasks = db.query(Task).filter(Task.user_id == user_id).all()
        for task in tasks:
            if task.scheduled_at or task.due_date:
                try:
                    event_id = await self.upsert_task_event(db, task, user_id)
                    if event_id:
                        synced_tasks += 1
                except Exception as e:
                    log.warning(f"Task sync failed (task_id={task.id}): {e}")

        sessions = (
            db.query(ContextLog)
            .filter(
                ContextLog.user_id == user_id,
                ContextLog.ended_at.isnot(None),
                ContextLog.duration_minutes.isnot(None),
                ContextLog.duration_minutes >= 5,
                ContextLog.google_event_id.is_(None),
            )
            .all()
        )
        for ctx in sessions:
            try:
                event_id = await self.create_session_event(db, ctx, user_id)
                if event_id:
                    ctx.google_event_id = event_id
                    synced_sessions += 1
            except Exception as e:
                log.warning(f"Session sync failed (context_id={ctx.id}): {e}")

        db.commit()
        return {
            "synced_tasks": synced_tasks,
            "synced_sessions": synced_sessions,
        }


google_calendar_service = GoogleCalendarService()
