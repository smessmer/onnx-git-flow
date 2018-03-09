Simplify feature branch workflows for onnx and caffe2 repositories.

# Install

Just do:

    $ pip install .

or

    $ pip install -e .

if you want to get updates.

# Usage:

    # Creates and checks out new feature 'myfeature'
    $> git-feature create myfeature
    # Rebases 'myfeature' on top of current upstream/master  
    $> git-feature rebase myfeature
    # Pushes 'myfeature' to origin for creation of a pull request
    $> git-feature push myfeature
    # Removes 'myfeature' from local and 'origin' remote
    $> git-feature remove myfeature
