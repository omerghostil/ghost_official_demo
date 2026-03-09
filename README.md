# Ghost Brain Demo

מערכת דמו מקומית לניטור מצלמה חכם עם זיכרון טקסטואלי מתמשך.

## דרישות מקדימות

- Python 3.9+
- Node.js 18+
- מצלמת רשת מחוברת
- מפתח OpenAI API (לניתוח קולאז'ים וצ'אט)

## התקנה והרצה מהירה

### 1. Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. הגדרת מפתח OpenAI

ערוך את `backend/.env`:
```
OPENAI_API_KEY=sk-your-key-here
```

### 3. הרצת Backend

```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. גישה

פתח דפדפן ב: `http://localhost:3000`

## משתמשי Seed

| משתמש | סיסמה | תפקיד |
|--------|--------|--------|
| `ghost_admin` | `GhostDemo2024!` | admin |
| `ghost_viewer` | `ViewOnly1!` | client |

## מבנה DB

| טבלה | תיאור |
|-------|--------|
| `users` | משתמשים |
| `sessions` | סשנים |
| `cameras` | הגדרות מצלמה |
| `worker_state` | מצב workers |
| `capture_jobs` | משימות צילום |
| `background_frames` | פריימים שנדגמו |
| `collages` | קולאז'ים שנוצרו |
| `detections` | תוצאות זיהוי |
| `analyses` | תוצאות ניתוח OpenAI |
| `memory_entries` | רשומות זיכרון |
| `alert_rules` | חוקי התראה |
| `alerts` | אירועי התראה |
| `chat_messages` | הודעות צ'אט |
| `event_journal` | יומן אירועים |

## API Endpoints

### Auth
- `POST /auth/login` — התחברות
- `POST /auth/logout` — התנתקות
- `GET /auth/me` — פרטי משתמש נוכחי

### Camera
- `GET /camera/stream` — MJPEG streaming
- `GET /camera/status` — סטטוס מצלמה
- `POST /camera/reconnect` — חיבור מחדש
- `POST /camera/snapshot` — צילום מיידי

### Alerts
- `GET /alerts/rules` — חוקי התראה
- `POST /alerts/rules` — יצירת חוק
- `PATCH /alerts/rules/{id}` — עדכון חוק
- `DELETE /alerts/rules/{id}` — מחיקת חוק
- `GET /alerts/events` — אירועי התראה

### Chat
- `POST /chat/message` — שליחת הודעה
- `GET /chat/history` — היסטוריית צ'אט

### History
- `GET /history/memory` — רשומות זיכרון
- `GET /history/timeline` — ציר זמן

### Admin
- `GET /admin/users` — רשימת משתמשים
- `POST /admin/users` — יצירת משתמש
- `PATCH /admin/users/{id}` — עדכון משתמש
- `DELETE /admin/users/{id}` — מחיקת משתמש
- `POST /admin/users/{id}/reset-password` — איפוס סיסמה
- `GET /admin/health` — בריאות מערכת

### Health
- `GET /health` — בדיקת תקינות
- `GET /health/workers` — סטטוס workers
- `GET /health/storage` — שימוש באחסון

## ארכיטקטורת Workers

המערכת מפעילה 3 workers ברקע:

1. **CameraWorker** — ניטור חיבור מצלמה, reconnect אוטומטי
2. **MemoryWorker** — דגימת פריים כל 2 שניות, detection, significant change, collage
3. **AnalysisWorker** — שליחת קולאז'ים ל-OpenAI, שמירת זיכרון, הערכת התראות

**Supervisor** מנטר heartbeat, מבצע restart אוטומטי, ונכנס למצב DEGRADED אם worker נכשל 3 פעמים.

## Recovery

באתחול מחדש:
- collages במצב "processing" מוחזרים ל-"pending"
- workers מתחילים מחדש אוטומטית
- journal JSONL לא מושפע מ-restart

## מגבלות ידועות

- מצלמה אחת בלבד
- עד 4 חוקי התראה
- ללא mobile view
- ללא export
- ללא vector search
- ללא RTSP — רק webcam מקומית
- fallback stub ל-detection אם מודל ONNX חסר

## הרצת בדיקות

```bash
cd backend
source venv/bin/activate
python -m pytest tests/ -v
```
