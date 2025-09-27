# 🎾 Kourts API

A REST API for managing sports court bookings. Built this for managing tennis/padel court reservations with features like preventing double bookings, sending notifications, and handling match creation.

> **Note:** This is the public version of the original codebase, cleaned up and documented for sharing. That's why there's no commit history - this repo starts fresh from the polished version.

## What it does

- Manage multiple sports venues and their courts
- Book time slots with automatic conflict detection  
- Send booking confirmations via email and WhatsApp
- Let players create and join pickup matches
- Admin panel for venue owners
- Background job processing for notifications

## Features

- Multiple venues with different court types
- Time-based booking system with conflict prevention
- Database constraints to prevent double bookings (no more overbookings!)
- Email and WhatsApp notifications
- Social match system for pickup games
- Admin API with key authentication
- Async background jobs for sending notifications

## Tech Stack

- **FastAPI** - Python web framework
- **PostgreSQL** - Database with SQLModel ORM  
- **Alembic** - Database migrations
- **Pydantic** - Data validation
- **Async/await** throughout
- **SendGrid & Twilio** - For notifications (configurable)

## Project Structure

```
kourts/
├── app/
│   ├── api/           # API route handlers
│   ├── core/          # Configuration and database
│   ├── models/        # SQLModel database models
│   ├── schemas/       # Pydantic request/response schemas
│   ├── services/      # Business logic layer
│   └── workers/       # Background job processors
├── alembic/           # Database migrations
└── create_admin.py    # Script to create first admin user
```

## API Endpoints

### Admin Endpoints (Requires API Key)
```http
POST   /admin/venues           # Create venue
GET    /admin/venues           # List admin's venues
GET    /admin/venues/{id}      # Get venue details
PATCH  /admin/venues/{id}      # Update venue
DELETE /admin/venues/{id}      # Delete venue

POST   /admin/venues/{id}/kourts  # Create court
GET    /admin/venues/{id}/kourts  # List venue courts
GET    /admin/kourts/{id}         # Get court details
PATCH  /admin/kourts/{id}         # Update court
DELETE /admin/kourts/{id}         # Delete court

GET    /admin/bookings         # List/filter bookings
GET    /admin/bookings/{id}    # Get booking details
PATCH  /admin/bookings/{id}    # Update booking status
```

### Public Endpoints
```http
GET    /venues                    # List all venues
GET    /venues/{id}/kourts        # List venue courts
GET    /kourts/{id}/availability  # Check court availability

POST   /bookings                 # Create booking
GET    /bookings/{id}             # Get booking details
POST   /bookings/{id}/cancel      # Cancel booking

POST   /matches                  # Create match
GET    /matches                  # List matches
POST   /matches/{id}/join         # Join match
POST   /matches/{id}/leave        # Leave match
```

## Setup  

### What you need first
- **Python 3.9+**
- **PostgreSQL** (tested on 12+, but probably works on older versions)  
- **Git** (obviously)

### Installation

1. **Clone and setup**
```bash
git clone https://github.com/JaumeTorrelles/kourts-api.git
cd kourts-api

# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install everything
pip install -r requirements.txt
```

2. **Database setup**
```bash
# Create a PostgreSQL database
createdb kourts_db

# Copy environment file and edit it
cp .env.example .env
```

3. **Configure your .env file** (important!)
```
DATABASE_URL=postgresql://username:password@localhost/kourts_db
SENDGRID_API_KEY=your_sendgrid_key  # Optional, for emails
TWILIO_ACCOUNT_SID=your_twilio_sid  # Optional, for WhatsApp  
TWILIO_AUTH_TOKEN=your_twilio_token
```

4. **Setup database and create first admin**
```bash
# Setup database tables
alembic upgrade head

# Create your first admin user (will generate an API key)
python create_admin.py
```

5. **Start the server**
```bash
uvicorn app.main:app --reload
```

### Check if it's working
- API docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### First time setup
After creating your admin, you can:
1. Use the API key in the `X-Api-Key` header for admin endpoints
2. Create your first venue via `/admin/venues`
3. Add courts to your venue
4. Start taking bookings!

---