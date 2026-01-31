FROM debian:13
WORKDIR app
COPY . .
RUN apt-get update
RUN apt-get -y install pip python3-full python3-dev
RUN apt-get autoremove
RUN apt-get clean
RUN apt-get autoclean
# Create a virtual environment.
RUN mkdir /usr/local/venvs
RUN python3 -m venv /usr/local/venvs/dsconv
# Install packages.
RUN /usr/local/venvs/dsconv/bin/pip install numba
RUN /usr/local/venvs/dsconv/bin/pip install numpy
RUN /usr/local/venvs/dsconv/bin/pip install build
RUN /usr/local/venvs/dsconv/bin/pip install twine
RUN /usr/local/venvs/dsconv/bin/pip install coverage
RUN /usr/local/venvs/dsconv/bin/pip install pycodestyle
RUN /usr/local/venvs/dsconv/bin/pip install hatchling
# Installation of sphinx
RUN /usr/local/venvs/dsconv/bin/pip install sphinx
RUN /usr/local/venvs/dsconv/bin/pip install myst_parser
RUN /usr/local/venvs/dsconv/bin/pip install sphinx_autodoc_typehints
RUN /usr/local/venvs/dsconv/bin/pip install sphinx_design
RUN /usr/local/venvs/dsconv/bin/pip install sphinxcontrib_jquery
RUN /usr/local/venvs/dsconv/bin/pip install sphinx_math_dollar
RUN /usr/local/venvs/dsconv/bin/pip install sphinx_book_theme
RUN /usr/local/venvs/dsconv/bin/pip cache purge