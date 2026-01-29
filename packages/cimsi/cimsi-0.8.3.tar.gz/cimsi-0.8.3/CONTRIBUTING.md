# Contributing Guide

Welcome to `imsi`!

## Getting Started

- Fork the repository and create a branch from `main`.
- Install imsi locally by following the instructions in [`README.md`](README.md).
- Run the test suite to make sure everything tests as expected before you start your own development.

## Making Changes

- Make one branch per development feature.
- Following existing coding style (_we're improving as we go!_)
- Update and add tests.
- Update documentation.
- Use short descriptive commit messages by keeping the first line of commit messages under 50 characters, and add details when necessary.
   - Hint: Start the commit message with a verb or [conventional commit notation](https://www.conventionalcommits.org/).

## Merge Requests

For opening a new merge (pull) request:

1. Confirm that all tests pass locally first.
2. Ensure that there are no merge conflicts at the time the MR is submitted.
3. Ensure that CI pipelines pass.
4. Fill out the approriate merge request template completely.

### Checklist for Authors

- [ ] Tests pass locally.
- [ ] Tests are updated or added for the feature.
- [ ] Documentation is updated (docs, README, CLI help messages, in-line comments)
- [ ] Breaking changes are documented.
- [ ] Follow conventions for managing MRs:
    - [ ] Include **Closes** with the issue number on the MR ([hints here!]((https://docs.gitlab.com/user/project/issues/managing_issues/#closing-issues-automatically))).
    - [ ] Use the "**Draft:** " when the MR is still in progess, then remove it when it is ready to be **reviewed**.
- [ ] Tag the appropriate Reviewer(s)

### Checklist for Reviewers

Reviewers will:

- Mark the MR as "**approved**" upon review
- Defer to another reviewer where appropriate, including to help timeliness of reviews.
- Consider broader implications of CCCma software development, when appropriate.

Reviewers should:

- Provide clear, actionable feedback.
- Keep review focussed on the current MR, and open new Issues as needed.
- Ensure documentation is updated.
- Evaluate risks and backwards compatability.

#### Functional Reviewers

Functional Reviewers will:

- Be tagged for reviews relating to fixes, patches, and small feature development.

✅ Confirm that:

 - [ ] The change works as intended.
 - [ ] No existing workflows are broken.
 - [ ] Tests pass or have been updated.
 - [ ] Documentation, CLI, and/or config examples are updated (if relevant).

#### Integration Reviewers

Integration Reviewers will:

- Be tagged for reviews relating to large features and broader-scale development.
- Handle reversions that require deeper fixes beyond simple patching.
- Execute the merge upon review and approval.

✅ Confirm that:

 - [ ] The change is compatible with CCCma systems and operational pipelines.
 - [ ] Integration dependencies and environments are respected.
 - [ ] Broader model interactions have been considered.


## Creating an Issue

**Before you open an Issue**, search the issue tracker for similar entries. If you find an existing Issue is already open, upvote it or add context there is needed.

### Opening an Issue

- Open an Issue for bugs, requests, or documentation.
- Use the appropriate Issue template.
- Use the template to describe the Issue.
- Do not open an Issue for general disussion or support.

### Types of Issues

All Issues must be opened as one of the following types:

| Label   | Description |
|:--      | :--         |
| **bug** | Something is broken. |
| **enhancement** | Improvement to an existing feature. |
| **feature** | New additions or functionality. |
| **docs** | Standalone changes or additions to documentation. |

The Issue template you use will be pre-populated with one of these labels. **For Contributors, do not** add other labels to the Issue.
