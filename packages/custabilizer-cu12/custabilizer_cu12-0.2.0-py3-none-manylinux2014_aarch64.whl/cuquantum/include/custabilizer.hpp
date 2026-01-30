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
 * @brief Helper classes and utilities for cuStabilizer C++ API
 */

#pragma once

#include "cuda_runtime.h"
#include "custabilizer.h"
#include <stdexcept>
#include <string>
#include <vector>

#ifndef CUDA_CHECK
#define CUDA_CHECK(call)                                                        \
  do {                                                                          \
    cudaError_t error = call;                                                   \
    if (error != cudaSuccess) {                                                 \
      throw std::runtime_error("CUDA error at " + std::string(__FILE__) + ":" + \
                               std::to_string(__LINE__) + "[" + #call +         \
                               "]: " + cudaGetErrorString(error));              \
    }                                                                           \
  } while (0)
#define CUDA_CHECK_ADDED 1
#endif

#define CUSTABILIZER_CHECK(call, error_message)                                                 \
  do {                                                                                          \
    custabilizerStatus_t status = call;                                                         \
    if (status != CUSTABILIZER_STATUS_SUCCESS) {                                                \
      std::string msg = std::string(error_message) + ": " + custabilizerGetErrorString(status); \
      throw std::runtime_error(msg);                                                            \
    }                                                                                           \
  } while (0)

namespace custabilizer
{
namespace helpers
{

/**
 * @brief Helper class for managing FrameSimulator with automatic memory
 * management
 *
 * This RAII wrapper simplifies FrameSimulator lifecycle management by
 * automatically allocating device memory, initializing tables to zero, and
 * cleaning up resources.
 *
 * Example usage:
 * @code
 * custabilizer::FrameSimulator sim(3, 1024, 2);  // 3 qubits, 1024 samples, 2
 * measurements custabilizer::Circuit circuit("H 0\nCNOT 0 1\nM 0 1\n");
 * sim.apply_circuit(circuit.circuit);
 * // Automatic cleanup on scope exit
 * @endcode
 */
class FrameSimulator
{
public:
  custabilizerHandle_t handle = nullptr;
  custabilizerFrameSimulator_t frame_simulator = nullptr;
  uint32_t* x_table_d = nullptr;
  uint32_t* z_table_d = nullptr;
  uint32_t* m_table_d = nullptr;
  int64_t num_qubits;
  int64_t num_shots;
  int64_t num_measurements;
  int64_t num_detectors;
  int64_t table_stride_major;

  // Prevent copying
  FrameSimulator(const FrameSimulator&) = delete;
  FrameSimulator& operator=(const FrameSimulator&) = delete;

  /**
   * @brief Construct a new FrameSimulator with zero-initialized device tables
   *
   * @param num_qubits Number of qubits in the system
   * @param num_shots Number of Pauli frames (samples/batch size)
   * @param num_measurements Number of measurement records
   */
  FrameSimulator(size_t num_qubits,
                 size_t num_shots,
                 size_t num_measurements,
                 size_t num_detectors = 0)
      : num_qubits(num_qubits),
        num_shots(num_shots),
        num_measurements(num_measurements),
        num_detectors(num_detectors),
        table_stride_major(((num_shots + 31) / 32) * sizeof(uint32_t))
  {
    size_t x_table_size = table_stride_major * num_qubits;
    size_t z_table_size = table_stride_major * num_qubits;
    size_t m_table_size = table_stride_major * (num_measurements + num_detectors);

    try {
      CUDA_CHECK(cudaMalloc(&x_table_d, x_table_size));
      CUDA_CHECK(cudaMalloc(&z_table_d, z_table_size));
      CUDA_CHECK(cudaMalloc(&m_table_d, m_table_size));

      CUDA_CHECK(cudaMemset(x_table_d, 0, x_table_size));
      CUDA_CHECK(cudaMemset(z_table_d, 0, z_table_size));
      CUDA_CHECK(cudaMemset(m_table_d, 0, m_table_size));
      CUSTABILIZER_CHECK(custabilizerCreate(&handle), "Failed to create custabilizer handle");
      CUSTABILIZER_CHECK(
          custabilizerCreateFrameSimulator(handle, num_qubits, num_shots, num_measurements,
                                           table_stride_major, &frame_simulator),
          "Failed to create FrameSimulator");
    } catch (const std::runtime_error& e) {
      free_resources();
      throw;
    }
  }

  /**
   * @brief Ignore uninitialized resources and free initialized resources
   */
  void free_resources() noexcept
  {
    cudaFree(x_table_d);
    cudaFree(z_table_d);
    cudaFree(m_table_d);
    custabilizerDestroyFrameSimulator(frame_simulator);
    custabilizerDestroy(handle);
  }

  /**
   * @brief Destructor - automatically cleans up all resources
   */
  ~FrameSimulator() { free_resources(); }

  /**
   * @brief Apply a circuit to the frame simulator
   *
   * @param circuit Circuit to apply
   * @param randomize_measurements If true, randomize measurement outcomes
   * @param seed Random seed for measurement randomization
   * @param stream CUDA stream for asynchronous execution (default: 0)
   * @throws std::runtime_error if the operation fails
   */
  void apply_circuit(const custabilizerCircuit_t circuit,
                     bool randomize_measurements = false,
                     uint64_t seed = 0,
                     cudaStream_t stream = 0)
  {
    custabilizerStatus_t status = custabilizerFrameSimulatorApplyCircuit(
        handle, frame_simulator, circuit, randomize_measurements ? 1 : 0, seed, x_table_d,
        z_table_d, m_table_d, stream);
    if (status != CUSTABILIZER_STATUS_SUCCESS) {
      throw std::runtime_error("custabilizerFrameSimulatorApplyCircuit returned status " +
                               std::to_string(status));
    }
  }

  /**
   * @brief Copy X table from device to host
   *
   * @return std::vector<uint32_t> Host vector containing X table data
   */
  std::vector<uint32_t> get_x_table() const
  {
    int64_t table_size_words = (num_shots + 31) / 32 * num_qubits;
    std::vector<uint32_t> x_table_h(table_size_words);
    CUDA_CHECK(cudaMemcpy(x_table_h.data(), x_table_d, table_size_words * sizeof(uint32_t),
                          cudaMemcpyDeviceToHost));
    return x_table_h;
  }

  /**
   * @brief Copy Z table from device to host
   *
   * @return std::vector<uint32_t> Host vector containing Z table data
   */
  std::vector<uint32_t> get_z_table() const
  {
    int64_t table_size_words = (num_shots + 31) / 32 * num_qubits;
    std::vector<uint32_t> z_table_h(table_size_words);
    CUDA_CHECK(cudaMemcpy(z_table_h.data(), z_table_d, table_size_words * sizeof(uint32_t),
                          cudaMemcpyDeviceToHost));
    return z_table_h;
  }

  /**
   * @brief Copy M table from device to host
   *
   * @return std::vector<uint32_t> Host vector containing M table data
   */
  std::vector<uint32_t> get_m_table() const
  {
    int64_t table_size_words = (num_shots + 31) / 32 * num_measurements;
    std::vector<uint32_t> m_table_h(table_size_words);
    CUDA_CHECK(cudaMemcpy(m_table_h.data(), m_table_d, table_size_words * sizeof(uint32_t),
                          cudaMemcpyDeviceToHost));
    return m_table_h;
  }
};

/**
 * @brief Helper class for managing Circuit with automatic memory management
 *
 * This RAII wrapper simplifies Circuit lifecycle management by automatically
 * creating the handle, parsing circuit strings, allocating device buffers,
 * and cleaning up all resources.
 *
 * Example usage:
 * @code
 * custabilizer::Circuit circuit("H 0\nCNOT 0 1\nM 0 1\n");
 * // Use circuit.circuit in API calls
 * // Automatic cleanup on scope exit
 * @endcode
 */
class Circuit
{
public:
  custabilizerHandle_t handle = nullptr;
  custabilizerCircuit_t circuit = nullptr;
  void* circuit_buffer_d = nullptr;

  // Prevent copying
  Circuit(const Circuit&) = delete;
  Circuit& operator=(const Circuit&) = delete;

  /**
   * @brief Construct a new Circuit from a Stim-compatible circuit string
   *
   * @param circuit_string Circuit description in Stim format
   */
  Circuit(const std::string& circuit_string_cpp)
  {
    try {
      CUSTABILIZER_CHECK(custabilizerCreate(&handle), "Failed to create custabilizer handle");

      const char* circuit_string = circuit_string_cpp.c_str();
      int64_t circuit_buffer_size;
      CUSTABILIZER_CHECK(
          custabilizerCircuitSizeFromString(handle, circuit_string, &circuit_buffer_size),
          "Failed to get circuit size from string");

      CUDA_CHECK(cudaMalloc(&circuit_buffer_d, circuit_buffer_size));

      CUSTABILIZER_CHECK(
          custabilizerCreateCircuitFromString(handle, circuit_string, circuit_buffer_d,
                                              circuit_buffer_size, &circuit),
          "Failed to create circuit from string");
    } catch (const std::runtime_error& e) {
      free_resources();
      throw;
    }
  }

  /**
   * @brief Ignore uninitialized resources and free initialized resources
   */
  void free_resources() noexcept
  {
    cudaFree(circuit_buffer_d);
    custabilizerDestroyCircuit(circuit);
    custabilizerDestroy(handle);
  }

  /**
   * @brief Destructor - automatically cleans up all resources
   */
  ~Circuit() { free_resources(); }
};

} // namespace helpers

// Export helper classes to custabilizer namespace for public API
using helpers::Circuit;
using helpers::FrameSimulator;

} // namespace custabilizer

#ifdef CUDA_CHECK_ADDED
#undef CUDA_CHECK
#endif
