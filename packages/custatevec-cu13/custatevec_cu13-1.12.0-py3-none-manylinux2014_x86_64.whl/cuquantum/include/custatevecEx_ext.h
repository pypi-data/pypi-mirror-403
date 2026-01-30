/*
 * SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights
 * reserved. SPDX-License-Identifier: LicenseRef-NvidiaProprietary
 *
 * NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
 * property and proprietary rights in and to this material, related
 * documentation and any modifications thereto. Any use, reproduction,
 * disclosure or distribution of this material and related documentation
 * without an express license agreement from NVIDIA CORPORATION or
 * its affiliates is strictly prohibited.
 */

/** @file custatevecEx_ext.h
 *  @details cuStateVecEx extension header file
 */

/*
 * NOTE: This is an extension interface header for implementing custom communicators.
 * The declarations and definitions in this header are in a preliminary version and are
 * subject to change.
 */

#pragma once

#include <custatevecEx.h>

#if defined(__cplusplus)
#include <cstdint>                                // integer types

extern "C"
{

#else
#include <stdint.h>                               // integer types

#endif


/*
 * Extension struct
 */

typedef struct custatevecExCommunicator_t custatevecExCommunicator_t;
typedef struct custatevecExCommunicatorModule_t custatevecExCommunicatorModule_t;
typedef struct custatevecExCommunicatorInterface_t custatevecExCommunicatorInterface_t;

/*
 * Extension methods
 */

/*
 * Communicator module function pointers (IPC module lifecycle management)
 */

/** Get library version */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnGetVersion)(
        int32_t* major, int32_t* minor);

/** Initialize IPC library (e.g., MPI_Init) */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnInit)(
        void* moduleHandle, int *argc, char ***argv);

/** Check if IPC library is initialized (e.g., MPI_Initialized) */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnInitialized)(
        void* moduleHandle, int* flag);

/** Finalize IPC library (e.g., MPI_Finalize) */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnFinalize)(void* moduleHandle);

/** Check if IPC library is finalized (e.g., MPI_Finalized) */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnFinalized)(void* moduleHandle, int* flag);

/** Retrieve the number of processes and the rank of the current process */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnGetSizeAndRank)(void* moduleHandle, int32_t* size, int32_t* rank);

/** Create a communicator instance */
typedef custatevecExCommunicator_t* (*custatevecExCommunicator_FnCreateCommunicator)(void* moduleHandle);

/** Destroy communicator instance */
typedef void (*custatevecExCommunicator_FnDestroyCommunicator)(void* moduleHandle, custatevecExCommunicator_t* exCommunicator);

/*
 * Instance function pointers
 */

/* Abort */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnAbort)(custatevecExCommunicator_t* exCommunicator, int status);

/* GetCommSize */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnGetSize)(
        custatevecExCommunicator_t* exCommunicator, int* size);
/* GetCommRank */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnGetRank)(
        custatevecExCommunicator_t* exCommunicator, int* rank);
/* Barrier */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnBarrier)(custatevecExCommunicator_t* exCommunicator);
/* Broadcast */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnBcast)(
        custatevecExCommunicator_t* exCommunicator, void* buffer, int count, cudaDataType_t dataType, int root);
/* Allreduce */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnAllreduce)(
        custatevecExCommunicator_t* exCommunicator, const void* sendbuf, void* recvbuf, int count, cudaDataType_t dataType);
/* Allgather */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnAllgather)(
        custatevecExCommunicator_t* exCommunicator, const void* sendbuf, void* recvbuf, int count, cudaDataType_t dataType);
/* Allgatherv */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnAllgatherv)(
        custatevecExCommunicator_t* exCommunicator, const void* sendbuf, int sendcount,
        void* recvbuf, const int* recvcounts, const int* displs, cudaDataType_t dataType);
/* SendAsync */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnSendAsync)(
        custatevecExCommunicator_t* exCommunicator, const void* buf, int count,
        cudaDataType_t dataType, int peer, int32_t tag);
/* RecvAsync */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnRecvAsync)(
        custatevecExCommunicator_t* exCommunicator, void* buf, int count,
        cudaDataType_t dataType, int peer, int32_t tag);
/* SendRecvAsync */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnSendRecvAsync)(
        custatevecExCommunicator_t* exCommunicator, const void* sendbuf, void* recvbuf, int count,
        cudaDataType_t dataType, int peer, int32_t tag);
/* Synchronize */
typedef custatevecExCommunicatorStatus_t (*custatevecExCommunicator_FnSynchronize)(custatevecExCommunicator_t* exCommunicator);

/*
 * Function tables
 */

/**
 * \brief Module-level function table
 *
 * These functions operate on the IPC module as a whole and are called during module initialization
 * and finalization.
 */
struct custatevecExCommunicatorModule_t
{
    custatevecExCommunicator_FnGetVersion getVersion;
    custatevecExCommunicator_FnInit init;
    custatevecExCommunicator_FnInitialized initialized;
    custatevecExCommunicator_FnFinalize finalize;
    custatevecExCommunicator_FnFinalized finalized;
    custatevecExCommunicator_FnGetSizeAndRank getSizeAndRank;
    custatevecExCommunicator_FnCreateCommunicator createCommunicator;
    custatevecExCommunicator_FnDestroyCommunicator destroyCommunicator;
};

/**
 * \brief Instance-level function table for communicator operations
 *
 * These functions operate on specific communicator instances and are called
 * during communicator usage.
 */
struct custatevecExCommunicatorInterface_t
{
    custatevecExCommunicator_FnAbort abort;
    custatevecExCommunicator_FnGetSize getSize;
    custatevecExCommunicator_FnGetRank getRank;
    custatevecExCommunicator_FnBarrier barrier;
    custatevecExCommunicator_FnBcast bcast;
    custatevecExCommunicator_FnAllgather allgather;
    custatevecExCommunicator_FnAllgatherv allgatherv;
    custatevecExCommunicator_FnSendAsync sendAsync;
    custatevecExCommunicator_FnRecvAsync recvAsync;
    custatevecExCommunicator_FnSendRecvAsync sendRecvAsync;
    custatevecExCommunicator_FnSynchronize synchronize;
    custatevecExCommunicator_FnAllreduce allreduce;
};

/**
 * \brief Communicator instance
 *
 * Represents a specific communicator instance with its instance-level operations.
 */
struct custatevecExCommunicator_t
{
    const custatevecExCommunicatorInterface_t* intf;
};

#if defined(__cplusplus)
} // extern "C"
#endif
