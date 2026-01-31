"""Function to register commands."""

import abc

__all__ = [
    "REGISTERED_COMMANDS",
    "Command",
    "register_command",
    "deprecate_command",
]


REGISTERED_COMMANDS = dict()
DEPRECATED_COMMANDS = set()


class Command(abc.ABC):
    """Sub-command for CLI interface.

    Parameters
    ----------
    name : str
        Name of the sub-command.
    logger : logging.Logger
        Logger to log the command run.

    Examples
    --------
    >>> class MyCommand(Command):
    ...     def add_parser(self, main_parser):
    ...         parser = main_parser.add_parser(self.name)
    ...         parser.add_argument("foo")
    ...     def run(self, args):
    ...         self.logger.info("Run my command")
    ...         print(args.foo)
    """

    def __init__(self, name, logger):
        self._name = name
        self._logger = logger

    @property
    def name(self):
        """Name of the command for :meth:`add_parser`."""
        return self._name

    @property
    def logger(self):
        """Logger for :meth:`run`."""
        return self._logger

    @abc.abstractmethod
    def add_parser(self, main_parser):
        """Add the command parser to main parser.

        Parameters
        ----------
        main_parser : argparse._SubParsersAction
            Subparser constructor having :class:`heavyedge.cli.ConfigArgumentParser` as
            parser class.
        """
        ...

    @abc.abstractmethod
    def run(self, args):
        """Run the command.

        Parameters
        ----------
        args : argparse.Namespace
        """
        ...


def register_command(name, desc):
    """Decorator to register the command class for the argument parser.

    Parameters
    ----------
    name : str
        The unique name of the command.
    desc : str
        A short description of the command's purpose.

    Examples
    --------
    Decorate the class definition.

    >>> from heavyedge.cli import Command, register_command
    >>> @register_command("foo", "My command")
    ... class MyCommand(Command):
    ...     ...

    See Also
    --------
    heavyedge.cli.Command
    """

    def register(cls):
        REGISTERED_COMMANDS[name] = (cls, desc)
        return cls

    return register


def deprecate_command(version, use_instead):
    """Decorator to mark a command as deprecated.

    Deprecated commands are still accessible, but are not displayed in the help message.
    Additionally, warning is raised when the command is used.

    Parameters
    ----------
    version : str
        Version when the command is deprecated.
    use_instead : str
        Other API which user should use.

    Examples
    --------
    Decorate the class definition.

    >>> from heavyedge.cli import Command, register_command, deprecate_command
    >>> @deprecate_command("1.5", "other command")
    ... @register_command("foo", "My command")
    ... class MyCommand(Command):
    ...     ...
    """

    def register(cls):
        DEPRECATED_COMMANDS.add(cls)

        cls.run = _run_deprecated_command(cls.run, version, use_instead)

        return cls

    return register


def _run_deprecated_command(original_run, version, use_instead):
    removed_version = str(int(version.split(".")[0]) + 1) + ".0"

    def run(self, args):
        self.logger.warning(
            f"Command '{self.name}' is deprecated since HeavyEdge {version} "
            f"and will be removed in {removed_version}. "
            f"Use {use_instead} instead.",
        )
        return original_run(self, args)

    return run
