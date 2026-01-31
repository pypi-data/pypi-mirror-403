# DPPS Calibration Pipeline

Welcome to `calibpipe` project. The project provides a selection of calibration tools
for CTA raw data calibration. For full details see [project documentation][calibpipe-doc].

## Installation

### Installation for users

Currently the package is under active development. First, create and activate a fresh conda environment:

```
mamba create -n calibpipe -c conda-forge python==3.12 ctapipe python-eccodes
mamba activate calibpipe
```
and then install `calibpipe` using `pip` and TestPyPI:

```
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ calibpipe
```

### Installation for developers

## Contributing

If you would like to contribute to this project please start from reading the [Contributing Guidelines][contributing].
Then you can configure the project locally for development as outlined in the [Development Instructions][developing], and start to contribute.
If you develop a new tool, don't forget to add a corresponding record to the `[project.scripts]` section of `pyproject.toml`

Enjoy!

[contributing]:http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/latest/development/index.html
[developing]:http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/latest/getting_started/index.html#development-setup
[calibpipe-doc]:http://cta-computing.gitlab-pages.cta-observatory.org/dpps/calibrationpipeline/calibpipe/latest/index.html
