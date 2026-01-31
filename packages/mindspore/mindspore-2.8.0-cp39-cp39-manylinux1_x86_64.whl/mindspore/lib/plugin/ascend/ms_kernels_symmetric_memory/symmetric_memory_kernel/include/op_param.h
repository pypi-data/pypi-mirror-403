/**
 * Copyright 2024 Huawei Technologies Co., Ltd
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#ifndef MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_OP_PARAM_H_
#define MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_OP_PARAM_H_

#include <stdint.h>
#include <vector>

namespace mindspore {
namespace symmetricmemory {
constexpr auto kSymmetricMemorySignalWaitUntilOpName = "SignalWaitUntil";
constexpr auto kSymmetricMemoryPutMemSignalOpName = "PutMemSignal";
constexpr auto kSymmetricMemorySignalOpOpName = "SignalOp";
constexpr auto kSymmetricMemoryGetMemOpName = "GetMem";
constexpr auto kSymmetricMemoryPutMemOpName = "PutMem";

struct PutMemSignalParam {
  int64_t signal_op = 0;
  int64_t target_pe = 0;
  bool non_blocking = false;
};

struct SignalWaitUntilParam {
  int64_t compare_op = 0;
};

struct SignalOpParam {
  int64_t signal_op = 0;
  int64_t target_pe = 0;
};

struct PutMemParam {
  int64_t target_pe = 0;
  bool non_blocking = false;
};

struct GetMemParam {
  int64_t target_pe = 0;
  bool non_blocking = false;
};



}  // namespace symmetricmemory
}  // namespace mindspore

#endif  // MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_OP_PARAM_H_
