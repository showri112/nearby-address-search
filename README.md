# Address Book API

A simple API for managing addresses and searching for nearby addresses using geographic coordinates.

## Setup & Installation

1. Create and activate a virtual environment (Windows):
```bash
python -m venv venv
venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the app in development mode:
```bash
uvicorn app.main:app --reload
```

4. API will be available at: http://localhost:8000
   - Swagger docs: http://localhost:8000/docs

## Project Structure

```
app/
  __init__.py
  main.py
  database.py
  models.py
  schemas.py
  crud.py
  routers.py
  utils.py
main.py
requirements.txt
README.md
```

## API Endpoints

### Create Address
```bash
curl -X POST http://localhost:8000/addresses/ \
  -H "Content-Type: application/json" \
  -d '{"street":"123 Main St","city":"New York","country":"USA","latitude":40.7128,"longitude":-74.0060}'
```

### Get All Addresses
```bash
curl http://localhost:8000/addresses/
```

### Get Address by ID
```bash
curl http://localhost:8000/addresses/{address_id}
```

### Update Address
```bash
curl -X PUT http://localhost:8000/addresses/{address_id} \
  -H "Content-Type: application/json" \
  -d '{"street":"456 Oak Ave","city":"Boston","country":"USA","latitude":42.3601,"longitude":-71.0589}'
```

### Delete Address
```bash
curl -X DELETE http://localhost:8000/addresses/{address_id}
```

### Search Nearby Addresses
```bash
curl -X POST http://localhost:8000/search/nearby \
  -H "Content-Type: application/json" \
  -d '{"latitude":40.7128,"longitude":-74.0060,"distance_km":15}'
```

## Performance Optimization for `/search/nearby`

The search endpoint is optimized in two stages to handle large databases efficiently:

**Stage 1: Bounding Box Filter (Database)**
Instead of calculating distance for every address in the database, we first filter using a geographic bounding box:
- Convert the search radius to latitude/longitude offsets
- Query only addresses within this box using database WHERE clause
- This reduces addresses by ~80-95% without heavy calculations

**Stage 2: Precise Distance Calculation**
Only the filtered addresses get the exact Haversine distance calculated and sorted by distance.

**NumPy Speedup:**
If NumPy is available, it vectorizes all distance calculations at once (5-10x faster for large result sets).

This approach turns what could be millions of distance calculations into thousands, making it practical for real-world databases.

## Project Structure

```
main.py         - API routes and logic
models.py       - Database models
schemas.py      - Input validation schemas
database.py     - Database config
requirements.txt - Dependencies
```

## Database

Uses SQLite database (`address_book.db`). To reset it, just delete the file and restart the app.
