# Dockerfile for building PyPI-compatible manylinux wheels
# Uses manylinux_2_28_x86_64 (glibc 2.28) which covers CentOS 8+ and Ubuntu 20.04+
# Reference: https://peps.python.org/pep-0599/

FROM quay.io/pypa/manylinux_2_28_x86_64:latest

# Install additional build tools (including auditwheel which is already in manylinux)
RUN yum install -y \
    cmake \
    git \
    ca-certificates \
    && yum clean all

WORKDIR /build

# Copy project
COPY . /build/

# Copy build script
COPY build_wheels.sh /build_wheels.sh
RUN chmod +x /build_wheels.sh

# Build wheels for each Python version with proper manylinux tagging
RUN /build_wheels.sh

VOLUME /build/dist
CMD ["/bin/bash"]
