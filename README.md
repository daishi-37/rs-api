## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate 
cd app && pip install -r requirements.txt
cp .env.example .env
vi .env
python -m alembic upgrade head
python -m app.main
```
