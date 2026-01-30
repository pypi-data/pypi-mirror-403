from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import ANALYTICS_HELP_TEXT

from pygeai.core.utils.console import Console
from pygeai.analytics.managers import AnalyticsManager
import csv
from datetime import datetime, timedelta


def show_help():
    help_text = build_help_text(analytics_commands, ANALYTICS_HELP_TEXT)
    Console.write_stdout(help_text)


def get_default_date_range():
    today = datetime.now()
    first_day_current_month = today.replace(day=1)
    last_day_last_month = first_day_current_month - timedelta(days=1)
    first_day_last_month = last_day_last_month.replace(day=1)
    
    start_date = first_day_last_month.strftime('%Y-%m-%d')
    end_date = last_day_last_month.strftime('%Y-%m-%d')
    
    return start_date, end_date


START_DATE_OPTION = Option(
    "start_date",
    ["--start-date", "-s"],
    "Start date in YYYY-MM-DD format (defaults to first day of last month)",
    True
)

END_DATE_OPTION = Option(
    "end_date",
    ["--end-date", "-e"],
    "End date in YYYY-MM-DD format (defaults to last day of last month)",
    True
)

AGENT_NAME_OPTION = Option(
    "agent_name",
    ["--agent-name", "-a"],
    "Name of the agent to filter results",
    True
)

CSV_EXPORT_OPTION = Option(
    "csv_file",
    ["--csv", "-c"],
    "Export results to CSV file",
    True
)


def get_agents_created_and_modified(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_agents_created_and_modified(start_date, end_date)
    Console.write_stdout(f"Agents created and modified:\n  Created: {result.createdAgents}\n  Modified: {result.modifiedAgents}")


agents_created_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_total_requests_per_day(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")
    agent_name = opts.get("agent_name")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_total_requests_per_day(start_date, end_date, agent_name)
    Console.write_stdout("Total requests per day:")
    for item in result.requestsPerDay:
        Console.write_stdout(f"  {item.date}: {item.totalRequests} requests ({item.totalRequestsWithError} errors)")


total_requests_per_day_options = [START_DATE_OPTION, END_DATE_OPTION, AGENT_NAME_OPTION]


def get_total_cost(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_total_cost(start_date, end_date)
    Console.write_stdout(f"Total cost: ${result.totalCost:.2f}")


total_cost_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_average_cost_per_request(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_average_cost_per_request(start_date, end_date)
    Console.write_stdout(f"Average cost per request: ${result.averageCost:.4f}")


average_cost_per_request_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_total_tokens(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_total_tokens(start_date, end_date)
    Console.write_stdout(f"Total tokens:\n  Input: {result.totalInputTokens}\n  Output: {result.totalOutputTokens}\n  Total: {result.totalTokens}")


total_tokens_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_overall_error_rate(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_overall_error_rate(start_date, end_date)
    Console.write_stdout(f"Overall error rate: {result.errorRate:.2%}")


error_rate_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_top_agents_by_requests(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_top_10_agents_by_requests(start_date, end_date)
    Console.write_stdout("Top 10 agents by requests:")
    for idx, agent in enumerate(result.topAgents, 1):
        Console.write_stdout(f"  {idx}. {agent.agentName}: {agent.totalRequests} requests")


top_agents_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_total_active_users(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    result = manager.get_total_active_users(start_date, end_date)
    Console.write_stdout(f"Total active users: {result.totalActiveUsers}")


active_users_options = [START_DATE_OPTION, END_DATE_OPTION]


def get_full_report(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    start_date = opts.get("start_date")
    end_date = opts.get("end_date")
    csv_file = opts.get("csv_file")

    if not start_date or not end_date:
        start_date, end_date = get_default_date_range()
        Console.write_stdout(f"Using default date range: {start_date} to {end_date}")

    manager = AnalyticsManager()
    
    Console.write_stdout(f"\n{'='*80}")
    Console.write_stdout(f"ANALYTICS FULL REPORT - Period: {start_date} to {end_date}")
    Console.write_stdout(f"{'='*80}\n")
    
    report_data = {}
    
    try:
        Console.write_stdout("LAB METRICS")
        Console.write_stdout("-" * 80)
        agents_created = manager.get_agents_created_and_modified(start_date, end_date)
        Console.write_stdout(f"Agents Created: {agents_created.createdAgents}")
        Console.write_stdout(f"Agents Modified: {agents_created.modifiedAgents}")
        report_data["Agents Created"] = agents_created.createdAgents
        report_data["Agents Modified"] = agents_created.modifiedAgents
    except Exception as e:
        Console.write_stdout(f"Error retrieving agents data: {e}")
    
    try:
        flows_created = manager.get_flows_created_and_modified(start_date, end_date)
        Console.write_stdout(f"Flows Created: {flows_created.createdFlows}")
        Console.write_stdout(f"Flows Modified: {flows_created.modifiedFlows}")
        report_data["Flows Created"] = flows_created.createdFlows
        report_data["Flows Modified"] = flows_created.modifiedFlows
    except Exception as e:
        Console.write_stdout(f"Error retrieving flows data: {e}")
    
    try:
        processes_created = manager.get_processes_created_and_modified(start_date, end_date)
        Console.write_stdout(f"Processes Created: {processes_created.createdProcesses}")
        Console.write_stdout(f"Processes Modified: {processes_created.modifiedProcesses}")
        report_data["Processes Created"] = processes_created.createdProcesses
        report_data["Processes Modified"] = processes_created.modifiedProcesses
    except Exception as e:
        Console.write_stdout(f"Error retrieving processes data: {e}")
    
    Console.write_stdout("\nREQUEST METRICS")
    Console.write_stdout("-" * 80)
    
    try:
        total_requests = manager.get_total_requests(start_date, end_date)
        Console.write_stdout(f"Total Requests: {total_requests.totalRequests}")
        report_data["Total Requests"] = total_requests.totalRequests
    except Exception as e:
        Console.write_stdout(f"Error retrieving total requests: {e}")
    
    try:
        total_errors = manager.get_total_requests_with_error(start_date, end_date)
        Console.write_stdout(f"Total Requests with Error: {total_errors.totalRequestsWithError}")
        report_data["Total Requests with Error"] = total_errors.totalRequestsWithError
    except Exception as e:
        Console.write_stdout(f"Error retrieving error requests: {e}")
    
    try:
        error_rate = manager.get_overall_error_rate(start_date, end_date)
        Console.write_stdout(f"Overall Error Rate: {error_rate.errorRate:.2%}")
        report_data["Overall Error Rate (%)"] = f"{error_rate.errorRate:.2%}"
    except Exception as e:
        Console.write_stdout(f"Error retrieving error rate: {e}")
    
    try:
        avg_request_time = manager.get_average_request_time(start_date, end_date)
        Console.write_stdout(f"Average Request Time: {avg_request_time.averageTime:.2f} ms")
        report_data["Average Request Time (ms)"] = f"{avg_request_time.averageTime:.2f}"
    except Exception as e:
        Console.write_stdout(f"Error retrieving average request time: {e}")
    
    Console.write_stdout("\nCOST METRICS")
    Console.write_stdout("-" * 80)
    
    try:
        total_cost = manager.get_total_cost(start_date, end_date)
        Console.write_stdout(f"Total Cost: ${total_cost.totalCost:.2f}")
        report_data["Total Cost (USD)"] = f"{total_cost.totalCost:.2f}"
    except Exception as e:
        Console.write_stdout(f"Error retrieving total cost: {e}")
    
    try:
        avg_cost = manager.get_average_cost_per_request(start_date, end_date)
        Console.write_stdout(f"Average Cost per Request: ${avg_cost.averageCost:.4f}")
        report_data["Average Cost per Request (USD)"] = f"{avg_cost.averageCost:.4f}"
    except Exception as e:
        Console.write_stdout(f"Error retrieving average cost: {e}")
    
    Console.write_stdout("\nTOKEN METRICS")
    Console.write_stdout("-" * 80)
    
    try:
        total_tokens = manager.get_total_tokens(start_date, end_date)
        Console.write_stdout(f"Total Input Tokens: {total_tokens.totalInputTokens}")
        Console.write_stdout(f"Total Output Tokens: {total_tokens.totalOutputTokens}")
        Console.write_stdout(f"Total Tokens: {total_tokens.totalTokens}")
        report_data["Total Input Tokens"] = total_tokens.totalInputTokens
        report_data["Total Output Tokens"] = total_tokens.totalOutputTokens
        report_data["Total Tokens"] = total_tokens.totalTokens
    except Exception as e:
        Console.write_stdout(f"Error retrieving token data: {e}")
    
    try:
        avg_tokens = manager.get_average_tokens_per_request(start_date, end_date)
        Console.write_stdout(f"Average Input Tokens per Request: {avg_tokens.averageInputTokens:.2f}")
        Console.write_stdout(f"Average Output Tokens per Request: {avg_tokens.averageOutputTokens:.2f}")
        Console.write_stdout(f"Average Total Tokens per Request: {avg_tokens.averageTotalTokens:.2f}")
        report_data["Average Input Tokens per Request"] = f"{avg_tokens.averageInputTokens:.2f}"
        report_data["Average Output Tokens per Request"] = f"{avg_tokens.averageOutputTokens:.2f}"
        report_data["Average Total Tokens per Request"] = f"{avg_tokens.averageTotalTokens:.2f}"
    except Exception as e:
        Console.write_stdout(f"Error retrieving average tokens: {e}")
    
    Console.write_stdout("\nUSER & AGENT METRICS")
    Console.write_stdout("-" * 80)
    
    try:
        active_users = manager.get_total_active_users(start_date, end_date)
        Console.write_stdout(f"Total Active Users: {active_users.totalActiveUsers}")
        report_data["Total Active Users"] = active_users.totalActiveUsers
    except Exception as e:
        Console.write_stdout(f"Error retrieving active users: {e}")
    
    try:
        active_agents = manager.get_total_active_agents(start_date, end_date)
        Console.write_stdout(f"Total Active Agents: {active_agents.totalActiveAgents}")
        report_data["Total Active Agents"] = active_agents.totalActiveAgents
    except Exception as e:
        Console.write_stdout(f"Error retrieving active agents: {e}")
    
    try:
        active_projects = manager.get_total_active_projects(start_date, end_date)
        Console.write_stdout(f"Total Active Projects: {active_projects.totalActiveProjects}")
        report_data["Total Active Projects"] = active_projects.totalActiveProjects
    except Exception as e:
        Console.write_stdout(f"Error retrieving active projects: {e}")
    
    Console.write_stdout("\nTOP 10 AGENTS BY REQUESTS")
    Console.write_stdout("-" * 80)
    
    try:
        top_agents_requests = manager.get_top_10_agents_by_requests(start_date, end_date)
        for idx, agent in enumerate(top_agents_requests.topAgents, 1):
            Console.write_stdout(f"{idx}. {agent.agentName}: {agent.totalRequests} requests")
    except Exception as e:
        Console.write_stdout(f"Error retrieving top agents by requests: {e}")
    
    Console.write_stdout("\nTOP 10 AGENTS BY TOKENS")
    Console.write_stdout("-" * 80)
    
    try:
        top_agents_tokens = manager.get_top_10_agents_by_tokens(start_date, end_date)
        for idx, agent in enumerate(top_agents_tokens.topAgents, 1):
            Console.write_stdout(f"{idx}. {agent.agentName}: {agent.totalTokens} tokens")
    except Exception as e:
        Console.write_stdout(f"Error retrieving top agents by tokens: {e}")
    
    Console.write_stdout("\nTOP 10 USERS BY REQUESTS")
    Console.write_stdout("-" * 80)
    
    try:
        top_users_requests = manager.get_top_10_users_by_requests(start_date, end_date)
        for idx, user in enumerate(top_users_requests.topUsers, 1):
            Console.write_stdout(f"{idx}. {user.userEmail}: {user.totalRequests} requests")
    except Exception as e:
        Console.write_stdout(f"Error retrieving top users by requests: {e}")
    
    Console.write_stdout("\nTOP 10 USERS BY COST")
    Console.write_stdout("-" * 80)
    
    try:
        top_users_cost = manager.get_top_10_users_by_cost(start_date, end_date)
        for idx, user in enumerate(top_users_cost.topUsers, 1):
            Console.write_stdout(f"{idx}. {user.userEmail}: ${user.totalCost:.2f}")
    except Exception as e:
        Console.write_stdout(f"Error retrieving top users by cost: {e}")
    
    Console.write_stdout(f"\n{'='*80}\n")
    
    if csv_file:
        try:
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['Metric', 'Value'])
                writer.writerow(['Report Period', f"{start_date} to {end_date}"])
                writer.writerow(['Generated At', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
                writer.writerow([])
                for key, value in report_data.items():
                    writer.writerow([key, value])
            Console.write_stdout(f"Report exported to: {csv_file}")
        except Exception as e:
            Console.write_stdout(f"Error exporting to CSV: {e}")


full_report_options = [START_DATE_OPTION, END_DATE_OPTION, CSV_EXPORT_OPTION]


analytics_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display analytics help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "agents_created",
        ["agents-created", "ac"],
        "Get total agents created and modified",
        get_agents_created_and_modified,
        ArgumentsEnum.OPTIONAL,
        [],
        agents_created_options
    ),
    Command(
        "requests_per_day",
        ["requests-per-day", "rpd"],
        "Get total requests per day",
        get_total_requests_per_day,
        ArgumentsEnum.OPTIONAL,
        [],
        total_requests_per_day_options
    ),
    Command(
        "total_cost",
        ["total-cost", "tc"],
        "Get total cost for the period",
        get_total_cost,
        ArgumentsEnum.OPTIONAL,
        [],
        total_cost_options
    ),
    Command(
        "average_cost",
        ["average-cost", "ac"],
        "Get average cost per request",
        get_average_cost_per_request,
        ArgumentsEnum.OPTIONAL,
        [],
        average_cost_per_request_options
    ),
    Command(
        "total_tokens",
        ["total-tokens", "tt"],
        "Get total tokens consumed",
        get_total_tokens,
        ArgumentsEnum.OPTIONAL,
        [],
        total_tokens_options
    ),
    Command(
        "error_rate",
        ["error-rate", "er"],
        "Get overall error rate",
        get_overall_error_rate,
        ArgumentsEnum.OPTIONAL,
        [],
        error_rate_options
    ),
    Command(
        "top_agents",
        ["top-agents", "ta"],
        "Get top 10 agents by requests",
        get_top_agents_by_requests,
        ArgumentsEnum.OPTIONAL,
        [],
        top_agents_options
    ),
    Command(
        "active_users",
        ["active-users", "au"],
        "Get total active users",
        get_total_active_users,
        ArgumentsEnum.OPTIONAL,
        [],
        active_users_options
    ),
    Command(
        "full_report",
        ["full-report", "fr"],
        "Get comprehensive analytics report",
        get_full_report,
        ArgumentsEnum.OPTIONAL,
        [],
        full_report_options
    ),
]
