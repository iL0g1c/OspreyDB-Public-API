# OspreyDB Public API V2 Documentation
This documentation outlines the usage, endpoints, and constraints for the OspreyDB Public API version 2 (v2).\
Base URL: ```https://api.gms-admin.net1.```
## Rate Limiting
To ensure stability and fair usage, the API implements rate limiting via Flask-Limiter. Limits are applied per IP address.
  - Default Limit: 10 requests per second across all endpoints.
  - If you exceed these limits, the API will return a 429 Too Many Requests status code.

## Pagination
For endpoints that return lists of data, pagination is enabled by default to optimize performance. Note that default per_page values vary by endpoint in the v2 API.
### Standard Query Parameters
| Parameter | Type | Default | Description                    |
|-----------|------|---------|--------------------------------|
| page      | int  | 1       | The page number to retrieve.   |
| per_page  | int  | 10-20   | Items per page (Maximum: 100). |

### Standard Paginated Response Example
```
{
  "count": 45,
  "page": 1,
  "per_page": 20,
  "results": [...]
}
```

## Endpoints
### Filter Events
Filters any event using server-side aggregation. Allows searching by account, event type, and date range.
  - URL: ```/api/v2/events/filter```
  - Method: ```GET```
  - Query Parameters:
    - ```page``` (int, default: 1)
    - ```per_page``` (int, default: 20)
    - ```acid``` (int, optional): The Account ID to filter by.
    - ```event_type``` (string, default: "all"): The type of event to match. Use "on-off" to filter for both "online" and "offline" events.
    - ```after``` (string, optional): ISO date string to filter events occurring after this time.
    - ```before``` (string, optional): ISO date string to filter events occurring before this time.
  - Example Request: ```GET /api/v2/events/filter?acid=12345&event_type=login&page=1&per_page=5```

**Example Response:**
```
{
  "count": 1,
  "page": 1,
  "per_page": 5,
  "results": [
    {
      "accountID": 12345,
      "event": {
        "type": "login",
        "timestamp": "2026-05-11T12:00:00Z"
      }
    }
  ]
}
```
### Get Account Details
Retrieves the full profile for a specific account. Unlike the v1 API which uses path parameters, v2 uses a query parameter.
  - URL: ```/api/v2/users/```
  - Method: ```GET```
  - Query Params:* ```acid``` (int) — Required
  - Example Request: ```GET /api/v2/users/?acid=12345```

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
### Callsign Cross-Check
Performs cross-account callsign similarity pairing. Calculates seed documents based on an Account ID or Regex pattern, extracts callsigns, and paginates through matches from other accounts.

  - URL: ```/api/v2/callsign-cross-check```
  - Method: ```GET```
  - Query Parameters:
    - ```page``` (int, default: 1)
    - ```per_page``` (int, default: 10)
    - ```acid``` (int, optional): The Account ID to use as a seed.
    - ```pattern``` (string, optional): Regex pattern to find seed callsigns (e.g., ```/pattern/flags```). Valid flags: i, m, x, s.
    - Note: You must provide either acid or pattern.
  - Example Request: ```GET /api/v2/callsign-cross-check?acid=12345```

**Example Response:**
```
{
  "count": 2,
  "page": 1,
  "per_page": 10,
  "results": [
    {
      "accountID": 67890,
      "currentCallsign": "HAWK-2",
      "matchedDetails": [
        "HAWK-2 (seed ACID(s): 12345)"
      ]
    }
  ]
}
```
### Get Earliest Event
Returns the absolute earliest recorded event for a specific account.
  - URL: ```/api/v2/events/earliest```
  - Method: ```GET```
  - Query Params:
    - ```acid``` (int) — Required
  - Example Request: ```GET /api/v2/events/earliest?acid=12345```

**Example Response:**
```
{
  "event": {
    "type": "account_created",
    "timestamp": "2024-01-01T08:00:00Z"
  }
}
```

### Search Users
Search accounts by an exact past callsign or a regex pattern.

  - URL: ```/api/v2/users/search```
  - Method: ```GET```
  - Query Parameters:
    - ```page``` (int, default: 1)
    - ```per_page``` (int, default: 10)
    - ```exact_callsign``` (string, optional): Searches for an exact case-insensitive match in past callsigns.
    - ```pattern``` (string, optional): Regex pattern to search past callsigns (e.g., /pattern/flags). Valid flags: i, m, x, s.
    - Note: You must provide either exact_callsign or pattern.
  - Example Request: ```GET /api/v2/users/search?pattern=/^RAVEN/i```

**Example Response:**
```
{
  "count": 1,
  "page": 1,
  "per_page": 10,
  "results": [
    {
      "accountID": 12345,
      "currentCallsign": "RAVEN-1",
      "pastCallsigns": ["RAVEN-1", "HAWK-2"]
    }
  ]
}
```
## Error Handling
The API uses standard HTTP status codes to indicate success or failure:
| Status Code               | Description                                                                                                        |
|---------------------------|--------------------------------------------------------------------------------------------------------------------|
| 200 OK                    | The request was successful.                                                                                        |
| 400 Bad Request           | Missing required parameters (e.g., neither acid nor pattern provided), invalid parameter types, or bad formatting. |
| 404 Not Found             | The requested Account ID (acid) or event does not exist.                                                           |
| 429 Too Many Requests     | You have hit the rate limit (10 req/sec).                                                                          |
| 500 Internal Server Error | An unexpected error occurred on the server.                                                                        |

**Example Error Response:**
```
{
  "error": "Must provide 'acid' or 'pattern'"
}
```
