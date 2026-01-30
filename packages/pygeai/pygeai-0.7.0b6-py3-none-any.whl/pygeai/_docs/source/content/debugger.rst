PyGEAI Debugger
===============

Overview
--------

``geai-dbg`` is an interactive command-line debugger for PyGEAI applications. It enables developers to debug the ``geai`` CLI, custom Python scripts that use PyGEAI, or specific PyGEAI modules. The debugger pauses execution at specified breakpoints, allowing inspection of variables, stack navigation, code stepping, and interactive control of program flow.

The debugger provides features similar to Python's built-in ``pdb`` debugger, including:

- **Multiple debugging modes**: Debug geai CLI, Python files, or specific modules
- **Breakpoint management**: Set, list, enable/disable, and remove breakpoints with optional conditions
- **Stepping**: Step into, over, and out of function calls
- **Stack navigation**: Move up and down the call stack to inspect different frames
- **Variable inspection**: Print, pretty-print, and examine local/global variables
- **Source code display**: View source code around the current execution point
- **Performance optimization**: Module filtering to minimize overhead
- **Command history**: Uses readline for command history and editing

Installation and Setup
----------------------

``geai-dbg`` is included in the ``pygeai`` package. Ensure ``pygeai`` is installed in your Python environment:

.. code-block:: bash

    pip install pygeai

No additional setup is required. The debugger is located in the ``pygeai.dbg`` module and can be invoked via the ``geai-dbg`` command.

Usage Modes
-----------

The debugger supports three distinct usage modes:

Mode 1: Debug geai CLI (Default)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Debug the ``geai`` CLI tool with your command arguments:

.. code-block:: bash

    geai-dbg
    geai-dbg ail lrs
    geai-dbg chat "Hello, AI"

This runs the ``geai`` CLI under the debugger with an automatic breakpoint at ``pygeai.cli.geai:main``.

Mode 2: Debug Python Files
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Debug any Python script that uses PyGEAI:

.. code-block:: bash

    geai-dbg my_script.py
    geai-dbg my_script.py --input data.csv --output results.json
    geai-dbg -b process_data my_script.py

The debugger automatically detects whether your script imports PyGEAI and adjusts module filtering accordingly.

Mode 3: Debug Specific Modules
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Debug a specific module and function directly:

.. code-block:: bash

    geai-dbg -m pygeai.cli.geai:main
    geai-dbg -m pygeai.chat:send_message -b process_response

This imports the module, sets up debugging, and runs the specified function.

Command-Line Options
--------------------

.. code-block:: text

    geai-dbg [OPTIONS] [target] [args...]

    Options:
      -h, --help            Show help message
      -m MODULE:FUNC        Debug a module function (e.g., pygeai.cli.geai:main)
      -b BREAKPOINT         Set initial breakpoint ([module:]function)
      --filter PREFIX       Only trace modules with this prefix
      --trace-all           Trace all modules (warning: slow)
      -v, --verbose         Enable verbose logging for pygeai modules
      --log-level LEVEL     Log level for verbose mode: DEBUG, INFO, WARNING, ERROR (default: DEBUG)

    Examples:
      geai-dbg                                 Debug the geai CLI
      geai-dbg script.py arg1 arg2             Debug a Python file with arguments
      geai-dbg -v script.py                    Debug with verbose logging (DEBUG level)
      geai-dbg -v --log-level INFO script.py   Debug with INFO level logging
      geai-dbg -m pygeai.cli.geai:main         Debug a specific module function
      geai-dbg -b main script.py               Break on 'main' function
      geai-dbg --filter pygeai script.py       Only trace pygeai modules

Programmatic Usage
------------------

Debug a Python File
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pygeai.dbg import debug_file
    
    # Set up debugger for a file
    dbg = debug_file('my_script.py', args=['--verbose'])
    dbg.add_breakpoint(function_name='process_data')
    dbg.add_breakpoint(module='pygeai.chat', function_name='send_message')
    
    # Run with debugging
    dbg.run()
    
    # Enable verbose logging with custom log level
    dbg = debug_file('my_script.py', verbose=True, log_level='INFO')
    dbg.run()

Debug a Module
~~~~~~~~~~~~~~

.. code-block:: python

    from pygeai.dbg import debug_module
    
    # Debug a specific module function
    dbg = debug_module('pygeai.cli.geai', 'main')
    dbg.add_breakpoint(module='pygeai.core.llm', function_name='get_completion')
    dbg.run()

Advanced Configuration
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pygeai.dbg import Debugger
    
    def my_function():
        # Your code here
        pass
    
    # Create custom debugger
    dbg = Debugger(target=my_function, module_filter='')  # Trace all modules
    dbg.add_breakpoint(function_name='helper_func', condition='x > 100')
    dbg.run()

Interactive Commands
--------------------

Once paused at a breakpoint, the following commands are available at the ``(geai-dbg)`` prompt:

Flow Control
~~~~~~~~~~~~

**continue, c**
    Resume execution until the next breakpoint is hit or the program completes.

**step, s**
    Execute the current line and stop at the first possible occasion (either in a function that is called or on the next line in the current function).

**next, n**
    Continue execution until the next line in the current function is reached or it returns (step over function calls).

**return, ret**
    Continue execution until the current function returns.

**run, r**
    Run the program to completion, disabling all breakpoints and skipping further pauses.

**quit, q**
    Exit the debugger, terminating the program with a clean exit status (0).

Stack Navigation
~~~~~~~~~~~~~~~~

**where, w, bt**
    Display the stack trace, showing all frames from the current execution point to the top of the call stack.

**up, u**
    Move up one level in the stack trace (to an older frame). This allows you to inspect the context of the caller.

**down, d**
    Move down one level in the stack trace (to a newer frame).

Source Display
~~~~~~~~~~~~~~

**list, l [n]**
    Show source code around the current line. Optional argument ``n`` specifies the number of lines of context (default: 10).

Variable Inspection
~~~~~~~~~~~~~~~~~~~

**print, p <expression>**
    Evaluate and print the value of a Python expression in the current frame's context.
    
    Example: ``p x + y``

**pp <expression>**
    Pretty-print the value of a Python expression using ``pprint.pprint()``.
    
    Example: ``pp locals()``

**locals, loc**
    Display all local variables in the current frame.

**globals, glob**
    Display all global variables in the current frame (excluding built-ins).

**args, a**
    Display the arguments of the current function.

Breakpoint Management
~~~~~~~~~~~~~~~~~~~~~

**break, b**
    List all breakpoints with their status, hit counts, and conditions.

**b <function>**
    Set a breakpoint on any function with the given name.
    
    Example: ``b main``

**b <module>:<function>**
    Set a breakpoint on a specific function in a specific module.
    
    Example: ``b pygeai.cli.geai:main``

**clear, cl <breakpoint>**
    Remove a breakpoint. Use the same syntax as setting a breakpoint.
    
    Example: ``cl main`` or ``cl pygeai.cli.geai:main``

**clearall, cla**
    Remove all breakpoints.

**enable, en <breakpoint>**
    Enable a disabled breakpoint.
    
    Example: ``en main``

**disable, dis <breakpoint>**
    Disable a breakpoint without removing it.
    
    Example: ``dis main``

Other Commands
~~~~~~~~~~~~~~

**help, h, ?**
    Display a list of available commands and their descriptions.

**<Python code>**
    Execute arbitrary Python code in the current frame's context. For example, ``x = 42`` or ``print(sys.argv)``.

Examples
--------

Example 1: Debug a Chat Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a chat application script:

.. code-block:: python

    # chat_app.py
    from pygeai.chat import ChatClient
    
    def process_message(message):
        client = ChatClient()
        response = client.send_message(message)
        return response.content
    
    def main():
        msg = "Hello, AI!"
        result = process_message(msg)
        print(result)
    
    if __name__ == "__main__":
        main()

Debug it:

.. code-block:: bash

    # Break on process_message
    geai-dbg -b process_message chat_app.py
    
    # Or with module-specific breakpoint
    geai-dbg -b pygeai.chat:send_message chat_app.py

Interactive session:

.. code-block:: text

    (geai-dbg) p message
    'Hello, AI!'
    (geai-dbg) s              # Step into send_message
    (geai-dbg) l              # List source code
    (geai-dbg) p self.config  # Inspect client configuration
    (geai-dbg) c              # Continue

Example 2: Debug geai CLI
~~~~~~~~~~~~~~~~~~~~~~~~~~

Debug the ``geai`` CLI with specific arguments:

.. code-block:: bash

    geai-dbg ail lrs

Output:

.. code-block:: text

    2026-01-14 15:04:57,263 - geai.dbg - INFO - GEAI debugger started.
    2026-01-14 15:04:57,264 - geai.dbg - INFO - Breakpoint added: pygeai.cli.geai:main (enabled, hits: 0)
    2026-01-14 15:04:57,264 - geai.dbg - INFO - Setting trace and running target
    2026-01-14 15:04:57,264 - geai.dbg - INFO - Breakpoint hit at pygeai.cli.geai.main (hit #1)
    
    ============================================================
    Paused at pygeai.cli.geai.main (line 42)
    
    Source (/path/to/pygeai/cli/geai.py):
       39  
       40  class CLIDriver:
       41      def main(self):
    -> 42          parser = ArgumentParser()
       43          args = parser.parse_args()
       44          return self.execute(args)
       45  
    ============================================================
    Type 'h' for help, 'c' to continue
    (geai-dbg) p sys.argv
    ['geai', 'ail', 'lrs']
    (geai-dbg) c

Example 3: Debug with Conditional Breakpoints
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pygeai.dbg import debug_file
    
    dbg = debug_file('process_data.py')
    
    # Only break when count exceeds 1000
    dbg.add_breakpoint(
        function_name='process_batch',
        condition='len(batch) > 1000'
    )
    
    dbg.run()

Example 4: Debug SDK Internals
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

    # Debug the CLI and inspect how commands are processed
    geai-dbg -m pygeai.cli.geai:main -b parse_command

Interactive session:

.. code-block:: text

    (geai-dbg) p command
    (geai-dbg) pp locals()
    (geai-dbg) where  # See the full call stack

Example 5: Stack Navigation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Navigate the call stack:

.. code-block:: text

    (geai-dbg) where
    Stack trace (most recent call last):
       #0  __main__.level_3 at /path/to/script.py:15
      > #1  __main__.level_2 at /path/to/script.py:10
       #2  __main__.level_1 at /path/to/script.py:5
    
    (geai-dbg) up
    Frame #0: __main__.level_2
    
    (geai-dbg) locals
    Local variables:
    {'value': 'level 2'}
    
    (geai-dbg) down
    Frame #1: __main__.level_3

Example 6: Breakpoint Management
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Manage breakpoints during debugging:

.. code-block:: text

    (geai-dbg) b
    Breakpoints:
      1. pygeai.cli.geai:main (enabled, hits: 1)
    
    (geai-dbg) b process_data
    Breakpoint added: *:process_data (enabled, hits: 0)
    
    (geai-dbg) b pygeai.core:helper_function
    Breakpoint added: pygeai.core:helper_function (enabled, hits: 0)
    
    (geai-dbg) dis process_data
    Breakpoint disabled: *:process_data (disabled, hits: 0)
    
    (geai-dbg) cl pygeai.core:helper_function
    Breakpoint removed: pygeai.core:helper_function

Example 7: Verbose Logging
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Debug with verbose logging to see PyGEAI internal logs:

.. code-block:: bash

    # Enable verbose logging with DEBUG level (default)
    geai-dbg -v my_script.py
    
    # Enable verbose logging with INFO level
    geai-dbg -v --log-level INFO my_script.py
    
    # Enable verbose logging with ERROR level only
    geai-dbg -v --log-level ERROR my_script.py

Programmatically:

.. code-block:: python

    from pygeai.dbg import debug_file
    
    # Enable verbose logging with DEBUG level
    dbg = debug_file('my_script.py', verbose=True)
    dbg.run()
    
    # Enable verbose logging with INFO level
    dbg = debug_file('my_script.py', verbose=True, log_level='INFO')
    dbg.run()

Advanced Features
-----------------

Module Filtering
~~~~~~~~~~~~~~~~

The debugger includes a performance optimization that only traces modules matching a specified prefix. This significantly reduces overhead compared to tracing all Python code.

**Automatic detection** (for file debugging):

- Scripts without PyGEAI imports: filters to ``__main__`` only
- Scripts with PyGEAI imports: traces all modules (empty filter)

**Manual control**:

.. code-block:: bash

    # Only trace pygeai modules (default for geai CLI)
    geai-dbg --filter pygeai my_script.py
    
    # Only trace your script
    geai-dbg --filter __main__ my_script.py
    
    # Trace everything (slow!)
    geai-dbg --trace-all my_script.py

Programmatically:

.. code-block:: python

    # Fast: only trace __main__
    dbg = debug_file('script.py', module_filter='__main__')
    
    # Slower: trace pygeai and __main__
    dbg = debug_file('script.py', module_filter='')

Conditional Breakpoints
~~~~~~~~~~~~~~~~~~~~~~~

Breakpoints can include conditions that must be met for the breakpoint to trigger:

.. code-block:: python

    from pygeai.dbg import Debugger
    
    dbg = Debugger(target=my_function)
    dbg.add_breakpoint(
        module="my_module",
        function_name="process_item",
        condition="item > 100"
    )

The breakpoint will only trigger when ``item > 100`` evaluates to ``True`` in the function's context.

Command History
~~~~~~~~~~~~~~~

The debugger uses Python's ``readline`` module to provide command history and line editing. You can use:

- **Up/Down arrows**: Navigate through command history
- **Ctrl+R**: Search command history

Command history is saved to ``~/.geai_dbg_history`` and persists across debugging sessions.

Helper Functions
~~~~~~~~~~~~~~~~

The ``pygeai.dbg`` module provides convenient helper functions:

**debug_file(filepath, args, module_filter, breakpoint_specs, verbose, log_level)**
    Debug a Python file by executing it under the debugger.
    
    :param filepath: Path to the Python file to debug (required)
    :param args: Command-line arguments to pass to the script (optional)
    :param module_filter: Module prefix to trace, None auto-detects (optional)
    :param breakpoint_specs: List of (module, function) tuples for initial breakpoints (optional)
    :param verbose: Enable verbose logging for pygeai modules (default: False)
    :param log_level: Log level for verbose mode: 'DEBUG', 'INFO', 'WARNING', 'ERROR' (default: 'DEBUG')
    :return: Configured Debugger instance
    :raises: FileNotFoundError if the file doesn't exist

**debug_module(module_name, function_name, args, module_filter)**
    Debug a specific module and function.
    
    :param module_name: Fully qualified module name, e.g., 'pygeai.cli.geai' (required)
    :param function_name: Function to call (default: 'main')
    :param args: Command-line arguments (optional)
    :param module_filter: Module prefix to trace (optional)
    :return: Configured Debugger instance with automatic breakpoint
    :raises: ImportError if module or function cannot be imported

Tips and Best Practices
-----------------------

1. **Start with targeted breakpoints**: Set specific breakpoints on the functions you want to debug rather than using wildcards.

2. **Use step wisely**: The ``step`` command can be slow if it steps into many library functions. Use ``next`` to stay at the same level.

3. **Inspect the stack**: Use ``where`` to understand the call chain, especially in complex codebases.

4. **Pretty-print complex data**: Use ``pp`` instead of ``p`` for dictionaries, lists, and other complex structures.

5. **Disable instead of removing**: Use ``disable`` to temporarily turn off breakpoints you might need again, rather than removing them.

6. **Use module filtering**: When debugging custom code, set ``module_filter`` to your package name to avoid tracing unrelated code.

7. **Conditional breakpoints**: Use conditions to break only when specific criteria are met, reducing manual stepping.

8. **Strategic breakpoints**: Set breakpoints only where needed. Specific module:function breakpoints are faster than wildcards.

Performance Considerations
--------------------------

**Module Filtering**

Module filtering defaults to sensible values:

- ``__main__`` for scripts without PyGEAI imports
- Empty string (all modules) for scripts with PyGEAI imports
- Inherited from module name for module debugging

Users can override with ``--filter`` or ``--trace-all``.

**Overhead**

The debugger uses ``sys.settrace`` which has performance overhead. The module filter helps minimize this, but expect slower execution than running without the debugger.

Troubleshooting
---------------

**Debugger Not Stopping**

1. Check module filter matches your code
2. Verify breakpoint module/function names are correct
3. Use ``--trace-all`` to debug filtering issues

**Source Code Not Available**

Some modules (built-ins, compiled extensions) don't have accessible source. The debugger will notify you when source is unavailable.

**Performance Issues**

1. Reduce module filter scope
2. Use specific breakpoints instead of wildcards
3. Disable conditional breakpoints if not needed

**Breakpoint not hitting**

- Check that the module and function names match exactly (use ``lm`` to list loaded modules)
- Verify the breakpoint is enabled (use ``b`` to list breakpoints)
- Check if a condition is preventing the breakpoint from triggering

**Can't see local variables**

Make sure you're in the correct frame. Use ``where`` to see the stack and ``up``/``down`` to navigate.

Code Examples
-------------

See the ``pygeai/tests/snippets/dbg/`` directory for complete working examples:

- ``basic_debugging.py`` - Simple debugging with variable inspection
- ``file_debugging.py`` - Demonstrates debugging Python files
- ``module_debugging.py`` - Shows module debugging capabilities
- ``breakpoint_management.py`` - Examples of managing breakpoints
- ``stack_navigation.py`` - Shows stack traversal with up/down

Run these examples with:

.. code-block:: bash

    python pygeai/tests/snippets/dbg/basic_debugging.py
    python pygeai/tests/snippets/dbg/file_debugging.py
    python pygeai/tests/snippets/dbg/module_debugging.py

Notes
-----

- **Ctrl+D and Ctrl+C**:
  - Pressing ``Ctrl+D`` at the ``(geai-dbg)`` prompt terminates the debugger gracefully.
  - Pressing ``Ctrl+C`` resumes execution, equivalent to the ``continue`` command.

- **Python Code Execution**:
  - Arbitrary Python code executed at the prompt runs in the context of the current frame, with access to local and global variables.

- **Breakpoint Persistence**:
  - Breakpoints persist across ``continue`` commands but are cleared when the program exits. They are not saved to disk.

- **Logging**:
  - The debugger logs to stdout with timestamps, including breakpoint hits, state changes, and errors.
  - PyGEAI module logging is disabled by default. Enable it with ``-v/--verbose`` flag.
  - When verbose mode is enabled, the log level can be controlled with ``--log-level`` (default: DEBUG).

- **Frame Context**:
  - When you move up/down the stack with ``up``/``down``, the current frame changes, affecting what ``locals``, ``globals``, and expression evaluation see.

For issues or feature requests, contact the PyGEAI development team or file an issue on the project's GitHub repository.

.. seealso::

   - ``geai`` CLI documentation for details on the underlying command-line tool
   - Python's ``sys.settrace`` documentation for technical details on the debugging mechanism
   - Python's ``pdb`` module for comparison with the standard Python debugger
