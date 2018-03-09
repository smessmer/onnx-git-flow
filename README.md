Simplify feature branch workflows for onnx and caffe2 repositories.

# Install

Just do:

    $ pip install .

or

    $ pip install -e .

if you want to get updates.

# Usage

Create and check out new feature 'myfeature'

    $> git-feature create myfeature

Rebase 'myfeature' on top of current upstream/master

    $> git-feature rebase myfeature

Push 'myfeature' to origin for creation of a pull request

    $> git-feature push myfeature

Remove 'myfeature' from local and 'origin' remote

    $> git-feature remove myfeature
