#!/usr/bin/env python3

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import subprocess
import re
import sys
import os
print(sys.version_info)
if sys.version_info.major != 3 or sys.version_info.minor != 5:
    # Python 3.5 has issues with typing module
    from typing import List, Text, Union, IO, Any

if sys.version_info[0] == 3:
    DEVNULL = subprocess.DEVNULL  # type: Union[IO[Any], int]
else:
    # Python 2 doesn't have DEVNULL
    DEVNULL = open(os.devnull, 'wb')


OFFICIAL_REPO_URL_PREFIXES = [
    'https://github\\.com/onnx/',
    'git@github\\.com:onnx/',
    'https://github\\.com/caffe2/',
    'git@github\\.com:caffe2/',
]


def _contains(list, regex):  # type: (List[Text], Text) -> bool
    matches = [item for item in list if re.match(regex, item)]
    return len(matches) > 0


def _get_current_branch():  # type: () -> Text
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('UTF-8').strip()


def _remote_has_branch(remote, branch):  # type: (Text, Text) -> bool
    output = subprocess.check_output(['git', 'ls-remote', '--heads', remote, branch]).decode('UTF-8').strip()
    return output != ''


def _local_has_branch(branch):  # type: (Text) -> bool
    try:
        subprocess.check_call(['git', 'rev-parse', '--verify', branch], stdout=DEVNULL, stderr=DEVNULL)  # type: ignore
        return True
    except subprocess.CalledProcessError:
        return False


def _exec(commands):  # type: (List[List[Text]]) -> None
    print("# Will run command sequence:")
    for command in commands:
        print("# $> %s" % " ".join(command))
    print()
    print('-----------------------------------------------------------')
    print('Off we go...')
    print('-----------------------------------------------------------')
    for i in range(len(commands)):
        command = commands[i]
        print("$> %s" % " ".join(command))
        try:
            subprocess.check_call(command)
            print()
        except subprocess.CalledProcessError:
            print()
            print('-----------------------------------------------------------')
            print("This command failed:")
            print("$> %s" % " ".join(command))
            print()
            if (i == len(commands)-1):
                print("Please fix it and rerun it, then the action is finished.")
            else:
                print("Please fix, rerun it, and then, to finish the action, run:")
                for j in range(i + 1, len(commands)):
                    print("$> %s" % " ".join(commands[j]))
            print('-----------------------------------------------------------')
            exit(1)


def _error(message):  # type: (Text) -> None
    print("Error: %s" % message)
    exit(1)


def _check(condition, message):  # type: (bool, Text) -> None
    if not condition:
        _error(message)


class GitFeatureApp(object):
    def __init__(self):  # type: () -> None
        self._actions = {
            'create': self._create_feature_action,
            'rebase': self._rebase_feature_action,
            'push': self._push_feature_action,
            'remove': self._remove_feature_action,
        }
        self._parse_args()

    def _parse_args(self):  # type: () -> None
        parser = argparse.ArgumentParser(description="Create, rebase and delete git feature branches.",
            formatter_class=argparse.RawTextHelpFormatter,
            epilog=
            "Examples:\n" +
            "  $> git-feature create myfeature   # Creates and checks out new feature 'myfeature'\n" +
            "  $> git-feature rebase myfeature   # Rebases 'myfeature' on top of current upstream/master\n" +
            "  $> git-feature push myfeature     # Pushes 'myfeature' to origin for creation of a pull request\n" +
            "  $> git-feature remove myfeature   # Removes 'myfeature' from local and 'origin' remote\n")
        parser.add_argument('action', choices=self._actions.keys())
        parser.add_argument('feature_name', type=str)
        args = parser.parse_args()
        assert args.action in self._actions.keys()
        self._action = self._actions[args.action]
        self._feature_name = args.feature_name

    def run(self):  # type: () -> None
        self._repo_setup_checks()
        self._action()

    def _repo_setup_checks(self):  # type: () -> None
        remotes = subprocess.check_output(['git', 'remote', '-v']).decode('UTF-8').split('\n')
        _check(any(
            [_contains(remotes, "upstream\t%s[a-zA-Z0-9\\-]+(\\.git)? \\(fetch\\)\s*$" % url_prefix) for url_prefix in OFFICIAL_REPO_URL_PREFIXES]
        ), "Remote repository 'upstream' not setup correctly (fetch)")
        _check(any(
            [_contains(remotes, "upstream\t%s[a-zA-Z0-9\\-]+(\\.git)? \\(push\\)\s*$" % url_prefix) for url_prefix in OFFICIAL_REPO_URL_PREFIXES]
        ), "Remote repository 'upstream' not setup correctly (push)")
        _check(_contains(remotes, "origin\thttps://github\\.com/[a-zA-Z0-9\\-]+/[a-zA-Z0-9\\-]+(\\.git)? \\(fetch\\)\s*$") or
               _contains(remotes, "origin\tgit@github\\.com:[a-zA-Z0-9\\-]+/[a-zA-Z0-9\\-]+(\\.git)? \\(fetch\\)\s*$"),
               "Remote repository 'origin' not setup correctly (fetch)")
        _check(_contains(remotes, "origin\thttps://github\\.com/[a-zA-Z0-9\\-]+/[a-zA-Z0-9\\-]+(\\.git)? \\(push\\)\s*$") or
               _contains(remotes, "origin\tgit@github\\.com:[a-zA-Z0-9\\-]+/[a-zA-Z0-9\\-]+(\\.git)? \\(push\\)\s*$"),
               "Remote repository 'origin' not setup correctly (push)")
        _check(not any(
            [_contains(remotes, "origin\t%s[a-zA-Z0-9\\-]+(\\.git)? \\(fetch\\)\s*$" % url_prefix) for url_prefix in OFFICIAL_REPO_URL_PREFIXES]
        ), "Remote repository 'origin' points to official repository. Please point it to your own fork.")

    def _create_feature_action(self):  # type: () -> None
        print('-----------------------------------------------------------')
        print("Creating feature %s" % self._feature_name)
        print('-----------------------------------------------------------')
        _exec([
            ['git', 'fetch', 'upstream'],
            ['git', 'checkout', '-b', self._feature_name, 'upstream/master', '--no-track'],
            ['git', 'submodule', 'update', '--init', '--recursive'],
            ['git', 'push', '--set-upstream', 'origin', self._feature_name],
        ])

    def _rebase_feature_action(self):  # type: () -> None
        print('-----------------------------------------------------------')
        print("Rebasing feature %s on top of upstream/master" % self._feature_name)
        print('-----------------------------------------------------------')
        _exec([
            ['git', 'fetch', 'upstream'],
            ['git', 'checkout', self._feature_name],
            ['git', 'rebase', 'upstream/master'],
            ['git', 'submodule', 'update', '--init', '--recursive'],
        ])

    def _remove_feature_action(self):  # type: () -> None
        print('-----------------------------------------------------------')
        print("Removing feature %s" % self._feature_name)
        print('-----------------------------------------------------------')
        commands = []
        if _get_current_branch() == self._feature_name:
            commands.append(['git', 'checkout', 'upstream/master'])
        if _local_has_branch(self._feature_name):
            commands.append(['git', 'branch', '-d', self._feature_name])
        if _remote_has_branch('origin', self._feature_name):
            commands.append(['git', 'push', 'origin', ':%s' % self._feature_name])
        if len(commands) == 0:
            _error("Branch '%s' not found, neither in local repository nor in 'origin' remote" % self._feature_name)
        _exec(commands)

    def _push_feature_action(self):  # type: () -> None
        print('-----------------------------------------------------------')
        print("Pushing feature %s to origin" % self._feature_name)
        print('-----------------------------------------------------------')
        _exec([
            ['git', 'push', '--set-upstream', 'origin', self._feature_name],
        ])


def main():  # type: () -> None
    app = GitFeatureApp()
    app.run()

if __name__ == '__main__':
    main()
