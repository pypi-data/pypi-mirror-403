# PostGIS Infrastructure Support

## Overview

Add PostGIS geospatial support as an infrastructure component. Unlike other infra modules, PostGIS is a Postgres extension rather than a separate service, so it requires special handling to modify the existing postgres docker service.

## Use Case

Enable paxx-generated projects to support location-based features:
- Store geographic points (lat/lng)
- Query by distance (`ST_DWithin`)
- Query by bounding box / viewport (`ST_Intersects`, `ST_MakeEnvelope`)
- Calculate distances between points

## File Structure

```
src/paxx/infra/postgis/
├── __init__.py
├── config.py
├── dependencies.txt
├── docker_service.yml      # empty - special case
└── templates/
    └── geo.py.jinja        # spatial helpers
```

## Implementation Details

### 1. config.py

Standard `InfraConfig` dataclass with:
- `name: "postgis"`
- `dependencies: ["geoalchemy2>=0.14"]`
- No new env vars (uses existing DATABASE_URL)
- Flag indicating it modifies postgres rather than adding a service

### 2. dependencies.txt

```
geoalchemy2>=0.14
```

### 3. docker_service.yml

Empty file - PostGIS doesn't add a new service, it upgrades postgres.

### 4. templates/geo.py.jinja

Provides:
- Re-exports of `Geography`, `Geometry` types
- `make_point(lng, lat)` - create PostGIS point
- `distance_within(column, lat, lng, radius_meters)` - filter by radius
- `bbox_filter(column, west, south, east, north)` - viewport queries
- `distance_meters(column, lat, lng)` - calculate distance

### 5. cli/infra.py modifications

Add `_upgrade_postgres_to_postgis()` function that:
1. Finds postgres service in docker-compose.yml (checks: db, postgres, database)
2. Extracts version from current image
3. Replaces with `postgis/postgis:{version}-3.4`

Add special case in `add()` command for postgis.
Add description to `list` command.

## Usage

```bash
paxx infra add postgis
```

Output:
```
Adding infrastructure: postgis
  Updated db service to PostGIS image
  Created core/geo.py
  Updated pyproject.toml

Next steps:
  1. Run: uv sync
  2. Restart database: docker compose down && docker compose up -d
```

### In Models

```python
from core.geo import Geography
from sqlalchemy.orm import Mapped, mapped_column

class Hide(Base):
    __tablename__ = "hides"

    location: Mapped[Geography] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        index=True,  # Creates GIST index
    )
```

### In Services

```python
from core.geo import distance_within, bbox_filter, distance_meters

# Viewport query
stmt = select(Hide).where(
    Hide.active == True,
    bbox_filter(Hide.location, west, south, east, north)
)

# Proximity check
stmt = select(Hide).where(
    distance_within(Hide.location, lat, lng, radius_meters=100)
)

# Order by distance
stmt = select(Hide).order_by(
    distance_meters(Hide.location, lat, lng)
)
```

## Testing

After implementation:
1. Bootstrap a test project
2. Add postgis infra
3. Verify docker-compose.yml updated
4. Verify core/geo.py created
5. Verify pyproject.toml has geoalchemy2
6. Create a model with Geography column
7. Run migration
8. Test spatial queries
