---
file_format: mystnb
kernelspec:
    name: python3

---
```{highlight} shell
```

# Installation

## Stable release

To install `qblox-scheduler` follow the {ref}`installation guide of quantify-core <quantify-core:installation>`.

## Update to the latest version

To update to the latest version

```console
$ pip install --upgrade qblox-scheduler
```

## From sources

The sources for `qblox-scheduler` can be downloaded from the [GitLab repo](https://gitlab.com/qblox/packages/software/qblox-scheduler).

You can clone the public repository:

```console
$ git clone git@gitlab.com:quantify-os/qblox-scheduler.git
$ # or if you prefer to use https:
$ # git clone https://gitlab.com/qblox/packages/software/qblox-scheduler.git/
```

Once you have a copy of the source, you can install it with:

```console
$ python -m pip install --upgrade .
```

## Setting up for local development

In order to develop the code locally, the package can be installed in the "editable mode" with the `-e` flag. `[dev]` optional requirement set will pull all (necessary and recommended) development requirements:

```console
$ python -m pip install -e ".[dev]"
```

Contributions are very welcome! To set up an environment for local development see the instructions in the {ref}`installation guide of quantify-core <quantify-core:installation>`. You only need to replace `quantify-core` with `qblox-scheduler` in the provided commands.

If you need any help reach out to us by [creating a new issue](https://gitlab.com/qblox/packages/software/qblox-scheduler/-/issues).

## Jupyter and Plotly

`qblox-scheduler` uses the [ploty] graphing framework for some components, which can require some additional set-up
to run with a Jupyter environment - please see [this page for details.]

[ploty]: https://plotly.com/
[this page for details.]: https://plotly.com/python/getting-started/
