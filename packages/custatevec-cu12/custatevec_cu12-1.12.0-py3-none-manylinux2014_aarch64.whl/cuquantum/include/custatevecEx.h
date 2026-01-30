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

/** @file custatevecEx.h
 *  @details cuStateVec Scaling API
 */

#pragma once

#include <custatevec.h>

#if defined(__cplusplus)
#include <cstdint>                                // integer types
#include <cstdio>                                 // FILE

extern "C"
{

#else
#include <stdint.h>                               // integer types
#include <stdio.h>                                // FILE

#endif


/**
 * \defgroup ex_enumerators custatevecEx Enumerators
 *
 * \{ */

/**
 * \typedef custatevecExCommunicatorStatus_t
 * \brief Status code returned by communicator method functions
 *
 * \details
 * This status code is returned by communicator functions defined in custatevecEx_ext.h.
 * This enum only implements the success code.  Other status codes are implementation dependent.
 */
enum custatevecExCommunicatorStatus_t
{
    CUSTATEVEC_EX_COMMUNICATOR_STATUS_SUCCESS = 0,   /**< Operation completed successfully. */
};
typedef enum custatevecExCommunicatorStatus_t custatevecExCommunicatorStatus_t;

/**
 * \typedef custatevecExStateVectorCapability_t
 * \brief Bitmask that specifies state vector capability.
 * This enum is reserved for future use.
 */
typedef enum custatevecExStateVectorCapability_t
{
    CUSTATEVEC_EX_SV_CAPABILITY_NONE = 0, /**< No capability enabled */
} custatevecExStateVectorCapability_t;


/**
 * \typedef custatevecExStateVectorDistributionType_t
 * \brief Enum that specifies the distribution type of state vector.
 */
typedef enum custatevecExStateVectorDistributionType_t
{
    CUSTATEVEC_EX_SV_DISTRIBUTION_SINGLE_DEVICE = 0, ///< State vector on single device
    CUSTATEVEC_EX_SV_DISTRIBUTION_MULTI_DEVICE = 1,  ///< State vector distributed to multiple devices
    CUSTATEVEC_EX_SV_DISTRIBUTION_MULTI_PROCESS = 2, ///< State vector distributed to multiple processes
} custatevecExStateVectorDistributionType_t;

/**
 * \typedef custatevecExGlobalIndexBitClass_t
 * \brief Communication method for global index bit operations in multi-process distributions.
 *
 * Operations on global index bits require data transfers. This enum specifies
 * the communication method to use.
 */

typedef enum custatevecExGlobalIndexBitClass_t
{
    CUSTATEVEC_EX_GLOBAL_INDEX_BIT_CLASS_INTERPROC_P2P = 1, ///< Inter-process GPUDirect P2P
    CUSTATEVEC_EX_GLOBAL_INDEX_BIT_CLASS_COMMUNICATOR = 2,  ///< Communication via custatevecExCommunicator
} custatevecExGlobalIndexBitClass_t;

/**
 * \typedef custatevecExStateVectorProperty_t
 * \brief Specifies the name of state vector property.
 */
typedef enum custatevecExStateVectorProperty_t
{
    CUSTATEVEC_EX_SV_PROP_DISTRIBUTION_TYPE = 0,    ///< Returns ::custatevecExStateVectorDistributionType_t
    CUSTATEVEC_EX_SV_PROP_DATA_TYPE = 1,            ///< Returns cudaDataType_t
    CUSTATEVEC_EX_SV_PROP_NUM_WIRES = 2,            ///< Returns int32_t
    CUSTATEVEC_EX_SV_PROP_WIRE_ORDERING = 3,        ///< Returns int32_t array
    CUSTATEVEC_EX_SV_PROP_NUM_LOCAL_WIRES = 4,      ///< Returns int32_t
    CUSTATEVEC_EX_SV_PROP_NUM_DEVICE_SUBSVS = 5,    ///< Returns int32_t
    CUSTATEVEC_EX_SV_PROP_DEVICE_SUBSV_INDICES = 6, ///< Returns int32_t array
} custatevecExStateVectorProperty_t;

/**
 * \typedef custatevecExPermutationType_t
 * \brief Specifies the permutation type.
 */
typedef enum custatevecExPermutationType_t
{
    CUSTATEVEC_EX_PERMUTATION_SCATTER = 0,  ///< Scatter permutation
    CUSTATEVEC_EX_PERMUTATION_GATHER = 1,   ///< Gather permutation
} custatevecExPermutationType_t;


/**
 * \typedef custatevecExMatrixType_t
 * \brief Specifies the type of matrix.
 */
typedef enum custatevecExMatrixType_t
{
    CUSTATEVEC_EX_MATRIX_DENSE = 1,          ///< Dense matrix
    CUSTATEVEC_EX_MATRIX_DIAGONAL = 2,       ///< Diagonal matrix
    CUSTATEVEC_EX_MATRIX_ANTI_DIAGONAL = 4,  ///< Anti-diagonal matrix
} custatevecExMatrixType_t;

/**
 * \typedef custatevecExSVUpdaterConfigName_t
 * \brief Specifies the configuration argument type of SVUpdater.
 */
typedef enum custatevecExSVUpdaterConfigName_t
{
    CUSTATEVEC_EX_SVUPDATER_CONFIG_MAX_NUM_HOST_THREADS = 0, ///< Number of host threads, int32_t
    CUSTATEVEC_EX_SVUPDATER_CONFIG_DENSE_FUSION_SIZE = 1,    ///< Dense fusion size, int32_t
    CUSTATEVEC_EX_SVUPDATER_CONFIG_DIAGONAL_FUSION_SIZE = 2, ///< Diagonal fusion size, int32_t
} custatevecExSVUpdaterConfigName_t;


/**
 * \typedef custatevecExMemorySharingMethod_t
 * \brief Specifies the method to share device virtual memory among processes.
 */

typedef enum custatevecExMemorySharingMethod_t
{
    CUSTATEVEC_EX_MEMORY_SHARING_METHOD_AUTODETECT = 0,     ///< Auto-detect
    CUSTATEVEC_EX_MEMORY_SHARING_METHOD_NONE = 1,           ///< No P2P memory sharing
    CUSTATEVEC_EX_MEMORY_SHARING_METHOD_FABRIC_HANDLE = 2,  ///< Use FabricHandle
    CUSTATEVEC_EX_MEMORY_SHARING_METHOD_PIDFD = 3,          ///< Use pidfd syscalls with POSIX file descriptor
} custatevecExMemorySharingMethod_t;


/** \} end of enumerators */

/**
 * \defgroup ex_structs custatevecEx data structures
 *
 * \{ */

/**
 * \struct custatevecExSVUpdaterConfigItem_t
 * \brief Specifies the configuration item of SVUpdater.
 */
typedef struct custatevecExSVUpdaterConfigItem_t
{
    custatevecExSVUpdaterConfigName_t name;  ///< Configuration name
    union
    {
        int32_t int32;                       ///< int32 value
        char placeholder[32];                ///< Placeholder to keep 32 bytes for the value member
    } value __attribute__((aligned(16)));    ///< Configuration value
                                             // 16-byte alignment for gcc and clang
} custatevecExSVUpdaterConfigItem_t;

/** \} end of data structures */

/**
 * \defgroup ex_descriptors custatevecEx descriptors
 * \{ */

/**
 * \typedef custatevecExDictionaryDescriptor_t
 * \brief This descriptor holds a handle to a dictionary instance.
 */
typedef struct custatevecExDictionary* custatevecExDictionaryDescriptor_t;

/**
 * \typedef custatevecExCommunicatorDescriptor_t
 * \brief This descriptor holds a handle to an inter-process communication object.
 *
 * This abstraction enables communication between processes for multi-process state
 * vector operations.
 */
typedef struct custatevecExCommunicator_t* custatevecExCommunicatorDescriptor_t;

/**
 * \typedef custatevecExStateVectorDescriptor_t
 * \brief This descriptor holds a handle to a state vector instance.
 */
typedef struct custatevecExStateVector* custatevecExStateVectorDescriptor_t;

/**
 * \typedef custatevecExSVUpdaterDescriptor_t
 * \brief This descriptor holds a handle to an SVUpdater instance.
 */
typedef struct custatevecExSVUpdater* custatevecExSVUpdaterDescriptor_t;

/**
 * \typedef custatevecExResourceManagerDescriptor_t
 * \brief This descriptor holds a handle to a resource manager instance.
 * \note Custom resource manager is not supported in this release.
 */
typedef struct custatevecExResourceManager* custatevecExResourceManagerDescriptor_t;

/** \} end of custatevecEx descriptors */


/**
 * \defgroup ex_dictionary_api custatevecEx Dictionary API
 * \{ */

/**
 * \brief Destroy dictionary instance
 *
 * \param[in] dictionary dictionary descriptor instance
 *
 * \details ::custatevecExDictionaryDestroy() destroys dictionary instance.
 * Dictionary is the object to hold key-value pairs.
 */

custatevecStatus_t
custatevecExDictionaryDestroy(custatevecExDictionaryDescriptor_t dictionary);

/** \} end of Dictionary API */


/**
 * \defgroup ex_communicator_api custatevecEx Communicator API
 *
 * The Communicator API provides an abstraction for inter-process communication
 * in multi-process quantum circuit simulation. The library provides built-in
 * implementations for Open MPI and MPICH, and allows custom communicator plugins
 * via the extension interface (custatevecEx_ext.h).
 *
 * The API separates IPC library lifecycle from communicator instance management:
 * - Call ::custatevecExCommunicatorInitialize() once per process to initialize the IPC library
 * - Call ::custatevecExCommunicatorCreate() to create communicator instances (multiple instances supported)
 * - Call ::custatevecExCommunicatorDestroy() to destroy each instance when done
 * - Call ::custatevecExCommunicatorFinalize() once per process to finalize the IPC library
 * \{ */

/**
 * \brief Initialize inter-process communication
 *
 * \param[in] communicatorType communicator type
 * \param[in] libraryPath path to the inter-process communication library (can be null)
 * \param[in,out] argc pointer to argument count
 * \param[in,out] argv pointer to argument vector
 * \param[out] exCommStatus pointer to the variable that receives the status from communicator's init() method
 *
 * \details
 * The communicator is the abstraction of inter-process communication in cuStateVec Ex API.
 * This function initializes the underlying inter-process communication library and
 * prepares it for creating communicator instances via ::custatevecExCommunicatorCreate().
 *
 * The library provides two built-in communicator implementations for Open MPI and MPICH.
 * To use these, specify ::CUSTATEVEC_COMMUNICATOR_TYPE_OPENMPI or
 * ::CUSTATEVEC_COMMUNICATOR_TYPE_MPICH for \p communicatorType. The API loads the MPI
 * library from the path specified by \p libraryPath.
 * If null, it defaults to "libmpi.so" and follows the standard library search order.
 *
 * The \p exCommStatus argument returns the result of the call to the init() method of the underlying
 * implementation.  For built-in communicators, it returns the return value of MPI_Init() as
 * \p custatevecExCommunicatorStatus_t.
 *
 * The built-in implementation skips calling MPI_Init() if MPI is already initialized.
 * In this case, ::CUSTATEVEC_EX_COMMUNICATOR_STATUS_SUCCESS is returned to the \p exCommStatus argument.
 *
 * To use other inter-process communication libraries, users can build a custom communicator.
 * To use it, specify ::CUSTATEVEC_COMMUNICATOR_TYPE_EXTERNAL for \p communicatorType
 * and provide the path to the custom communicator library in \p libraryPath.
 * If \p libraryPath is null for external communicators, the API searches for the required symbols
 * in the current process, allowing applications to provide their own communicator implementation
 * without a separate shared library.
 *
 * This API returns successfully if the specified shared object is properly loaded and
 * the IPC library is properly initialized.
 *
 * \note This function is intended for application initialization.
 *       It should be called once per process before any other communicator operations.
 *
 * \note The communicator dynamically loads the library that provides inter-process communication
 *       features. During the lifetime of the application, only one library may be used.
 *       This API returns ::CUSTATEVEC_STATUS_ALREADY_INITIALIZED on successive calls after the first
 *       successful initialization.
 *       If an application directly links to an MPI library, the communicator should use the same
 *       library binary. Otherwise, this API may fail or the communicator may not function properly.
 */

custatevecStatus_t
custatevecExCommunicatorInitialize(
        custatevecCommunicatorType_t communicatorType,
        const char* libraryPath,
        int* argc,
        char*** argv,
        custatevecExCommunicatorStatus_t* exCommStatus);

/**
 * \brief Finalize inter-process communication library
 *
 * \param[out] exCommStatus pointer to the variable that receives the status from communicator's finalize() method
 *
 * \details
 * This function finalizes the underlying inter-process communication library and
 * releases all associated resources.
 *
 * The \p exCommStatus argument returns the result of the call to the communicator provider's finalize() method.
 * For built-in communicators, it returns the return value of MPI_Finalize() as
 * \p custatevecExCommunicatorStatus_t.
 *
 * The built-in implementation skips calling MPI_Finalize() if MPI_Init() was not called
 * by ::custatevecExCommunicatorInitialize(). In this case, ::CUSTATEVEC_EX_COMMUNICATOR_STATUS_SUCCESS is
 * returned.
 *
 * \note This function is intended for application finalization.
 *       All communicator instances must be destroyed before calling this function.
 */

custatevecStatus_t
custatevecExCommunicatorFinalize(
        custatevecExCommunicatorStatus_t* exCommStatus);

/**
 * \brief Get the global size and rank
 *
 * \param[out] size pointer to the variable that receives the global number of processes
 * \param[out] rank pointer to the variable that receives the global rank of the calling process
 * \param[out] exCommStatus pointer to the variable that receives the status from communicator operations
 *
 * \details
 * This function retrieves the number of processes and the rank of the calling process.
 * These values are identical to those obtained from MPI_COMM_WORLD for MPI-based communicator.
 *
 * The \p size argument returns the global number of processes.
 * The \p rank argument returns the global rank of the calling process (0-indexed, range [0, size)).
 * The \p exCommStatus argument returns the status of the communicator operations.
 *
 * ::custatevecExCommunicatorInitialize() must be called before calling this function.
 * If the IPC library is not initialized, this function returns ::CUSTATEVEC_STATUS_NOT_INITIALIZED.
 */

custatevecStatus_t
custatevecExCommunicatorGetSizeAndRank(
        int32_t*                          size,
        int32_t*                          rank,
        custatevecExCommunicatorStatus_t* exCommStatus);

/**
 * \brief Create communicator instance
 *
 * \param[out] exCommunicator pointer to the variable that receives the created communicator instance
 *
 * \details
 * This function creates a communicator instance using the IPC library initialized by
 * ::custatevecExCommunicatorInitialize().
 *
 * ::custatevecExCommunicatorInitialize() must be called before calling this function.
 * If the IPC library is not initialized, this function returns ::CUSTATEVEC_STATUS_NOT_INITIALIZED.
 */

custatevecStatus_t
custatevecExCommunicatorCreate(
        custatevecExCommunicatorDescriptor_t* exCommunicator);

/**
 * \brief Destroy communicator instance
 *
 * \param[in] exCommunicator communicator instance to destroy
 *
 * \details
 * This function destroys a communicator instance and releases all associated resources.
 */

custatevecStatus_t
custatevecExCommunicatorDestroy(
        custatevecExCommunicatorDescriptor_t exCommunicator);

/** \} end of Communicator API */


/**
 * \defgroup ex_state_vector_api custatevecEx StateVector API
 * \{ */

/**
 * \brief Create configuration for single device state vector
 *
 * \param[out] svConfig dictionary instance that holds state vector configuration
 * \param[in] svDataType state vector data type
 * \param[in] numWires number of wires of state vector
 * \param[in] numDeviceWires number of wires of state vector on device
 * \param[in] deviceId device id where the entire state vector will be allocated
 * \param[in] capability bit mask to specify optional features of state vector
 *
 * \details
 * This function creates a dictionary that holds state vector configuration
 * for a single device state vector according to the given set of arguments.
 * The state vector will be allocated on the single device specified by \p deviceId.
 *
 * The \p numWires argument specifies the number of wires of state vector, and the
 * \p numDeviceWires argument specifies the number of wires allocated on the device.
 *
 * The \p capability argument is to enable optional features.  The value is specified
 * as a bit-wise OR of ::custatevecExStateVectorCapability_t.  As the present version
 * does not have any capability defined, the value should be 0.
 *
 * For the present release, the same value should be specified to the \p numWires
 * and \p numDeviceWires arguments.  These two arguments are declared for a future
 * extension.
 *
 * \note
 * This function creates a logical configuration and does not validate actual system or
 * hardware requirements (e.g., non-existent deviceId, required memory capacity).
 * Validation occurs when calling ::custatevecExStateVectorCreateSingleProcess() to create
 * the state vector instance.
 */

custatevecStatus_t
custatevecExConfigureStateVectorSingleDevice(
        custatevecExDictionaryDescriptor_t* svConfig,
        cudaDataType_t                      svDataType,
        int32_t                             numWires,
        int32_t                             numDeviceWires,
        int32_t                             deviceId,
        uint32_t                            capability);

/**
 * \brief Create configuration for multi-device state vector
 *
 * \param[out] svConfig dictionary instance that holds state vector configuration
 * \param[in] svDataType state vector data type
 * \param[in] numWires number of wires of state vector
 * \param[in] numDeviceWires number of wires of state vector on each device
 * \param[in] deviceIds host pointer to an array of device ids
 * \param[in] numDevices number of devices
 * \param[in] networkType device network topology type
 * \param[in] capability bit mask to specify optional features of state vector
 *
 * \details
 * This function creates a dictionary that holds state vector configuration
 * for multi-device state vector within a single process. The state vector is
 * distributed across multiple devices specified by \p deviceIds.  The specified devices
 * should be able to communicate with each other by GPUDirect P2P.
 *
 * The \p numDevices should be a power-of-two value. The following relationship
 * should be satisfied:
 *
 * numWires = log2(numDevices) + numDeviceWires
 *
 * The \p networkType argument specifies the device interconnect topology.
 * Use ::CUSTATEVEC_DEVICE_NETWORK_TYPE_SWITCH for GPUs connected by switches  (e.g., via NVSwitch or PCIe switch)
 * or ::CUSTATEVEC_DEVICE_NETWORK_TYPE_FULLMESH for direct all-to-all connectivity (e.g., direct NVLink mesh).
 *
 * The \p capability argument enables optional features. The value should be 0
 * as no capabilities are currently defined.
 *
 * \note
 * This function creates a logical configuration and does not validate actual system or
 * hardware requirements (e.g., non-existent deviceIds, P2P capability, required memory capacity).
 * Validation occurs when calling ::custatevecExStateVectorCreateSingleProcess() to create
 * the state vector instance.
 */

custatevecStatus_t
custatevecExConfigureStateVectorMultiDevice(
        custatevecExDictionaryDescriptor_t*      svConfig,
        cudaDataType_t                           svDataType,
        int32_t                                  numWires,
        int32_t                                  numDeviceWires,
        const int32_t*                           deviceIds,
        int32_t                                  numDevices,
        custatevecDeviceNetworkType_t            networkType,
        uint32_t                                 capability);


/**
 * \brief Create configuration for multi-process distributed state vector
 *
 * \param[out] svConfig dictionary instance that holds state vector configuration
 * \param[in] svDataType state vector data type
 * \param[in] numWires number of wires of state vector
 * \param[in] numDeviceWires number of wires of state vector on each device
 * \param[in] deviceId device id for this process
 * \param[in] memorySharingMethod method for sharing GPU virtual device memory between processes
 * \param[in] globalIndexBitClasses host pointer to an array of global index bit classes for each layer
 * \param[in] numGlobalIndexBitsPerLayer host pointer to an array specifying number of global index bits per layer
 * \param[in] numGlobalIndexBitLayers number of global index bit layers
 * \param[in] transferWorkspaceSizeInBytes size in bytes of workspace memory for inter-process data transfers
 * \param[in] auxConfig pointer to auxiliary configuration
 * \param[in] capability bit mask to specify optional features of state vector
 *
 * \details
 * This function creates a dictionary that holds state vector configuration
 * for multi-process distributed state vector according to the given set of arguments.
 * In this configuration, the state vector is distributed across multiple processes,
 * with each process owning a single device to allocate one sub state vector.
 *
 * The \p numWires argument specifies the number of wires of state vector, and the
 * \p numDeviceWires argument specifies the number of wires allocated on each device.
 * The following relationship should be satisfied where numProcesses is the
 * number of processes to which state vector is distributed.
 *
 * numWires = log2(numProcesses) + numDeviceWires
 *
 * The \p deviceId argument specifies the device ID where the sub state vector will be
 * allocated. If set to -1, the device ID will be dynamically assigned during state vector
 * creation using the formula: deviceId = processRank % numDevicesInHardwareNode, where
 * processRank is obtained from the communicator and numDevicesInHardwareNode is the total
 * number of CUDA devices available in the hardware node.
 *
 * The \p memorySharingMethod argument specifies the method for sharing GPU virtual device memory
 * between processes by inter-process GPUDirect P2P.  Virtual device memory is utilized to
 * allocate the device memory for state vector.
 * If ::CUSTATEVEC_EX_GLOBAL_INDEX_BIT_CLASS_INTERPROC_P2P is specified in \p globalIndexBitClasses,
 * it's required to specify an available memory sharing method.
 * Use ::CUSTATEVEC_EX_MEMORY_SHARING_METHOD_AUTODETECT for automatic selection, or specify
 * a particular method when the suitable sharing method is known.
 * ::CUSTATEVEC_EX_MEMORY_SHARING_METHOD_FABRIC_HANDLE is the requirement to enable multi-node
 * NVLink.  ::CUSTATEVEC_EX_MEMORY_SHARING_METHOD_PIDFD uses POSIX file descriptors to export
 * and import virtual device memory among processes.  All GPUs that are assigned to distributed
 * processes should be in a single hardware node due to the limitation of POSIX file descriptor
 * sharing.
 *
 * If ::CUSTATEVEC_EX_GLOBAL_INDEX_BIT_CLASS_INTERPROC_P2P is not specified in
 * \p globalIndexBitClasses, use ::CUSTATEVEC_EX_MEMORY_SHARING_METHOD_NONE that indicates
 * no memory sharing is required.
 * If another memory sharing method is specified, it will be silently ignored.
 *
 * The process-to-process communication is organized in layers that correspond to network
 * hierarchy.  Each layer represents a different communication datalink (e.g., PCIe Switch,
 * NVLink with NVSwitch) between processes with appropriate communication methods.
 *
 * The \p globalIndexBitClasses, \p numGlobalIndexBitsPerLayer, and \p numGlobalIndexBitLayers
 * arguments specify the communication datalink in each network layer:
 *
 * - \p globalIndexBitClasses[i] specifies the communication class for layer i, which should be
 *   one of ::custatevecExGlobalIndexBitClass_t values (network topology types, P2P variants, or communicator).
 * - \p numGlobalIndexBitsPerLayer[i] specifies the number of global index bits assigned to layer i.
 * - \p numGlobalIndexBitLayers specifies the total number of layers.  The max acceptable number is 8.
 *
 * The sum of all elements in \p numGlobalIndexBitsPerLayer should equal log2(numProcesses).
 *
 * The \p transferWorkspaceSizeInBytes argument specifies the size in bytes of the device buffer
 * allocated for inter-process data transfers. This device buffer serves as workspace during
 * communication between processes. The API may internally adjust the specified value to the
 * closest power-of-two number that is smaller than or equal to the given value.
 * Larger buffer sizes can improve performance depending on the system hardware configuration.
 * If the specified size is too small for optimal performance, the API will automatically
 * increase it to an appropriate value.
 *
 * The \p auxConfig argument specifies auxiliary configuration setup.  No auxiliary configuration
 * is currently defined; this argument must be NULL.
 *
 * The \p capability argument is to enable optional features.  The value is specified
 * as a bit-wise OR of ::custatevecExStateVectorCapability_t.  As the present version
 * does not have any capability defined, the value should be 0.
 *
 * \note
 * This function creates a logical configuration and does not validate actual system or
 * hardware requirements (e.g., non-existent deviceId, memory sharing method availability,
 * required memory capacity). Validation occurs when calling
 * ::custatevecExStateVectorCreateMultiProcess() to create the state vector instance,
 * which may return ::CUSTATEVEC_STATUS_INVALID_CONFIGURATION if the system does not
 * support the requested configuration.
 */

custatevecStatus_t
custatevecExConfigureStateVectorMultiProcess(
        custatevecExDictionaryDescriptor_t*      svConfig,
        cudaDataType_t                           svDataType,
        int32_t                                  numWires,
        int32_t                                  numDeviceWires,
        int32_t                                  deviceId,
        custatevecExMemorySharingMethod_t        memorySharingMethod,
        const custatevecExGlobalIndexBitClass_t* globalIndexBitClasses,
        const int32_t*                           numGlobalIndexBitsPerLayer,
        int32_t                                  numGlobalIndexBitLayers,
        size_t                                   transferWorkspaceSizeInBytes,
        const void*                              auxConfig,
        uint32_t                                 capability);


/**
 * \brief Create state vector
 *
 * \param[out] stateVector a host pointer to the variable that receives state vector instance
 * \param[in] svConfig state vector configuration created by a state vector configuration function
 * \param[in] streams a pointer to a host array that holds CUDA streams
 * \param[in] numStreams the number of streams given by the streams argument
 * \param[in] resourceManager resource manager
 *
 * \details
 * This function creates a state vector instance according to the \p svConfig argument and returns
 * the instance to the \p stateVector argument. The \p svConfig should be created by
 * ::custatevecExConfigureStateVectorSingleDevice() or ::custatevecExConfigureStateVectorMultiDevice().
 *
 * The \p streams and \p numStreams arguments specify CUDA streams.  CUDA API calls and kernel
 * launches are serialized on the given streams.  The number of streams should match the
 * number of devices where the state vector is allocated.  All CUDA calls serialized on
 * the streams are synchronized by calling ::custatevecExStateVectorSynchronize().
 * If a null pointer is passed to the \p streams argument, all calls are serialized on the default
 * streams.  In this case, the value of the \p numStreams argument should be 0.
 *
 * The \p resourceManager argument specifies the resource manager.  If a null pointer is
 * specified, the library default resource manager is used.
 *
 * This API returns ::CUSTATEVEC_STATUS_INVALID_CONFIGURATION if an argument specified by
 * custatevecExConfigureStateVectorSingleDevice() or custatevecExConfigureStateVectorMultiDevice()
 * is invalid, such as specifying device ID that does not exist.
 *
 * When using multiple devices (multi-device state vector), the following requirements must be met:
 * \li All devices must be of the same GPU generation (same compute capability).
 * \li GPUDirect P2P must be available between all devices.
 * If these requirements are not met, this API returns ::CUSTATEVEC_STATUS_INVALID_CONFIGURATION.
 *
 * This API returns ::CUSTATEVEC_STATUS_NOT_SUPPORTED if no CUDA-capable GPU devices are found
 * in the system.
 *
 * \note
 * Custom resource manager is not enabled in this release.  Please pass nullptr to the
 * \p resourceManager argument.  Otherwise, this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 */

custatevecStatus_t
custatevecExStateVectorCreateSingleProcess(
        custatevecExStateVectorDescriptor_t*     stateVector,
        const custatevecExDictionaryDescriptor_t svConfig,
        cudaStream_t const*                      streams,
        int32_t                                  numStreams,
        custatevecExResourceManagerDescriptor_t  resourceManager);

/**
 * \brief Create multi-process distributed state vector
 *
 * \param[out] stateVector a host pointer to the variable that receives state vector instance
 * \param[in] svConfig state vector configuration created by custatevecExConfigureStateVectorMultiProcess
 * \param[in] stream CUDA stream for this process
 * \param[in] exCommunicator communicator descriptor for inter-process communication
 * \param[in] resourceManager resource manager
 *
 * \details
 * This function creates a multi-process distributed state vector instance according to the
 * \p svConfig argument and returns the instance to the \p stateVector argument.
 * The \p svConfig should be created by ::custatevecExConfigureStateVectorMultiProcess().
 * The state vector is distributed across multiple processes.  Each process owns single device
 * to allocate one sub state vector.
 *
 * The \p stream argument specifies the CUDA stream for this process, corresponding to the fact that
 * one process manages one device.  All CUDA calls in this process are serialized on this
 * stream and synchronized by calling ::custatevecExStateVectorSynchronize().  A null pointer
 * is treated as the CUDA default stream.
 *
 * The \p exCommunicator argument specifies a custatevecExCommunicatorDescriptor_t instance that
 * is created by ::custatevecExCommunicatorCreate().
 *
 * The \p resourceManager argument specifies the resource manager.
 *
 * This API returns ::CUSTATEVEC_STATUS_INVALID_CONFIGURATION if an argument specified by
 * ::custatevecExConfigureStateVectorMultiProcess() is invalid, such as specifying \p deviceId
 * that does not exist, \p memorySharingMethod is not available on the system, or the number
 * of processes does not match the configuration.
 *
 * The number of processes must be a power-of-two number greater than 1. The number of processes
 * must equal (1 << numGlobalBits) where numGlobalBits is the sum of all values in
 * \p numGlobalIndexBitsPerLayer as specified in ::custatevecExConfigureStateVectorMultiProcess().
 *
 * This API returns ::CUSTATEVEC_STATUS_NOT_SUPPORTED if no CUDA-capable GPU devices are found
 * in the system.
 *
 * \note
 * Custom resource manager is not enabled in this release.  Please pass nullptr to the
 * \p resourceManager argument.  Otherwise, this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 */

custatevecStatus_t
custatevecExStateVectorCreateMultiProcess(
        custatevecExStateVectorDescriptor_t*     stateVector,
        const custatevecExDictionaryDescriptor_t svConfig,
        cudaStream_t                             stream,
        custatevecExCommunicatorDescriptor_t     exCommunicator,
        custatevecExResourceManagerDescriptor_t  resourceManager);


/**
 * \brief Destroy state vector instance
 *
 * \param[in] stateVector state vector instance
 *
 * \details
 * This function destroys state vector instance.
 */

custatevecStatus_t
custatevecExStateVectorDestroy(custatevecExStateVectorDescriptor_t stateVector);

/**
 * \brief Retrieve state vector properties
 *
 * \param[in] stateVector state vector instance
 * \param[in] property a value of ::custatevecExStateVectorProperty_t
 * \param[out] value host pointer to a host buffer that receives the value of the specified property
 * \param[in] sizeInBytes byte size of the value buffer
 *
 * \details
 * This function retrieves state vector properties.
 * The \p property argument specifies one of properties, and the property value is
 * returned to the host buffer specified by the \p value argument.
 *
 * The following is the table for properties and corresponding data types.
 *
 * ::custatevecExStateVectorProperty_t          | data type
 * -----------------------------------          | ---------
 * ::CUSTATEVEC_EX_SV_PROP_DISTRIBUTION_TYPE    | ::custatevecExStateVectorDistributionType_t
 * ::CUSTATEVEC_EX_SV_PROP_DATA_TYPE            | cudaDataType_t
 * ::CUSTATEVEC_EX_SV_PROP_NUM_WIRES            | int32_t
 * ::CUSTATEVEC_EX_SV_PROP_WIRE_ORDERING        | int32_t[]
 * ::CUSTATEVEC_EX_SV_PROP_NUM_LOCAL_WIRES      | int32_t
 * ::CUSTATEVEC_EX_SV_PROP_NUM_DEVICE_SUBSVS    | int32_t
 * ::CUSTATEVEC_EX_SV_PROP_DEVICE_SUBSV_INDICES | int32_t[]
 *
 * Each property enum returns the values as described below.
 * - ::CUSTATEVEC_EX_SV_PROP_DISTRIBUTION_TYPE returns the distribution type of
 *   state vector.
 * - ::CUSTATEVEC_EX_SV_PROP_DATA_TYPE returns the data type of state vector.
 *   The value is CUDA_C_32F or CUDA_C_64F.
 * - ::CUSTATEVEC_EX_SV_PROP_NUM_WIRES returns the number of wires.
 * - ::CUSTATEVEC_EX_SV_PROP_WIRE_ORDERING returns the wire ordering of state vector as
 *   int32_t array.  The length of array is the number of wires.
 * - ::CUSTATEVEC_EX_SV_PROP_NUM_LOCAL_WIRES returns the number of local wires that is wires
 *   local to the sub state vector.
 * - ::CUSTATEVEC_EX_SV_PROP_NUM_DEVICE_SUBSVS returns the number of sub state vectors
 *   placed on device.
 * - ::CUSTATEVEC_EX_SV_PROP_DEVICE_SUBSV_INDICES returns the array of the sub state vector
 *   indices placed on device(s).  The array length is the number of the sub state vectors
 *   placed on device.
 *
 * The \p sizeInBytes argument specifies the byte size of the \p value buffer and
 * should be equal to or larger than the required byte size.
 * Otherwise, this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 */

custatevecStatus_t
custatevecExStateVectorGetProperty(const custatevecExStateVectorDescriptor_t stateVector,
                                   custatevecExStateVectorProperty_t         property,
                                   void*                                     value,
                                   size_t                                    sizeInBytes);


/**
 * \brief Set the compute precision mode for a state vector instance.
 *
 * \param[in,out] stateVector state vector instance
 * \param[in] mode Compute precision mode as defined by ::custatevecMathMode_t.
 *
 * \details
 * This function sets the compute precision mode for the specified state vector instance.
 * Each state vector can have its own compute precision mode independently.
 *
 * The compute precision mode controls the precision and performance characteristics
 * of mathematical operations performed on the state vector.
 *
 * The default math mode for the cuStateVec Ex API is ::CUSTATEVEC_MATH_MODE_ALLOW_FP32_EMULATED_BF16X9.
 * To disable the use of BF16x9 floating point emulation, set the mode to
 * ::CUSTATEVEC_MATH_MODE_DISALLOW_FP32_EMULATED_BF16X9.
 */
custatevecStatus_t custatevecExStateVectorSetMathMode(
        custatevecExStateVectorDescriptor_t stateVector,
        custatevecMathMode_t mode);


/**
 * \brief Set the zero state to state vector
 *
 * \param[in,out] stateVector state vector instance
 *
 * \details
 * This function sets the zero state (|0000...00>).
 */

custatevecStatus_t
custatevecExStateVectorSetZeroState(custatevecExStateVectorDescriptor_t stateVector);


/**
 * \brief Copy state vector elements to host buffer
 *
 * \param[in] stateVector state vector instance
 * \param[out] state pointer to a host buffer that receives state vector elements
 * \param[in] dataType dataType of the state vector elements
 * \param[in] begin index of state vector element where the copy begins
 * \param[in] end index of state vector element where the copy ends
 * \param[in] maxNumConcurrentCopies Max number of parallel copies.
 *
 * \details
 * State vector elements in [\p begin, \p end) are copied to the host buffer specified by the \p state
 * argument.  The data type specified by the \p dataType argument should equal to that specified
 * when configuring state vector.  The host buffer should be large enough to hold copied elements.
 *
 * State vector elements in the range [\p begin, \p end) should be accessible in the current process.
 * For single-device state vector, the whole state vector is allocated in a single process.
 * For multi-device state vector, the state vector is sliced and distributed to multiple devices.
 * However, all state vector elements are accessible in the process.
 * Thus, [begin, end) is in the range of [0, svSize).
 * For multi-process state vectors, the state vector is distributed to multiple processes. Each
 * process has one process-local slice that is called sub-state vector.
 * The range must be within:
 * [(subSV_index * subSV_size), (subSV_index + 1) * subSV_size),
 * where subSV_index is the sub-state vector index and subSV_size is the sub-state vector size.
 * ::custatevecExStateVectorGetProperty with ::CUSTATEVEC_EX_SV_PROP_DEVICE_SUBSV_INDICES returns
 * the sub-state vector indices allocated in the process.
 *
 * The \p dataType argument should be identical to that of the state vector instance specified by
 * the \p stateVector argument.  Otherwise, this API returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 *
 * The \p maxNumConcurrentCopies argument specifies the max number of concurrent copies that can be utilized
 * during the copy of state vector elements.  The actual number of concurrent copies is implementation defined.
 *
 * \note The call to ::custatevecExStateVectorGetState() can be asynchronous.  Please call
 * ::custatevecExStateVectorSynchronize() to complete the copying of state vector elements.
 */

custatevecStatus_t
custatevecExStateVectorGetState(const custatevecExStateVectorDescriptor_t stateVector,
                                void*                                     state,
                                cudaDataType_t                            dataType,
                                custatevecIndex_t                         begin,
                                custatevecIndex_t                         end,
                                int32_t                                   maxNumConcurrentCopies);

/**
 * \brief Set complex value array on host to state vector
 *
 * \param[out] stateVector state vector instance
 * \param[in] state pointer to a complex vector on host
 * \param[in] dataType dataType of the state vector elements
 * \param[in] begin index of state vector element where the copy begins
 * \param[in] end index of state vector element where the copy ends
 * \param[in] maxNumConcurrentCopies Max number of parallel copies.
 *
 * \details
 * Complex values given by the \p state argument are copied to the specified state
 * vector.  The copy range in the state vector index is [\p begin, \p end).  The data type of complex values
 * should equal to that specified on configuring state vector.
 *
 * State vector elements in the range [\p begin, \p end) should be accessible in the current process.
 * For single-device state vector, the whole state vector is allocated in a single process.
 * For multi-device state vector, the state vector is sliced and distributed to multiple devices.
 * However, all state vector elements are accessible in the process.
 * Thus, [begin, end) is in the range of [0, svSize).
 * For multi-process state vectors, the state vector is distributed to multiple processes. Each
 * process has one process-local slice that is called sub-state vector.
 * The range must be within:
 * [(subSV_index * subSV_size), (subSV_index + 1) * subSV_size),
 * where subSV_index is the sub-state vector index and subSV_size is the sub-state vector size.
 * ::custatevecExStateVectorGetProperty with ::CUSTATEVEC_EX_SV_PROP_DEVICE_SUBSV_INDICES returns
 * the sub-state vector indices allocated in the process.
 *
 * The \p maxNumConcurrentCopies argument specifies the max number of concurrent copies that can be utilized
 * during the copy of state vector elements.  The actual number of concurrent copies is implementation defined.
 *
 * \note The call to ::custatevecExStateVectorSetState() can be asynchronous.  Please call
 * ::custatevecExStateVectorSynchronize() to complete the copying of state vector elements.
 */

custatevecStatus_t
custatevecExStateVectorSetState(custatevecExStateVectorDescriptor_t stateVector,
                                const void*                         state,
                                cudaDataType_t                      dataType,
                                custatevecIndex_t                   begin,
                                custatevecIndex_t                   end,
                                int32_t                             maxNumConcurrentCopies);



/**
 * \brief Reassign wire ordering to state vector
 *
 * \param[in,out] stateVector state vector instance
 * \param[in] wireOrdering the pointer to a integer host array that holds wire ordering
 * \param[in] wireOrderingLen the length of wire ordering
 *
 * \details
 * Reassign (overwrite) wire ordering of the given state vector.
 * The elements given by the \p wireOrdering argument should be in [0, \p numWires) where
 * \p numWires represents the number of wires of the state vector.  Otherwise this API
 * returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 * The \p wireOrderingLen argument represents the length of wire ordering.  The value should
 * match the number of wires.  Otherwise this API returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 */

custatevecStatus_t
custatevecExStateVectorReassignWireOrdering(custatevecExStateVectorDescriptor_t stateVector,
                                            const int32_t*                      wireOrdering,
                                            int32_t                             wireOrderingLen);



/**
 * \brief Permute index bits and wires of state vector
 *
 * \param[in,out] stateVector StateVector instance
 * \param[in] permutation a host pointer to an integer array specifying the permutation
 * \param[in] permutationLen length of the permutation
 * \param[in] permutationType permutation type (scatter or gather)
 *
 * \details Permutes index bits of state vector, and the wire ordering is
 * accordingly updated to reflect the permuted index bit ordering.
 *
 * Permutation is specified by the \p permutation argument as an integer array.
 * The \p permutationLen argument specifies the length of the permutation.
 * The function can apply two types of permutation, scatter or gather, which is
 * specified by the \p permutationType argument.
 *
 * The wire ordering is updated as defined in the following formulas.
 *
 * \code
 * // When CUSTATEVEC_EX_PERMUTATION_SCATTER specified.
 * dstWires[permutation[idx]] = srcWires[idx]
 *
 * // When CUSTATEVEC_EX_PERMUTATION_GATHER specified.
 * dstWires[idx] = srcWires[permutation[idx]]
 *
 * \endcode
 *
 * By definition, the elements of permutation array should be integers in [0, numWires - 1] where
 * numWires represents the number of wires of the specified state vector instance.
 * If ::CUSTATEVEC_EX_PERMUTATION_SCATTER is specified to the \p permutationType, the permutation
 * length should be identical to the number of wires.
 * If ::CUSTATEVEC_EX_PERMUTATION_GATHER is specified to the \p permutationType and
 * \p permutationLen is smaller than the number of wires in state vector, wires that don't
 * appear in the \p permutation argument are sorted and appended to the permutation array.
 *
 * Ex. numWires = 5, permutation = {0, 2, 3}, permutationLen = 3.
 * Wires {1, 4} don't appear.  Those two wires are sorted and appended to the permutation. Therefore,
 * the complemented permutation is {0, 2, 3, 1, 4}.
 *
 */

custatevecStatus_t
custatevecExStateVectorPermuteIndexBits(custatevecExStateVectorDescriptor_t stateVector,
                                        const int32_t*                      permutation,
                                        int32_t                             permutationLen,
                                        custatevecExPermutationType_t       permutationType);


/**
 * \brief Get resources from device sub state vector
 *
 * \param[in] stateVector StateVector instance
 * \param[in] subSVIndex sub state vector index
 * \param[out] deviceId device id
 * \param[out] d_subSV a host pointer that receives the specified sub state vector pointer.
 * \param[out] stream a host pointer to CUDA stream
 * \param[out] handle a host pointer to ::custatevecHandle_t
 *
 * \details Get the computing resource associated with the device state vector.
 * The \p subSVIndex argument specifies the sub state vector index.
 * The \p deviceId, \p d_subSV arguments return the device id, the device memory pointer
 * of the specified sub state vector.
 * The \p stream and \p handle arguments return the CUDA stream and the cuStateVec handle.
 * All CUDA calls in custatevecEx API are serialized on the returned stream. The returned
 * cuStateVec handle can be passed to cuStateVec APIs to operate on the returned device pointer.
 *
 * The number of the device sub state vectors is retrieved by calling
 * ::custatevecExStateVectorGetProperty() API with ::CUSTATEVEC_EX_SV_PROP_NUM_DEVICE_SUBSVS
 * specified as the property name, and the sub state vector indices are retrieved
 * by specifying ::CUSTATEVEC_EX_SV_PROP_DEVICE_SUBSV_INDICES, respectively.
 * A single-device state vector always has one device sub-state vector.
 *
 * The \p deviceId, \p d_subSV, and \p stream arguments must not be null pointers.
 * Otherwise, this API returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 * A null pointer can be passed to the \p handle argument.  For this case, the cuStateVec handle
 * will not be returned.
 */

custatevecStatus_t
custatevecExStateVectorGetResourcesFromDeviceSubSV(
        custatevecExStateVectorDescriptor_t stateVector,
        int32_t                             subSVIndex,
        int32_t*                            deviceId,
        void**                              d_subSV,
        cudaStream_t*                       stream,
        custatevecHandle_t*                 handle);


/**
 * \brief Get resources from device sub state vector view
 *
 * \param[in] stateVector StateVector instance
 * \param[in] subSVIndex sub state vector index
 * \param[out] deviceId device id
 * \param[out] d_subSV a host pointer that receives the specified sub state vector pointer.
 * \param[out] stream a host pointer to CUDA stream
 * \param[out] handle a host pointer to ::custatevecHandle_t
 *
 * \details This API works almost the same as
 * ::custatevecExStateVectorGetResourcesFromDeviceSubSV() except for the returned device pointer
 * is immutable.
 *
 * Please refer to the documentation of ::custatevecExStateVectorGetResourcesFromDeviceSubSV() API
 * for the descriptions of the arguments.
 */

custatevecStatus_t
custatevecExStateVectorGetResourcesFromDeviceSubSVView(
        const custatevecExStateVectorDescriptor_t stateVector,
        int32_t                                   subSVIndex,
        int32_t*                                  deviceId,
        const void**                              d_subSV,
        cudaStream_t*                             stream,
        custatevecHandle_t*                       handle);

/**
 * \brief Flush all operations and synchronize
 *
 * \param[in] stateVector state vector instance
 *
 * \details
 * This function flushes all operations issued before the call of this function and
 * synchronizes all streams associated with the specified state vector instance.
 * For multi-process state vectors, a barrier among processes will be issued in addition to
 * the synchronization in the current process.
 */

custatevecStatus_t
custatevecExStateVectorSynchronize(custatevecExStateVectorDescriptor_t stateVector);


/** \} end of StateVector API */

/**
 * \defgroup ex_simulator_api custatevecEx Simulator API
 * \{ */

/**
 * \brief Calculate abs2sum array for a given set of wires
 *
 * \param[in] stateVector StateVector instance
 * \param[out] abs2sum pointer to a host or device array of sums of squared absolute values
 * \param[in] outputOrdering pointer to a host array of output tensor ordering
 * \param[in] outputOrderingLen the length of outputOrdering
 * \param[in] maskBitString pointer to a host array for a bit string to specify mask bits
 * \param[in] maskWireOrdering pointer to a host array that specifies the wire ordering of maskBitString
 * \param[in] maskLen the length of mask
 *
 * \details Calculates an array of sums of squared absolute values of state vector elements.
 * The abs2sum array can be on host or device. The tensor ordering of the abs2sum array is specified
 * by the \p outputOrdering and the \p outputOrderingLen arguments. Unspecified wires are folded
 * (summed up).
 *
 * The \p maskBitString, \p maskWireOrdering and \p maskLen arguments set a bit string to mask
 * the state vector.  The abs2sum array is calculated by using state vector elements that
 * match the mask bit string. If the \p maskLen argument is 0, null pointers can be specified to the
 * \p maskBitString and \p maskWireOrdering arguments, and all state vector elements are used
 * for calculation.
 *
 * By definition, all values in \p outputOrdering and \p maskWireOrdering arguments should be in [0, numWires).
 * The \p outputOrdering and \p maskWireOrdering arguments should not contain overlapping or duplicate wires.
 * This function returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements are not
 * satisfied.
 *
 * The empty \p outputOrdering can be specified to calculate the norm of state vector. In this case,
 * 0 is passed to the \p outputOrderingLen argument and the \p outputOrdering argument can be a null
 * pointer.
 *
 * For distributed state vector configurations, the \p abs2sum argument should point to an array on the host.
 *
 * \note Since the size of abs2sum array is proportional to \f$ 2^{outputOrderingLen} \f$ ,
 * the max length of \p outputOrdering depends on the amount of available memory and \p maskLen.
 */

custatevecStatus_t custatevecExAbs2SumArray(custatevecExStateVectorDescriptor_t stateVector,
                                            double*                             abs2sum,
                                            const int32_t*                      outputOrdering,
                                            int32_t                             outputOrderingLen,
                                            const int32_t*                      maskBitString,
                                            const int32_t*                      maskWireOrdering,
                                            int32_t                             maskLen);

/**
 * \brief Perform qubit measurements
 *
 * \param[in] stateVector StateVector instance
 * \param[out] bitString host pointer that receives the measured bit string
 * \param[in] bitStringOrdering pointer to a host array of bit string ordering
 * \param[in] bitStringOrderingLen length of bitStringOrdering
 * \param[in] randnum random number, [0, 1).
 * \param[in] collapse Collapse operation
 * \param[in] reserved Reserved argument.  A null pointer should be passed.
 *
 * \details This function executes multiple single qubit measurements with a single call
 * and returns a bit string that represents the measurement outcomes.
 * The \p bitStringOrdering argument specifies wires to be measured.
 *
 * The measurement result is stored in \p bitString as a 64-bit integer bit mask.  The ordering of
 * \p bitString is specified by the \p bitStringOrdering and \p bitStringOrderingLen arguments.  The idx-th bit
 * of \p bitString corresponds to the measurement outcome of bitStringOrdering[idx].
 *
 * By definition, all values in \p bitStringOrdering arguments should be in [0, numWires).
 * The \p bitStringOrdering argument should not contain duplicate wires.
 * This function returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements are not
 * satisfied.
 *
 * The \p collapse argument specifies the operation applied for the state vector.
 *
 * If ::CUSTATEVEC_COLLAPSE_NONE is specified, this function only returns the measured
 * bit string without modifying the state vector.
 *
 * If ::CUSTATEVEC_COLLAPSE_NORMALIZE_AND_ZERO is specified, this function collapses the state vector.
 *
 * If ::CUSTATEVEC_COLLAPSE_RESET is specified, the state vector is collapsed as
 * ::CUSTATEVEC_COLLAPSE_NORMALIZE_AND_ZERO does.  Then, the measurement outcome is checked.
 * If the measurement outcome for a specified wire is |1>, the wire is flipped (reset) to |0>.
 * Otherwise, the state vector is not modified.
 *
 * If a random number is not in [0, 1), this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 * At least one wire should be specified, otherwise this function returns
 * ::CUSTATEVEC_STATUS_INVALID_VALUE.
 */

custatevecStatus_t custatevecExMeasure(custatevecExStateVectorDescriptor_t stateVector,
                                       custatevecIndex_t*                  bitString,
                                       const int32_t*                      bitStringOrdering,
                                       int32_t                             bitStringOrderingLen,
                                       double                              randnum,
                                       custatevecCollapseOp_t              collapse,
                                       const void*                         reserved);

/**
 * \brief Sample bit strings from the state vector.
 *
 * \param[in] stateVector State vector instance
 * \param[out] bitStrings pointer to a host array to store sampled bit strings
 * \param[in] bitStringOrdering pointer to a host array of bit string ordering for sampling
 * \param[in] bitStringOrderingLen length of bitStringOrdering
 * \param[in] randnums pointer to an array of random numbers
 * \param[in] numShots the number of shots
 * \param[in] output the order of sampled bit strings
 * \param[in] reserved Reserved argument. A null pointer should be passed.
 *
 * \details This function performs sampling.
 * The \p bitStringOrdering and \p bitStringOrderingLen arguments specify wires to be sampled.
 * Sampled bit strings are represented as an array of ::custatevecIndex_t and
 * are stored to the host memory buffer that the \p bitStrings argument points to.
 *
 * By definition, all values in \p bitStringOrdering arguments should be in [0, numWires).
 * The \p bitStringOrdering argument should not contain duplicate wires.
 * This function returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements are not
 * satisfied.
 *
 * The \p randnums argument is an array of user-generated random numbers whose length is \p numShots.
 * The range of random numbers should be in [0, 1).  A random number given by the \p randnums
 * argument is clipped to [0, 1) if its range is not in [0, 1).
 *
 * The \p output argument specifies the order of sampled bit strings:
 *   - If ::CUSTATEVEC_SAMPLER_OUTPUT_RANDNUM_ORDER is specified,
 * the order of sampled bit strings is the same as that in the \p randnums argument.
 *   - If ::CUSTATEVEC_SAMPLER_OUTPUT_ASCENDING_ORDER is specified, bit strings are returned in the
 * ascending order.
 *
 */

custatevecStatus_t custatevecExSample(custatevecExStateVectorDescriptor_t stateVector,
                                      custatevecIndex_t*                  bitStrings,
                                      const int32_t*                      bitStringOrdering,
                                      int32_t                             bitStringOrderingLen,
                                      const double*                       randnums,
                                      int32_t                             numShots,
                                      custatevecSamplerOutput_t           output,
                                      const void*                         reserved);

/**
 * \brief Apply gate matrix
 *
 * \param[in,out] stateVector state vector instance
 * \param[in] matrix pointer to a buffer that holds matrix elements
 * \param[in] matrixDataType data type of matrix
 * \param[in] exMatrixType enumerator specifying the matrix type and layout
 * \param[in] layout enumerator specifying the matrix layout
 * \param[in] adjoint apply adjoint of matrix
 * \param[in] targets pointer to a host array of target wires
 * \param[in] numTargets the number of target wires
 * \param[in] controls pointer to a host array of control wires
 * \param[in] controlBitValues pointer to a host array of control bit values
 * \param[in] numControls the number of control wires
 *
 * \details Apply gate matrix for state vector.
 *
 * The \p matrix argument is a host or device pointer that points to matrix element array.
 * For distributed state vector configurations, the \p matrix argument should be a host pointer.
 * Otherwise, this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 * The \p matrixDataType argument specifies the data type of matrix elements.  The value
 * should be CUDA_C_32F or CUDA_C_64F for complex 64 or complex 128 type, respectively.
 *
 * The \p exMatrixType argument specifies the matrix types, dense (square), diagonal
 * or anti-diagonal.  The memory layout of the matrix is row- or column-major, which
 * is specified by the \p layout argument.
 *
 * The matrix type is dense (square) if ::CUSTATEVEC_EX_MATRIX_DENSE is specified.
 * The \p matrix argument points to a buffer that holds dense matrix as two-dimensional
 * array.  The matrix dimension is  (\f$2^\text{numTargets} \times 2^\text{numTargets}\f$ ).
 * The memory layout follows the specification of the \p layout argument.  The layout
 * is row-major if ::CUSTATEVEC_MATRIX_LAYOUT_ROW, or column-major if
 * ::CUSTATEVEC_MATRIX_LAYOUT_COL is specified.
 *
 * The matrix type is diagonal if ::CUSTATEVEC_EX_MATRIX_DIAGONAL is specified.
 * The \p matrix argument points to a buffer that accommodates a complex vector
 * of diagonal elements.  The vector length is identical to the matrix dimension,
 * (\f$2^\text{numTargets}\f$ ).
 * The memory layout of the diagonal elements is identical for row- and column-major
 * layouts. Thus, the memory layout specification by the \p layout argument is ignored.
 *
 * The matrix type is anti-diagonal if ::CUSTATEVEC_EX_MATRIX_ANTI_DIAGONAL is specified.
 * The \p matrix argument points to a buffer that accommodates
 * a complex vector of anti-diagonal elements.  The vector length is identical to the
 * matrix dimension, (\f$2^\text{numTargets}\f$ ). The memory layout is specified by
 * the \p layout argument expressed as shown below,
 *
 * \code
 *
 * elements[idx] = matrix(idx, dim - (idx + 1))  // row-major layout
 *
 * elements[idx] = matrix(dim - (idx + 1), idx)  // col-major layout
 *
 * \endcode
 *
 * by using elements[idx] for the idx-th anti-diagonal element and matrix(row, col) for
 * the matrix element at (row, col).
 *
 * The \p targets and \p controls arguments specify target and control wires in the
 * state vector. The \p controlBitValues argument specifies bit values of control wires.
 * The ordering of \p controlBitValues is specified by the \p controls argument. If a null
 * pointer is specified to this argument, all control bit values are set to 1.
 *
 * By definition, all target and control values should be in [0, numWires).
 * Wires in \p targets and \p controls arguments should not overlap or have duplicates.
 * This function returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements are not
 * satisfied.
 *
 * For distributed state vector configurations, the \p numTargets argument should be equal to or
 * less than \c numDeviceWires when \p exMatrixType is ::CUSTATEVEC_EX_MATRIX_DENSE or
 * ::CUSTATEVEC_EX_MATRIX_ANTI_DIAGONAL.
 * If a larger matrix is passed, this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE. 
 */

custatevecStatus_t custatevecExApplyMatrix(custatevecExStateVectorDescriptor_t stateVector,
                                           const void*                         matrix,
                                           cudaDataType_t                      matrixDataType,
                                           custatevecExMatrixType_t            exMatrixType,
                                           custatevecMatrixLayout_t            layout,
                                           int32_t                             adjoint,
                                           const int32_t*                      targets,
                                           int32_t                             numTargets,
                                           const int32_t*                      controls,
                                           const int32_t*                      controlBitValues,
                                           int32_t                             numControls);

/**
 * \brief Apply the exponential of a multi-qubit Pauli operator.
 *
 * \param[in,out] stateVector state vector instance
 * \param[in] theta theta
 * \param[in] paulis host pointer to ::custatevecPauli_t array
 * \param[in] targets pointer to a host array of target wires
 * \param[in] numTargets the number of target wires
 * \param[in] controls pointer to a host array of control wires
 * \param[in] controlBitValues pointer to a host array of control bit values
 * \param[in] numControls the number of control wires
 *
 * \details Apply exponential of a tensor product of Pauli operators, \f$ e^{i \theta P} \f$,
 * where \f$P\f$ is the tensor product
 * \f$P = paulis[0] \otimes paulis[1] \otimes \cdots \otimes paulis[numTargets-1]\f$
 * acting on the wires specified by the \p targets argument. The \p paulis and \p numTargets
 * arguments specify the Pauli operators and their count.
 *
 * At least one target and a corresponding Pauli basis should be specified.
 *
 * The \p controls and \p numControls arguments specify the control wires
 * in the state vector.
 *
 * By definition, all target and control values should be in [0, numWires).
 * The \p targets and \p controls arguments should not contain overlapping or duplicate wires.
 * This function returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements are not
 * satisfied.
 *
 * The \p controlBitValues argument specifies bit values of control wires. The ordering
 * of \p controlBitValues is specified by the \p controls argument. If a null pointer is
 * specified to this argument, all control bit values are set to 1.
 */

custatevecStatus_t custatevecExApplyPauliRotation(
        custatevecExStateVectorDescriptor_t stateVector,
        double                              theta,
        const custatevecPauli_t*            paulis,
        const int32_t*                      targets,
        int32_t                             numTargets,
        const int32_t*                      controls,
        const int32_t*                      controlBitValues,
        int32_t                             numControls);

/**
 * \brief Compute expectation values for a batch of (multi-qubit) Pauli operators.
 *
 * \param[in] stateVector state vector instance
 * \param[out] expectationValues pointer to a host array to store expectation values
 * \param[in] pauliOperatorArrays pointer to a host array of Pauli operator arrays
 * \param[in] numPauliOperatorArrays the number of Pauli operator arrays
 * \param[in] basisWiresArray host array of basis wire arrays
 * \param[in] numBasisWiresArray host array of the number of basis wires
 *
 * This function computes multiple expectation values for given sequences of
 * Pauli operators by a single call.
 *
 * A single Pauli operator sequence, pauliOperators, is represented by using an array
 * of ::custatevecPauli_t. The basis wires on which these Pauli operators are acting are
 * represented by an array of wires.
 *
 * The length of pauliOperators and basisWires are the same and specified by numBasisWires.
 *
 * The number of Pauli operator sequences is specified by the \p numPauliOperatorArrays argument.
 *
 * Multiple sequences of Pauli operators are represented in the form of arrays of arrays
 * in the following manners:
 *   - The \p pauliOperatorArrays argument is an array of arrays of ::custatevecPauli_t.
 *   - The \p basisWiresArray is an array of the wire arrays.
 *   - The \p numBasisWiresArray argument holds an array of the length of Pauli operator sequences and
 *     wire arrays.
 *
 * By definition, all wires in each array of \p basisWiresArray arguments should be in [0, numWires).
 * Each array in \p basisWiresArray should not contain duplicate wires.
 * This function returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements are not
 * satisfied.
 *
 * Computed expectation values are stored in a host buffer specified by the \p expectationValues
 * argument of length \p numPauliOperatorArrays.
 *
 * This function returns ::CUSTATEVEC_STATUS_INVALID_VALUE if wires specified
 * for a Pauli operator sequence has duplicates and/or points to a wire that does not exist.
 *
 * This function accepts empty Pauli operator sequence to get the norm of the state vector.
 */

custatevecStatus_t custatevecExComputeExpectationOnPauliBasis(
        custatevecExStateVectorDescriptor_t stateVector,
        double*                             expectationValues,
        const custatevecPauli_t**           pauliOperatorArrays,
        int32_t                             numPauliOperatorArrays,
        const int32_t**                     basisWiresArray,
        const int32_t*                      numBasisWiresArray);

/** \} end of Simulator API */


/**
 * \defgroup ex_sv_updater custatevecEx State Vector Updater API
 * \{ */

/**
 * \brief Create SVUpdater configuration
 *
 * \param[out] svUpdaterConfig SVUpdater configuration
 * \param[in] dataType data type used in SVUpdater
 * \param[in] configItems host pointer to the array of Configuration items
 * \param[in] numConfigItems the number of configuration items
 *
 * This function creates the configuration dictionary for SVUpdater.
 * The \p dataType argument specifies the value type internally used in SVUpdater. Its
 * value should be CUDA_C_32F or CUDA_C_64F.
 * The \p configItems and \p numConfigItems arguments are the array of
 * \p custatevecExSVUpdaterConfigItem_t.
 *
 * The following configuration items are available:
 * - ::CUSTATEVEC_EX_SVUPDATER_CONFIG_MAX_NUM_HOST_THREADS
 *     - Type: int32_t, acceptable range: [1, 32]
 *     - Description: The maximum number of host threads utilized during the call to
 *       custatevecExSVUpdaterApply().
 * - ::CUSTATEVEC_EX_SVUPDATER_CONFIG_DENSE_FUSION_SIZE
 *     - Type: int32_t, acceptable range: [1, 10]
 *     - Description: The maximum number of targets for fused dense gate matrices.
 * - ::CUSTATEVEC_EX_SVUPDATER_CONFIG_DIAGONAL_FUSION_SIZE
 *     - Type: int32_t, acceptable range: [0, 20]
 *     - Description: The maximum number of targets for fused diagonal gate matrices. If 0 is
 *       specified, diagonal gate matrices are not fused.
 *
 * The \p configItems should not contain duplicate items with the same name.
 * For configurations that are not specified, system default values will be used.
 *
 * The \p configItems can be a null pointer. In that case, \p numConfigItems should
 * be set to 0.
 *
 * It's the user's responsibility to destroy the created svUpdaterConfig object by
 * calling ::custatevecExDictionaryDestroy().
 *
 * \note Default configuration is recommended for optimal performance.
 * For ::CUSTATEVEC_EX_SVUPDATER_CONFIG_MAX_NUM_HOST_THREADS, values between 4 and 16 generally
 * provide good performance.
 * For ::CUSTATEVEC_EX_SVUPDATER_CONFIG_DENSE_FUSION_SIZE, values between 4 and 6 are
 * automatically selected by the library.
 * These values correspond to the upper limit where gate application kernels remain
 * memory-bound rather than compute-bound, ensuring optimal performance.
 * For ::CUSTATEVEC_EX_SVUPDATER_CONFIG_DIAGONAL_FUSION_SIZE, the library default is recommended.
 * The value is automatically adjusted based on the number of qubits in the state vector.
 */

custatevecStatus_t custatevecExConfigureSVUpdater(
        custatevecExDictionaryDescriptor_t*      svUpdaterConfig,
        cudaDataType_t                           dataType,
        const custatevecExSVUpdaterConfigItem_t* configItems,
        int32_t                                  numConfigItems);

/**
 * \brief Create SVUpdater
 *
 * \param[out] svUpdater created SVUpdater
 * \param[in] svUpdaterConfig SVUpdater configuration
 * \param[in] resourceManager resource manager
 *
 * This function creates SVUpdater instance.
 *
 * \note
 * Custom resource manager is not enabled in this release.  Please pass nullptr to the
 * \p resourceManager argument.  Otherwise, this function returns ::CUSTATEVEC_STATUS_INVALID_VALUE.
 */

custatevecStatus_t custatevecExSVUpdaterCreate(
        custatevecExSVUpdaterDescriptor_t*       svUpdater,
        const custatevecExDictionaryDescriptor_t svUpdaterConfig,
        custatevecExResourceManagerDescriptor_t  resourceManager);



/**
 * \brief Destroy SVUpdater instance
 *
 * \param[in] svUpdater SVUpdater instance
 *
 * \details
 * This function destroys SVUpdater instance.
 */

custatevecStatus_t custatevecExSVUpdaterDestroy(
        custatevecExSVUpdaterDescriptor_t svUpdater);


/**
 * \brief Clear operations queued in SVUpdater
 *
 * \param[in,out] svUpdater SVUpdater instance
 *
 * \details
 * This function clears queued operations in SVUpdater.
 */

custatevecStatus_t custatevecExSVUpdaterClear(
        custatevecExSVUpdaterDescriptor_t svUpdater);

/**
 * \brief Enqueue matrix to SVUpdater
 *
 * \param[in,out] svUpdater SVUpdater instance
 * \param[in] matrix pointer to a host buffer that holds matrix elements
 * \param[in] matrixDataType data type of matrix
 * \param[in] exMatrixType enumerator specifying the matrix type
 * \param[in] layout enumerator specifying the matrix layout
 * \param[in] adjoint apply adjoint of matrix
 * \param[in] targets pointer to a host array of target wires
 * \param[in] numTargets the number of target wires
 * \param[in] controls pointer to a host array of control wires
 * \param[in] controlBitValues pointer to a host array of control bit values
 * \param[in] numControls the number of control wires
 *
 * \details This function enqueues a gate matrix to SVUpdater.
 *
 * The \p matrix argument is a host pointer that points to matrix element array.
 * The \p matrixDataType argument specifies the data type of matrix elements.  The value
 * should be CUDA_C_32F or CUDA_C_64F for complex 64 or complex 128 type, respectively.
 * Only CUDA_C_64F is acceptable if the SVUpdater data type is CUDA_C_64F by calling
 * ::custatevecExConfigureSVUpdater().  Also, CUDA_C_64F and CUDA_C_32F are acceptable
 * if the SVUpdater data type is CUDA_C_32F.
 *
 * The \p exMatrixType argument specifies the matrix types, dense (square), diagonal
 * or anti-diagonal.  The memory layout of the matrix is row- or column-major, which
 * is specified by the \p layout argument.
 *
 * The matrix type is dense (square) if ::CUSTATEVEC_EX_MATRIX_DENSE is specified.
 * The \p matrix argument points to a buffer that holds dense matrix as two-dimensional
 * array.  The matrix dimension is  (\f$2^\text{numTargets} \times 2^\text{numTargets}\f$ ).
 * The memory layout follows the specification of the \p layout argument.  The layout
 * is row-major if ::CUSTATEVEC_MATRIX_LAYOUT_ROW, or column-major if
 * ::CUSTATEVEC_MATRIX_LAYOUT_COL is specified.
 *
 * The matrix type is diagonal if ::CUSTATEVEC_EX_MATRIX_DIAGONAL is specified.
 * The \p matrix argument points to a buffer that accommodates a complex vector
 * of diagonal elements.  The vector length is identical to the matrix dimension,
 * (\f$2^\text{numTargets}\f$ ).
 * The memory layout of the diagonal elements is identical for row- and column-major
 * layouts. Thus, the memory layout specification by the \p layout argument is ignored.
 *
 * The matrix type is anti-diagonal if ::CUSTATEVEC_EX_MATRIX_ANTI_DIAGONAL is specified.
 * The \p matrix argument points to a buffer that accommodates
 * a complex vector of anti-diagonal elements.  The vector length is identical to the
 * matrix dimension, (\f$2^\text{numTargets}\f$ ). The memory layout is specified by
 * the \p layout argument expressed as shown below,
 *
 * \code
 *
 * elements[idx] = matrix(idx, dim - (idx + 1))  // row-major layout
 *
 * elements[idx] = matrix(dim - (idx + 1), idx)  // col-major layout
 *
 * \endcode
 *
 * by using elements[idx] for the idx-th anti-diagonal element and matrix(row, col) for
 * the matrix element at (row, col).
 *
 * The \p targets and \p controls arguments specify target and control wires in the
 * state vector. The \p controlBitValues argument specifies bit values of control wires.
 * The ordering of \p controlBitValues is specified by the \p controls argument. If a null
 * pointer is specified to this argument, all control bit values are set to 1.
 *
 * The max number of targets is limited to 15 if ::CUSTATEVEC_EX_MATRIX_DENSE or
 * ::CUSTATEVEC_EX_MATRIX_ANTI_DIAGONAL specified, and 30 if ::CUSTATEVEC_EX_MATRIX_DIAGONAL,
 * specified, respectively. However, 10 or more targets is not recommended;
 * the recommended number of targets for typical usage is 6 or fewer.
 *
 * By definition, all target and control values should be in [0, numWires).
 * The \p targets and \p controls arguments should not contain overlapping wires.
 *
 * For distributed state vector configurations, the total number of wires involved
 * (\p numTargets + \p numControls) should not exceed \c numDeviceWires or the number of
 * local wires on each device. Note that this constraint is not validated by
 * custatevecExSVUpdaterEnqueueMatrix(). The validation occurs later during the call to
 * ::custatevecExSVUpdaterApply() where the StateVector instance is provided, and
 * ::CUSTATEVEC_STATUS_INVALID_VALUE is returned if the constraint is violated.
 */

custatevecStatus_t custatevecExSVUpdaterEnqueueMatrix(
        custatevecExSVUpdaterDescriptor_t svUpdater,
        const void*                       matrix,
        cudaDataType_t                    matrixDataType,
        custatevecExMatrixType_t          exMatrixType,
        custatevecMatrixLayout_t          layout,
        int32_t                           adjoint,
        const int32_t*                    targets,
        int32_t                           numTargets,
        const int32_t*                    controls,
        const int32_t*                    controlBitValues,
        int32_t                           numControls);

/**
 * \brief Enqueue mixed unitary channel.
 *
 * \param[in,out] svUpdater SVUpdater instance
 * \param[in] unitaries host pointer to an array of unitary matrix elements
 * \param[in] unitariesDataType dataType of the specified unitary matrices
 * \param[in] exMatrixTypes matrix types of the specified unitary matrices
 * \param[in] numUnitaries the number of matrices.
 * \param[in] layout layout of the specified unitary matrices
 * \param[in] probabilities host array that holds the probabilities
 * \param[in] channelWires wires that sampled unitary channel is applied
 * \param[in] numChannelWires the number of wires
 *
 * \details This function enqueues a mixed unitary channel to SVUpdater.
 *
 * The \p unitaries argument is a host pointer to an array of unitary matrices.  Each array element
 * in the unitaries argument points to an array of matrix elements that represents a unitary matrix.
 * The actual data type of matrix elements is specified by the \p unitariesDataType argument.
 * The \p exMatrixTypes is a host array that specifies the matrix types of unitary matrices.
 * The matrix types specified by \p exMatrixTypes determine the lengths of matrix element arrays
 * specified by the \p unitaries argument.
 * The \p layout argument specifies the matrix layout in the same way as described in
 * ::custatevecExSVUpdaterEnqueueMatrix().
 *
 * The \p probabilities argument is a host array that represents the probabilities
 * associated with the specified unitary matrices to be randomly sampled.
 * The array length is \p numUnitaries.
 * The total sum of all probabilities must be less than or equal to 1.0. When the sum
 * is less than 1.0, the remaining probability corresponds to no transformation,
 * implementing a probabilistic quantum channel where the state vector remains unchanged
 * with probability (1 - sum_of_probabilities).
 * The probabilities are used as-is for sampling without normalization in this API.
 *
 * If any probability value in the \p probabilities array is zero or negative,
 * ::CUSTATEVEC_STATUS_INVALID_VALUE is returned.
 *
 * Only CUDA_C_64F is acceptable if the SVUpdater data type is CUDA_C_64F by calling
 * ::custatevecExConfigureSVUpdater().  Also, CUDA_C_64F and CUDA_C_32F are acceptable
 * if the SVUpdater data type is CUDA_C_32F.
 *
 * The \p channelWires and \p numChannelWires arguments specify the wires on which the sampled unitary
 * matrix is to be applied.
 * The max number of wires are limited to 15 if ::CUSTATEVEC_EX_MATRIX_DENSE or
 * ::CUSTATEVEC_EX_MATRIX_ANTI_DIAGONAL specified, and 30 if ::CUSTATEVEC_EX_MATRIX_DIAGONAL,
 * specified, respectively. However, 10 or more wires is not recommended;
 * the recommended number of wires for typical usage is 6 or fewer.
 *
 * For distributed state vector configurations, the \p numChannelWires argument should be equal to or
 * less than \c numDeviceWires, or the number of local wires on each device. Note that this constraint
 * is not validated by custatevecExSVUpdaterEnqueueUnitaryChannel(). The validation occurs later during
 * the call to ::custatevecExSVUpdaterApply() where the StateVector instance is provided, and
 * ::CUSTATEVEC_STATUS_INVALID_VALUE is returned if the constraint is violated.
 *
 * By definition, all wires in \p channelWires argument should be in [0, \c numWires).
 * custatevecExSVUpdaterApply() returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements
 * are not satisfied.
 */

custatevecStatus_t custatevecExSVUpdaterEnqueueUnitaryChannel(
        custatevecExSVUpdaterDescriptor_t   svUpdater,
        const void* const*                  unitaries,
        cudaDataType_t                      unitariesDataType,
        const custatevecExMatrixType_t*     exMatrixTypes,
        int32_t                             numUnitaries,
        custatevecMatrixLayout_t            layout,
        const double*                       probabilities,
        const int32_t*                      channelWires,
        int32_t                             numChannelWires);

/**
 * \brief Enqueue general channel.
 *
 * \param[in,out] svUpdater SVUpdater instance
 * \param[in] matrices host pointer to an array of matrix elements
 * \param[in] matrixDataType dataType of the matrices
 * \param[in] exMatrixTypes matrix types of the specified matrices
 * \param[in] numMatrices the number of matrices.
 * \param[in] layout layout of the matrices
 * \param[in] channelWires wires that the general channel is applied
 * \param[in] numChannelWires the number of wires
 *
 * \details This function enqueues a general channel to SVUpdater.
 *
 * The \p matrices argument is a host pointer to an array of matrices that are assumed
 * to be Kraus operators defining the general quantum channel. Each array element
 * in the matrices argument points to an array of matrix elements that represents a matrix.
 * The actual data type of matrix elements is specified by the \p matrixDataType argument.
 * The \p numMatrices argument specifies the number of matrices.
 * The \p exMatrixTypes is a host array that specifies the matrix types of the matrices.
 * The matrix types specified by \p exMatrixTypes determine the lengths of matrix element
 * arrays specified by the \p matrices argument.
 * The \p layout argument specifies the matrix layout in the same way as described in
 * ::custatevecExSVUpdaterEnqueueMatrix().
 * If a general channel is queued to SVUpdater, state vector will be normalized, and its
 * norm will be 1 after the call of ::custatevecExSVUpdaterApply().
 *
 * Only CUDA_C_64F is acceptable if the SVUpdater data type is CUDA_C_64F by calling
 * ::custatevecExConfigureSVUpdater().  Also, CUDA_C_64F and CUDA_C_32F are acceptable
 * if the SVUpdater data type is CUDA_C_32F.
 *
 * The \p channelWires and \p numChannelWires arguments specify the wires on which the general
 * channel is to be applied.
 * The max number of wires is limited to 15 for all matrix types.
 * However, 10 or more wires is not recommended;
 * the recommended number of wires for typical usage is 6 or fewer.
 *
 * For distributed state vector configurations, the \p numChannelWires argument should be equal to or
 * less than \c numDeviceWires, or the number of local wires on each device. Note that this constraint
 * is not validated by custatevecExSVUpdaterEnqueueGeneralChannel(). The validation occurs later during
 * the call to ::custatevecExSVUpdaterApply() where the StateVector instance is provided, and
 * ::CUSTATEVEC_STATUS_INVALID_VALUE is returned if the constraint is violated.
 *
 * By definition, all wires in \p channelWires argument should be in [0, \c numWires).
 * custatevecExSVUpdaterApply() returns ::CUSTATEVEC_STATUS_INVALID_WIRE if the above requirements
 * are not satisfied.
 *
 * It is the user's responsibility to provide a complete set of Kraus operators. The completeness
 * of Kraus operators is validated immediately during ::custatevecExSVUpdaterEnqueueGeneralChannel()
 * by computing the minimum expectation value using eigenvalues of the Kraus operators. If an
 * incomplete set of Kraus operators is provided, ::custatevecExSVUpdaterEnqueueGeneralChannel()
 * returns ::CUSTATEVEC_STATUS_NUMERICAL_ERROR.
 */

custatevecStatus_t custatevecExSVUpdaterEnqueueGeneralChannel(
        custatevecExSVUpdaterDescriptor_t   svUpdater,
        const void* const*                  matrices,
        cudaDataType_t                      matrixDataType,
        const custatevecExMatrixType_t*     exMatrixTypes,
        int32_t                             numMatrices,
        custatevecMatrixLayout_t            layout,
        const int32_t*                      channelWires,
        int32_t                             numChannelWires);

/**
 * \brief Get the max number of required random numbers.
 *
 * \param[in] svUpdater SVUpdater instance
 * \param[out] maxNumRequiredRandnums the max required number of random numbers.
 *
 * \details Get the max required number of random numbers to call ::custatevecExSVUpdaterApply().
 */

custatevecStatus_t custatevecExSVUpdaterGetMaxNumRequiredRandnums(
        custatevecExSVUpdaterDescriptor_t   svUpdater,
        int32_t*                            maxNumRequiredRandnums);

/**
 * \brief Apply queued operations
 *
 * \param[in,out] svUpdater SVUpdater instance
 * \param[in,out] stateVector state vector instance
 * \param[in] randnums a host pointer to an array of random numbers in the range [0, 1)
 * \param[in] numRandnums the number of random numbers
 *
 * \details Apply operations queued in SVUpdater to the specified state vector.
 *
 * The data type of state vector should be identical to that of SVUpdater specified
 * by calling ::custatevecExConfigureSVUpdater().  Otherwise, this API returns
 * ::CUSTATEVEC_STATUS_INVALID_VALUE.
 * The \p randnums and \p numRandnums arguments pass the array of random numbers
 * that is utilized to apply noise channels. Each random number in the \p randnums array
 * must be in the range [0, 1). The number of required random numbers is retrieved by calling
 * ::custatevecExSVUpdaterGetMaxNumRequiredRandnums().
 *
 * It's a user's responsibility to generate the required number of random numbers in the valid range.
 * If a given random number is not in the range, the value is clipped.
 *
 * This function performs validation of queued operations against the provided state vector and
 * may return the following error codes:
 *
 * - ::CUSTATEVEC_STATUS_INVALID_WIRE: This error is returned if any queued operation references
 *   wire indices that do not exist in the provided state vector. All wires from enqueued operations
 *   (targets, controls, and channelWires) are validated against the wire range [0, numWires) of
 *   the specified state vector instance during the call to this API.
 *
 * - ::CUSTATEVEC_STATUS_INVALID_VALUE: For distributed state vector configurations, this error
 *   is returned if any queued matrix operation has a total number of wires (targets + controls
 *   for matrices, or channelWires for channels) that exceeds the number of local wires on each
 *   device as described in documentation of ::custatevecExSVUpdaterEnqueueMatrix(),
 *   ::custatevecExSVUpdaterEnqueueUnitaryChannel(), and ::custatevecExSVUpdaterEnqueueGeneralChannel().
 *   This check is performed here when the StateVector instance is available.
 *
 * - ::CUSTATEVEC_STATUS_NUMERICAL_ERROR: This error can occur in two scenarios:
 *   (1) When the state vector norm becomes almost close to zero during the application of
 *   operations, making normalization impossible. (2) For general channels, if the completeness of
 *   Kraus operators is violated as determined by computing expectation values during the application
 *   process.
 */

custatevecStatus_t custatevecExSVUpdaterApply(
        custatevecExSVUpdaterDescriptor_t   svUpdater,
        custatevecExStateVectorDescriptor_t stateVector,
        const double*                       randnums,
        int32_t                             numRandnums);

/** \} end of SVUpdater API */

#if defined(__cplusplus)
} // extern "C"
#endif
