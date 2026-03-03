with open("main.py", "r") as f:
    text = f.read()

import_str = """from api.calendar import (
    router as calendar_router,
    public_router as calendar_public_router,
)
from api.auth import router as auth_router
from api.sentiment import router as sentiment_router
from api.reports import router as reports_router
from api.nudges import router as nudges_router
from api.dreams import router as dreams_router
from api.sleep import router as sleep_router
from api.burnout import router as burnout_router
from api.schedule import router as schedule_router
from api.habit_stacking import router as habit_stacking_router
from api.anomalies import router as anomalies_router
from api.location import router as location_router
from api.websocket import router as websocket_router
"""

if "from api.auth import router as auth_router" not in text:
    old_import = """from api.calendar import (
    router as calendar_router,
    public_router as calendar_public_router,
)"""
    text = text.replace(old_import, import_str)

router_str = """app.include_router(
    calendar_public_router,
    prefix="/api/calendar",
    tags=["Calendar Public"],
)

app.include_router(auth_router, prefix="/api/auth", tags=["Auth"])
app.include_router(sentiment_router, prefix="/api/sentiment", tags=["Sentiment"], dependencies=auth_dep)
app.include_router(reports_router, prefix="/api/reports", tags=["Reports"], dependencies=auth_dep)
app.include_router(nudges_router, prefix="/api/nudges", tags=["Nudges"], dependencies=auth_dep)
app.include_router(dreams_router, prefix="/api/dreams", tags=["Dreams"], dependencies=auth_dep)
app.include_router(sleep_router, prefix="/api/sleep", tags=["Sleep"], dependencies=auth_dep)
app.include_router(burnout_router, prefix="/api/burnout", tags=["Burnout"], dependencies=auth_dep)
app.include_router(schedule_router, prefix="/api/schedule", tags=["Schedule"], dependencies=auth_dep)
app.include_router(habit_stacking_router, prefix="/api/habits", tags=["Habit Stacking"], dependencies=auth_dep)
app.include_router(anomalies_router, prefix="/api/anomalies", tags=["Anomalies"], dependencies=auth_dep)
app.include_router(location_router, prefix="/api/location", tags=["Location"], dependencies=auth_dep)
app.include_router(websocket_router, prefix="/ws", tags=["WebSocket"])
"""

if 'prefix="/api/auth"' not in text:
    old_router = """app.include_router(
    calendar_public_router,
    prefix="/api/calendar",
    tags=["Calendar Public"],
)"""
    text = text.replace(old_router, router_str)

with open("main.py", "w") as f:
    f.write(text)

print("Updated main.py")
