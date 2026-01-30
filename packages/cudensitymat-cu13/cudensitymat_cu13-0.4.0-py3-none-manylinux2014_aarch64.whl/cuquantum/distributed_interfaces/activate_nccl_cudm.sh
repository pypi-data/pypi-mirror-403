#!/bin/bash

# Copyright (c) 2026-2026, NVIDIA CORPORATION & AFFILIATES
# SPDX-License-Identifier: BSD-3-Clause

# This script will build and activate the cuDensityMat NCCL interface.
# It requires the NVIDIA CUDA compiler (nvcc).
#
# Please check/set the following environment variables:
#  - $CUDA_PATH = Path to your CUDA installation directory.
#  - $NCCL_PATH = Path to your NCCL library installation directory.
#                 If your NCCL library is installed in system
#                 directories as opposed to its own (root) directory,
#                 ${NCCL_PATH}/include is expected to contain the 'nccl.h' header.
#                 ${NCCL_PATH}/lib or ${NCCL_PATH}/lib64 is expected to contain 'libnccl.so'.
#
# Run (inside the current directory): source ./activate_nccl_cudm.sh

# Libraries to be linked with your application (dynamically or statically):
#  libcudensitymat, libcutensor, libcublasLt, libnccl, libcudart, libdl

# This script exports an environment variable $CUDENSITYMAT_COMM_LIB (below).
# This environment variable is mandatory for enabling distributed execution.
# You should add it to your ~/.bashrc file. The NCCL functionality will not
# work if this environment variable is not set.

# Note: Unlike the MPI interface, NCCL requires:
#  1. A pre-initialized ncclComm_t communicator provided by the user
#  2. All data buffers to reside in GPU memory
#  3. NCCL does not use message tags (tags are ignored in send/recv)

if [ -z "${CUDA_PATH}" ]
then
    echo "Environment variable CUDA_PATH is not set: Please set it to point to the CUDA root directory!"
    return
fi

if [ -z "${NCCL_PATH}" ]
then
    echo "Environment variable NCCL_PATH is not set: Please set it to point to the NCCL root directory!"
    echo "Note that NCCL_PATH/include is expected to contain the nccl.h header file."
    return
fi

# Find NCCL library (handles pip packages that only have versioned .so.2)
NCCL_LIB=""
for libdir in "${NCCL_PATH}/lib64" "${NCCL_PATH}/lib"; do
    if [ -f "${libdir}/libnccl.so" ]; then
        NCCL_LIB="${libdir}/libnccl.so"
        break
    elif [ -f "${libdir}/libnccl.so.2" ]; then
        NCCL_LIB="${libdir}/libnccl.so.2"
        break
    fi
done

if [ -z "${NCCL_LIB}" ]; then
    echo "Could not find libnccl.so or libnccl.so.2 in ${NCCL_PATH}/lib or ${NCCL_PATH}/lib64"
    return
fi

echo "Using NCCL library: ${NCCL_LIB}"
NCCL_LIB_DIR=$(dirname "${NCCL_LIB}")

# Compile with nvcc for convenient CUDA runtime linking
# Use -Xlinker to pass the library path directly to the linker
nvcc -shared -Xcompiler -fPIC \
    -I${CUDA_PATH}/include -I../include -I${NCCL_PATH}/include \
    cudensitymat_distributed_interface_nccl.c \
    -Xlinker ${NCCL_LIB} \
    -L${CUDA_PATH}/lib64 -lcudart \
    -o libcudensitymat_distributed_interface_nccl.so

if [ $? -eq 0 ]; then
    export CUDENSITYMAT_COMM_LIB=${PWD}/libcudensitymat_distributed_interface_nccl.so
    echo "NCCL interface built successfully."
    echo "CUDENSITYMAT_COMM_LIB set to: ${CUDENSITYMAT_COMM_LIB}"
else
    echo "Failed to build NCCL interface."
fi

