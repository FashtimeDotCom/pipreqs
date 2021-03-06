#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""pipreqs - Generate pip requirements.txt file based on imports

Usage:
    pipreqs <path>
    pipreqs <path>[options]

Options:
    --debug  prints debug information.
    --savepath path to requirements.txt (Optional)
"""
from __future__ import print_function
import os
import sys
import re
import logging

from docopt import docopt
import yarg
from yarg.exceptions import HTTPError


REGEXP = [
    re.compile(r'^import (.+)$'),
    re.compile(r'from (.*?) import (?:.*)')
]


def get_all_imports(start_path):
    imports = []
    packages = []
    logging.debug('Traversing tree, start: %s', start_path)
    for root, dirs, files in os.walk(start_path):
        packages.append(os.path.basename(root))
        files = [fn for fn in files if os.path.splitext(fn)[1] == ".py"]
        packages += [os.path.splitext(fn)[0] for fn in files]
        for file_name in files:
            with open(os.path.join(root, file_name), "r") as file_object:
                lines = filter(lambda l:len(l) > 0, map(lambda l:l.strip(), file_object))
                for line in lines:
                    if line[0] == "#":
                        continue
                    if "(" in line:
                        break
                    for rex in REGEXP:
                        s = rex.match(line)
                        if not s:
                            continue
                        for item in s.groups():
                            if "," in item:
                                for match in item.split(","):
                                    imports.append(match.strip())
                            else:
                                to_append = item.partition(' as ')[0].partition('.')[0]
                                imports.append(to_append.strip())
    third_party_packages = set(imports) - set(set(packages) & set(imports))
    logging.debug('Found third-party packages: %s', third_party_packages)
    with open(os.path.join(os.path.dirname(__file__), "stdlib"), "r") as f:
        data = [x.strip() for x in f.readlines()]
        return list(set(third_party_packages) - set(data))


def generate_requirements_file(path, imports):
    with open(path, "w") as out_file:
        logging.debug('Writing %d requirements to file %s', (len(imports), path))
        fmt = '{name} == {version}'
        out_file.write('\n'.join(fmt.format(**item) for item in imports) + '\n')


def get_imports_info(imports):
    result = []
    for item in imports:
        try:
            data = yarg.get(item)
        except HTTPError:
            logging.debug('Package does not exist or network problems')
            continue
        if not data or not data.release_ids:
            continue
        last_release = data.release_ids[-1]
        result.append({'name': item, 'version': last_release})
    return result


def init(args):
    print("Looking for imports")
    imports = get_all_imports(args['<path>'])
    print("Getting latest version of packages information from PyPi")
    imports_with_info = get_imports_info(imports)
    print("Found third-party imports: " + ", ".join(imports))
    path = args["--savepath"] if args["--savepath"] else os.path.join(args['<path>'], "requirements.txt")
    generate_requirements_file(path, imports_with_info)
    print("Successfuly saved requirements file in: " + path)


def main():  # pragma: no cover
    args = docopt(__doc__, version='xstat 0.1')
    log_level = logging.DEBUG if args['--debug'] else logging.WARNING
    logging.basicConfig(level=log_level, format='%(levelname)s: %(message)s')

    try:
        init(args)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == '__main__':
    main()  # pragma: no cover
