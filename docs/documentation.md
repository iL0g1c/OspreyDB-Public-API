# API Documentation: OspreyDB-Public-API
This documentation outlines the usage, endpoints, and constraints for the OspreyDB Public API.
**Base URL:** https://api.gms-admin.net/api/v1/
## 1. Rate Limiting
To ensure stability and fair usage, the API implements rate limiting via Flask-Limiter. Limits are applied per IP address.
  * **Default Limit:** 10 requests per second across all endpoints.
  * **Restricted Endpoints:** Certain high-load routes, such as account events, are capped at 5 requests per second.
If you exceed these limits, the API will return a 429 Too Many Requests status code.

## 2. Pagination
For endpoints that return lists of data, pagination is enabled by default to optimize performance.
### Query Parameters
| Parameter | Type | Default | Description                    |
|-----------|------|---------|--------------------------------|
| page      | int  | 1       | The page number to retrieve.   |
| per_page  | int  | 20      | Items per page (Maximum: 100). |

**Example:** https://api.gms-admin.net/api/v1/online?page=2&per_page=10

### Standard Paginated Response
```
{
  "count": 20,
  "page": 1,
  "per_page": 20,
  "results": [...]
}
```

## 3. Endpoints
### Get Account Details
Retrieves the full profile for a specific account using its unique Account ID (acid).
  * URL: /users/<acid>
  * Method: GET
  * Path Params: acid (integer)
  * Example Request: GET https://api.gms-admin.net/api/v1/users/12345

**Example Response:**
```
{
  "_id": "60d5ec...",
  "accountID": 12345,
  "currentCallsign": "RAVEN-1",
  "Online": true,
  "events": [...],
  "pastCallsigns": ["HAWK-2", "VULTURE-5"]
}
```
### Get Account Events
A specialized route to retrieve only the events array for a specific user. This is useful for reducing bandwidth when you don't need the full profile.
  * URL: /users/<acid>/events
  * Method: GET
  * Rate Limit: 5 requests per second.
  * Example Request: GET https://api.gms-admin.net/api/v1/users/12345/events

**Example Response:**
```
{
  "events": [
    {"type": "login", "timestamp": "2026-05-11T12:00:00Z"},
    {"type": "callsign_change", "old": "HAWK-2", "new": "RAVEN-1"}
  ]
}
```
### Get Online Accounts
Returns a paginated list of all accounts where the status is currently set to Online: true.
  * URL: /online
  * Method: GET
  * Example Request: GET https://api.gms-admin.net/api/v1/online?page=1&per_page=5

### Search by Callsign
Searches the database for accounts matching a specific callsign. This endpoint performs a dual-search against both currentCallsign and pastCallsigns.
  * URL: /searchMethod: GET
  * Query Params: callsign (string) — Required
  * Example Request: GET https://api.gms-admin.net/api/v1/search?callsign=RAVEN-1

Example Response:
```
{
  "count": 1,
  "page": 1,
  "per_page": 20,
  "results": [
    {
      "accountID": 12345,
      "currentCallsign": "RAVEN-1",
      "pastCallsigns": ["HAWK-2"]
    }
  ]
}
```

## 4. Error Handling
The API uses standard HTTP status codes to indicate success or failure:
| Status Code               | Description                                                             |
|---------------------------|-------------------------------------------------------------------------|
| 200 OK                    | The request was successful.                                             |
| 400 Bad Request           | Missing parameters (e.g., missing callsign in search) or invalid types. |
| 404 Not Found             | The requested Account ID (acid) does not exist.                         |
| 429 Too Many Requests     | You have hit the rate limit.                                            |
| 500 Internal Server Error | Something went wrong on our end.                                        |

Example Error Response:
```
{
  "error": "Missing 'callsign' query parameter"
}
```
