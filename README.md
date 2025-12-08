# Campaign Management Service

This Django application provides APIs to manage campaigns, including creating, listing, and redeeming discounts. It follows a **service-layer architecture** to separate business logic from app logic.

## Features

- **Campaign Management:** CRUD operations for campaigns.
- **Public APIs:**

  - `available` – fetch applicable discounts for a user/cart.
  - `redeem` – redeem a discount in an atomic operation.

- **Service Layer Architecture:** Business logic (availability and redemption) is separated from the view logic.
- **Caching:** Redis is used to reduce database query hits.
- **Database:** PostgreSQL for high compatibility, transactional integrity, and row-level locking to prevent race conditions.
- **Throttling:** APIs are rate-limited using DRF throttling classes.

## Installation

1. Clone the repository.
2. Create a virtual environment and activate it:

```bash
python -m venv .venv
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

4. Setup Postgres:

```
docker run -d \
  --name my-postgres \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=campaign_manager \
  -p 5432:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:17
```

5. Setup Redis

```
docker run -d \
  --name my-redis \
  -p 6379:6379 \
  -v redisdata:/data \
  redis:8 \
  redis-server --appendonly yes
```

6. Apply migrations:

```bash
python manage.py migrate
```

## Setup

1. Create a superuser to access protected endpoints:

```bash
python manage.py createsuperuser
```

2. Load sample data (users, campaigns, redemptions):

```bash
python manage.py load_sample_data
```

3. Start the development server:

```bash
python manage.py runserver
```

## API Documentation

The API documentation is auto-generated using **DRF Spectacular** and accessible at:

[http://localhost:8000/api/docs/#/](http://localhost:8000/api/docs/#/)

It includes all API operations, including CRUD operations for campaigns and public actions for fetching available discounts and redeeming them.

## Testing

Run tests using:

```bash
python manage.py test --keepdb
```

The `--keepdb` option preserves the test database to speed up subsequent test runs.

## Notes

- **Service Layer:** `CampaignService` handles all business logic related to campaign availability and redemption.
- **Caching:** Redis is used to improve performance and reduce repeated database queries.
- **Database Choice:** PostgreSQL is used for its support of row-level locking and high compatibility with Django.
- **Rate Limiting:** APIs uses throttling to prevent abuse (`user` and `redeem` scopes).
- **Performance Consideration**: To further increase in perfomance, combination of uswgi and nginx is to be used. This would be needed to handle the expected load. But haven't included config and setup them in this project.
