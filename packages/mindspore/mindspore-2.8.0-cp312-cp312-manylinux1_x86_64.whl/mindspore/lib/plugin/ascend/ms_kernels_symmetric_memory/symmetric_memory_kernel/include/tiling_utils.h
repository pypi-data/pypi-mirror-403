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

#ifndef MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_TILING_UTILS_H_
#define MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_TILING_UTILS_H_

#include <cstdint>
#include <functional>
#include <memory>
#include <sstream>
#include <string>
#include <unordered_map>
#include <vector>
#include <utility>

#include "include/symmetric_memory_op.h"
#include "src/log/log.h"

namespace mindspore {
namespace symmetricmemory {
struct RuningInfo {
  symmetricmemory::ShapeInfoList input_shapes;
  symmetricmemory::InputsImmutableInfoList input_infos;
  symmetricmemory::ShapeInfoList output_shapes;
  symmetricmemory::InputsImmutableInfoList output_infos;
};
}  // namespace symmetricmemory
}  // namespace mindspore

#endif  // MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_TILING_UTILS_H_
