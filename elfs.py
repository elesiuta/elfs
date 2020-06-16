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
import difflib
import json
import os
import setuptools
import shlex
import subprocess
import sys


def setup(help_text: str):
    setuptools.setup(
        name="elfs",
        version="0.4.0",
        description="Easy Launcher For (the) Shell",
        long_description=help_text,
        long_description_content_type="text/markdown",
        url="https://github.com/elesiuta/elfs",
        py_modules=["elfs"],
        entry_points={"console_scripts": ["elfs = elfs:main"]},
        classifiers=[
            "Programming Language :: Python :: 3",
            "License :: OSI Approved :: MIT License",
            "Operating System :: OS Independent",
            "Environment :: Console",
        ],
    )


def colourStr(string: str, colour: str) -> str:
    colours = {
        "R": "\033[91m",
        "G": "\033[92m",
        "B": "\033[94m",
        "Y": "\033[93m",
        "V": "\033[95m"
    }
    return colours[colour] + string + "\033[0m"


def readJson(file_path: str) -> dict:
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8", errors="surrogateescape") as json_file:
            data = json.load(json_file)
        return data
    return {}


def writeJson(file_path: str, data: dict) -> None:
    if not os.path.isdir(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path, "w", encoding="utf-8", errors="surrogateescape") as json_file:
        json.dump(data, json_file, indent=2, separators=(',', ': '), sort_keys=True, ensure_ascii=False)


def main() -> int:
    # argparse
    parser = argparse.ArgumentParser(description="Easy Launcher For (the) Shell",
                                     usage="%(prog)s [options] [command [initial-arguments ...]]")
    parser.add_argument("command", action="store", nargs=argparse.REMAINDER,
                        help=argparse.SUPPRESS)
    maingrp = parser.add_mutually_exclusive_group()
    maingrp.add_argument("-c", dest="add_command", action="store_true",
                         help="Add the command to your spellbook")
    maingrp.add_argument("-cc", dest="add_command_comments", metavar=("name", "desc", "rs"), nargs=3,
                         help="Add the command to your spellbook with comments")
    maingrp.add_argument("-t", dest="add_template", metavar=("name", "template"), nargs=2,
                         help="Add the command to a new script from a template")
    maingrp.add_argument("-d", dest="add_dir", metavar="path",
                         help="Add a directory path to your config")
    maingrp.add_argument("-e", dest="add_extension", metavar=(".ext", "path"), nargs=2,
                         help="Add an extension and the path to an executable for it")
    maingrp.add_argument("-l", "--list", dest="list", action="store_true",
                         help="List entire collection (or specify: cmd, dir, ext, files)")
    maingrp.add_argument("-s", "--search", dest="search", action="store_true",
                         help="Search entire collection for command")
    parser.add_argument("-n", "--dry-run", dest="dry_run", action="store_true",
                        help="Print command instead of executing it")
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
            "spellbook": ""
        }
    # init file dictionary
    file_dict = {}
    file_extra = []
    for directory in config["directories"]:
        for file_name in os.listdir(directory):
            if os.path.isfile(os.path.join(directory, file_name)):
                if file_name not in file_dict:
                    file_dict[file_name] = directory
                else:
                    file_extra.append(os.path.join(directory, file_name))
    # add dir
    if args.add_dir:
        if not os.path.isdir(args.add_dir):
            raise Exception("Path not found: %s", args.add_dir)
        if os.path.abspath(args.add_dir) not in config["directories"]:
            config["directories"].append(os.path.abspath(args.add_dir))
        if not config["spellbook"]:
            config["spellbook"] = os.path.join(os.path.abspath(args.add_dir), "spellbook.json")
        writeJson(config_path, config)
        return 0
    # add template
    if args.add_template:
        template_path = os.path.join(file_dict[args.add_template[1]], args.add_template[1])
        new_script_path = os.path.join(file_dict[args.add_template[1]], args.add_template[0])
        if not os.path.isfile(template_path) or os.path.isfile(new_script_path):
            raise Exception("Template either does not exist or new script will overwrite an existing file")
        with open(template_path, "r") as template_file:
            template = template_file.readlines()
        new_script = []
        for line in template:
            new_script.append(line.replace("###REPLACE###", " ".join(args.command)))
        with open(new_script_path, "w") as new_script_file:
            new_script_file.writelines(new_script)
        return 0
    # add extension
    if args.add_extension:
        config["executables"][args.add_extension[0]] = args.add_extension[1]
        writeJson(config_path, config)
        return 0
    # init spellbook
    spellbook = readJson(config["spellbook"])
    if not spellbook:
        spellbook = {"spells": []}
    # add command
    if args.add_command:
        spell = {
            "cmd": args.command,
            "desc": "",
            "name": "",
            "replace-str": ""
        }
        spellbook["spells"].append(spell)
        writeJson(config["spellbook"], spellbook)
        return 0
    if args.add_command_comments:
        spell = {
            "cmd": args.command,
            "desc": args.add_command_comments[1],
            "name": args.add_command_comments[0],
            "replace-str": args.add_command_comments[2]
        }
        spellbook["spells"].append(spell)
        writeJson(config["spellbook"], spellbook)
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
            print(colourStr("Commands found in spell book", "V"))
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
    # search collection
    if args.search:
        search_str = " ".join(args.command)
        search_results = []
        search_index = []
        search_index += list(file_dict.keys())
        search_index += [os.path.basename(file_path) for file_path in file_extra]
        search_index += [spell["name"] for spell in spellbook["spells"]]
        search_index += [spell["desc"] for spell in spellbook["spells"]]
        search_index += [" ".join(spell["cmd"]) for spell in spellbook["spells"]]
        fuzzy_search = difflib.get_close_matches(search_str, search_index)
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
    # exact match only if not searching
    if not args.search:
        if not args.command:
            parser.print_usage()
            return 0
        if args.command[0] in file_dict:
            command_type = "file"
            forward_args = args.command[1:]
            command_file_path = os.path.join(file_dict[args.command[0]], args.command[0])
        elif args.command[0] in [spell["name"] for spell in spellbook["spells"]]:
            command_type = "spellbook"
            forward_args = args.command[1:]
            for spell in spellbook["spells"]:
                if args.command[0] == spell["name"]:
                    break
        else:
            print(colourStr("Command not found", "Y"))
            return 0
    # build command
    if command_type == "file":
        command_bin = config["executables"][os.path.splitext(command_file_path)[1]]
        command = [command_bin, command_file_path] + forward_args
    elif command_type == "spellbook":
        command = spell["cmd"]
        if spell["replace-str"] and forward_args:
            j = 0
            for i in range(len(command)):
                while spell["replace-str"] in command[i]:
                    command[i] = command[i].replace(spell["replace-str"], forward_args[j], 1)
                    j = min(j + 1, len(forward_args) - 1)
    # execute command
    if args.dry_run:
        print(colourStr("Command: ", "B") + shlex.join(command))
        return 0
    else:
        return subprocess.Popen(command).wait()


if __name__ == "__main__":
    sys.exit(main())
