# Install and add to your Oasis

This guide provides step-by-step instructions for installing and using the plugin on a [NOMAD Oasis](https://nomad-lab.eu/prod/v1/docs/reference/glossary.html#deployment-nomad-oasis).

## Installation


Install the plugin in your local environment directly from PyPI:

```sh
pip install nomad-analysis
```

If you are using [uv](https://github.com/astral-sh/uv) (recommended) to manage your Python environments, you can install the plugin with:

```sh
uv pip install nomad-analysis
```

## Adding to your Oasis

The plugin is designed to be used within an [Oasis](https://nomad-lab.eu/prod/v1/docs/reference/glossary.html#deployment-nomad-oasis) instance. To add the plugin to your Oasis, follow these steps:

### Update your Oasis configuration

Oasis is usually built with a [distribution repository](https://nomad-lab.eu/prod/v1/docs/reference/glossary.html#distribution-distro).
You can create one for yourself using our [distribution template](https://github.com/FAIRmat-NFDI/nomad-distro-template). To add the plugin to your Oasis, simply update the distribution's dependency
in the `pyproject.toml` file:

```toml
# pyproject.toml
[project.optional-dependencies]
plugins = [
  ...,
  "nomad-analysis",
]
```

### Configure the plugin (optional)

You can configure the plugin by updating the `nomad.yaml` of your distribution. For example, exclusively include only one entry point from the plugin by:

```yaml
plugins:
  entry_points:
    include:
      - 'nomad_analysis.jupyter:schema_entry_point'
    # Or exclude specific entry points:
    # exclude:
    #   - 'nomad_analysis.actions:action_entry_point'
```

By default, all entry points from the plugin are included, so this step is optional. You can find all available entry points under [Reference > Entry Points](../reference/entry_points.md).

### Rebuild and deploy

Rebuild your Oasis Docker image and redeploy:

```sh
docker compose build
docker compose up -d
```

Read the [NOMAD plugin documentation](https://nomad-lab.eu/prod/v1/docs/howto/oasis/configure.html#plugins)
for all details on how to deploy plugins on your NOMAD instance. If you want to get started with a new Oasis,
start [here](https://nomad-lab.eu/prod/v1/docs/howto/oasis/install.html#how-to-install-a-nomad-oasis).
