FROM riscv64/ubuntu AS builder

RUN apt-get update -qq && \
    DEBIAN_FRONTEND=noninteractive apt-get -y install --no-install-recommends \
    ca-certificates \
    cmake \
    file \
    g++-riscv64-linux-gnu \
    git \
    libjpeg-dev \
    libssl-dev \
    make \
    python3 \
    python3-dev \
    python3-pip \
    zlib1g && \
    apt-get autoclean && apt-get clean && apt-get autoremove -y && \
    update-ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY shared-dir /shared-dir

WORKDIR /shared-dir

RUN mkdir /tmp/deps && \
    NO_GUI=1 pip wheel --wheel-dir /tmp/deps ./raviewer


FROM alpine:latest

COPY --from=builder /tmp/deps /deps
