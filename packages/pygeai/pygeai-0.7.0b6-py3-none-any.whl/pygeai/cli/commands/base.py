import signal
import sys
import time
from datetime import datetime
from typing import Optional

from pygeai.cli.commands import ArgumentsEnum, Command, Option
from pygeai.cli.commands.admin import admin_commands
from pygeai.cli.commands.analytics import analytics_commands
from pygeai.cli.commands.assistant import assistant_commands
from pygeai.cli.commands.auth import auth_commands
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.chat import chat_commands
from pygeai.cli.commands.configuration import configure, configuration_options
from pygeai.cli.commands.embeddings import embeddings_commands
from pygeai.cli.commands.evaluation import evaluation_commands
from pygeai.cli.commands.feedback import feedback_commands
from pygeai.cli.commands.files import files_commands
from pygeai.cli.commands.gam import gam_commands
from pygeai.cli.commands.lab.spec import spec_commands
from pygeai.cli.commands.llm import llm_commands
from pygeai.cli.commands.migrate import migrate_commands
from pygeai.cli.commands.organization import organization_commands
from pygeai.cli.commands.rag import rag_commands
from pygeai.cli.commands.rerank import rerank_commands
from pygeai.cli.commands.lab.ai_lab import ai_lab_commands
from pygeai.cli.commands.secrets import secrets_commands
from pygeai.cli.commands.usage_limits import usage_limit_commands
from pygeai.cli.commands.version import check_new_version
from pygeai.cli.texts.help import HELP_TEXT
from pygeai import __version__ as cli_version
from pygeai.core.utils.console import Console
from pygeai.health.clients import HealthClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(base_commands, HELP_TEXT)
    Console.write_stdout(help_text)


def show_version():
    """
    Displays version in stdout
    """
    Console.write_stdout(
        f" - Globant Enterprise AI: GEAI cli utility. Version: {cli_version}"
    )


def check_for_updates():
    """
    Checks if there are updates available
    """
    package_name = 'pygeai'
    version_status = check_new_version(package_name)
    Console.write_stdout(f"{version_status}")


def check_api_status(option_list: list = None):
    """
    Checks API status with optional monitoring capabilities
    
    :param option_list: List of tuples (option, value) including monitor, file, interval, and count
    """
    if option_list is None or not any(option_list):
        api_status = HealthClient().check_api_status()
        Console.write_stdout(f"API Status: {api_status}")
        return
    
    options_dict = {opt.name: arg for opt, arg in option_list}
    
    monitor = 'monitor' in options_dict
    file_path = options_dict.get('file')
    interval = int(options_dict.get('interval', 5)) if 'interval' in options_dict else 5
    count = int(options_dict.get('count', 0)) if 'count' in options_dict else 0
    
    if not monitor:
        api_status = HealthClient().check_api_status()
        Console.write_stdout(f"API Status: {api_status}")
        return
    
    health_client = HealthClient()
    check_count = 0
    success_count = 0
    failure_count = 0
    downtime_periods = []
    current_downtime_start = None
    interrupted = False
    
    file_handle = None
    if file_path:
        try:
            file_handle = open(file_path, 'w')
            file_handle.write("Timestamp,Status,Running,Version,Error\n")
        except Exception as e:
            Console.write_stdout(f"Warning: Could not open file {file_path}: {e}")
            file_handle = None
    
    def signal_handler(sig, frame):
        nonlocal interrupted
        interrupted = True
    
    signal.signal(signal.SIGINT, signal_handler)
    
    Console.write_stdout(f"Monitoring API status every {interval} seconds. Press Ctrl+C to stop...")
    Console.write_stdout("")
    
    try:
        while True:
            timestamp = datetime.now()
            timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            
            try:
                api_status = health_client.check_api_status()
                check_count += 1
                
                running = api_status.get('running', False)
                version = api_status.get('version', 'N/A')
                
                if running:
                    success_count += 1
                    status = "✓ UP"
                    if current_downtime_start:
                        downtime_end = timestamp
                        downtime_periods.append((current_downtime_start, downtime_end))
                        current_downtime_start = None
                else:
                    failure_count += 1
                    status = "✗ DOWN"
                    if not current_downtime_start:
                        current_downtime_start = timestamp
                
                Console.write_stdout(f"[{timestamp_str}] {status} - Version: {version}")
                
                if file_handle:
                    file_handle.write(f"{timestamp_str},{'UP' if running else 'DOWN'},{running},{version},\n")
                    file_handle.flush()
                    
            except Exception as e:
                check_count += 1
                failure_count += 1
                status = "✗ ERROR"
                error_msg = str(e)
                
                Console.write_stdout(f"[{timestamp_str}] {status} - {error_msg}")
                
                if not current_downtime_start:
                    current_downtime_start = timestamp
                
                if file_handle:
                    file_handle.write(f"{timestamp_str},ERROR,False,N/A,{error_msg}\n")
                    file_handle.flush()
            
            if count > 0 and check_count >= count:
                break
            
            if interrupted:
                Console.write_stdout("\nMonitoring stopped by user.")
                break
            
            time.sleep(interval)
            
    finally:
        if current_downtime_start:
            downtime_periods.append((current_downtime_start, datetime.now()))
        
        if file_handle:
            file_handle.close()
        
        Console.write_stdout("")
        Console.write_stdout("=" * 60)
        Console.write_stdout("MONITORING SUMMARY")
        Console.write_stdout("=" * 60)
        Console.write_stdout(f"Total checks performed: {check_count}")
        Console.write_stdout(f"Successful checks: {success_count}")
        Console.write_stdout(f"Failed checks: {failure_count}")
        
        if success_count > 0:
            uptime_percentage = (success_count / check_count) * 100
            Console.write_stdout(f"Uptime: {uptime_percentage:.2f}%")
        
        if downtime_periods:
            total_downtime = sum(
                (end - start).total_seconds()
                for start, end in downtime_periods
            )
            Console.write_stdout(f"Estimated total downtime: {total_downtime:.2f} seconds ({total_downtime/60:.2f} minutes)")
            Console.write_stdout(f"Number of downtime incidents: {len(downtime_periods)}")
        else:
            Console.write_stdout("No downtime detected during monitoring period")
        
        if file_path:
            Console.write_stdout(f"Results saved to: {file_path}")
        Console.write_stdout("=" * 60)


"""
Commands that have available subcommands should have action None, so the parser knows that it shouldn't
run any action but instead send it to process again to identify subcommand.
"""

base_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "version",
        ["version", "v"],
        "Display version text",
        show_version,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "check_updates",
        ["check-updates", "cu"],
        "Search for available updates",
        check_for_updates,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "check_status",
        ["status", "s"],
        "Check API status for Globant Enterprise AI instance",
        check_api_status,
        ArgumentsEnum.OPTIONAL,
        [],
        [
            Option(
                "monitor",
                ["--monitor", "-m"],
                "Enable continuous monitoring mode",
                False
            ),
            Option(
                "file",
                ["--file", "-f"],
                "Log status checks to specified file",
                True
            ),
            Option(
                "interval",
                ["--interval", "-i"],
                "Interval in seconds between checks (default: 5)",
                True
            ),
            Option(
                "count",
                ["--count", "-c"],
                "Number of times to check before stopping (default: infinite)",
                True
            ),
        ]
    ),
    Command(
        "configure",
        ["configure", "config", "c"],
        "Setup the environment variables required to interact with GEAI",
        configure,
        ArgumentsEnum.OPTIONAL,
        [],
        configuration_options
    ),
    Command(
        "organization",
        ["organization", "org"],
        "Invoke organization endpoints to handle project parameters",
        None,
        ArgumentsEnum.REQUIRED,
        organization_commands,
        [],
    ),
    Command(
        "analytics",
        ["analytics", "anl"],
        "Invoke analytics endpoints to retrieve metrics and insights",
        None,
        ArgumentsEnum.REQUIRED,
        analytics_commands,
        [],
    ),
    Command(
        "assistant",
        ["assistant", "ast"],
        "Invoke assistant endpoints to handle assistant parameters",
        None,
        ArgumentsEnum.REQUIRED,
        assistant_commands,
        [],
    ),
    Command(
        "rag_assistant",
        ["rag"],
        "Invoke rag assistant endpoints to handle RAG assistant parameters",
        None,
        ArgumentsEnum.REQUIRED,
        rag_commands,
        [],
    ),
    Command(
        "chat",
        ["chat"],
        "Invoke chat endpoints to handle chat with assistants parameters",
        None,
        ArgumentsEnum.REQUIRED,
        chat_commands,
        [],
    ),
    Command(
        "admin",
        ["admin", "adm"],
        "Invoke admin endpoints designed for internal use",
        None,
        ArgumentsEnum.REQUIRED,
        admin_commands,
        []
    ),
    Command(
        "auth",
        ["auth"],
        "Invoke auth endpoints for token generation",
        None,
        ArgumentsEnum.REQUIRED,
        auth_commands,
        []
    ),

    Command(
        "llm",
        ["llm"],
        "Invoke llm endpoints for provider's and model retrieval",
        None,
        ArgumentsEnum.REQUIRED,
        llm_commands,
        []
    ),
    Command(
        "files",
        ["files"],
        "Invoke files endpoints for file handling",
        None,
        ArgumentsEnum.REQUIRED,
        files_commands,
        []
    ),
    Command(
        "usage_limit",
        ["usage-limit", "ulim"],
        "Invoke usage limit endpoints for organization and project",
        None,
        ArgumentsEnum.REQUIRED,
        usage_limit_commands,
        []
    ),
    Command(
        "embeddings",
        ["embeddings", "emb"],
        "Invoke embeddings endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        embeddings_commands,
        []
    ),
    Command(
        "feedback",
        ["feedback", "fbk"],
        "Invoke feedback endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        feedback_commands,
        []
    ),
    Command(
        "rerank",
        ["rerank", "rr"],
        "Invoke rerank endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        rerank_commands,
        []
    ),
    Command(
        "evaluation",
        ["evaluation", "eval"],
        "Invoke evaluation endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        evaluation_commands,
        []
    ),
    Command(
        "gam",
        ["gam"],
        "Invoke GAM authentication endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        gam_commands,
        []
    ),
    Command(
        "secrets",
        ["secrets", "sec"],
        "Handle Globant Enterprise AI secrets",
        None,
        ArgumentsEnum.REQUIRED,
        secrets_commands,
        []
    ),
    Command(
        "ai_lab",
        ["ai-lab", "ail"],
        "Invoke AI Lab endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        ai_lab_commands,
        []
    ),
    Command(
        "ai_lab_spec",
        ["ai-lab-spec", "spec"],
        "Invoke AI Lab endpoints",
        None,
        ArgumentsEnum.REQUIRED,
        spec_commands,
        []
    ),
    Command(
        "migrate",
        ["migrate", "mig"],
        "Invoke migrate procedures",
        None,
        ArgumentsEnum.REQUIRED,
        migrate_commands,
        []
    ),
    #Command(
    #    "docs",
    #    ["docs"],
    #    "View PyGEAI SDK documentation",
    #    None,
    #    ArgumentsEnum.NOT_AVAILABLE,
    #    docs_commands,
    #    []
    #),

]


base_options = (
    Option(
        "output",
        ["--output", "-o"],
        "Set output file to save the command result",
        True
    ),
    Option(
        "verbose",
        ["--verbose", "-v"],
        "Enable verbose mode with detailed logging output",
        False
    ),
)
