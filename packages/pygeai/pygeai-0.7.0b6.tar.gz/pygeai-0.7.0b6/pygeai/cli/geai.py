import sys
import logging
from typing import List, Optional

from pygeai import logger
from pygeai.cli.commands.base import base_commands, base_options
from pygeai.cli.commands import ArgumentsEnum, Command
from pygeai.cli.parsers import CommandParser
from pygeai.cli.texts.help import CLI_USAGE
from pygeai.cli.error_handler import ErrorHandler, ExitCode
from pygeai.core.base.session import get_session
from pygeai.core.common.exceptions import UnknownArgumentError, MissingRequirementException, WrongArgumentError, \
    InvalidAgentException
from pygeai.core.utils.console import Console


def setup_verbose_logging() -> None:
    """
    Configure verbose logging for the CLI.
    
    Sets up a console handler with DEBUG level logging and a formatted output
    that includes timestamp, logger name, level, and message.
    """
    if logger.handlers:
        for handler in logger.handlers:
            if not isinstance(handler, logging.NullHandler):
                return
    
    logger.setLevel(logging.DEBUG)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    logger.propagate = False
    logger.debug("Verbose mode enabled")


def main() -> int:
    """
    Main entry point for the GEAI CLI application.

    :return: int - Exit code indicating success or error.
    """
    try:
        driver = CLIDriver()
        return driver.main()
    except MissingRequirementException as e:
        error_msg = ErrorHandler.handle_missing_requirement(str(e))
        Console.write_stderr(error_msg)
        return ExitCode.MISSING_REQUIREMENT


class CLIDriver:
    """
    Main CLI driver for the GEAI command-line interface.
    
    The CLIDriver orchestrates command parsing, execution, and error handling
    for all GEAI CLI operations. It supports multi-profile session management
    via the --alias flag and provides comprehensive error handling with
    user-friendly messages.
    """

    def __init__(self, session=None, credentials_file=None) -> None:
        """
        Initialize the CLI driver with optional session and credentials file.
        
        Sets up the session to be used while running commands, either with a 
        specified alias, environment variables, or function parameters.
        Once the session is defined, it won't change during the execution.
        
        :param session: Optional session object. If None, uses 'default' or
                       alias-specified session from command-line arguments.
        :param credentials_file: Optional path to custom credentials file.
        """
        from pygeai.core.common.config import get_settings
        
        arguments = sys.argv
        
        if credentials_file or "--credentials" in arguments or "--creds" in arguments:
            if not credentials_file:
                credentials_file = self._get_credentials_file(arguments)
            get_settings(credentials_file=credentials_file)
            logger.debug(f"Using custom credentials file: {credentials_file}")
        
        if "-a" in arguments or "--alias" in arguments:
            alias = self._get_alias(arguments)
            session = get_session(alias)

        self.session = get_session("default") if session is None else session

    def _get_alias(self, arguments: List[str]) -> str:
        """
        Retrieves and removes alias and alias flag from argument list.

        :param arguments: List[str] - Command line arguments.
        :return: str - The alias value.
        :raises ValueError: If alias flag is present but no value provided.
        """
        alias_index = None

        if "-a" in arguments:
            alias_index = arguments.index("-a")
        elif "--alias" in arguments:
            alias_index = arguments.index("--alias")

        try:
            _ = arguments.pop(alias_index)
            alias = arguments.pop(alias_index)
            return alias
        except IndexError as e:
            Console.write_stderr("-a/--alias option requires an alias. Please provide a valid alias after the option")
            raise MissingRequirementException("Couldn't find a valid alias in parameter list.")

    def _get_credentials_file(self, arguments: List[str]) -> str:
        """
        Retrieves and removes credentials file path and flag from argument list.

        :param arguments: List[str] - Command line arguments.
        :return: str - The credentials file path.
        :raises ValueError: If credentials flag is present but no value provided.
        """
        creds_index = None

        if "--credentials" in arguments:
            creds_index = arguments.index("--credentials")
        elif "--creds" in arguments:
            creds_index = arguments.index("--creds")

        try:
            _ = arguments.pop(creds_index)
            credentials_file = arguments.pop(creds_index)
            return credentials_file
        except IndexError as e:
            Console.write_stderr("--creds/--credentials option requires a file path. Please provide a valid path after the option.")
            raise MissingRequirementException("Couldn't find a valid path in parameter list.")

    def main(self, args: Optional[List[str]] = None) -> int:
        """
        Execute the CLI command based on provided arguments.
        
        If no argument is received, it defaults to help (first command in base_command list).
        Otherwise, it parses the arguments received to identify the appropriate command and either
        execute it or parse it again to detect subcommands.

        :param args: Optional[List[str]] - Command line arguments. If None, uses sys.argv.
        :return: int - Exit code (0 for success, non-zero for errors).
        """
        try:
            argv = sys.argv if args is None else args
            
            if "--verbose" in argv or "-v" in argv:
                setup_verbose_logging()
                argv_copy = [a for a in argv if a not in ("--verbose", "-v")]
                if args is None:
                    sys.argv = argv_copy
                else:
                    args = argv_copy
                argv = argv_copy
            
            logger.debug(f"Running geai with: {' '.join(a for a in argv)}")
            logger.debug(f"Session: {self.session.alias if hasattr(self.session, 'alias') else 'default'}")
            
            if len(argv) > 1:
                arg = argv[1] if args is None else args[1]
                arguments = argv[2:] if args is None else args[2:]
                
                logger.debug(f"Identifying command for argument: {arg}")
                command = CommandParser(base_commands, base_options).identify_command(arg)
                logger.debug(f"Command identified: {command.name}")
            else:
                logger.debug("No arguments provided, defaulting to help command")
                command = base_commands[0]
                arguments = []

            self.process_command(command, arguments)
            logger.debug("Command completed successfully")
            return ExitCode.SUCCESS
        except UnknownArgumentError as e:
            if hasattr(e, 'available_commands') and e.available_commands:
                error_msg = ErrorHandler.handle_unknown_command(e.arg, e.available_commands)
            elif hasattr(e, 'available_options') and e.available_options:
                error_msg = ErrorHandler.handle_unknown_option(e.arg, e.available_options)
            else:
                error_msg = ErrorHandler.format_error("Unknown Argument", str(e))
            
            Console.write_stderr(error_msg)
            return ExitCode.USER_INPUT_ERROR
        except WrongArgumentError as e:
            error_msg = ErrorHandler.handle_wrong_argument(str(e), CLI_USAGE)
            Console.write_stderr(error_msg)
            return ExitCode.USER_INPUT_ERROR
        except MissingRequirementException as e:
            error_msg = ErrorHandler.handle_missing_requirement(str(e))
            Console.write_stderr(error_msg)
            return ExitCode.MISSING_REQUIREMENT
        except InvalidAgentException as e:
            error_msg = ErrorHandler.handle_invalid_agent(str(e))
            Console.write_stderr(error_msg)
            return ExitCode.SERVICE_ERROR
        except KeyboardInterrupt:
            message = ErrorHandler.handle_keyboard_interrupt()
            Console.write_stdout(message)
            return ExitCode.KEYBOARD_INTERRUPT
        except Exception as e:
            error_msg = ErrorHandler.handle_unexpected_error(e)
            Console.write_stderr(error_msg)
            return ExitCode.UNEXPECTED_ERROR

    def process_command(self, command: Command, arguments: list[str]):
        """
        If the command has no action associated with it, it means it has subcommands, so it must be parsed again
        to identify it.
        """
        logger.debug(f"Processing command: {command.name}, arguments: {arguments}")
        
        if command.action:
            if command.additional_args == ArgumentsEnum.NOT_AVAILABLE:
                logger.debug(f"Executing command {command.name} without arguments")
                command.action()
            else:
                logger.debug(f"Extracting options for command {command.name}")
                option_list = CommandParser(base_commands, command.options).extract_option_list(arguments)
                logger.debug(f"Options extracted: {len(option_list)} items")
                command.action(option_list)
        elif command.subcommands:
            subcommand_arg = arguments[0] if len(arguments) > 0 else None
            subcommand_arguments = arguments[1:] if len(arguments) > 1 else []
            
            logger.debug(f"Command has subcommands, identifying: {subcommand_arg}")
            
            available_commands = command.subcommands
            available_options = command.options
            parser = CommandParser(available_commands, available_options)

            if not subcommand_arg:
                logger.debug(f"No subcommand specified, using default: {command.subcommands[0].name}")
                subcommand = command.subcommands[0]
            else:
                subcommand = parser.identify_command(subcommand_arg)
                logger.debug(f"Subcommand identified: {subcommand.name}")

            if subcommand.additional_args == ArgumentsEnum.NOT_AVAILABLE:
                logger.debug(f"Executing subcommand {subcommand.name} without arguments")
                subcommand.action()
            else:
                logger.debug(f"Extracting options for subcommand {subcommand.name}")
                option_list = CommandParser(None, subcommand.options).extract_option_list(subcommand_arguments)
                logger.debug(f"Options extracted: {len(option_list)} items")
                subcommand.action(option_list)
