# Easy Launcher For the Shell (temporary name)
Install from source with
```
python elfs.py --setup install --user
```
Install from PyPI with
```
pip install elfs
```
Command Line Interface
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
