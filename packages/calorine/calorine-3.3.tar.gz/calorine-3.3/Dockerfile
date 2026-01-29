# Base image
FROM nvidia/cuda:12.9.1-devel-ubuntu24.04

# Base packages
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    TZ=Europe/Gothenburg

# OS deps (graphviz+pandoc). Use --no-install-recommends and clean the lists.
RUN echo python3 --version
RUN \
  apt-get update && \
  apt-get install -y --no-install-recommends \
    git \
    graphviz \
    pandoc \
    python3-pip \
    python3-dev \
    zip && \
  rm -rf /var/lib/apt/lists/*

# One layer, no cache kept
RUN pip3 install --no-cache-dir --break-system-packages \
    build \
    coverage \
    flake8 \
    flake8-quotes \
    pytest \
    setuptools \
    setuptools_scm \
    twine \
    xdoctest \
    \
    sphinx \
    sphinx_autodoc_typehints \
    sphinx-rtd-theme \
    pydata-sphinx-theme \
    sphinx_sitemap \
    sphinxcontrib-bibtex \
    sphinx-design \
    nbsphinx \
    nbmake \
    \
    ase \
    numpy \
    pandas \
    pybind11 \
    scikit-learn \
    tqdm \
    torch \
    \
    dynasor \
    euphonic \
    hiphive \
    matplotlib \
    phonopy \
    seekpath

# Install resINS for the INS tutorial notebook
RUN pip3 install --no-cache-dir --break-system-packages git+https://github.com/pace-neutrons/resins.git

# Install GPUMD
RUN \
  git clone https://github.com/brucefan1983/GPUMD.git && \
  cd GPUMD && \
  git checkout v4.7 && \
  cd src && \
  make CFLAGS="-std=c++14 -O3 -arch=sm_72 -DDEBUG" -j4 && \
  mv gpumd nep /usr/local/bin/ && \
  cd ../.. && \
  rm -fr GPUMD

CMD ["/bin/bash"]
