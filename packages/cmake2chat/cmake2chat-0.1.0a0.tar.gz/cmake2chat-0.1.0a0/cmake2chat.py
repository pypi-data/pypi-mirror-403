# Copyright (c) 2026 Jifeng Wu
# Licensed under the MIT License. See LICENSE file in the project root for full license information.
import argparse
import codecs
import json
import os.path
import sys

from build_filesystem_trie import (
    build_filesystem_trie,
    iterate_relative_path_components_is_dir_tuples
)
from cowlist import COWList


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('path', help='Path to cmake project root')
    parser.add_argument('-o', '--output', default='-', help='Output JSON file (default: - for stdout)')
    parser.add_argument('--recurse-dotted', action='store_true', help='Include hidden files/directories')
    args = parser.parse_args()

    prefix, trie = build_filesystem_trie(args.path, recurse_dotted=args.recurse_dotted)

    cmake_files_json = [
        {'role': 'user', 'content': filesystem_trie_to_filesystem_tree_view(trie)}
    ]

    for (
        cmakelists_path_components,
        cmakelists_content
    ) in find_cmakelists_paths_and_contents(prefix, trie, COWList((trie.value,))):
        cmake_files_json.append(
            {'role': 'user', 'content': os.path.join(*cmakelists_path_components)}
        )
        cmake_files_json.append(
            {'role': 'user', 'content': cmakelists_content}
        )

    if args.output != '-':
        with codecs.open(args.output, 'w', encoding='utf-8') as f:
            json.dump(cmake_files_json, f, indent=2)
            f.write('\n')
    else:
        json.dump(cmake_files_json, sys.stdout, indent=2)
        sys.stdout.write('\n')


def filesystem_trie_to_filesystem_tree_view(
        filesystem_trie,
):
    # type: (...) -> str
    lines = []
    for relative_path_components, is_dir in iterate_relative_path_components_is_dir_tuples(
        filesystem_trie
    ):
        lines.append(
            '%s- %s%s' % (
                '  ' * (len(relative_path_components) - 1),
                relative_path_components[-1],
                '/' if is_dir else '',
            )
        )
    return '\n'.join(lines)


def find_cmakelists_paths_and_contents(prefix, trie, relative_path_components):
    """
    Yield (relative_path_components, file_contents) 
    for every CMakeLists.txt under prefix.
    relative_path_components is relative to prefix.
    """
    # If this is a file named CMakeLists.txt
    if trie.is_end and trie.value == 'CMakeLists.txt':
        path = os.path.join(*prefix.extend(relative_path_components))
        with codecs.open(path, 'r', encoding='utf-8') as f:
            yield relative_path_components, f.read()
    # If this is a directory, search children:
    elif trie.children:
        for child_name, child in trie.children.items():
            for _ in find_cmakelists_paths_and_contents(
                prefix,
                child,
                relative_path_components.append(child_name)
            ):
                yield _


if __name__ == '__main__':
    main()
