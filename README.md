# Easy Launcher For the Shell (temporary name)
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
  -c                Add the command to your spellbook
  -cc name desc rs  Add the command to your spellbook with comments
  -t name template  Add the command to a new script from a template
  -d path           Add a directory path to your config
  -e .ext path      Add an extension and the path to an executable for it
  -l, --list        List entire collection (or specify: cmd, dir, ext, files)
  -s, --search      Search entire collection for command
  -n, --dry-run     Print command instead of executing it
```
### Examples
```
// add a directory
$ elfs -d ~/scripts
// run your script from any directory
$ elfs myscript.py arg0 arg1 arg2
<script output>
```
```
// add an extension and executable for running files in your directory
$ elfs -e .sh /bin/bash
```
```
// add a command
$ elfs -cc spam "print spam" "" echo spam
// run the command
$ elfs spam
spam
```
```
// add a command with replacement
$ elfs -cc "more spam" "even more spam" {} echo spam {} eggs {}
$ elfs "more spam" bacon spam
spam bacon eggs spam
```
```
// multiple commands (needs to run in a shell, elfs uses Popen shell=False)
$ elfs -cc "double spam" "" "" bash -c "echo spam && echo spam"
$ elfs "double spam"
spam spam
```
```
// see the command without running it (quotes may appear slightly different)
$ elfs -n "double spam"
Command: bash -c "echo spam && echo spam"
```
```
// list all commands and files
$ elfs -l
```
```
// search commands and files with fuzzy matches
$ elfs -s dble spam
0. bash -c "echo spam && echo spam"
Enter a number to select and run a match, anything else to cancel
Supply any extra arguments (if needed) separated by spaces
>>> 
```
```
// add a command to easily edit your spellbook
$ elfs -cc "edit" "" "" nano ~/scripts/spellbook.json
```
