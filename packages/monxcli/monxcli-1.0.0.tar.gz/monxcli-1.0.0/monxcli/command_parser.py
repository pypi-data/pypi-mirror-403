import argparse
import inspect

class CommandProxy:
    """
    Core command-handling object that supports automatic group registration
    based on the module where the command is defined.
    """
    
    def __init__(self):
        self.parser = argparse.ArgumentParser(description="Git-like Command-based function execution.")
        self.subparsers = self.parser.add_subparsers(dest="command", required=True)
        self.groups = {}
        self.commands = {}

    def _get_group_for_module(self, func):
        """
        Determine the group name based on the module where the function is defined.
        """       
        module_name = func.__module__.split('.')
        if len(module_name) != 2:
            print('looks like your script is not in a folder?')
            print(f'please move {module_name} into a folder')
            raise Exception('module must be in inside folder')
        MODULE_KEY = module_name[0]
        if MODULE_KEY not in self.groups:
            # Create a new group if it doesn't already exist
            group_parser = self.subparsers.add_parser(MODULE_KEY, help=f"Commands from the {module_name} module.")
            group_subparsers = group_parser.add_subparsers(dest="sub_group_command", required=True)
            sub_group_parser = group_subparsers.add_parser(module_name[1], help=f"Commands from the {module_name} module.")
            sub_group_subparsers = sub_group_parser.add_subparsers(dest="subcommand", required=True)
            self.groups[MODULE_KEY] = sub_group_subparsers
        return self.groups[MODULE_KEY]

    def command(self):
        """
        Decorator to register a command automatically under a group based on its module.
        """
        def decorator(func):
            # Determine the group dynamically from the module name
            subparsers = self._get_group_for_module(func)

            # Create a subparser for this command
            subparser = subparsers.add_parser(func.__name__, help=func.__doc__)
            sig = inspect.signature(func)

            # Add arguments to the subparser based on function signature
            for param in sig.parameters.values():
                name = param.name
                default = param.default
                param_type = type(default) if default is not inspect.Parameter.empty else str
                required = default is inspect.Parameter.empty
                if name == 'self':
                    continue
                subparser.add_argument(
                    f"--{name}",
                    type=param_type,
                    required=required,
                    default=None if required else default,
                    help=f"{name} ({param_type.__name__})"
                )

            # Store the function in the commands dictionary
            module_name = func.__module__.split('.')
            MODULE_KEY = module_name[0]
            SUB_KEY = module_name[1]
            if MODULE_KEY not in self.commands:
                self.commands[MODULE_KEY] = {}
                self.commands[MODULE_KEY][SUB_KEY] = dict()
            self.commands[MODULE_KEY][SUB_KEY][func.__name__] = func
            return func

        return decorator

    def execute(self):
        """Execute the appropriate command based on parsed arguments."""
        
        args = self.parser.parse_args()
        command_name = args.command
        sub_group_command = getattr(args, "sub_group_command", None)
        subcommand = getattr(args,'subcommand')

        if sub_group_command:
            # Dispatch to subcommand
            func = self.commands.get(command_name, {}).get(sub_group_command).get(subcommand)

        if func:
            # Filter out 'command' and 'subcommand' from the arguments
            filtered_args = {key: value for key, value in vars(args).items() if key not in ['command', 'subcommand', 'sub_group_command']}    
            func(**filtered_args)
        else:
            self.parser.error(f"Unknown command: {command_name}")

class LazyCommandParser:
    """
    Wrapper around CommandProxy that collects command definitions and
    delays execution until explicitly invoked.
    """
    def __init__(self):
        self._proxy = CommandProxy()
        # Expose the command decorator from the proxy
        self.command = self._proxy.command

    def __call__(self):
        """
        Execute the CommandProxy when the parser is called.
        """
        self._proxy.execute()