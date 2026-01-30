Analytics
=========

The GEAI Analytics module provides comprehensive insights into your GEAI platform usage, costs, performance, and adoption metrics. Through the PyGEAI SDK's ``analytics`` CLI command, you can access detailed analytics data programmatically, enabling you to monitor platform usage, track costs, identify trends, and generate reports for stakeholders.

.. contents:: Table of Contents
   :depth: 3
   :local:

Overview
--------

The Analytics module offers access to various metrics across different dimensions:

- **Lab Metrics**: Track creation and modification of agents, flows, and processes
- **Request Metrics**: Monitor total requests, error rates, and response times
- **Cost Metrics**: Analyze spending patterns and cost per request
- **Token Metrics**: Track token consumption across users and agents
- **User & Agent Activity**: Monitor active users, agents, and projects
- **Top Performers**: Identify top agents and users by requests, tokens, and cost

All analytics commands support flexible date range filtering, with automatic defaults to the previous month when dates are not specified.

Prerequisites
-------------

- **CLI Installation**: Ensure the ``geai`` CLI is installed
- **Authentication**: Obtain your API token from the GEAI platform
- **Permissions**: Analytics access permissions are required

Set your API token as an environment variable:

.. code-block:: bash

   export GEAI_APITOKEN="your-api-token-here"

Date Range Defaults
-------------------

All analytics commands support optional date range parameters. When ``--start-date`` and ``--end-date`` are not specified, commands automatically default to the previous month.

**Example**: If today is January 15, 2024, the default range would be:

- **Start Date**: 2023-12-01 (first day of December)
- **End Date**: 2023-12-31 (last day of December)

Common Options
--------------

Most analytics commands support the following options:

``--start-date, -s DATE``
  Start date for the analytics period in YYYY-MM-DD format.
  **Default**: First day of the previous month

``--end-date, -e DATE``
  End date for the analytics period in YYYY-MM-DD format.
  **Default**: Last day of the previous month

``--agent-name, -a NAME``
  Filter results by specific agent name (where applicable)

Available Commands
------------------

Help
^^^^

Display help information for analytics commands.

.. code-block:: bash

   geai analytics help
   geai analytics h

Lab Metrics
^^^^^^^^^^^

Agents Created and Modified
""""""""""""""""""""""""""""

Get the total number of agents created and modified within a date range.

**Command:**

.. code-block:: bash

   geai analytics agents-created --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics ac -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Agents created and modified:
     Created: 15
     Modified: 42

Request Metrics
^^^^^^^^^^^^^^^

Requests Per Day
""""""""""""""""

Get total requests per day, including error counts.

**Command:**

.. code-block:: bash

   geai analytics requests-per-day --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics rpd -s "2024-01-01" -e "2024-01-31"

**With agent filter:**

.. code-block:: bash

   geai analytics rpd -s "2024-01-01" -e "2024-01-31" --agent-name "Sales Assistant"

**Example Output:**

.. code-block:: text

   Total requests per day:
     2024-01-01: 450 requests (5 errors)
     2024-01-02: 523 requests (3 errors)
     2024-01-03: 601 requests (8 errors)
     ...

Error Rate
""""""""""

Get the overall error rate as a percentage.

**Command:**

.. code-block:: bash

   geai analytics error-rate --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics er -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Overall error rate: 1.24%

Cost Metrics
^^^^^^^^^^^^

Total Cost
""""""""""

Get the total cost incurred during the specified period.

**Command:**

.. code-block:: bash

   geai analytics total-cost --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics tc -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Total cost: $456.78

Average Cost Per Request
""""""""""""""""""""""""

Get the average cost per request.

**Command:**

.. code-block:: bash

   geai analytics average-cost --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics ac -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Average cost per request: $0.0367

Token Metrics
^^^^^^^^^^^^^

Total Tokens
""""""""""""

Get total input, output, and combined token counts.

**Command:**

.. code-block:: bash

   geai analytics total-tokens --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics tt -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Total tokens:
     Input: 1,234,567
     Output: 987,654
     Total: 2,222,221

User & Agent Metrics
^^^^^^^^^^^^^^^^^^^^

Active Users
""""""""""""

Get the total number of active users during the period.

**Command:**

.. code-block:: bash

   geai analytics active-users --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics au -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Total active users: 45

Top Performers
^^^^^^^^^^^^^^

Top Agents by Requests
"""""""""""""""""""""""

Get the top 10 agents ranked by number of requests.

**Command:**

.. code-block:: bash

   geai analytics top-agents --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics ta -s "2024-01-01" -e "2024-01-31"

**Example Output:**

.. code-block:: text

   Top 10 agents by requests:
     1. Sales Assistant: 2,340 requests
     2. Customer Support Bot: 1,890 requests
     3. Code Reviewer: 1,456 requests
     4. Data Analyst: 1,234 requests
     5. Content Generator: 1,089 requests
     ...

Full Report
^^^^^^^^^^^

Get a comprehensive analytics report combining all metrics.

**Command:**

.. code-block:: bash

   geai analytics full-report
   geai analytics fr

**With custom date range:**

.. code-block:: bash

   geai analytics full-report --start-date "2024-01-01" --end-date "2024-01-31"
   geai analytics fr -s "2024-01-01" -e "2024-01-31"

**Export to CSV:**

.. code-block:: bash

   geai analytics full-report --csv report.csv
   geai analytics fr -s "2024-01-01" -e "2024-01-31" -c january_report.csv

**Report Sections:**

1. **Lab Metrics**
   
   - Agents Created
   - Agents Modified
   - Flows Created
   - Flows Modified
   - Processes Created
   - Processes Modified

2. **Request Metrics**
   
   - Total Requests
   - Total Requests with Error
   - Overall Error Rate
   - Average Request Time (ms)

3. **Cost Metrics**
   
   - Total Cost (USD)
   - Average Cost per Request (USD)

4. **Token Metrics**
   
   - Total Input Tokens
   - Total Output Tokens
   - Total Tokens
   - Average Input Tokens per Request
   - Average Output Tokens per Request
   - Average Total Tokens per Request

5. **User & Agent Metrics**
   
   - Total Active Users
   - Total Active Agents
   - Total Active Projects

6. **Top 10 Agents by Requests**
7. **Top 10 Agents by Tokens**
8. **Top 10 Users by Requests**
9. **Top 10 Users by Cost**

**Example Output:**

.. code-block:: text

   Using default date range: 2023-12-01 to 2023-12-31

   ================================================================================
   ANALYTICS FULL REPORT - Period: 2023-12-01 to 2023-12-31
   ================================================================================

   LAB METRICS
   --------------------------------------------------------------------------------
   Agents Created: 15
   Agents Modified: 42
   Flows Created: 8
   Flows Modified: 23
   Processes Created: 5
   Processes Modified: 12

   REQUEST METRICS
   --------------------------------------------------------------------------------
   Total Requests: 12,450
   Total Requests with Error: 125
   Overall Error Rate: 1.00%
   Average Request Time: 1,234.56 ms

   COST METRICS
   --------------------------------------------------------------------------------
   Total Cost: $456.78
   Average Cost per Request: $0.0367

   TOKEN METRICS
   --------------------------------------------------------------------------------
   Total Input Tokens: 1,234,567
   Total Output Tokens: 987,654
   Total Tokens: 2,222,221
   Average Input Tokens per Request: 99.50
   Average Output Tokens per Request: 79.00
   Average Total Tokens per Request: 178.50

   USER & AGENT METRICS
   --------------------------------------------------------------------------------
   Total Active Users: 45
   Total Active Agents: 28
   Total Active Projects: 12

   TOP 10 AGENTS BY REQUESTS
   --------------------------------------------------------------------------------
   1. Sales Assistant: 2,340 requests
   2. Customer Support Bot: 1,890 requests
   ...

   ================================================================================

**CSV Export Format:**

.. code-block:: text

   Metric,Value
   Report Period,2024-01-01 to 2024-01-31
   Generated At,2024-02-15 14:30:45

   Agents Created,15
   Agents Modified,42
   Flows Created,8
   Flows Modified,23
   Processes Created,5
   Processes Modified,12
   Total Requests,12450
   Total Requests with Error,125
   Overall Error Rate (%),1.00%
   Average Request Time (ms),1234.56
   Total Cost (USD),456.78
   Average Cost per Request (USD),0.0367
   Total Input Tokens,1234567
   Total Output Tokens,987654
   Total Tokens,2222221
   Average Tokens per Request,178.50
   Total Active Users,45
   Total Active Agents,28
   Total Active Projects,12

Python SDK Usage
----------------

In addition to the CLI, you can use the Analytics module programmatically through the Python SDK.

**Example:**

.. code-block:: python

   from pygeai.analytics.managers import AnalyticsManager

   # Initialize the manager
   manager = AnalyticsManager()

   # Get agents created and modified
   result = manager.get_agents_created_and_modified(
       start_date="2024-01-01",
       end_date="2024-01-31"
   )
   print(f"Created: {result.createdAgents}")
   print(f"Modified: {result.modifiedAgents}")

   # Get total cost
   cost = manager.get_total_cost(
       start_date="2024-01-01",
       end_date="2024-01-31"
   )
   print(f"Total Cost: ${cost.totalCost:.2f}")

   # Get top agents by requests
   top_agents = manager.get_top_10_agents_by_requests(
       start_date="2024-01-01",
       end_date="2024-01-31"
   )
   for agent in top_agents.topAgents:
       print(f"{agent.agentName}: {agent.totalRequests} requests")

Available Manager Methods
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Lab Metrics:**

- ``get_agents_created_and_modified(start_date, end_date)``
- ``get_agents_created_and_modified_per_day(start_date, end_date)``
- ``get_flows_created_and_modified(start_date, end_date)``
- ``get_flows_created_and_modified_per_day(start_date, end_date)``
- ``get_processes_created_and_modified(start_date, end_date)``

**Request Metrics:**

- ``get_total_requests(start_date, end_date, agent_name=None)``
- ``get_total_requests_per_day(start_date, end_date, agent_name=None)``
- ``get_total_requests_with_error(start_date, end_date)``
- ``get_overall_error_rate(start_date, end_date)``
- ``get_average_request_time(start_date, end_date)``
- ``get_average_requests_per_day(start_date, end_date)``
- ``get_average_requests_per_user(start_date, end_date)``
- ``get_average_requests_per_user_per_date(start_date, end_date)``

**Cost Metrics:**

- ``get_total_cost(start_date, end_date)``
- ``get_total_cost_per_day(start_date, end_date)``
- ``get_average_cost_per_request(start_date, end_date)``
- ``get_average_cost_per_user(start_date, end_date)``
- ``get_average_cost_per_user_per_date(start_date, end_date)``

**Token Metrics:**

- ``get_total_tokens(start_date, end_date)``
- ``get_number_of_tokens_per_agent(start_date, end_date)``
- ``get_number_of_tokens_per_day(start_date, end_date)``
- ``get_average_tokens_per_request(start_date, end_date)``

**User & Agent Metrics:**

- ``get_total_active_users(start_date, end_date, agent_name=None)``
- ``get_total_active_agents(start_date, end_date)``
- ``get_total_active_projects(start_date, end_date)``
- ``get_agent_usage_per_user(start_date, end_date)``
- ``get_average_users_per_agent(start_date, end_date)``
- ``get_average_users_per_project(start_date, end_date)``

**Top Performers:**

- ``get_top_10_agents_by_requests(start_date, end_date)``
- ``get_top_10_agents_by_tokens(start_date, end_date)``
- ``get_top_10_users_by_requests(start_date, end_date)``
- ``get_top_10_users_by_cost(start_date, end_date)``

Best Practices
--------------

1. **Regular Monitoring**: Run analytics reports regularly to track trends and identify patterns
2. **CSV Export**: Export to CSV for further analysis in spreadsheet applications or BI tools
3. **Compare Periods**: Generate reports for different time periods to compare performance
4. **Cost Optimization**: Monitor cost metrics to identify opportunities for optimization
5. **Error Analysis**: Track error rates to quickly identify and address issues
6. **Resource Planning**: Use active user and agent metrics for capacity planning
7. **Performance Tuning**: Monitor average request times to identify performance bottlenecks

Common Use Cases
----------------

Monthly Reporting
^^^^^^^^^^^^^^^^^

Generate a monthly report automatically using default dates:

.. code-block:: bash

   #!/bin/bash
   # Run on the 1st of each month
   REPORT_FILE="analytics_$(date -d 'last month' +%Y-%m).csv"
   geai analytics full-report --csv "$REPORT_FILE"

Cost Tracking
^^^^^^^^^^^^^

Track costs over time:

.. code-block:: bash

   # Q1 2024
   geai analytics total-cost -s "2024-01-01" -e "2024-03-31"
   
   # Compare to Q4 2023
   geai analytics total-cost -s "2023-10-01" -e "2023-12-31"

Performance Monitoring
^^^^^^^^^^^^^^^^^^^^^^

Monitor error rates and response times:

.. code-block:: bash

   geai analytics error-rate -s "2024-01-01" -e "2024-01-31"
   geai analytics requests-per-day -s "2024-01-01" -e "2024-01-31"

Agent Analysis
^^^^^^^^^^^^^^

Identify top-performing agents:

.. code-block:: bash

   geai analytics top-agents -s "2024-01-01" -e "2024-01-31"

Troubleshooting
---------------

**Error: Authentication Failed**

Ensure your API token is properly configured:

.. code-block:: bash

   export GEAI_APITOKEN="your-api-token-here"

**Error: Insufficient Permissions**

Contact your GEAI administrator to ensure you have analytics access permissions.

**Empty Results**

If metrics show zero or empty values:

- Verify the date range includes periods with activity
- Check that you're querying the correct organization/project
- Ensure there was actual usage during the specified period

**Date Format Errors**

Always use YYYY-MM-DD format for dates:

.. code-block:: bash

   # Correct
   geai analytics total-cost -s "2024-01-01" -e "2024-01-31"
   
   # Incorrect
   geai analytics total-cost -s "01/01/2024" -e "01/31/2024"

See Also
--------

- :doc:`cli` - General CLI documentation
- API Documentation: https://docs.globant.ai/en/wiki?2725,Analytics+API
- ``geai analytics help`` - View all available analytics commands
