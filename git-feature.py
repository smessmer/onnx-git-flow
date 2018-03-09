#!/usr/bin/env python3

import argparse
import subprocess
import re
from typing import List


def _contains(list: List[str], regex: str) -> bool:
    matches = [item for item in list if re.match(regex, item)]
    return len(matches) > 0


def _get_current_branch() -> str:
    return subprocess.check_output(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).decode('UTF-8').strip()


def _remote_has_branch(remote: str, branch: str) -> bool:
    output = subprocess.check_output(['git', 'ls-remote', '--heads', remote, branch]).decode('UTF-8').strip()
    return output != ''


def _local_has_branch(branch: str) -> bool:
    try:
        subprocess.check_call(['git', 'rev-parse', '--verify', branch], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


def _exec(commands: List[List[str]]) -> None:
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


def _error(message: str) -> None:
    print("Error: %s" % message)
    exit(1)


def _check(condition, message) -> None:
    if not condition:
        _error(message)


class GitFeatureApp(object):
    def __init__(self) -> None:
        self._actions = {
            'create': self._create_feature_action,
            'rebase': self._rebase_feature_action,
            'push': self._push_feature_action,
            'remove': self._remove_feature_action,
        }
        self._parse_args()

    def _parse_args(self) -> None:
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

    def run(self) -> None:
        self._repo_setup_checks()
        self._action()

    def _repo_setup_checks(self) -> None:
        remotes = subprocess.check_output(['git', 'remote', '-v']).decode('UTF-8').split('\n')
        _check(_contains(remotes, "upstream\thttps://github\\.com/onnx/onnx(\\.git)? \\(fetch\\)\s*$") or
                 _contains(remotes, "upstream\tgit@github\\.com:onnx/onnx(\\.git)? \\(fetch\\)\s*$"),
               "Remote repository 'upstream' not setup correctly")
        _check(_contains(remotes, "upstream\thttps://github\\.com/onnx/onnx(\\.git)? \\(push\\)\s*$") or
               _contains(remotes, "upstream\tgit@github\\.com:onnx/onnx(\\.git)? \\(push\\)\s*$"),
               "Remote repository 'upstream' not setup correctly")
        _check(_contains(remotes, "origin\thttps://github\\.com/[a-zA-Z\\-]+/onnx(\\.git)? \\(fetch\\)\s*$") or
               _contains(remotes, "origin\tgit@github\\.com:[a-zA-Z\\-]+/onnx(\\.git)? \\(fetch\\)\s*$"),
               "Remote repository 'origin' not setup correctly")
        _check(_contains(remotes, "origin\thttps://github\\.com/[a-zA-Z\\-]+/onnx(\\.git)? \\(push\\)\s*$") or
               _contains(remotes, "origin\tgit@github\\.com:[a-zA-Z\\-]+/onnx(\\.git)? \\(push\\)\s*$"),
               "Remote repository 'origin' not setup correctly")

    def _create_feature_action(self) -> None:
        print('-----------------------------------------------------------')
        print("Creating feature %s" % self._feature_name)
        print('-----------------------------------------------------------')
        _exec([
            ['git', 'fetch', 'upstream'],
            ['git', 'checkout', '-b', self._feature_name, 'upstream/master', '--no-track'],
            ['git', 'submodule', 'update', '--init', '--recursive'],
            ['git', 'push', '--set-upstream', 'origin', self._feature_name],
        ])

    def _rebase_feature_action(self) -> None:
        print('-----------------------------------------------------------')
        print("Rebasing feature %s on top of upstream/master" % self._feature_name)
        print('-----------------------------------------------------------')
        _exec([
            ['git', 'fetch', 'upstream'],
            ['git', 'checkout', self._feature_name],
            ['git', 'rebase', 'upstream/master'],
            ['git', 'submodule', '--init', '--recursive'],
        ])

    def _remove_feature_action(self) -> None:
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

    def _push_feature_action(self) -> None:
        print('-----------------------------------------------------------')
        print("Pushing feature %s to origin" % self._feature_name)
        print('-----------------------------------------------------------')
        _exec([
            ['git', 'push', '--set-upstream', 'origin', self._feature_name],
        ])


def main() -> None:
    app = GitFeatureApp()
    app.run()

if __name__ == '__main__':
    main()
