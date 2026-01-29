# monxcli



## Getting started

an arg parser decorator to simplify argument parsing


## Name
monxcli

## Description
"A lightweight and extensible CLI framework for building modular, Git-like command-line tools. Simplify command grouping, subcommand handling, and argument parsing with a decorator-based approach."


## Usage
the following structure should be use. Scripts are group according to modules
```
<folder>/
        + <folder>/
            - yourscript.py
        main.py

example
monxcli
├── monxcli/
├── main.py
├── mc <-- example scripts are in this module 
│   ├── __init__.py
│   └── math_commands.py
```
### using the decorator example:

Import the commands module and use the @commands.command decorator to define your CLI commands. The decorator automatically registers your functions with the argument parser.

For example, the code below creates two commands for your CLI under the mc group and the math_command subgroup. The functions will be registered as subcommands, and their arguments will be mapped to CLI options.

```
from monxcli.commands import commands  # Shared LazyCommandParser

@commands.command()
@staticmethod
def add(x: int, y: int):
    """Adds two numbers."""
    print(f"The result of {x} + {y} is {x + y}")

@commands.command()
@staticmethod
def subtract(x: int, y: int):
    """Subtracts two numbers."""
    print(f"The result of {x} - {y} is {x - y}")

```

To activate the CLI, your main function should  just import the modules where the commands are defined. Monxcli will take of the rest.

```
from mc import math_commands  # just import your module/script here

from monxcli.commands import commands  # Shared LazyCommandParser


if __name__ == "__main__":
    # Execute commands only if the script is run as the main module
    commands()
```

running the main script example:
```
> python3 main.py mc math_commands add --x 3 --y 3
```

mc is the folder or module and math_commands is the submodule, 'add' is the function you want to call then --x and --y are the arguments passed to your functions.

result:
```
$ python3 main.py mc math_commands add --x 3 --y 3
The result of 3 + 3 is 33
```
## Support
contact author https://gitlab.com/mongkoy/


## Project status
on-going
