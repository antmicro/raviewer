FROM riscv64/ubuntu

RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install \
    cmake \
    file \
    gcc-riscv64-linux-gnu \
    git \
    libjpeg-dev \
    libssl-dev \
    python3 \
    python3-dev \
    python3-pip \
    zlib1g && \
    rm -rf /var/lib/apt/lists/*

COPY shared-dir /workspace

WORKDIR /workspace

RUN NO_GUI=1 pip wheel ./raviewer

RUN mkdir /output
