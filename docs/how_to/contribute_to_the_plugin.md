# Contribute to the Plugin

Easiest way to contribute to the code or documentation is to create [GitHub Issues](https://github.com/FAIRmat-NFDI/nomad-analysis/issues)
for any problems
you encounter or improvements you suggest while using the plugin. This way,
maintainers can triage and address them in a timely manner.

If you want to directly contribute to the development, you can work on your
changes locally and create a Pull Request to submit them on the GitHub
repository. The following sections explains how to set up a development
environment and use it to develop the code and documentation locally.

## Code Contribution

### Using a minimal dev environment

To get started with local development in a minimal environment, clone the
repository and setup a virtual Python environment:

```sh
git clone https://github.com/FAIRmat-NFDI/nomad-analysis.git
cd nomad-analysis
python3.12 -m venv .pyenv
source .pyenv/bin/activate
```

Finally, install the package in editable mode with development dependencies:

```sh
pip install -e '.[dev]'
```

### Using the Dev Distro

If you're working within the [NOMAD development distro](https://github.com/FAIRmat-NFDI/dev_distro), you can set up the plugin for development as part of the entire distribution. This allows you to test your changes in an environment that closely mimics production.

To do this, follow the instructions in the distribution's README to set up the
development environment. The plugin is included as a submodule in editable
mode, so any changes you make to the plugin's code will be reflected when you
run the distribution's services.

In short, the steps are:

```sh
# Add the plugin as a submodule
git submodule add https://github.com/FAIRmat-NFDI/nomad-analysis.git packages/nomad-analysis

# Add the plugin to the distribution's dependencies in pyproject.toml
uv add packages/nomad-analysis

# Set up and run the development server
uv run poe setup
uv run poe start
```

### Running Tests

When developing, you can run the plugin's tests locally to ensure your changes don't break existing functionality:

```sh
uv run pytest -sv tests
```

| Flag | Description |
|------|-------------|
| `-s` | Show print statements and stdout |
| `-v` | Verbose output with test names |


### Linting and Formatting

We use [Ruff](https://docs.astral.sh/ruff/) for code formatting and linting.
You can run it locally to ensure your code adheres to the style guidelines:

```sh
# Check for formatting issues
uv run ruff format . --check
# Check for linting issues
uv run ruff check .
```

Formatting and some linting issues can be automatically fixed by running:
```sh
uv run ruff format .
uv run ruff check . --fix
```

Once you've made your changes and ensured that tests pass and code is properly
formatted, you can [create a Pull Request](#creating-a-pull-request) to submit
your contributions.

## Documentation Contribution

You can also use the development environment (see above) to work on the documentation. The documentation is built using [MkDocs](https://www.mkdocs.org/) and can be served locally for previewing changes.

To

### Running the Documentation Server Locally

To preview documentation changes locally, run the MkDocs development server:

```sh
uv run mkdocs serve
```

The documentation is usually served locally at [http://127.0.0.1:8000/](http://127.0.0.1:8000/).


### Documentation Structure

```
docs/
├── index.md                    # Homepage
├── tutorial/                   # Learning-oriented guides
├── how_to/                     # Task-oriented guides
├── explanation/                # Understanding-oriented content
└── reference/                  # Information-oriented content
    ├── schemas/                # Schema documentation (auto-generated)
    └── glossary.md             # Terms and definitions
```

### Documentation PR Previews

Once you've made changes to the documentation locally, you can [create a Pull Request](#creating-a-pull-request) to submit your contributions. For documentation changes, a preview is automatically deployed. Look
for a comment by **github-actions** bot on your PR with the preview URL.


## Creating a Pull Request (PR)

In your local clone, create a new branch for your feature or fix:

  ```sh
  git checkout -b feature/my-new-feature
  ```

!!! tip "Forking the repository"
    If you don't have write access to the main repository, fork it first and clone your fork locally. Then create a branch in your fork. Check out the [GitHub documentation](https://docs.github.com/en/get-started/quickstart/fork-a-repo) for detailed instructions on forking.

Make your changes and ensure tests pass:
```sh
uv run pytest -sv tests
uv run ruff check .
uv run ruff format . --check
```

Commit your changes:
```sh
git add .
git commit -m "feat: add my new feature"
```

Push to your branch on GitHub:
```sh
git push origin feature/my-new-feature
```

Open a Pull Request on GitHub:

- Go to the [`nomad-analysis`
](https://github.com/FAIRmat-NFDI/nomad-analysis) repository on GitHub
- Toggle to the "Pull requests" tab and click "New pull request"
- Select your branch as the source and the `develop` branch of the repository as the target.
- Fill in the PR description with details about your changes
- Request reviews from maintainers
- Address review feedback and ensure CI checks pass.

!!! tip "PR from clones and forks"
    Check the GitHub documentation for detailed instructions on creating a pull request for [clones](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request) and [forks](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/proposing-changes-to-your-work-with-pull-requests/creating-a-pull-request-from-a-fork).

Once your PR is approved and CI checks pass, it will be merged into the
`develop` branch and eventually released in a future version of the plugin.
