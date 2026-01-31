# timeback-oneroster

Python client for the OneRoster v1.2 API.

## Installation

```bash
# pip
pip install timeback-oneroster

# uv (add to a project)
uv add timeback-oneroster

# uv (install into current environment)
uv pip install timeback-oneroster
```

## Quick Start

```python
from timeback_oneroster import OneRosterClient

async def main():
    client = OneRosterClient(
        env="staging",  # or "production"
        client_id="your-client-id",
        client_secret="your-client-secret",
    )

    # List all schools
    schools = await client.schools.list()
    for school in schools:
        print(school.name)

    # Get a specific user
    user = await client.users.get("user-sourced-id")
    print(f"{user.given_name} {user.family_name}")

    await client.close()
```

## Client Structure

```python
client = OneRosterClient(options)

# Rostering
client.users        # All users
client.students     # Students (filtered users)
client.teachers     # Teachers (filtered users)
client.classes      # Classes
client.schools      # Schools
# client.courses    # Coming soon
# client.enrollments # Coming soon
# client.terms      # Coming soon
```

## Resource Operations

Each resource supports:

```python
# List all items
users = await client.users.list()

# List with type-safe filtering (recommended)
active_teachers = await client.users.list(
    where={"status": "active", "role": "teacher"}
)

# With operators
teachers_or_aides = await client.users.list(
    where={"role": {"in_": ["teacher", "aide"]}}
)

# Not equal
non_deleted = await client.users.list(
    where={"status": {"ne": "deleted"}}
)

# Sorting
sorted_users = await client.users.list(
    where={"status": "active"},
    sort="familyName",
    order_by="asc",
)

# Legacy filter string (still supported)
active_users = await client.users.list(filter="status='active'")

# Get by sourcedId
user = await client.users.get("user-id")

# Create (where supported)
create_result = await client.classes.create({
    "title": "Math 101",
    "course": {"sourcedId": "course-id"},
    "school": {"sourcedId": "school-id"},
})
print(create_result.sourced_id_pairs.allocated_sourced_id)

# Update (where supported)
await client.classes.update("class-id", {"title": "Math 102"})

# Delete (where supported)
await client.classes.delete("class-id")
```

## Nested Resources

```python
# Schools
classes = await client.schools("school-id").classes()
students = await client.schools("school-id").students()
teachers = await client.schools("school-id").teachers()
courses = await client.schools("school-id").courses()

# Classes
students = await client.classes("class-id").students()
teachers = await client.classes("class-id").teachers()
enrollments = await client.classes("class-id").enrollments()

# Enroll a student
await client.classes("class-id").enroll({"sourcedId": "student-id", "role": "student"})

# Users
classes = await client.users("user-id").classes()
demographics = await client.users("user-id").demographics()

# Students / Teachers
classes = await client.students("student-id").classes()
classes = await client.teachers("teacher-id").classes()
```

## Filtering

The client supports type-safe filtering with the `where` parameter:

```python
# Simple equality
users = await client.users.list(where={"status": "active"})

# Multiple conditions (AND)
users = await client.users.list(
    where={"status": "active", "role": "teacher"}
)

# Operators
users = await client.users.list(where={"score": {"gte": 90}})        # >=
users = await client.users.list(where={"score": {"gt": 90}})         # >
users = await client.users.list(where={"score": {"lte": 90}})        # <=
users = await client.users.list(where={"score": {"lt": 90}})         # <
users = await client.users.list(where={"status": {"ne": "deleted"}}) # !=
users = await client.users.list(where={"email": {"contains": "@school.edu"}})  # substring

# Match any of multiple values (OR)
users = await client.users.list(
    where={"role": {"in_": ["teacher", "aide"]}}
)

# Exclude multiple values
users = await client.users.list(
    where={"status": {"not_in": ["deleted", "inactive"]}}
)

# Explicit OR across fields
users = await client.users.list(
    where={"OR": [{"role": "teacher"}, {"status": "active"}]}
)
```

## Pagination

For large datasets, use streaming:

```python
# Collect all users
all_users = await client.users.stream().to_list()

# With limits
first_100 = await client.users.stream(max_items=100).to_list()

# With filtering
active_users = await client.users.stream(
    where={"status": "active"}
).to_list()

# Get first item only
first_user = await client.users.stream().first()
```

## Configuration

```python
OneRosterClient(
    # Environment-based (recommended)
    env="production",  # or "staging"
    client_id="...",
    client_secret="...",

    # Or explicit URLs
    base_url="https://api.example.com",
    auth_url="https://auth.example.com/oauth2/token",
    client_id="...",
    client_secret="...",

    # Optional
    timeout=30.0,  # Request timeout in seconds
)
```

## Environment Variables

If credentials are not provided explicitly, the client reads from:

- `ONEROSTER_CLIENT_ID`
- `ONEROSTER_CLIENT_SECRET`
- `ONEROSTER_BASE_URL` (optional)
- `ONEROSTER_TOKEN_URL` (optional)

## Error Handling

```python
from timeback_oneroster import OneRosterError, NotFoundError, AuthenticationError

try:
    user = await client.users.get("invalid-id")
except NotFoundError as e:
    print(f"User not found: {e.sourced_id}")
except AuthenticationError:
    print("Invalid credentials")
except OneRosterError as e:
    print(f"API error: {e}")
```

## Async Context Manager

```python
async with OneRosterClient(client_id="...", client_secret="...") as client:
    schools = await client.schools.list()
# Client is automatically closed
```

## FastAPI Integration

```python
from fastapi import FastAPI, Depends
from timeback_oneroster import OneRosterClient

app = FastAPI()

async def get_oneroster():
    client = OneRosterClient(
        env="production",
        client_id="...",
        client_secret="...",
    )
    try:
        yield client
    finally:
        await client.close()

@app.get("/schools")
async def list_schools(client: OneRosterClient = Depends(get_oneroster)):
    return await client.schools.list()
```
