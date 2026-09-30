<p align="center">
    <a href="https://github.com/illinoisdata/bolo/blob/main/LICENSE"><img alt="License" src="https://img.shields.io/github/license/illinoisdata/bolo.svg?color=blue"></a>
    <a href="https://github.com/illinoisdata/bolo-templates/releases"><img alt="bolo-templates release" src="https://img.shields.io/github/v/release/illinoisdata/bolo-templates?include_prereleases&label=templates"></a>
    <a href="https://pypi.org/project/pybolo"><img alt="PyPI" src="https://img.shields.io/pypi/v/pybolo.svg"></a>
</p>

<p align="center">
  <img src="assets/logo.png" alt="bolo logo" width="180">
</p>

<h1 align="center">Bolo: Curated, Verified, and Ready-to-run Inference Pipelines for HuggingFace Models</h1>

**Bolo** gives you curated, verified, and ready-to-run inference pipelines for HuggingFace models: one call, no glue code.

## Install

```bash
pip install pybolo
```

Each model also needs its own dependencies, listed in its `requirements.txt`; see the **[website](http://www.bolobao.ai/)** for how to install them.

## Python API

```python
import bolo

bolo.fetch_templates()                                 # optional: pre-download the templates (otherwise fetched on first use)
bolo.list_params("<REPO_ID>")                          # show the template's parameters and defaults
result = bolo.pipeline("<REPO_ID>", device="cuda:0")   # run inference, overriding any parameter
```

## CLI

```bash
bolo fetch-templates               # optional: pre-download the templates (otherwise fetched on first use)
bolo run <REPO_ID> device=cuda:0   # run inference, parameters as KEY=VALUE
```

## Platforms
`bolo` is developed and tested on Red Hat Enterprise Linux machine equipped with NVIDIA A40 GPU, with CUDA version 13.0. 

## Contributing

Contributions are welcome! Please open an issue or pull request on [GitHub](https://github.com/illinoisdata/bolo/issues).

- Each issue must be labeled with a label.
- Every `bug` issue will only be closed when PyPI is updated.
- For `bug` issue, please refer to `tracker` issue for progress.
- For `TODO` issue, please refer to **Notion sprint** for progress (each `TODO` issue contains the specific sprint page).

## License

MIT — see [LICENSE](LICENSE) for details.

## Acknowledgement
- Thanks Jojo and her sister for designing the mascot.