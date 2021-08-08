# MIT License

# Copyright (c) 2020 Eric Lesiuta

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import argparse
import collections
import difflib
import json
import mimetypes
import os
import re
import shlex
import subprocess
import sys
import typing

VERSION = "1.3.0"


def initParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Almost, but not quite, entirely unlike aliases",
                                     usage="%(prog)s [options] [command [initial-arguments ...]]")
    parser.add_argument("command", action="store", nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)
    maingrp = parser.add_mutually_exclusive_group()
    maingrp.add_argument("-c", dest="add_c", metavar="name",
                         help="add the command to your spellbook")
    maingrp.add_argument("-cc", dest="add_cc", metavar=("name", "desc"), nargs=2,
                         help="also add description with command")
    maingrp.add_argument("-ccc", dest="add_ccc", metavar=("name", "desc", "rs"), nargs=3,
                         help="also add replace-str with command")
    maingrp.add_argument("-d", dest="add_dir", metavar="path",
                         help="add a directory path to your config")
    maingrp.add_argument("-e", dest="add_extension", metavar=(".ext", "path"), nargs=2,
                         help="add an extension and the path to an executable for it")
    maingrp.add_argument("-l", "--list", dest="list", action="store_true",
                         help="list entire collection (or specify: cmd, dir, ext, files)")
    maingrp.add_argument("-s", "--search", dest="search", action="store_true",
                         help="search entire collection for command")
    maingrp.add_argument("--_completion", dest="print_completions", type=str,
                         help=argparse.SUPPRESS)
    maingrp.add_argument("--_return_completion", dest="return_completions", type=str,
                         help=argparse.SUPPRESS)
    maingrp.add_argument("--reg-fish", dest="reg_fish_completer", action="store_true",
                         help=argparse.SUPPRESS)
    maingrp.add_argument("--reg-xonsh", dest="reg_xonsh_completer", action="store_true",
                         help=argparse.SUPPRESS)
    maingrp.add_argument("--reg-zsh", dest="reg_zsh_completer", action="store_true",
                         help=argparse.SUPPRESS)
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true",
                        help="print command instead of executing it")
    parser.add_argument("--version", action="version", version=VERSION)
    return parser


def colourStr(string: str, colour: str) -> str:
    colours = {
        "R": "\033[91m",
        "G": "\033[92m",
        "B": "\033[94m",
        "Y": "\033[93m",
        "V": "\033[95m"
    }
    return colours[colour] + string + "\033[0m"


def elfsXompletionWrapper(prefix: str, line: str, begidx: int, endidx: int, ctx: dict) -> typing.Union[None, set]:
    if line.startswith("elfs "):
        # get regular completions
        sys.argv = ["elfs", "--_return_completion", line]
        completions = main()
        # xonsh seems to need quotes to autocomplete paths, and splits off prefix on a space (even when escaped)
        # this slightly improves it for paths without spaces (without needing quotes)
        # trying anything more, eg. with shlex is problematic
        if os.path.isdir(os.path.dirname(prefix)):
            completions += os.listdir(os.path.dirname(prefix))
        else:
            completions += os.listdir()
        # format completions for xonsh -remove descriptions -escape spaces -filter by prefix
        if len(completions) >= 1:
            return {completion.split("\t")[0].replace(" ", "\\ ") for completion in completions if completion.startswith(prefix)}
    return None


def getCompletions(command: list, command_str: str, last_char: str, file_dict: dict, spellbook_dict: dict) -> list:
    # get position of current argument, where position 0 is "elfs"
    position = len(command) - 1
    if last_char == " ":
        # append empty string for the current (empty) argument for consistent indexing
        position += 1
        command.append("")
    # start off without any completions and append
    completions = []
    if (position == 1) or (position == 2 and command[1] in ["-n", "--dry-run"]):
        completions += [
            "-h\thelp",
            "-c\tadd name command",
            "-cc\tadd name desc command",
            "-ccc\tadd name desc rs command",
            "-d\tadd directory",
            "-e\tadd extension",
            "-l\tlist",
            "-s\tsearch"
        ]
        if command[position].startswith("--"):
            completions += [
                "--help\thelp",
                "--list\tlist",
                "--search\tsearch"
            ]
    if (position == 1) or (position == 2 and command[1] in ["-s", "--search"]):
        completions += ["-n\tdry-run"]
        if command[position].startswith("--"):
            completions += ["--dry-run\tdry-run"]
    if position <= 3 and command[position - 1] in ["-l", "--list"]:
        completions += [
            "cmd",
            "dir",
            "ext",
            "files"
        ]
    # add files and commands from spellbook to completions
    if (
        (position == 1) or
        (position <= 3 and command[position - 1] in ["-n", "--dry-run", "-s", "--search"])
    ):
        completions += [file_name for file_name in file_dict.keys()]
        completions += [spell_name + "\t" + spellbook_dict[spell_name]["desc"][:16] for spell_name in spellbook_dict.keys()]
    # extend with completions from target file
    if (
        (position >= 2 and command[1] in file_dict) or
        (position >= 3 and command[1] in ["-n", "--dry-run"] and command[2] in file_dict)
    ):
        new_position = position - 1
        new_command = command[1:]
        if command[1] in ["-n", "--dry-run"]:
            new_position = position - 2
            new_command = command[2:]
        file_name = new_command[0]
        completion_namespace = {
            "position": new_position,
            "command": new_command,
            "pos": new_position,
            "cmd": new_command
        }
        completion_rules = []
        if os.path.isfile(os.path.join(file_dict[file_name], file_name + ".elfs.json")):
            completion_rules = readJson(os.path.join(file_dict[file_name], file_name + ".elfs.json"))
        elif str(mimetypes.guess_type(file_name)[0]).startswith("text"):
            try:
                source = ""
                with open(os.path.join(file_dict[file_name], file_name), "r") as f:
                    source = f.read()
                if "# TAB-COMPLETION START" in source and "# TAB-COMPLETION END" in source:
                    start = source.index("# TAB-COMPLETION START") + len("# TAB-COMPLETION START")
                    end = source.index("# TAB-COMPLETION END")
                    completion_rules = json.loads(source[start:end])
            except Exception as e:
                print("\nError elfs line: %s %s %s" % (sys.exc_info()[2].tb_lineno, type(e).__name__, e.args), file=sys.stderr)
        for rule in completion_rules:
            try:
                if "command" in rule:
                    command_str_stripped = re.sub("^%s +(-n +|--dry-run +)?" % (command[0]), "", command_str, count=1)
                    completer_command = [arg.replace("(commandline)", command_str_stripped) for arg in rule["command"]]
                    completer_process = subprocess.run(completer_command, cwd=file_dict[file_name], stdout=subprocess.PIPE, universal_newlines=True)
                    for completion in completer_process.stdout.splitlines():
                        completions.append(completion)
                elif eval(rule["expression"], completion_namespace, completion_namespace):
                    completions += rule["completions"]
            except Exception as e:
                print("\nError elfs line: %s %s %s" % (sys.exc_info()[2].tb_lineno, type(e).__name__, e.args), file=sys.stderr)
    return completions


def readJson(file_path: str) -> dict:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="surrogateescape") as json_file:
            data = json.load(json_file)
        return data
    return {}


def writeJson(file_path: str, data: dict, spellbook: bool = False) -> None:
    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    normal_json = json.dumps(data, indent=2, separators=(',', ': '), sort_keys=True, ensure_ascii=False)
    if spellbook:
        normal_json = normal_json.splitlines(keepends=True)
        pretty_json = []
        is_cmd = False
        for line in normal_json:
            if not is_cmd and line != '      "cmd": [\n':
                pretty_json.append(line)
            elif line == '      "cmd": [\n':
                pretty_json.append('      "cmd": [')
                is_cmd = True
            elif line == '      ],\n':
                pretty_json[-1] += '],\n'
                is_cmd = False
            elif is_cmd:
                pretty_json[-1] += line[8:-1]
                if pretty_json[-1][-1] == ',':
                    pretty_json += ' '
            else:
                raise Exception("Pretty JSON Error: unexpected command or format")
        with open(file_path, "w", encoding="utf-8", errors="surrogateescape") as json_file:
            json_file.writelines(pretty_json)
    else:
        with open(file_path, "w", encoding="utf-8", errors="surrogateescape") as json_file:
            json_file.write(normal_json)


def main() -> typing.Union[int, list]:
    # parse arguments
    parser = initParser()
    args = parser.parse_args()
    # init config
    config_path = os.path.join(os.path.expanduser("~"), ".config", "elfs", "config.json")
    config = readJson(config_path)
    if not config:
        config = {
            "directories": [],
            "executables": {
                ".py": sys.executable
            },
            "spellbook": os.path.join(os.path.expanduser("~"), ".config", "elfs", "spellbook.json")
        }
    # init file dictionary
    file_dict = collections.OrderedDict()
    file_splitext = {}
    file_extra = []
    for directory in config["directories"]:
        for file_name in sorted(os.listdir(directory)):
            if os.path.isfile(os.path.join(directory, file_name)):
                if file_name[-10:] != ".elfs.json":
                    if file_name not in file_dict:
                        file_dict[file_name] = directory
                    else:
                        file_extra.append(os.path.join(directory, file_name))
                    if os.path.splitext(file_name)[0] not in file_splitext:
                        file_splitext[os.path.splitext(file_name)[0]] = os.path.splitext(file_name)[1]
                    else:
                        file_splitext[os.path.splitext(file_name)[0]] = False
    # init spellbook
    spellbook = readJson(config["spellbook"])
    if not spellbook:
        spellbook = {"spells": []}
    spellbook_dict = {}
    for spell in spellbook["spells"]:
        if spell["name"] not in spellbook_dict:
            spellbook_dict[spell["name"]] = spell
    # print completions
    if args.print_completions:
        command_str, last_char = args.print_completions, args.print_completions[-1]
        try:
            command = shlex.split(args.print_completions)
        except Exception:
            command = shlex.split(shlex.quote(args.print_completions))
        completions = getCompletions(command, command_str, last_char, file_dict, spellbook_dict)
        if completions:
            print("\n".join(completions))
        return 0
    # return completions
    if args.return_completions:
        command_str, last_char = args.return_completions, args.return_completions[-1]
        try:
            command = shlex.split(args.return_completions)
        except Exception:
            command = shlex.split(shlex.quote(args.return_completions))
        completions = getCompletions(command, command_str, last_char, file_dict, spellbook_dict)
        return completions
    # register fish completions
    if args.reg_fish_completer:
        with open(os.path.expanduser("~/.config/fish/config.fish"), "a+") as f:
            f.seek(0)
            if "ELFS TAB-COMPLETION" not in f.read():
                fishrc = [
                    "\n# ELFS TAB-COMPLETION START",
                    "\ncomplete -c elfs -a '(elfs --_completion (commandline -cp))'",
                    "\n# ELFS TAB-COMPLETION END",
                    "\n\n"
                ]
                f.writelines(fishrc)
        return 0
    # register xonsh completions
    if args.reg_xonsh_completer:
        with open(os.path.expanduser("~/.xonshrc"), "a+") as f:
            f.seek(0)
            if "ELFS TAB-COMPLETION" not in f.read():
                xonshrc = [
                    "\n# ELFS TAB-COMPLETION START",
                    "\nfrom elfs import elfsXompletionWrapper",
                    "\ncompleter add elfs elfsXompletionWrapper",
                    "\n# ELFS TAB-COMPLETION END",
                    "\n\n"
                ]
                f.writelines(xonshrc)
        return 0
    # register zsh completions
    if args.reg_zsh_completer:
        print("TODO")
        return 0
    # add command
    if args.add_c or args.add_cc or args.add_ccc:
        if args.add_c:
            name, description, replace_str = args.add_c[0], "", ""
        elif args.add_cc:
            name, description, replace_str = args.add_cc[0], args.add_cc[1], ""
        elif args.add_ccc:
            name, description, replace_str = args.add_ccc[0], args.add_ccc[1], args.add_ccc[2]
        spell = {
            "cmd": args.command,
            "desc": description,
            "name": name,
            "replace-str": replace_str
        }
        spellbook["spells"].append(spell)
        writeJson(config["spellbook"], spellbook, True)
        if spell["name"] and (spell["name"] in spellbook_dict or spell["name"] in file_dict):
            warning_msg = colourStr("Warning: ", "Y") + spell["name"]
            warning_msg += colourStr(" already exists in your collection, only the first entry will run with", "Y")
            print(warning_msg + " elfs " + spell["name"])
        return 0
    # add dir
    if args.add_dir:
        if not os.path.isdir(args.add_dir):
            print(colourStr("Path not found: ", "R") + args.add_dir)
            return 1
        if os.path.abspath(args.add_dir) not in config["directories"]:
            config["directories"].append(os.path.abspath(args.add_dir))
        writeJson(config_path, config)
        return 0
    # add extension
    if args.add_extension:
        config["executables"][args.add_extension[0]] = args.add_extension[1]
        writeJson(config_path, config)
        return 0
    # list collection
    if args.list:
        print(colourStr("Config path: ", "V") + config_path)
        print(colourStr("Spellbook path: ", "V") + config["spellbook"])
        if not args.command or args.command[0][0] == "e":
            print(colourStr("Known extensions and associated executables", "V"))
            for ext in config["executables"]:
                print(colourStr(ext + ": ", "B") + config["executables"][ext])
            print("")
        if not args.command or args.command[0][0] == "d":
            print(colourStr("Directories added to search path", "V"))
            for directory in config["directories"]:
                print(directory)
            print("")
        if not args.command or args.command[0][0] == "f":
            print(colourStr("Files found in directories", "V"))
            last_directory = ""
            for file_name in file_dict:
                if file_dict[file_name] != last_directory:
                    last_directory = file_dict[file_name]
                    print(colourStr(last_directory, "B"))
                print(file_name)
            if file_extra:
                print(colourStr("Extra files (duplicate names)", "V"))
                for file_path in file_extra:
                    print(file_path)
            print("")
        if not args.command or args.command[0][0] == "c":
            print(colourStr("Commands found in spellbook", "V"))
            for spell in spellbook["spells"]:
                spell_str = ""
                spell_str += colourStr("Name: ", "B") + spell["name"] + " "
                spell_str += colourStr("Description: ", "B") + spell["desc"] + " "
                spell_str += colourStr("Replace-str: ", "B") + spell["replace-str"] + "\n"
                spell_str += colourStr("Command: ", "B") + shlex.join(spell["cmd"]) + "\n"
                print(spell_str)
            if not spellbook["spells"]:
                print("")
        return 0
    # search collection (then prompt for selection to optionally run)
    if args.search:
        search_str = " ".join(args.command)
        search_results = []
        search_index = []
        search_index += list(file_dict.keys())
        search_index += [os.path.basename(file_path) for file_path in file_extra]
        search_index += [spell["name"] for spell in spellbook["spells"]]
        search_index += [spell["desc"] for spell in spellbook["spells"]]
        search_index += [" ".join(spell["cmd"]) for spell in spellbook["spells"]]
        fuzzy_search = difflib.get_close_matches(search_str, search_index, cutoff=0.4)
        for file_name in file_dict:
            if search_str in file_name or file_name in fuzzy_search:
                search_results.append({"label": os.path.join(file_dict[file_name], file_name), "type": "file"})
        for file_path in file_extra:
            if search_str in os.path.basename(file_path) or os.path.basename(file_path) in fuzzy_search:
                search_results.append({"label": file_path, "type": "file"})
        for spell in spellbook["spells"]:
            if (
                search_str in spell["name"] or spell["name"] in fuzzy_search or
                search_str in spell["desc"] or spell["desc"] in fuzzy_search or
                search_str in " ".join(spell["cmd"]) or " ".join(spell["cmd"]) in fuzzy_search
            ):
                search_results.append({"label": shlex.join(spell["cmd"]), "type": "spellbook", "spell": spell})
        if len(search_results) == 0:
            print(colourStr("No matches found", "Y"))
            return 0
        print(colourStr("Search results:", "V"))
        for i in range(len(search_results)):
            print(colourStr(str(i) + ". ", "G"), search_results[i]["label"])
        print("Enter a " + colourStr("number", "G") + " to select and run a match, anything else to cancel")
        print("Supply any extra arguments (if needed) separated by spaces")
        if not sys.stdin.isatty():
            print(colourStr("Warning: stdin is not connected to a terminal", "Y"))
        search_input = input(">>> ")
        try:
            search_input = shlex.split(search_input)
            search_selection = search_results[int(search_input[0])]
            command_type = search_selection["type"]
            forward_args = search_input[1:]
            if command_type == "file":
                command_file_path = search_selection["label"]
            elif command_type == "spellbook":
                spell = search_selection["spell"]
        except Exception:
            print(colourStr("No match selected", "Y"))
            return 0
    # find exact match (precedence: files in dir order -> spellbook in list order -> imply file extension if unambiguous)
    if not args.search:
        if not args.command:
            parser.print_usage()
            return 0
        if args.command[0] not in file_dict and args.command[0] not in spellbook_dict:
            if args.command[0] in file_splitext and file_splitext[args.command[0]]:
                args.command[0] += file_splitext[args.command[0]]
        if args.command[0] in file_dict:
            command_type = "file"
            forward_args = args.command[1:]
            command_file_path = os.path.join(file_dict[args.command[0]], args.command[0])
        elif args.command[0] in spellbook_dict:
            command_type = "spellbook"
            forward_args = args.command[1:]
            spell = spellbook_dict[args.command[0]]
        else:
            print(colourStr("Command not found", "Y"))
            return 0
    # build command (from search selection or exact match if not searching)
    if command_type == "file":
        command = [command_file_path] + forward_args
        if os.path.splitext(command_file_path)[1] in config["executables"]:
            command.insert(0, config["executables"][os.path.splitext(command_file_path)[1]])
    elif command_type == "spellbook":
        command = spell["cmd"]
        j = -1
        if spell["replace-str"] and forward_args:
            for i in range(len(command)):
                while spell["replace-str"] in command[i]:
                    j = min(j + 1, len(forward_args) - 1)
                    command[i] = command[i].replace(spell["replace-str"], forward_args[j], 1)
                    if spell["replace-str"] in forward_args[j]:
                        if command[i].count(spell["replace-str"]) > 1:
                            print(colourStr("Indeterminate replace-str in arg: ", "R") + command[i])
                            return 1
                        else:
                            break
        command += forward_args[j+1:]
    # execute command
    if args.dry_run:
        print(colourStr("Command: ", "B") + shlex.join(command))
        return 0
    else:
        return subprocess.Popen(command).wait()


if __name__ == "__main__":
    sys.exit(main())
