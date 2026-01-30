/*
 * Copyright 2025-2026 NVIDIA CORPORATION & AFFILIATES.  All rights reserved.
 *
 * NOTICE TO LICENSEE:
 *
 * This source code and/or documentation ("Licensed Deliverables") are
 * subject to NVIDIA intellectual property rights under U.S. and
 * international Copyright laws.
 *
 * These Licensed Deliverables contained herein is PROPRIETARY and
 * CONFIDENTIAL to NVIDIA and is being provided under the terms and
 * conditions of a form of NVIDIA software license agreement by and
 * between NVIDIA and Licensee ("License Agreement") or electronically
 * accepted by Licensee.  Notwithstanding any terms or conditions to
 * the contrary in the License Agreement, reproduction or disclosure
 * of the Licensed Deliverables to any third party without the express
 * written consent of NVIDIA is prohibited.
 *
 * NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
 * LICENSE AGREEMENT, NVIDIA MAKES NO REPRESENTATION ABOUT THE
 * SUITABILITY OF THESE LICENSED DELIVERABLES FOR ANY PURPOSE.  IT IS
 * PROVIDED "AS IS" WITHOUT EXPRESS OR IMPLIED WARRANTY OF ANY KIND.
 * NVIDIA DISCLAIMS ALL WARRANTIES WITH REGARD TO THESE LICENSED
 * DELIVERABLES, INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY,
 * NONINFRINGEMENT, AND FITNESS FOR A PARTICULAR PURPOSE.
 * NOTWITHSTANDING ANY TERMS OR CONDITIONS TO THE CONTRARY IN THE
 * LICENSE AGREEMENT, IN NO EVENT SHALL NVIDIA BE LIABLE FOR ANY
 * SPECIAL, INDIRECT, INCIDENTAL, OR CONSEQUENTIAL DAMAGES, OR ANY
 * DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
 * WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS
 * ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE
 * OF THESE LICENSED DELIVERABLES.
 *
 * U.S. Government End Users.  These Licensed Deliverables are a
 * "commercial item" as that term is defined at 48 C.F.R. 2.101 (OCT
 * 1995), consisting of "commercial computer software" and "commercial
 * computer software documentation" as such terms are used in 48
 * C.F.R. 12.212 (SEPT 1995) and is provided to the U.S. Government
 * only as a commercial end item.  Consistent with 48 C.F.R.12.212 and
 * 48 C.F.R. 227.7202-1 through 227.7202-4 (JUNE 1995), all
 * U.S. Government End Users acquire the Licensed Deliverables with
 * only those rights set forth herein.
 *
 * Any use of the Licensed Deliverables in individual and commercial
 * software must include, in the user documentation and internal
 * comments to the code, the above Disclaimer and U.S. Government End
 * Users Notice.
 * </blockquote>}
 */

/**
 * @file
 * \brief This file contains all public declarations of the cuPauliProp library.
 */

#pragma once

#include <library_types.h>    // CUDA data types
#include <cuComplex.h>        // CUDA complex numbers
#include <cuda_runtime_api.h> // CUDA runtime API
#include <stdint.h>           // C integer types
 
// LIBRARY VERSION
#define CUPAULIPROP_MAJOR 0 //!< cuPauliProp major version
#define CUPAULIPROP_MINOR 2 //!< cuPauliProp minor version
#define CUPAULIPROP_PATCH 0 //!< cuPauliProp patch version
#define CUPAULIPROP_VERSION (CUPAULIPROP_MAJOR * 10000 + CUPAULIPROP_MINOR * 100 + CUPAULIPROP_PATCH)

// MACRO CONSTANTS
#define CUPAULIPROP_ALLOCATOR_NAME_LEN 64

#if defined(__cplusplus)
extern "C" {
#endif // defined(__cplusplus)

//CONSTANTS AND ENUMERATIONS
 
/**
 * \defgroup constenums Constants and Enumerations
 * \{
 */
 
/**
 * \brief Return status of the library API functions.
 *
 * \details All library API functions return a status
 * which can take one of the following values.
 */
typedef enum
{
  /** The operation has completed successfully. */
  CUPAULIPROP_STATUS_SUCCESS                   = 0,
  /** The library is not initialized. */
  CUPAULIPROP_STATUS_NOT_INITIALIZED           = 1,
  /** An invalid parameter value was passed to a function (normally indicates a user mistake). */
  CUPAULIPROP_STATUS_INVALID_VALUE             = 2,
  /** An internal library error. */
  CUPAULIPROP_STATUS_INTERNAL_ERROR            = 3,
  /** The requested operation is not supported by the library. */
  CUPAULIPROP_STATUS_NOT_SUPPORTED             = 4,
  /** A CUDA error (runtime or any CUDA library). */
  CUPAULIPROP_STATUS_CUDA_ERROR                = 5,
  /** Distributed communication service failure. */
  CUPAULIPROP_STATUS_DISTRIBUTED_FAILURE       = 6,
} cupaulipropStatus_t;

/**
* \brief Supported compute types.
*/
typedef enum
{
  CUPAULIPROP_COMPUTE_32F = (1U << 2U),  ///< single-precision floating-point compute type
  CUPAULIPROP_COMPUTE_64F = (1U << 4U),  ///< double-precision floating-point compute type
} cupaulipropComputeType_t;

/**
 * \brief Memory spaces for workspace buffer allocation.
 */
typedef enum
{
  CUPAULIPROP_MEMSPACE_DEVICE = 0,  ///< Device memory space (GPU)
  CUPAULIPROP_MEMSPACE_HOST   = 1,  ///< Host memory space (CPU)
} cupaulipropMemspace_t;
 
/**
* \brief Kinds of workspace memory buffers.
*/
typedef enum
{
  CUPAULIPROP_WORKSPACE_SCRATCH = 0,  ///< Scratch workspace memory
//CUPAULIPROP_WORKSPACE_CACHE   = 1,  ///< Cache workspace memory (must stay valid with unmodified content until all referencing operations are completed)
} cupaulipropWorkspaceKind_t;

/**
 * \brief Pauli operator expansion truncation strategies.
 */
typedef enum
{
  CUPAULIPROP_TRUNCATION_STRATEGY_COEFFICIENT_BASED = 0,  ///< Coefficient-based truncation strategy
  CUPAULIPROP_TRUNCATION_STRATEGY_PAULI_WEIGHT_BASED = 1, ///< Pauli weight-based truncation strategy
} cupaulipropTruncationStrategyKind_t;

/**
 * \brief Sort order for Pauli expansions.
 */
typedef enum
{
  CUPAULIPROP_SORT_ORDER_NONE = 0,                 ///< No sort order (unsorted)
  CUPAULIPROP_SORT_ORDER_INTERNAL = 1,             ///< Internal sort order (implementation-defined)
  CUPAULIPROP_SORT_ORDER_LITTLE_ENDIAN_BITWISE = 2 ///< Little-endian bitwise sort order
} cupaulipropSortOrder_t;

/**
 * \brief Pauli operators.
 */
typedef enum
{
  CUPAULIPROP_PAULI_I = 0,  ///< Identity operator
  CUPAULIPROP_PAULI_X = 1,  ///< Pauli-X operator
  CUPAULIPROP_PAULI_Y = 2,  ///< Pauli-Y operator
  CUPAULIPROP_PAULI_Z = 3,  ///< Pauli-Z operator
} cupaulipropPauliKind_t;

/**
 * \brief Clifford gates.
 */
typedef enum
{
  CUPAULIPROP_CLIFFORD_GATE_I = 0,       ///< Identity gate
  CUPAULIPROP_CLIFFORD_GATE_X = 1,       ///< Pauli-X gate
  CUPAULIPROP_CLIFFORD_GATE_Y = 2,       ///< Pauli-Y gate
  CUPAULIPROP_CLIFFORD_GATE_Z = 3,       ///< Pauli-Z gate
  CUPAULIPROP_CLIFFORD_GATE_H = 4,       ///< Hadamard gate
  CUPAULIPROP_CLIFFORD_GATE_S = 5,       ///< Phase gate
  CUPAULIPROP_CLIFFORD_GATE_CX = 7,      ///< CX (CNOT) gate
  CUPAULIPROP_CLIFFORD_GATE_CY = 8,      ///< CY gate
  CUPAULIPROP_CLIFFORD_GATE_CZ = 9,      ///< CZ gate
  CUPAULIPROP_CLIFFORD_GATE_SWAP = 10,   ///< SWAP gate
  CUPAULIPROP_CLIFFORD_GATE_ISWAP = 11,  ///< iSWAP gate
  CUPAULIPROP_CLIFFORD_GATE_SQRTX = 12,  ///< Sqrt X gate
  CUPAULIPROP_CLIFFORD_GATE_SQRTY = 13,  ///< Sqrt Y gate
  CUPAULIPROP_CLIFFORD_GATE_SQRTZ = 14,  ///< Sqrt Z gate
} cupaulipropCliffordGateKind_t;

/** 
 * \brief Kinds of quantum operators
 */
typedef enum
{
  CUPAULIPROP_EXPANSION_KIND_PAULI_ROTATION_GATE = 0,
  CUPAULIPROP_EXPANSION_KIND_CLIFFORD_GATE = 1,
  CUPAULIPROP_EXPANSION_KIND_PAULI_NOISE_CHANNEL = 2
} cupaulipropQuantumOperatorKind_t;

// TYPES AND STRUCTURES
 
/**
 * \defgroup typestructs Types and Data Structures
 * \{
 */

/**
 * \brief Opaque data structure holding the library context (context handle).
 *
 * \details Context handle holds the library context (device properties, system information, etc.).
 * A context handle must be initialized prior and destroyed after any other library API call
 * using the `cupaulipropCreate` and `cupaulipropDestroy` API functions, respectively.
 */
typedef void * cupaulipropHandle_t;

/**
 * \brief Opaque data structure describing a workspace memory buffer.
 */
typedef void * cupaulipropWorkspaceDescriptor_t;

/**
 * \brief Opaque data structure representing a Pauli operator expansion,
 * that is, a linear combination of Pauli operator terms.
 */
typedef void * cupaulipropPauliExpansion_t;

/**
 * \brief Opaque data structure describing a subset of Pauli operator terms (view)
 * inside a Pauli operator expansion.
 */
typedef void * cupaulipropPauliExpansionView_t;

/**
 * \brief Opaque data structure representing a quantum operator
 * which includes quantum gates and quantum channels.
 */
typedef void * cupaulipropQuantumOperator_t;

/**
 * \brief Type of packed integer for representing Pauli operator terms.
 */
typedef uint64_t cupaulipropPackedIntegerType_t;

/**
 * \brief Explicit data structure specifying a Pauli operator term,
 * that is, a single Pauli string in a Pauli expansion.
 *
 * \details A Pauli operator term is a single Pauli string in a Pauli expansion.
 * It is represented by two non-owning pointers into the array containing the Pauli string (X and Z bits) and into the array containing the coefficients respectively.
 * The length of the `xzbits` array element containing the packed Pauli string is equal
 * to twice the number of qubits divided by the number of bits in the packed integer type `cupaulipropPackedIntegerType_t`.
 */
typedef struct
{
  const cupaulipropPackedIntegerType_t * xzbits;  ///< non-owning pointer to the packed X and Z bits arranged as an array of `cupaulipropPackedIntegerType_t`
  const void * coef;  ///< non-owning pointer to the coefficient (real/complex float/double)
} cupaulipropPauliTerm_t;

/**
 * \brief Explicit data structure specifying a truncation strategy.
 * \details A truncation strategy is a combination of a strategy kind and a parameter structure.
 * The parameter structure is a pointer to a struct containing the parameters for the truncation strategy.
 * Each kind of truncation strategy has its own explicit data structure for its parameters.
 */
typedef struct
{
  cupaulipropTruncationStrategyKind_t strategy; ///< which kind of truncation strategy to apply
  void * paramStruct; ///< pointer to the parameter structure for the truncation strategy
} cupaulipropTruncationStrategy_t;

/**
 * \brief Explicit data structure specifying parameters for the coefficient-based truncation strategy.
 * \details The coefficient-based truncation strategy truncates the Pauli operator expansion based on the coefficients of the Pauli operator terms.
 * Terms in the Pauli operator expansion with coefficients of magnitude equal or less than the cutoff value are truncated.
 */
typedef struct
{
  double cutoff;  ///< cutoff value for the magnitude of the Pauli term's coefficient
} cupaulipropCoefficientTruncationParams_t;

/**
 * \brief Explicit data structure specifying parameters for the Pauli weight-based truncation strategy.
 * \details The Pauli weight-based truncation strategy truncates the Pauli operator expansion based on the Pauli weight, that is, the number of non-identity Paulis in the Pauli string.
 * Terms in the Pauli operator expansion with Pauli weight greater than the cutoff value are truncated.
 */
typedef struct
{
  int32_t cutoff;  ///< cutoff value for the number of non-identity Paulis in the Pauli string
} cupaulipropPauliWeightTruncationParams_t;

/** \} end typestructs */
 
// API FUNCTIONS
 
/**
 * \defgroup contextAPI Library Initialization and Management API
 * \{
 */
 
/**
 * \brief Returns the semantic version number of the cuPauliProp library.
 */
size_t cupaulipropGetVersion();

/**
 * \brief Returns the description string for an error code.
 * 
 * \param[in] error Error code to get the description string for.
 * \returns the error description string.
 * \remarks non-blocking, no reentrant, and thread-safe.
 */
const char * cupaulipropGetErrorString(cupaulipropStatus_t error);

/**
 * \brief Returns the number of packed integers of cupaulipropPackedIntegerType_t needed to represent
 * the X bits (or equivalently, the Z bits) of a single Pauli string.
 * 
 * \details Each Pauli string is represented by storing X bits and Z bits separately in packed integers.
 * This function returns the number of packed integers needed for ONE set of bits (either X or Z).
 * The total storage for a complete Pauli string is twice this value (one set for X bits, one set for Z bits).
 * For example, for 64 qubits, this returns 1, and the total storage is 2 uint64 integers (1 for X bits + 1 for Z bits).
 * For 65 qubits, this returns 2, and the total storage is 4 uint64 integers (2 for X bits + 2 for Z bits).
 * Note that the integers are required to be zero padded for the most significant bits if the number of qubits is not a multiple of 64.
 * 
 * \param[in] numQubits Number of qubits.
 * \param[out] numPackedIntegers Number of uint64 integers needed to store X bits (or Z bits) for one Pauli string.
 * To get the total storage requirement, multiply this value by 2.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropGetNumPackedIntegers(int32_t numQubits,
                                                    int32_t * numPackedIntegers);                       

/**
 * \brief Creates and initializes the library context.
 * 
 * \param[out] handle Library handle.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropCreate(cupaulipropHandle_t * handle); 
 
/**
 * \brief Destroys the library context.
 * 
 * \param[in] handle Library handle.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropDestroy(cupaulipropHandle_t handle);
 
/** \} end contextAPI */
 
/**
 * \defgroup workspaceAPI Workspace Management API
 * \{
 */
 
/**
 * \brief Creates a workspace descriptor.
 * 
 * \param[in] handle Library handle.
 * \param[out] workspaceDesc Workspace descriptor.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropCreateWorkspaceDescriptor(cupaulipropHandle_t handle, 
                                                         cupaulipropWorkspaceDescriptor_t * workspaceDesc);

/**
 * \brief Destroys a workspace descriptor.
 * 
 * \param[inout] workspaceDesc Workspace descriptor.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropDestroyWorkspaceDescriptor(cupaulipropWorkspaceDescriptor_t workspaceDesc);

/**
 * \brief Queries the required workspace buffer size.
 * 
 * \param[in] handle Library handle.
 * \param[in] workspaceDesc Workspace descriptor.
 * \param[in] memSpace Memory space.
 * \param[in] workspaceKind Workspace kind.
 * \param[out] memoryBufferSize Required workspace buffer size in bytes.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropWorkspaceGetMemorySize(const cupaulipropHandle_t handle,
                                                      const cupaulipropWorkspaceDescriptor_t workspaceDesc,
                                                      cupaulipropMemspace_t memSpace,
                                                      cupaulipropWorkspaceKind_t workspaceKind,
                                                      int64_t * memoryBufferSize);

/**
 * \brief Attaches memory to a workspace buffer.
 * 
 * \param[in] handle Library handle.
 * \param[inout] workspaceDesc Workspace descriptor.
 * \param[in] memSpace Memory space.
 * \param[in] workspaceKind Workspace kind.
 * \param[in] memoryBuffer Pointer to a user-owned memory buffer
 * to be used by the specified workspace.
 * \param[in] memoryBufferSize Size of the provided memory buffer in bytes.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropWorkspaceSetMemory(const cupaulipropHandle_t handle,
                                                  cupaulipropWorkspaceDescriptor_t workspaceDesc,
                                                  cupaulipropMemspace_t memSpace,
                                                  cupaulipropWorkspaceKind_t workspaceKind,
                                                  void * memoryBuffer,
                                                  int64_t memoryBufferSize);
 
/**
 * \brief Retrieves a workspace buffer.
 * 
 * \param[in] handle Library handle.
 * \param[in] workspaceDescr Workspace descriptor.
 * \param[in] memSpace Memory space.
 * \param[in] workspaceKind Workspace kind.
 * \param[out] memoryBuffer Pointer to a user-owned memory buffer
 * used by the specified workspace.
 * \param[out] memoryBufferSize Size of the memory buffer in bytes.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropWorkspaceGetMemory(const cupaulipropHandle_t handle,
                                                  const cupaulipropWorkspaceDescriptor_t workspaceDescr,
                                                  cupaulipropMemspace_t memSpace,
                                                  cupaulipropWorkspaceKind_t workspaceKind,
                                                  void ** memoryBuffer,
                                                  int64_t * memoryBufferSize);

/** \} end workspaceAPI */
 
/**
 * \defgroup pauliExpansionAPI Pauli Expansion API
 * \{
 */
 
/**
 * \brief Creates a Pauli operator expansion.
 *
 * \note The `xzBitsBuffer` and `coefBuffer` must both be either GPU-accessible memory
 * or CPU-accessible memory. Mixing memory types between these two buffers is not supported.
 *
 * \param[in] handle Library handle.
 * \param[in] numQubits Number of qubits.
 * \param[in] xzBitsBuffer Pointer to a user-owned memory buffer
 * to be used by the created Pauli operator expansion for storing the X and Z bits
 * for each Pauli operator term. The first `numTerms` Pauli operator terms will define
 * the current Pauli operator expansion.
 * \param[in] xzBitsBufferSize Size (in bytes) of the provided memory buffer for storing the X and Z bits.
 * \param[in] coefBuffer Pointer to a user-owned memory buffer
 * to be used by the created Pauli operator expansion for storing the coefficients
 * for all Pauli operator terms. The first `numTerms` Pauli operator terms will define
 * the current Pauli operator expansion.
 * \param[in] coefBufferSize Size (in bytes) of the provided memory buffer for storing the coefficients.
 * \param[in] dataType Data type of the coefficients in the Pauli operator expansion.  
 * \param[in] numTerms Number of the Pauli operator terms stored in the provided memory buffer
 * (the first `numTerms` components define the current Pauli operator expansion).
 * \param[in] sortOrder Sort order of the expansion. Use `CUPAULIPROP_SORT_ORDER_NONE` for unsorted expansions.
 * \param[in] hasDuplicates Whether or not there are duplicates in the expansion, i.e. several terms with identical X and Z bits.
 * \param[out] pauliExpansion Pauli operator expansion.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropCreatePauliExpansion(const cupaulipropHandle_t handle,
                                                    int32_t numQubits,
                                                    void * xzBitsBuffer,
                                                    int64_t xzBitsBufferSize,
                                                    void * coefBuffer,
                                                    int64_t coefBufferSize,
                                                    cudaDataType_t dataType,
                                                    int64_t numTerms,
                                                    cupaulipropSortOrder_t sortOrder,
                                                    int32_t hasDuplicates,
                                                    cupaulipropPauliExpansion_t * pauliExpansion);          


/**
 * \brief Destroys a Pauli operator expansion.
 * 
 * \param[inout] pauliExpansion Pauli operator expansion.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropDestroyPauliExpansion(cupaulipropPauliExpansion_t pauliExpansion);

/**
 * \brief Gets access to the storage of a Pauli operator expansion.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[out] xzBitsBuffer Pointer to a user-owned memory buffer
 * used by the Pauli operator expansion for storing the X and Z bits for each Pauli operator term.
 * \param[out] xzBitsBufferSize Size (in bytes) of the memory buffer for X and Z bits.
 * \param[out] coefBuffer Pointer to a user-owned memory buffer used by the Pauli operator expansion
 * for storing the coefficients for each Pauli operator term.
 * \param[out] coefBufferSize Size (in bytes) of the memory buffer for storing the coefficients.
 * \param[out] numTerms Current number of Pauli operator terms in the Pauli operator expansion
 * (first `numTerms` terms define the current Pauli operator expansion).
 * \param[out] location Storage location of the Pauli operator expansion
 * (whether it is on the host or device).
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetStorageBuffer(const cupaulipropHandle_t handle,
                                                              const cupaulipropPauliExpansion_t pauliExpansion,
                                                              void ** xzBitsBuffer,
                                                              int64_t * xzBitsBufferSize,
                                                              void ** coefBuffer,
                                                              int64_t * coefBufferSize,
                                                              int64_t * numTerms,
                                                              cupaulipropMemspace_t * location);

/**
 * \brief Gets the number of qubits of a Pauli operator expansion.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[out] numQubits Number of qubits.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetNumQubits(const cupaulipropHandle_t handle,      
                                                          const cupaulipropPauliExpansion_t pauliExpansion,
                                                          int32_t * numQubits);

/**
 * \brief Gets the number of terms in the Pauli operator expansion.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[out] numTerms Number of terms.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetNumTerms(const cupaulipropHandle_t handle,
                                                         const cupaulipropPauliExpansion_t pauliExpansion,
                                                         int64_t * numTerms);

/**
 * \brief Gets the data type of the coefficients in a Pauli operator expansion.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[out] dataType Data type.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetDataType(const cupaulipropHandle_t handle,
                                                         const cupaulipropPauliExpansion_t pauliExpansion,
                                                         cudaDataType_t * dataType);

/**
 * \brief Queries the sort order of a Pauli operator expansion.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[out] sortOrder Sort order of the Pauli operator expansion.
 * `CUPAULIPROP_SORT_ORDER_NONE` indicates the expansion is unsorted.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetSortOrder(const cupaulipropHandle_t handle,
                                                          const cupaulipropPauliExpansion_t pauliExpansion,
                                                          cupaulipropSortOrder_t * sortOrder);
              
/**
 * \brief Queries whether a Pauli operator expansion is deduplicated. i.e. guaranteed to not contain duplicate
 * Pauli strings or may otherwise potentially contain duplicates Pauli strings.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[out] isDeduplicated Indicating whether the Pauli operator expansion is deduplicated.
 * True (!= 0) if the Pauli operator expansion is guaranteed to not contain duplicate Pauli strings,
 * false (0) if no such guarantee can be made (though it may be incidentally the case).
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionIsDeduplicated(const cupaulipropHandle_t handle,
                                                            const cupaulipropPauliExpansion_t pauliExpansion,
                                                            int32_t * isDeduplicated);

/**
 * \brief Gets access to a specific term of a Pauli operator expansion.
 * 
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[in] termIndex Index of the term.
 * \param[out] term Pauli operator term.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetTerm(const cupaulipropHandle_t handle,
                                                     const cupaulipropPauliExpansion_t pauliExpansion,
                                                     int64_t termIndex,
                                                     cupaulipropPauliTerm_t * term);

/**
 * \brief Creates a non-owning view of a contiguous range of Pauli operator terms
 * inside a Pauli operator expansion.
 *
 * \param[in] handle Library handle.
 * \param[in] pauliExpansion Pauli operator expansion.
 * \param[in] startIndex Start index of the range (inclusive, first element in the range).
 * \param[in] endIndex End index of the range (exclusive, one past the last element).
 * \param[out] view View to a range of Pauli terms inside the Pauli operator expansion.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionGetContiguousRange(const cupaulipropHandle_t handle,
                                                                const cupaulipropPauliExpansion_t pauliExpansion,
                                                                int64_t startIndex,
                                                                int64_t endIndex,
                                                                cupaulipropPauliExpansionView_t * view);

/**
 * \brief Destroys a Pauli expansion view.
 * 
 * \param[inout] view Pauli expansion view.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropDestroyPauliExpansionView(cupaulipropPauliExpansionView_t view);

/**
 * \brief Returns the number of Pauli terms in a Pauli expansion view.
 * 
 * \param[in] handle Library handle.
 * \param[in] view Pauli expansion view.
 * \param[out] numTerms Number of terms.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewGetNumTerms(const cupaulipropHandle_t handle,
                                                             const cupaulipropPauliExpansionView_t view,
                                                             int64_t * numTerms);

/**
 * \brief Gets the storage location of a Pauli expansion view
 * (whether its elements are stored on the host or device).
 * 
 * \param[in] view Pauli expansion view.
 * \param[out] location Location.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewGetLocation(const cupaulipropPauliExpansionView_t view,
                                                             cupaulipropMemspace_t * location);

/**
 * \brief Gets a specific term of a Pauli expansion view.
 * 
 * \param[in] handle Library handle.
 * \param[in] view Pauli expansion view.
 * \param[in] termIndex Index of the term in the Pauli expansion view.
 * \param[out] term Pauli operator term.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewGetTerm(const cupaulipropHandle_t handle,
                                                         const cupaulipropPauliExpansionView_t view,
                                                         int64_t termIndex,
                                                         cupaulipropPauliTerm_t * term);

/**
 * \brief Prepares a Pauli expansion view for deduplication.
 * 
 * \details This function queries the workspace requirements for deduplicating
 * a Pauli expansion view (removing duplicate Pauli strings and summing their coefficients).
 * 
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to be deduplicated.
 * \param[in] sortOrder Sort order to apply to the output expansion. Use `CUPAULIPROP_SORT_ORDER_NONE` if sorting is not required.
 * Currently, only `CUPAULIPROP_SORT_ORDER_INTERNAL` and `CUPAULIPROP_SORT_ORDER_NONE` are supported.  
 * \param[in] maxWorkspaceSize Maximum workspace size limit in bytes.
 * \param[out] workspace Workspace descriptor with the required workspace buffer size.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewPrepareDeduplication(const cupaulipropHandle_t handle,
                                                                      const cupaulipropPauliExpansionView_t viewIn,
                                                                      cupaulipropSortOrder_t sortOrder,
                                                                      int64_t maxWorkspaceSize,
                                                                      cupaulipropWorkspaceDescriptor_t workspace);

/**
 * \brief Deduplicates a Pauli expansion view.
 * 
 * \details This function removes duplicate Pauli strings from a sorted Pauli expansion view
 * and sums their coefficients, populating the output expansion with the deduplicated view.
 *
 * \note This method is blocking, i.e. it will wait for the operation to complete before returning to the caller.
 * \note The storage location of both the input view and the output expansion must be GPU-accessible (i.e. `CUPAULIPROP_MEMSPACE_DEVICE`).
 *
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to be deduplicated.
 * \param[out] expansionOut Pauli expansion to be populated with the deduplicated view.
 * \param[in] sortOrder Sort order to apply to the output expansion. Use `CUPAULIPROP_SORT_ORDER_NONE` if sorting is not required.
 * Currently, only `CUPAULIPROP_SORT_ORDER_INTERNAL` and `CUPAULIPROP_SORT_ORDER_NONE` are supported.  
 * \param[in] workspace Allocated workspace descriptor.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewExecuteDeduplication(const cupaulipropHandle_t handle,
                                                                      const cupaulipropPauliExpansionView_t viewIn,
                                                                      cupaulipropPauliExpansion_t expansionOut,
                                                                      cupaulipropSortOrder_t sortOrder,
                                                                      cupaulipropWorkspaceDescriptor_t workspace,
                                                                      cudaStream_t stream);

/**
 * \brief Prepares a Pauli expansion view for sorting.
 * 
 * \details This function queries the workspace requirements for sorting
 * a Pauli expansion view according to the specified sort order.
 *
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to be sorted.
 * \param[in] sortOrder Sort order to apply.
 * \param[in] maxWorkspaceSize Maximum workspace size limit in bytes.
 * \param[out] workspace Workspace descriptor with the required workspace buffer size.
 * \return cupaulipropStatus_t
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewPrepareSort(const cupaulipropHandle_t handle,
                                                             const cupaulipropPauliExpansionView_t viewIn,
                                                             cupaulipropSortOrder_t sortOrder,
                                                             int64_t maxWorkspaceSize,
                                                             cupaulipropWorkspaceDescriptor_t workspace);

/**
 * \brief Sorts a Pauli expansion view.
 * 
 * \details This function sorts a Pauli expansion view according to the specified sort order,
 * writing the result to the output expansion.
 * 
 * \note This function is non-blocking, i.e. it will return immediately and the sorting will be performed asynchronously on the stream.
 * \note The storage location of both the input view and the output expansion must be GPU-accessible (i.e. `CUPAULIPROP_MEMSPACE_DEVICE`).
 *
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to be sorted.
 * \param[out] expansionOut Pauli expansion to be populated with the sorted view.
 * \param[in] sortOrder Sort order to apply.
 * \param[in] workspace Allocated workspace descriptor.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewExecuteSort(const cupaulipropHandle_t handle,
                                                             const cupaulipropPauliExpansionView_t viewIn,
                                                             cupaulipropPauliExpansion_t expansionOut,
                                                             cupaulipropSortOrder_t sortOrder,
                                                             cupaulipropWorkspaceDescriptor_t workspace,
                                                             cudaStream_t stream);

/**
 * \brief Populates a Pauli operator expansion from a Pauli expansion view.
 *
 * \note This function is non-blocking, i.e. it will return immediately and the population will be performed asynchronously on the stream.
 *
 * \note The Pauli expansion view must not belong to the same Pauli operator expansion.
 * \param[in] handle Library handle.
 * \param[in] viewIn Input Pauli expansion view.
 * \param[out] expansionOut Populated Pauli operator expansion.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
*/
cupaulipropStatus_t cupaulipropPauliExpansionPopulateFromView(const cupaulipropHandle_t handle,
                                                              const cupaulipropPauliExpansionView_t viewIn,
                                                              cupaulipropPauliExpansion_t expansionOut,
                                                              cudaStream_t stream);

/**
 * \brief Prepares a Pauli expansion view for computing the product trace of two Pauli expansion views.
 * 
 * \param[in] handle Library handle.
 * \param[in] view1 First Pauli expansion view to be traced.
 * \param[in] view2 Second Pauli expansion view to be traced.
 * \param[in] maxWorkspaceSize Maximum workspace size limit in bytes.
 * \param[out] workspace Workspace descriptor with the required workspace buffer size.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewPrepareTraceWithExpansionView(const cupaulipropHandle_t handle,
                                                                               const cupaulipropPauliExpansionView_t view1,
                                                                               const cupaulipropPauliExpansionView_t view2,
                                                                               int64_t maxWorkspaceSize,
                                                                               cupaulipropWorkspaceDescriptor_t workspace);

/**
 * \brief Computes the trace of two Pauli expansion views.
 * 
 * \details This function computes the trace `tr(view1 view2)` of the composition (i.e. product) of two Pauli expansion views.
 * Optionally, the adjoint of the first view `view1` can be taken when computing the trace.
 * Currently, both input views must not contain duplicates.
 * 
 * \note This function is non-blocking, i.e. it will return immediately and the tracing will be performed asynchronously on the stream.
 * \note The storage location of both input views must be GPU-accessible (i.e. `CUPAULIPROP_MEMSPACE_DEVICE`).
 *
 * \param[in] handle Library handle.
 * \param[in] view1 First Pauli expansion view.
 * \param[in] view2 Second Pauli expansion view.
 * \param[in] takeAdjoint1 Whether or not the adjoint of the first view is taken.
 * True  `(!= 0)` if the adjoint is taken, false `(0)` otherwise.
 * \param[out] trace Pointer to CPU-accessible memory where the trace value will be written.
 * The numerical type must match the data type of the views' coefficients.
 * \param[in] workspace Allocated workspace descriptor.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewComputeTraceWithExpansionView(const cupaulipropHandle_t handle,
                                                                               const cupaulipropPauliExpansionView_t view1,
                                                                               const cupaulipropPauliExpansionView_t view2,
                                                                               int32_t takeAdjoint1,
                                                                               void * trace,
                                                                               cupaulipropWorkspaceDescriptor_t workspace,
                                                                               cudaStream_t stream);

/**
 * \brief Prepares a Pauli expansion view for tracing with the zero state, i.e. computing `Tr(view * |0...0>)` .
 * 
 * \param[in] handle Library handle.
 * \param[in] view Pauli expansion view to be traced.
 * \param[in] maxWorkspaceSize Maximum workspace size limit in bytes.
 * \param[out] workspace Workspace descriptor with the required workspace buffer size.
 * \return cupaulipropStatus_t 
 */
 cupaulipropStatus_t cupaulipropPauliExpansionViewPrepareTraceWithZeroState(const cupaulipropHandle_t handle,
                                                                            const cupaulipropPauliExpansionView_t view,
                                                                            int64_t maxWorkspaceSize,
                                                                            cupaulipropWorkspaceDescriptor_t workspace);

/**
 * \brief Traces a Pauli expansion view with the zero state, i.e. computes `Tr(view * |0...0>)` .
 * 
 * \note This function is non-blocking, i.e. it will return immediately and the tracing will be performed asynchronously on the stream.
 * \note The storage location of the input view must be GPU-accessible (i.e. `CUPAULIPROP_MEMSPACE_DEVICE`).
 *  
 * \param[in] handle Library handle.
 * \param[in] view Pauli expansion view to be traced.
 * \param[out] trace Pointer to CPU-accessible memory where the trace value will be written.
 * The numerical type must match the data type of the views' coefficients.
 * \param[in] workspace Allocated workspace descriptor.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewComputeTraceWithZeroState(const cupaulipropHandle_t handle,
                                                                           const cupaulipropPauliExpansionView_t view,
                                                                           void * trace,
                                                                           cupaulipropWorkspaceDescriptor_t workspace,
                                                                           cudaStream_t stream);

/**
 * \brief Prepares a Pauli expansion view for quantum operator application.
 *
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to apply a quantum operator to.
 * \param[in] quantumOperator Quantum operator to be applied.
 * \param[in] sortOrder Sort order to apply to the output expansion. Use `CUPAULIPROP_SORT_ORDER_NONE` if sorting is not required.
 * Currently, only `CUPAULIPROP_SORT_ORDER_INTERNAL` and `CUPAULIPROP_SORT_ORDER_NONE` are supported.  
 * \param[in] keepDuplicates Whether or not the output expansion is allowed to contain duplicates.
 * \param[in] numTruncationStrategies Number of Pauli expansion truncation strategies.
 * \param[in] truncationStrategies Pauli expansion truncation strategies.
 * \param[in] maxWorkspaceSize Maximum workspace size limit in bytes.
 * \param[out] requiredXZBitsBufferSize Required size (in bytes) of the X and Z bits output buffer.
 * \param[out] requiredCoefBufferSize Required size (in bytes) of the coefficients output buffer.
 * \param[in] workspace Workspace descriptor with the required workspace buffer size.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewPrepareOperatorApplication(const cupaulipropHandle_t handle,
                                                                            const cupaulipropPauliExpansionView_t viewIn,
                                                                            const cupaulipropQuantumOperator_t quantumOperator,
                                                                            cupaulipropSortOrder_t sortOrder,
                                                                            int32_t keepDuplicates,
                                                                            int32_t numTruncationStrategies,
                                                                            const cupaulipropTruncationStrategy_t truncationStrategies[],
                                                                            int64_t maxWorkspaceSize,
                                                                            int64_t * requiredXZBitsBufferSize,
                                                                            int64_t * requiredCoefBufferSize,
                                                                            cupaulipropWorkspaceDescriptor_t workspace);

/**
 * \brief Computes the application of a quantum operator to a Pauli expansion view.
 * 
 * \details This function computes the application of a quantum operator to a Pauli expansion view.
 * Optionally, the adjoint of the quantum operator can be applied when computing the application.
 * Optionally, truncations can be applied to the output expansion to reduce the number of terms.
 *
 * \note This function is blocking on exit, i.e. it will wait for the operation to complete before returning to the caller.
 * \note The storage location of the input view and the output expansion must be GPU-accessible (i.e. `CUPAULIPROP_MEMSPACE_DEVICE`).
 *
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to apply a quantum operator to.
 * \param[inout] expansionOut Pauli expansion to be overwritten with the result.
 * The terms of the output expansion will be sorted with respect to the specified sortOrder
 * and their Pauli strings will be unique if keepDuplicates is set to false.
 * Their state is queryable on the output expansion after this function call via `cupaulipropPauliExpansionGetSortOrder()` and `cupaulipropPauliExpansionIsDeduplicated()`.
 * \param[in] quantumOperator Quantum operator to be applied.
 * \param[in] adjoint Whether or not the adjoint of the quantum operator is applied.
 * True (!= 0) if the adjoint is applied, false (0) otherwise.
 * \param[in] sortOrder Sort order to apply to the output expansion. Use `CUPAULIPROP_SORT_ORDER_NONE` if sorting is not required.
 * Currently, only `CUPAULIPROP_SORT_ORDER_INTERNAL` and `CUPAULIPROP_SORT_ORDER_NONE` are supported.
 * \param[in] keepDuplicates Whether or not the output expansion is allowed to contain duplicates.
 * \param[in] numTruncationStrategies Number of Pauli expansion truncation strategies.
 * \param[in] truncationStrategies Pauli expansion truncation strategies.
 * \param[in] workspace Allocated workspace descriptor.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewComputeOperatorApplication(const cupaulipropHandle_t handle,
                                                                            const cupaulipropPauliExpansionView_t viewIn,
                                                                            cupaulipropPauliExpansion_t expansionOut,
                                                                            const cupaulipropQuantumOperator_t quantumOperator,
                                                                            int32_t adjoint,
                                                                            cupaulipropSortOrder_t sortOrder,
                                                                            int32_t keepDuplicates,
                                                                            int32_t numTruncationStrategies,
                                                                            const cupaulipropTruncationStrategy_t truncationStrategies[],
                                                                            cupaulipropWorkspaceDescriptor_t workspace,
                                                                            cudaStream_t stream);

/**
 * \brief Prepares a Pauli expansion view for truncation.
 *
 * \details This function queries the workspace requirements for truncating
 * a Pauli expansion view based on the given truncation strategies.
 *
 * \param[in] handle Library handle.
 * \param[in] viewIn Pauli expansion view to be truncated.
 * \param[in] numTruncationStrategies Number of Pauli expansion truncation strategies.
 * \param[in] truncationStrategies Pauli expansion truncation strategies.
 * \param[in] maxWorkspaceSize Maximum workspace size limit in bytes.
 * \param[out] workspace Workspace descriptor with the required workspace buffer size.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewPrepareTruncation(const cupaulipropHandle_t handle,
                                                                   const cupaulipropPauliExpansionView_t viewIn,
                                                                   int32_t numTruncationStrategies,
                                                                   const cupaulipropTruncationStrategy_t truncationStrategies[],
                                                                   int64_t maxWorkspaceSize,
                                                                   cupaulipropWorkspaceDescriptor_t workspace);

/**
 * \brief Truncates a Pauli expansion view.
 * 
 * \details This function applies truncation strategies to a Pauli expansion view,
 * removing terms that do not satisfy the truncation criteria, and writes the result
 * to the output expansion.
 *
 * \note This function is blocking on exit, i.e. it will wait for the operation to complete before returning to the caller.
 * \note The storage location of the input view and the output expansion must be GPU-accessible (i.e. `CUPAULIPROP_MEMSPACE_DEVICE`).
 * 
 * \param[in] handle Library handle.
 * \param[in] viewIn Input Pauli expansion view to be truncated.
 * \param[inout] expansionOut Output Pauli operator expansion.
 * \param[in] numTruncationStrategies Number of Pauli expansion truncation strategies.
 * \param[in] truncationStrategies Pauli expansion truncation strategies.
 * \param[in] workspace Allocated workspace descriptor.
 * \param[in] stream CUDA stream to be used for the operation.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropPauliExpansionViewExecuteTruncation(const cupaulipropHandle_t handle,
                                                                   const cupaulipropPauliExpansionView_t viewIn,
                                                                   cupaulipropPauliExpansion_t expansionOut,
                                                                   int32_t numTruncationStrategies,
                                                                   const cupaulipropTruncationStrategy_t truncationStrategies[],
                                                                   cupaulipropWorkspaceDescriptor_t workspace,
                                                                   cudaStream_t stream);

/**
 * \brief Creates a Clifford gate.
 * 
 * \param[in] handle Library handle.
 * \param[in] cliffordGateKind Clifford gate kind.
 * \param[in] qubitIndices Qubit indices.
 * \param[out] oper Quantum operator associated with the Clifford gate.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropCreateCliffordGateOperator(const cupaulipropHandle_t handle,
                                                          cupaulipropCliffordGateKind_t cliffordGateKind,
                                                          const int32_t qubitIndices[],
                                                          cupaulipropQuantumOperator_t * oper);

/**
 * \brief Creates a Pauli rotation gate,  `exp(-i * angle/2 * P)`, for a rotation of `angle` around the Pauli string `P`.
 *
 * \param[in] handle Library handle.
 * \param[in] angle Rotation angle in radians.
 * \param[in] numQubits Number of qubits.
 * \param[in] qubitIndices Qubit indices. If NULL, the qubit indices are assumed to be [0, 1, 2, ..., numQubits-1].
 * \param[in] paulis Pauli operators for each qubit index.
 * \param[out] oper Quantum operator associated with the Pauli rotation gate.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropCreatePauliRotationGateOperator(const cupaulipropHandle_t handle,
                                                               double angle,
                                                               int32_t numQubits,
                                                               const int32_t qubitIndices[],
                                                               const cupaulipropPauliKind_t paulis[],
                                                               cupaulipropQuantumOperator_t * oper);

/**
 * \brief Creates a Pauli noise channel.
 * 
 * \param[in] handle Library handle.
 * \param[in] numQubits Number of qubits. Only 1 and 2 qubits are supported.
 * \param[in] qubitIndices Qubit indices.
 * \param[in] probabilities Probabilities for each Pauli channel.
    For a single qubit Pauli Channel, the probabilities are an array of length 4:  `PauliKind((i)%4)` (i.e. `[p_I, p_X, p_Y, p_Z]`).
    For a two qubit Pauli Channel, probabibilities is an array of length 16.
    The i-th element of the probabilities is associated with the i-th element of the 2-qubit Pauli strings in lexographic order.
    E.g. prob[i] corresponds to the Pauli string `PauliKind((i)%4), PauliKind_t((i)/4)`.
 * \param[out] oper Quantum operator associated with the Pauli channel.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropCreatePauliNoiseChannelOperator(const cupaulipropHandle_t handle,
                                                               int32_t numQubits,
                                                               const int32_t qubitIndices[],
                                                               const double probabilities[],
                                                               cupaulipropQuantumOperator_t * oper);

/**
 * \brief Creates a generalised amplitude damping channel.
 *
 * Letting \f$\gamma=\f$ `dampingProb` and \f$p=\f$ `exciteProb`, this channel is
 * described by Kraus operators:
 * \f[
 *  K_0 = \sqrt{1-p} \begin{pmatrix} 1 & 0 \\ 0 & \sqrt{1-\gamma} \end{pmatrix} \\
 *  K_1 = \sqrt{1-p} \begin{pmatrix} 0 & \sqrt{\gamma} \\ 0 & 0 \end{pmatrix} \\
 *  K_2 = \sqrt{p} \begin{pmatrix} \sqrt{1-\gamma} & 0 \\ 0 & 1 \end{pmatrix} \\
 *  K_3 = \sqrt{p} \begin{pmatrix} 0 & 0 \\ \sqrt{\gamma} & 0 \end{pmatrix}
 * \f]
 * 
 * \param[in] handle Library handle.
 * \param[in] qubitIndex Index of qubit upon which to operate.
 * \param[in] dampingProb Probability that the qubit is damped, i.e. decohered into a classical state.
 * \param[in] exciteProb Probability that damping results in excitation (driving to the one state) rather than dissipation (driving to the zero state).
 *            Set to zero for conventional, dissipative amplitude damping.
 * \param[out] oper Quantum operator associated with the channel.
 * \return cupaulipropStatus_t 
 */
 cupaulipropStatus_t cupaulipropCreateAmplitudeDampingChannelOperator(const cupaulipropHandle_t handle,
                                                                      int32_t qubitIndex,
                                                                      double dampingProb,
                                                                      double exciteProb,
                                                                      cupaulipropQuantumOperator_t * oper);

/**
 * \brief Queries what kind of gate or channel a quantum operator represents.
 * 
 * \param[in] handle Library handle.
 * \param[in] oper Quantum operator.
 * \param[out] kind Kind of the quantum operator.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropQuantumOperatorGetKind(const cupaulipropHandle_t handle,
                                                      const cupaulipropQuantumOperator_t oper,
                                                      cupaulipropQuantumOperatorKind_t * kind);

/**
 * \brief Destroys a quantum operator.
 * 
 * \param[in] oper Quantum operator.
 * \return cupaulipropStatus_t 
 */
cupaulipropStatus_t cupaulipropDestroyOperator(cupaulipropQuantumOperator_t oper);

#if defined(__cplusplus)
} // extern "C"
#endif // defined(__cplusplus)
