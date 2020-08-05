# Easy Launcher For the Shell
### Install from PyPI
```
pip install elfs
```
### Install from source
```
python setup.py install --user
```
### Command Line Interface
```
usage: elfs [options] [command [initial-arguments ...]]

Easy Launcher For (the) Shell

optional arguments:
  -h, --help        show this help message and exit
  -c                add the command to your spellbook
  -cc name desc rs  add the command to your spellbook with comments
  -d path           add a directory path to your config
  -e .ext path      add an extension and the path to an executable for it
  -l, --list        list entire collection (or specify: cmd, dir, ext, files)
  -s, --search      search entire collection for command
  -n, --dry-run     print command instead of executing it
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
```> elfs -cc spam "echo spam to output 3 times" "" echo spam spam spam```
- run the command  
```> elfs spam```
> spam spam spam
- add a command with a replace-str (metavar: rs) and run it  
```> elfs -cc menu "even more spam" {} echo spam {} spam {}```  
```> elfs menu bacon eggs```
> spam bacon spam eggs
- giving fewer arguments causes them to repeat  
```> elfs menu bacon```
> spam bacon spam bacon
- and extra arguments are passed along as normal  
```> elfs menu bacon eggs sausage spam```
> spam bacon spam eggs sausage spam
- command chaining (needs to run in a shell, elfs uses Popen shell=False)  
```> elfs -cc "double spam" "" "" bash -c "echo spam && echo spam"```  
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
```> elfs -cc "config" "" "" nano ~/.config/elfs/config.json```
- or add a command to edit your spellbook (you can move this file)  
```> elfs -cc "spells" "" "" nano ~/.config/elfs/spellbook.json```
