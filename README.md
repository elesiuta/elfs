# Enhanced aLiases For Shells (Name subject to change)
### Install from PyPI
```
pip install elfs
```
### Install from source
```
python setup.py install --user
```
### Enable dynamic tab-completion for fish or xonsh
```
elfs --reg-fish
elfs --reg-xonsh
```
### Command Line Interface
```
usage: elfs [options] [command [initial-arguments ...]]

Almost, but not quite, entirely unlike aliases

optional arguments:
  -h, --help         show this help message and exit
  -c name            add the command to your spellbook
  -cc name desc      also add description with command
  -ccc name desc rs  also add replace-str with command
  -d path            add a directory path to your config
  -e .ext path       add an extension and the path to an executable for it
  -l, --list         list entire collection (or specify: cmd, dir, ext, files)
  -s, --search       search entire collection for command
  -n, --dry-run      print command instead of executing it
  --version          show program's version number and exit
```
### Usage Notes
- Runs on any platform with python 3
- Unless using search (and select), the default behaviour is to find a command using exact matches only, and is selected in the following order of precedence
  1. files in order of directories listed in config
  2. names of commands from spellbook in order listed
  3. imply file extension if possible and unambiguous
- Commands without names (or duplicate names of lower precedence) can only be run via search
- Commands and files with spaces in their names need to be escaped or in quotes
- The first argument (that is not an option for elfs) is treated as the command or filename and all subsequent arguments are passed to the command or file to be executed (except for commands with a replace-str, see example)
- Pipes work as expected, you can pipe into or out from any command or file, however if you try piping into a search, it will interpret that as your selection
### Examples
- add a directory  
```> elfs -d ~/scripts```
- run your script from any directory  
```> elfs myscript.py arg0 arg1 arg2```
- file extension is implied only if unambiguous  
```> elfs myscript arg0 arg1 arg2```
- add an extension to run a file with a specific executable  
```> elfs -e .py /path/to/alternative/env/for/python```
- add a command  
```> elfs -cc spam "echo spam to output 3 times" echo spam spam spam```
- run the command  
```> elfs spam```
> spam spam spam
- add a command with a replace-str (metavar: rs) and run it  
```> elfs -ccc menu "even more spam" {} echo spam {} spam {}```  
```> elfs menu bacon eggs```
> spam bacon spam eggs
- giving fewer arguments causes them to repeat  
```> elfs menu bacon```
> spam bacon spam bacon
- and extra arguments are passed along as normal  
```> elfs menu bacon eggs sausage spam```
> spam bacon spam eggs sausage spam
- command chaining (needs to run in a shell, elfs uses Popen shell=False)  
```> elfs -c "double spam" bash -c "echo spam && echo spam"```  
```> elfs "double spam"```
> spam spam
- see the command without running it (quotes may appear slightly different)  
```> elfs -n "double spam"```
> Command: bash -c "echo spam && echo spam"
- list all commands and files  
```> elfs -l```
- search commands and files with fuzzy matches, then optionally select from a list of matches to execute  
```> elfs -s dble spam```
- add a command to quickly edit your config  
```> elfs -c "config" nano ~/.config/elfs/config.json```
- or add a command to edit your spellbook (you can move this file)  
```> elfs -c "spells" nano ~/.config/elfs/spellbook.json```
### Add dynamic tab-completion to your scripts
- create completion rules in the following json format
```json
[
  {
    "expression": "python_expression_for_rule_1",
    "completions": ["option1", "option2\thello", "option3\tworld"]
  },
  {
    "expression": "python_expression_for_rule_2",
    "completions": ["option1", "option4\toptional description"]
  }
]
```
- where the python expression is evaluated in a namespace with the following variables
  - position = current position in the command, where 0 is the current script
    - eg. `elfs[None] myscript.py[0] option[1] [2]`
    - position does not increment until the next space `elfs[None] myscript.py[0] option[1] op[2]`
  - command = command so far, as parsed by shlex
    - following the same example with `position=2`, `command=["myscript.py", "option", ""]`
    - and `command=["myscript.py", "option", "op"]`
  - eg. `"position == 2 and command[1] in ['option1', 'option2']"`
- the completions are shown for every expression that evaluates as true
- the completion rules can be placed in either of the following locations
  - inside `file_name.ext.elfs.json`, eg. `myscript.py.elfs.json`
  - or directly enclosed in `file_name.ext` with `# TAB-COMPLETION START` and `# TAB-COMPLETION END`
```python
# TAB-COMPLETION START
[
  ...
]
# TAB-COMPLETION END
```
