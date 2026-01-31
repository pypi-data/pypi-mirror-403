## Down-sampled convolutions

![License](https://img.shields.io/badge/License-BSD_2-blue.svg)
[![Downloads](https://static.pepy.tech/badge/dsconv)](https://pepy.tech/project/dsconv)
[![Downloads](https://static.pepy.tech/badge/dsconv/month)](https://pepy.tech/project/dsconv)
[![PyPI version](https://badge.fury.io/py/dsconv.svg)](https://pypi.org/project/dsconv/)

This module provides a function to compute ``F`` down-sampled convolutions using ``Numba`` and demonstrates how to publish this package on PyPI using GitLab INRIA CI/CD.

Python with ``pip``
-------------------

This example demonstrates how to use GitLab INRIA CI/CD with the ``pip`` project manager.
Please, first [read](https://inria-ci.gitlabpages.inria.fr/doc/page/gitlab/) how to enable CI on your project.

It contains jobs to ensure the python project can be build, do unit testing with ``python3 -m unittest`` and generate the code coverage with ``coverage`` and eventually publish the package.

It also adds badges: coverage, version and downloads.

Source code
-----------

You can find a dummy function that computes the down-sampled convolution of an input signal ``x`` with a batch of filters ``filters`` in the script ``src/dsconv/dsconv.py``.
The documentation includes an example that will be tested using [doctest](https://docs.python.org/3/library/doctest.html) Python module.

Dockerfile
----------

The Dockerfile use Debian 13 image and install Numba, NumPy as-well-as SciPy in a Python virtual environment ``dsconv``.
It also installs Sphinx to build documentation.

```bash
# Create a virtual environment.
RUN mkdir /usr/local/venvs
RUN python3 -m venv /usr/local/venvs/dsconv
```

The ``.gitlab-ci.yml`` includes a stage to build the docker image and to store it.

```yaml
build_docker_img:
  stage: build_img
  image: docker:stable
  script:
    - docker build -t "$CI_REGISTRY_IMAGE/debian13_dsconv" .
    - docker login -u gitlab-ci-token -p "$CI_JOB_TOKEN" "$CI_REGISTRY"
    - docker push "$CI_REGISTRY_IMAGE/debian13_dsconv"
  tags:
    - ci.inria.fr
    - small
    - linux
```

The build of the docker image triggers when a new branch is pushed or if the ``Dockerfile`` has been modified.

```yaml
  # no build of docker image if specs haven't changed
  rules:
    - if: $CI_COMMIT_BRANCH
      changes:
        - Dockerfile
      when: always
```

This example uses ``small`` runner.
It could be ``medium`` or ``large`` too.

Run unittest
------------

Use the module [doctest](https://docs.python.org/3/library/doctest.html) to check the example.
Use [coverage](https://coverage.readthedocs.io/en/7.7.1/) to get a coverage of the tests.
At the end of the stage we ask to store the artifacts for only 30 days (see [How can I manage and reduce my disk space?](https://gitlab.inria.fr/siteadmin/doc/-/wikis/faq#how-can-i-manage-and-reduce-my-disk-space) for more details).
We extract part of the ``.gitlab-ci.yml`` file to highlight where to find the source code related to the tests:

```yaml
whl_test:
  stage: test
  image: "$CI_REGISTRY_IMAGE/debian13_dsconv"
  coverage: '/Coverage:.*\%/'
  script:
    - source /usr/local/venvs/dsconv/bin/activate
    # Matches version in whl_pkg_rev
    - python3 -m pip install --no-deps dist/dsconv-0.0.0+${CI_COMMIT_SHA}-py3-none-any.whl
    - DSCONV_DIR=$(dirname $(python3 -c "import dsconv as mm; print(mm.__file__)"))
    # Check doctest.
    - python3 -m doctest -v src/dsconv/dsconv.py
    - coverage run -a --source $DSCONV_DIR tests/test_dsconv.py
    - coverage report $(find $DSCONV_DIR -name src/dsconv/dsconv.py) | tee /tmp/dsconv_coverage_report
    - COV=$(sed -e '/^$/d' /tmp/dsconv_cov_report | tail -1 | sed -e 's/.*\s\+//')
    # Print coverage.
    - 'echo Coverage: $COV'
    # Export coverage as html.
    - coverage html $(find $DSCONV_DIR -name "*.py")
  artifacts:
    paths:
      - htmlcov
    when: always
    expire_in: 30 days
```

Verification of PEP8
--------------------

Use the package [pycodestyle](https://pypi.org/project/pycodestyle/) to check if your code satisfies [PEP8](https://peps.python.org/pep-0008/).
Do not verify PEP8 before tag.
You can find more details in the ``pre_pages`` stage of ``.gitlab-ci.yml`` file.

GitLab pages
------------

A small example of Sphinx documentation using "book theme" is available in the folder ``sphinx/source/``.
You have to install the following packages:

```bash
pip install sphinx
pip install myst_parser
pip install sphinx_autodoc_typehints
pip install sphinx_design
pip install sphinxcontrib_jquery
pip install sphinx_math_dollar
pip install sphinx_book_theme
```

``pre_pages`` stage of ``.gitlab-ci.yml`` builds the documentation and store it as an artifact.
You can find the artifacts in the ``build/Jobs`` section then ``pre_pages`` job and eventually clicking the browse button.

``pages`` stage of ``.gitlab-ci.yml`` builds the documentation only if ``tag`` and publish it on GitLab pages.

Of note, you can locally build the documentation:

```bash
cd sphinx
make clean
make html
```

PyPI publication
----------------

To learn more about PyPI publication of your own package please have a look to the [documentation](https://packaging.python.org/en/latest/).
Note that you have to [setup a PyPI token](https://pypi.org/help/#apitoken) and store it in ``Settings/CI/CD/Variables`` section of your GitLab project or you can use [Trusted Publishers](https://pypi.org/manage/account/publishing/).
Currently, only projects hosted on https://gitlab.com are supported. Self-managed instances are not supported.
We extract part of the ``.gitlab-ci.yml`` file to highlight where to find the source code related to the PyPI publication:

```yaml
pypi_pub:
  stage: pkg_pub
  image: "$CI_REGISTRY_IMAGE/debian13_dsconv"
  script:
    - TOKEN=$(echo $PYPI_TOKEN | base64 -d)
    - python3 -m twine upload -u __token__ -p $(echo $TOKEN) --verbose --non-interactive dsconv-${CI_COMMIT_TAG}-py3-none-any.whl
```

The package publication triggers when a new tag is created.

```yaml
  rules:
    - if: '$CI_COMMIT_TAG'
      when: always
```