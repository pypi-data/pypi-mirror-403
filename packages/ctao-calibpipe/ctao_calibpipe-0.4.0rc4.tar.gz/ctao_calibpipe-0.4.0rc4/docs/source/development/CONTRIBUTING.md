# Contributing to DPPS CalibPipe

As main contributors are affiliated with the University of Geneva, we respect its [Code of Conduct][coc] and ask you to do the same.

## Questions, Bugs, Features

### Found an Issue or Bug?

If you find a bug in the source code, you can help us by submitting a Bug Report to our [GitLab Repository][gitlab-issues]. Even better, you can submit a Merge Request with a fix.

### Missing a Feature?

You can request a new feature by submitting an issue to our [GitLab Repository][gitlab-issues]. If you would like to implement a new feature, it should be discussed first in a [GitLab issue][gitlab-issues] that clearly outlines the changes and benefits of the feature.

### Want a Doc Fix?

If you have a suggestion for the documentation, you can open an issue and outline the problem or improvement you have. Creating the doc fix yourself is even better! For large fixes, please build and test the documentation before submitting the PR to ensure you haven't introduced any layout or formatting issues. Make sure your commit message follows the [Commit Message Guidelines][developers-commits].

## Issue Submission Guidelines

Before you submit your issue, search the archive to see if your question was already answered. If your issue appears to be a bug and hasn't been reported, open a new issue. Help us maximize the effort we can spend fixing issues and adding new features by not reporting duplicate issues.

The "[new issue][gitlab-new-issue]" form contains a number of predefined templates under the **Description** drop-down. Please select the relevant issue template and fill it out to simplify the understanding and proper treatment of the issue. Please add one of the following labels to your issue: `bug`, `suggestion`, `enhancement`, `discussion`, `documentation`, `question`. Do not add other labels or assign developers; this will be done by the project management.

## Merge Request Submission Guidelines

Before you submit your merge request, consider the following guidelines:

1. Search [GitLab][gitlab-merge-requests] for an open or closed Merge Request that relates to your submission to avoid duplicating effort.
<!-- 2. Create the [development environment](../getting_started/index.rst#development_setup). -->
2. Create the development environment following the instructions in {ref}`development_setup`.
3. Make your changes in a new git branch:
    ```shell
    git checkout -b my-fix-branch main
    ```
    - You do not need to fork the repository; instead, create a new branch in the central repository.
    - The branch name should follow the regular expression `(feature|bugfix|cleanup)/*` and be meaningful.
4. Create your patch commit, including appropriate test cases.
    - If it's your first commit in this repository, add yourself to the `AUTHORS` file.
5. Follow our Code Style Guidelines (they are enforced by the precommit hooks, don't forget to install them!):
    - [PEP8][pep8] standard for python code.
    - [numpydoc][numpydoc] for the documentation.
6. If the changes affect public APIs, change or add relevant documentation.
7. Commit your changes using a descriptive commit message that follows our [commit message conventions][developers-commits].
    ```shell
    git add <list of files you have modified>
    git commit
    ```
    Note: Do not add binary files, libraries, build artifacts, etc., to your commit.
8. Push your branch to GitLab:
    ```shell
    git push origin my-fix-branch
    ```
9. Test your code following the testing instructions.
10. In GitLab, open a merge request to `calibPipe:main` and fill out the merge request template.
11. If we suggest changes:
    - Make the required updates.
    - Re-run all applicable tests.
    - Commit your changes to your branch (e.g., `my-fix-branch`).
    - Push the updated branch to the GitLab repository (this will update your Merge Request).
    - You can also amend the initial commits and force push them to the branch:
        ```shell
        git rebase main -i
        git push origin my-fix-branch -f
        ```

## After Your Merge Request is Merged

After your merge request is merged, the branch you created will be automatically deleted from the central repository.

1. Check out the main branch:
    ```shell
    git checkout main -f
    ```
2. Delete the local branch:
    ```shell
    git branch -D my-fix-branch
    ```
3. Update your main with the latest upstream version:
    ```shell
    git pull --ff origin main
    ```

[coc]: https://www.unige.ch/ethique/charter/
[gitlab]: https://gitlab.cta-observatory.org/cta-computing/dpps/calibrationpipeline/calibpipe
[gitlab-issues]: https://gitlab.cta-observatory.org/cta-computing/dpps/calibrationpipeline/calibpipe/-/issues
[gitlab-merge-requests]: https://gitlab.cta-observatory.org/cta-computing/dpps/calibrationpipeline/calibpipe/-/merge_requests
[developers-commits]: https://chris.beams.io/posts/git-commit/
[gitlab-new-issue]: https://gitlab.cta-observatory.org/cta-computing/dpps/calibrationpipeline/calibpipe/-/issues/new
[pep8]: https://www.python.org/dev/peps/pep-0008/
[numpydoc]: https://numpydoc.readthedocs.io/en/latest/
