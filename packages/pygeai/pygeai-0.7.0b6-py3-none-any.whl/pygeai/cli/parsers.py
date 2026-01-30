from typing import List, Tuple, Optional

from pygeai import logger

from pygeai.cli.commands import Command, Option
from pygeai.core.common.exceptions import UnknownArgumentError, MissingRequirementException


class CommandParser:

    def __init__(
        self, 
        available_commands: Optional[List[Command]], 
        available_options: Optional[List[Option]]
    ) -> None:
        """
        Initialize a CommandParser with available commands and options.

        :param available_commands: Optional[List[Command]] - List of valid commands, or None.
        :param available_options: Optional[List[Option]] - List of valid options, or None.
        """
        self.available_commands = available_commands
        self.available_options = available_options

    def identify_command(self, arg: str) -> Command:
        """
        Analyzes the first argument and checks if it's a valid command.

        :param arg: str - The argument to be analyzed.
        :return: Command - The identified command object.
        :raises UnknownArgumentError: If the argument is not a valid command.
        """
        logger.debug(f"Searching for command matching: {arg}")
        command = self._get_associated_command(arg)
        if not command:
            logger.debug(f"No command found for: {arg}")
            raise UnknownArgumentError(
                f"'{arg}' is not a valid command.",
                arg=arg,
                available_commands=self.available_commands
            )
        
        logger.debug(f"Command found: {command.name} (identifiers: {command.identifiers})")
        return command

    def extract_option_list(self, arguments: List[str]) -> List[Tuple[Option, str]]:
        """
        Parses a list of arguments and returns the options being invoked.

        :param arguments: List[str] - The list of arguments received by the CLI utility.
        :return: List[Tuple[Option, str]] - A list of tuples containing Option objects and their values.
        :raises UnknownArgumentError: If an unknown option is provided.
        :raises MissingRequirementException: If a required option argument is missing.
        """
        logger.debug(f"Extracting options from arguments: {arguments}")
        flag_list: List[Tuple[Option, str]] = []

        complementary_arg = False
        for i, arg in enumerate(arguments):
            if complementary_arg:
                complementary_arg = False
                continue

            flag = self._get_associated_option(arg)
            if not flag:
                logger.debug(f"Unknown option: {arg}")
                raise UnknownArgumentError(
                    f"'{arg}' is not a valid option.",
                    arg=arg,
                    available_options=self.available_options
                )
            
            logger.debug(f"Option found: {flag.name} (identifiers: {flag.identifiers})")

            if flag.requires_args:
                complementary_arg = True
                try:
                    value = arguments[i + 1]
                    logger.debug(f"Option {flag.name} has value: {value}")
                    flag_list.append((flag, value))
                except IndexError:
                    logger.debug(f"Missing required argument for option: {flag.name}")
                    raise MissingRequirementException(f"'{flag.name}' requires an argument.")
            else:
                logger.debug(f"Option {flag.name} is a flag (no value required)")
                flag_list.append((flag, ""))

        logger.debug(f"Total options parsed: {len(flag_list)}")
        return flag_list

    def _get_associated_command(self, arg: str) -> Optional[Command]:
        """
        Finds the command associated with the given argument.

        :param arg: str - The argument to search for.
        :return: Optional[Command] - The associated command if found, None otherwise.
        """
        if not self.available_commands:
            return None
            
        for command in self.available_commands:
            if arg in command.identifiers:
                return command
        
        return None

    def _get_associated_option(self, arg: str) -> Optional[Option]:
        """
        Finds the option associated with the given argument.

        :param arg: str - The argument to search for.
        :return: Optional[Option] - The associated option if found, None otherwise.
        """
        if not self.available_options:
            return None
            
        for option in self.available_options:
            if arg in option.identifiers:
                return option
        
        return None
