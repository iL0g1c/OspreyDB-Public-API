# Program Overview
At OspreX, we take the security seriously. We encourage security researchers to help us identify vulnerabilities in our API. In return for your responsible disclosure, we offer up to 10 dollars and various swag in the GeoFS Open Source Community Server based on the severity of the impact.

# Safe Harbor
If you conduct your security research and disclosure in accordance with this policy, we will not initiate or support any legal action related to your research.

# Scope
## In-Scope
  * Primary API Endpoint: [https://api.gms-admin.net/api/v1](https://api.gms-admin.net/api/v1)
  * Tread carefully regarding container escapes, insecure Docker socket configurations, or SSRF (Server-Side Request Forgery) that could allow access to internal metadata or peer services. Please report these findings based on a theoretical Proof of Concept or limited interaction only.
## Out of Scope & Prohibited Actions
We use the "Stop at the Door" policy. The following actions are strictly prohibited and will result in immediate disqualification from the program and loss of Safe Harbor:
  * **Lateral Movement:** Attempting to pivot from the API to the host machine, other containers, or internal network services.
  * **Actual Data Access:** If you find a way to access data outside of OspreyDB, stop immediately. Do not attempt to download, view, or modify it.
  * **Infrastructure/Hosting Provider:** Vulnerabilities in the underlying hosting provider (e.g., Cloudflare or ISP) are out of scope unless they are caused by a misconfiguration in our API deployment.
# Severity Levels & Rewards
Use the CVSS (Common Vulnerability Scoring System) to categorize bugs. This prevents disputes over how much a bug is "worth."
In the event of duplicate reports, only the first researcher to report the vulnerability will be eligible for a reward.
| Severity | CVSS Range | OspreyDB-Specific Examples                                                                                                                                                                                                                               | Estimated Reward                          |
|----------|------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------------------------|
| Critical | 9.0 - 10.0 | Remote Code Execution (RCE) or gaining write/delete access to the MongoDB database. Finding a way to leak the .env file containing DATABASE_TOKEN or DASHBOARD_TOKEN.                                                                                    | $10 + Hacker Overlord Role (Or anything you want) + Hall of Fame |
| High     | 7.0 - 8.9  | Dashboard Auth Bypass: Successfully bypassing the DASHBOARD_TOKEN requirement to access the Flask-MonitoringDashboard. NoSQL Injection: Crafting a malicious query via the /search endpoint that allows extraction of unauthorized database collections. | $3 + Elite Hacker Role + Hall of Fame     |
| Medium   | 4.0 - 6.9  | Rate-Limit Bypass: Successfully spoofing the CF-Connecting-IP header to bypass the 10 req/sec limits or to falsely rate-limit other legitimate users' IP addresses.                                                                                      | White Hat Role + Hall of Fame             |
| Low      | 0.1 - 3.9  | Information Disclosure: Forcing the API to return unhandled Python/Werkzeug stack traces, or revealing internal server versions.                                                                                                                         | I-Can-Use-ChatGPT Role                    |

_Note: You will only receive rewards for the highest tier you reach. Also, for the first round, only one 10 dollar and one 3 dollar reward will be handed out. (Only the first to find this big of a bug will be rewarded, so be quick)._

# Rules of Engagement
To qualify for a reward and remain in "Safe Harbor" (legal protection), researchers must follow these rules:
  * No Data Disruption: Do not delete, modify, or pivot through data.
  * Confidentiality: Do not disclose the vulnerability to the public until it has been remediated and you have received explicit permission.
  * Exploitation Limit: Once a "Proof of Concept" (PoC) is established (e.g., proving you can read a file), stop testing and report it immediately.
# Focus Areas
We are particularly interested in vulnerabilities that could compromise the integrity of the OspreyDB database or the privacy of other services.\
Please focus your efforts on the following:
  * NoSQL Injection: The /api/v1/search endpoint utilizes a query parameter to search across multiple fields using an $or operator. We are interested in any payloads that can "break out" of this query to extract unauthorized data or bypass the pagination logic.
  * Rate-Limit Bypasses (IP Spoofing): The API relies on the CF-Connecting-IP header to identify users for rate limiting. We want to know if these limits can be bypassed by spoofing this header or if the implementation allows for IP-based denial of service against other users.
  * Administrative Access Bypass: The flask_monitoringdashboard is configured with a DASHBOARD_TOKEN. Any method that allows access to this dashboard without the correct token is a high priority.
  * Anything else you find.
  * Pagination Logic Flaws: The paginate_query and paginate_document_array functions handle user-supplied page and per_page integers. We are looking for vulnerabilities related to integer overflows, negative values that bypass constraints, or "Resource Exhaustion" via extremely high per_page requests that exceed the 100-item limit.
  * Container & Environment Security: Since the API runs within a Docker container, we are interested in vulnerabilities that could allow an attacker to view the .env file or environment variables, such as DATABASE_TOKEN.

# Submission Method & Template
Submit reports to Osprey via Discord DM "x_aiwass_x"\
**Suggested Reporting Format:**
  * Summary: Brief description of the vulnerability.
  * Impact: What can an attacker do with this?
  * Steps to Reproduce: Numbered list of steps.
  * Proof of Concept (PoC): URL, payload, or screenshot.
  * Any automated scripts that you used.
  * Recommended Fix: (Optional).
