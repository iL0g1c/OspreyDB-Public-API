# API Documentation: OspreyDB-Public-API
This documentation outlines the usage, endpoints, and constraints for the GMS Admin API.
**Base URL:** https://api.gms-admin.net/api/v1/
## 1. Rate Limiting
To ensure stability and fair usage, the API implements rate limiting via Flask-Limiter. Limits are applied per IP address.
  * **Default Limit:** 10 requests per second across all endpoints.
  * **Restricted Endpoints:** Certain high-load routes, such as account events, are capped at 5 requests per second.
If you exceed these limits, the API will return a 429 Too Many Requests status code.
