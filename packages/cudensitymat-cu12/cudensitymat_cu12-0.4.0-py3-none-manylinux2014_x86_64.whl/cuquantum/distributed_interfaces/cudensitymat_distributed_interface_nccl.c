/*
 * Copyright (c) 2026-2026, NVIDIA CORPORATION & AFFILIATES
 * SPDX-License-Identifier: BSD-3-Clause
 */

#include <cudensitymat.h> // cuDensityMat library header

#include <nccl.h> // NCCL library header
#include <cuda_runtime.h>

#include <stdlib.h>
#include <stdio.h>
#include <string.h>

/*
 * NCCL Distributed Interface for cuDensityMat
 *
 * This interface provides NCCL-based distributed communication for cuDensityMat.
 * Unlike MPI, NCCL is GPU-centric and stream-based.
 *
 * Caller must ensure stream ordering before calling these functions
 * Blocking operations use the default CUDA stream (0).
 * Async operations use the request's internal stream.
 *
 * Key differences from MPI implementation:
 * - All data buffers are assumed to reside in GPU memory
 * - Blocking ops use default stream, async ops use request's stream
 * - Barrier uses allreduce on a small buffer followed by stream sync
 * - Complex types are handled as pairs of real values
 *
 * The NCCL Distributed Interface is in an experimental state and we do not guarantee stability or performance.
 */

/** Internal structure to manage async requests with CUDA streams/events */
typedef struct {
    cudaStream_t stream;
    cudaEvent_t event;
    int initialized;
} NcclAsyncRequest;


/**
 * Converts CUDA data type to the corresponding NCCL data type.
 * For complex types, we use the underlying real type and double the count.
 * Returns the adjusted element count via the adjustedCount parameter.
 */
static ncclDataType_t convertCudaToNcclDataType(const cudaDataType_t cudaDataType,
                                                 int32_t count,
                                                 int32_t* adjustedCount)
{
    ncclDataType_t ncclType;
    *adjustedCount = count;

    switch (cudaDataType)
    {
    case CUDA_R_8I:
        ncclType = ncclInt8;
        break;
    case CUDA_R_16I:
        printf("#FATAL(cudensitymat:nccl-interface): CUDA_R_16I (INT16) is not supported by NCCL\n");
        exit(EXIT_FAILURE);
        break;
    case CUDA_R_32I:
        ncclType = ncclInt32;
        break;
    case CUDA_R_64I:
        ncclType = ncclInt64;
        break;
    case CUDA_R_32F:
        ncclType = ncclFloat32;
        break;
    case CUDA_R_64F:
        ncclType = ncclFloat64;
        break;
    case CUDA_C_32F:
        /* Complex float = 2 floats for element-wise operations */
        ncclType = ncclFloat32;
        *adjustedCount = count * 2;
        break;
    case CUDA_C_64F:
        /* Complex double = 2 doubles for element-wise operations */
        ncclType = ncclFloat64;
        *adjustedCount = count * 2;
        break;
    default:
        printf("#FATAL(cudensitymat:nccl-interface): Unknown CUDA data type: %d\n", (int)(cudaDataType));
        exit(EXIT_FAILURE);
    }
    return ncclType;
}

/** Extracts ncclComm_t from communicator (direct cast, no wrapper struct) */
static ncclComm_t getNcclComm(const cudensitymatDistributedCommunicator_t* comm)
{
    if (comm->commPtr == NULL) return NULL;
    /* commPtr points directly to ncclComm_t */
    return *((ncclComm_t*)(comm->commPtr));
}

/** Check NCCL result and convert to int error code */
static int checkNcclResult(ncclResult_t result)
{
    if (result != ncclSuccess)
    {
        printf("#ERROR(cudensitymat:nccl-interface): NCCL error: %s\n", ncclGetErrorString(result));
        return (int)result;
    }
    return 0;
}

#ifdef __cplusplus
extern "C" {
#endif

/** ncclCommCount wrapper - returns number of ranks in the communicator */
int cudensitymatNcclCommSize(const cudensitymatDistributedCommunicator_t* comm,
                              int32_t* numRanks)
{
    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL)
    {
        *numRanks = 0;
        return 0;
    }
    int count = 0;
    ncclResult_t result = ncclCommCount(ncclComm, &count);
    *numRanks = count;
    return checkNcclResult(result);
}

/**
 * Returns the size of the local subgroup of processes sharing node memory.
 *
 * NCCL doesn't expose shared memory topology directly. This implementation
 * returns 1, assuming each process manages a single GPU. For multi-GPU per
 * process scenarios, the user should handle this at a higher level.
 */
int cudensitymatNcclCommSizeShared(const cudensitymatDistributedCommunicator_t* comm,
                                    int32_t* numRanks)
{
    (void)comm; /* unused */
    /* NCCL doesn't have shared memory concept like MPI.
     * Return 1 as a conservative estimate (1 GPU per process). */
    *numRanks = 1;
    return 0;
}

/** ncclCommUserRank wrapper - returns the rank of this process */
int cudensitymatNcclCommRank(const cudensitymatDistributedCommunicator_t* comm,
                              int32_t* procRank)
{
    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL)
    {
        *procRank = -1;
        return 0;
    }
    int rank = -1;
    ncclResult_t result = ncclCommUserRank(ncclComm, &rank);
    *procRank = rank;
    return checkNcclResult(result);
}

/**
 * Barrier synchronization.
 *
 * NCCL doesn't have a dedicated barrier operation. We implement this using
 * a small allreduce (sum of a single int) on the provided buffer, which
 * forces all ranks to synchronize. Uses default stream and synchronizes.
 *
 * @param comm The distributed communicator
 * @param barrierBuffer Device pointer to a single int32_t for the allreduce
 */
int cudensitymatNcclBarrier(const cudensitymatDistributedCommunicator_t* comm,
                            void* barrierBuffer)
{
    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return 0;

    if (barrierBuffer == NULL)
    {
        printf("#ERROR(cudensitymat:nccl-interface): Barrier requires barrierBuffer\n");
        return -1;
    }

    /* Use in-place allreduce on a single int as barrier (default stream) */
    ncclResult_t result = ncclAllReduce(barrierBuffer, barrierBuffer, 1,
                                        ncclInt32, ncclSum, ncclComm, 0);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Synchronize to make the barrier blocking */
    cudaError_t cudaErr = cudaStreamSynchronize(0);
    if (cudaErr != cudaSuccess)
    {
        printf("#ERROR(cudensitymat:nccl-interface): CUDA error in barrier: %s\n",
               cudaGetErrorString(cudaErr));
        return (int)cudaErr;
    }
    return 0;
}

/** Allocates an async request with its own stream and event */
int cudensitymatNcclCreateRequest(cudensitymatDistributedRequest_t* request)
{
    NcclAsyncRequest* req = (NcclAsyncRequest*)malloc(sizeof(NcclAsyncRequest));
    if (req == NULL) return -1;

    /* Create non-blocking stream to allow overlap with default stream work */
    cudaError_t err = cudaStreamCreateWithFlags(&req->stream, cudaStreamNonBlocking);
    if (err != cudaSuccess)
    {
        free(req);
        return (int)err;
    }

    err = cudaEventCreate(&req->event);
    if (err != cudaSuccess)
    {
        cudaStreamDestroy(req->stream);
        free(req);
        return (int)err;
    }

    req->initialized = 1;
    *request = (cudensitymatDistributedRequest_t)req;
    return 0;
}

/** Frees a previously allocated async request */
int cudensitymatNcclDestroyRequest(cudensitymatDistributedRequest_t request)
{
    if (request == NULL) return -1;

    NcclAsyncRequest* req = (NcclAsyncRequest*)request;
    if (req->initialized)
    {
        cudaEventDestroy(req->event);
        cudaStreamDestroy(req->stream);
    }
    free(req);
    return 0;
}

/** Waits for completion of an async request */
int cudensitymatNcclWaitRequest(cudensitymatDistributedRequest_t request)
{
    if (request == NULL) return -1;

    NcclAsyncRequest* req = (NcclAsyncRequest*)request;
    cudaError_t err = cudaStreamSynchronize(req->stream);
    if (err != cudaSuccess)
    {
        printf("#ERROR(cudensitymat:nccl-interface): CUDA error in wait: %s\n",
               cudaGetErrorString(err));
        return (int)err;
    }
    return 0;
}

/** Tests for completion of an async request (non-blocking) */
int cudensitymatNcclTestRequest(cudensitymatDistributedRequest_t request,
                                 int32_t* completed)
{
    if (request == NULL)
    {
        *completed = 1;
        return -1;
    }

    NcclAsyncRequest* req = (NcclAsyncRequest*)request;
    cudaError_t err = cudaEventQuery(req->event);

    if (err == cudaSuccess)
    {
        *completed = 1;
    }
    else if (err == cudaErrorNotReady)
    {
        *completed = 0;
        err = cudaSuccess; /* Not an error, just not ready */
    }
    else
    {
        *completed = 0;
        printf("#ERROR(cudensitymat:nccl-interface): CUDA error in test: %s\n",
               cudaGetErrorString(err));
        return (int)err;
    }
    return 0;
}

/** Begin a group of communication operations.
 * 
 * NCCL point-to-point operations (ncclSend/ncclRecv) need to be grouped
 * together to avoid deadlocks. Call groupStart() before issuing multiple
 * async send/recv operations and groupEnd() after.
 */
int cudensitymatNcclGroupStart(void)
{
    ncclResult_t result = ncclGroupStart();
    return checkNcclResult(result);
}

/** End a group of communication operations.
 * 
 * This commits all NCCL operations issued since the matching groupStart().
 * NCCL will execute them together, handling the send/recv pairing properly.
 */
int cudensitymatNcclGroupEnd(void)
{
    ncclResult_t result = ncclGroupEnd();
    return checkNcclResult(result);
}

/** Blocking send using NCCL (uses default stream) */
int cudensitymatNcclSend(const cudensitymatDistributedCommunicator_t* comm,
                          const void* buffer,
                          int32_t count,
                          cudaDataType_t datatype,
                          int32_t destination,
                          int32_t tag)
{
    (void)tag; /* NCCL doesn't use tags */

    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    ncclResult_t result = ncclSend(buffer, (size_t)adjustedCount, ncclType,
                                   destination, ncclComm, 0);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Make it blocking */
    cudaError_t cudaErr = cudaStreamSynchronize(0);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/** Async send using NCCL (uses request's internal stream) */
int cudensitymatNcclSendAsync(const cudensitymatDistributedCommunicator_t* comm,
                               const void* buffer,
                               int32_t count,
                               cudaDataType_t datatype,
                               int32_t destination,
                               int32_t tag,
                               cudensitymatDistributedRequest_t request)
{
    (void)tag; /* NCCL doesn't use tags */

    if (request == NULL) return -1;
    NcclAsyncRequest* req = (NcclAsyncRequest*)request;

    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    ncclResult_t result = ncclSend(buffer, (size_t)adjustedCount, ncclType,
                                   destination, ncclComm, req->stream);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Record event for later wait/test */
    cudaError_t cudaErr = cudaEventRecord(req->event, req->stream);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/** Blocking receive using NCCL (uses default stream) */
int cudensitymatNcclRecv(const cudensitymatDistributedCommunicator_t* comm,
                          void* buffer,
                          int32_t count,
                          cudaDataType_t datatype,
                          int32_t source,
                          int32_t tag)
{
    (void)tag; /* NCCL doesn't use tags */

    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    ncclResult_t result = ncclRecv(buffer, (size_t)adjustedCount, ncclType,
                                   source, ncclComm, 0);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Make it blocking */
    cudaError_t cudaErr = cudaStreamSynchronize(0);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/** Async receive using NCCL (uses request's internal stream) */
int cudensitymatNcclRecvAsync(const cudensitymatDistributedCommunicator_t* comm,
                               void* buffer,
                               int32_t count,
                               cudaDataType_t datatype,
                               int32_t source,
                               int32_t tag,
                               cudensitymatDistributedRequest_t request)
{
    (void)tag; /* NCCL doesn't use tags */

    if (request == NULL) return -1;
    NcclAsyncRequest* req = (NcclAsyncRequest*)request;

    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    ncclResult_t result = ncclRecv(buffer, (size_t)adjustedCount, ncclType,
                                   source, ncclComm, req->stream);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Record event for later wait/test */
    cudaError_t cudaErr = cudaEventRecord(req->event, req->stream);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/** Broadcast using NCCL (uses default stream) */
int cudensitymatNcclBcast(const cudensitymatDistributedCommunicator_t* comm,
                           void* buffer,
                           int32_t count,
                           cudaDataType_t datatype,
                           int32_t root)
{
    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    /* NCCL broadcast uses separate send/recv buffers; for in-place we use same buffer */
    ncclResult_t result = ncclBroadcast(buffer, buffer, (size_t)adjustedCount,
                                        ncclType, root, ncclComm, 0);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Make it blocking */
    cudaError_t cudaErr = cudaStreamSynchronize(0);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/** AllReduce (sum) using NCCL (uses default stream) */
int cudensitymatNcclAllreduce(const cudensitymatDistributedCommunicator_t* comm,
                               const void* bufferIn,
                               void* bufferOut,
                               int32_t count,
                               cudaDataType_t datatype)
{
    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    ncclResult_t result = ncclAllReduce(bufferIn, bufferOut, (size_t)adjustedCount,
                                        ncclType, ncclSum, ncclComm, 0);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Make it blocking */
    cudaError_t cudaErr = cudaStreamSynchronize(0);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/** AllReduce (sum) in-place using NCCL */
int cudensitymatNcclAllreduceInPlace(const cudensitymatDistributedCommunicator_t* comm,
                                      void* buffer,
                                      int32_t count,
                                      cudaDataType_t datatype)
{
    /* NCCL supports in-place when sendbuff == recvbuff */
    return cudensitymatNcclAllreduce(comm, buffer, buffer, count, datatype);
}

/* AllReduce (min) in-place is not implemented for NCCL (not used by cuDensityMat) */


/** AllGather using NCCL (uses default stream) */
int cudensitymatNcclAllgather(const cudensitymatDistributedCommunicator_t* comm,
                               const void* bufferIn,
                               void* bufferOut,
                               int32_t count,
                               cudaDataType_t datatype)
{
    ncclComm_t ncclComm = getNcclComm(comm);
    if (ncclComm == NULL) return -1;

    int32_t adjustedCount;
    ncclDataType_t ncclType = convertCudaToNcclDataType(datatype, count, &adjustedCount);

    ncclResult_t result = ncclAllGather(bufferIn, bufferOut, (size_t)adjustedCount,
                                        ncclType, ncclComm, 0);
    if (result != ncclSuccess) return checkNcclResult(result);

    /* Make it blocking */
    cudaError_t cudaErr = cudaStreamSynchronize(0);
    if (cudaErr != cudaSuccess) return (int)cudaErr;

    return 0;
}

/**
 * Distributed communication service API wrapper binding table (imported by cuDensityMat).
 * The exposed C symbol must be named as "cudensitymatCommInterface".
 */
cudensitymatDistributedInterface_t cudensitymatCommInterface = {
    CUDENSITYMAT_DISTRIBUTED_INTERFACE_VERSION,
    cudensitymatNcclCommSize,
    cudensitymatNcclCommSizeShared,
    cudensitymatNcclCommRank,
    cudensitymatNcclBarrier,
    cudensitymatNcclCreateRequest,
    cudensitymatNcclDestroyRequest,
    cudensitymatNcclWaitRequest,
    cudensitymatNcclTestRequest,
    cudensitymatNcclGroupStart,
    cudensitymatNcclGroupEnd,
    cudensitymatNcclSend,
    cudensitymatNcclSendAsync,
    cudensitymatNcclRecv,
    cudensitymatNcclRecvAsync,
    cudensitymatNcclBcast,
    cudensitymatNcclAllreduce,
    cudensitymatNcclAllreduceInPlace,
    NULL,  /* allreduceInPlaceMin not implemented (not used by cuDensityMat) */
    NULL,  /* allreduceDoubleIntMinloc not implemented (not used by cuDensityMat) */
    cudensitymatNcclAllgather
};

#ifdef __cplusplus
} // extern "C"
#endif
