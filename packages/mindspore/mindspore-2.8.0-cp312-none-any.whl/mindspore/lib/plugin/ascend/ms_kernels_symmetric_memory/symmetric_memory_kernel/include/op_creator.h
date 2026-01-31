/**
 * Copyright 2024-2025 Huawei Technologies Co., Ltd
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

#ifndef MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_OP_CREATOR_H_
#define MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_OP_CREATOR_H_

#include <string>
#include "include/symmetric_memory_op.h"
#include "include/op_param.h"

namespace mindspore {
namespace symmetricmemory {
SymmetricMemoryOpPtr CreateSignalWaitUntilOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                      const SignalWaitUntilParam &param, const std::string &op_name);
SymmetricMemoryOpPtr CreatePutMemSignalOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const PutMemSignalParam &param, const std::string &op_name);
SymmetricMemoryOpPtr CreateSignalOpOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const SignalOpParam &param, const std::string &op_name);
SymmetricMemoryOpPtr CreateGetMemOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const GetMemParam &param, const std::string &op_name);
SymmetricMemoryOpPtr CreatePutMemOp(const InputsImmutableInfoList &inputs_ii, const OutputsImmutableInfoList &outputs_ii,
                                   const PutMemParam &param, const std::string &op_name);

bool IsSymmetricMemoryKernelDtypesSupported(const std::string op_name, InputDataTypes in_dtypes, InputDataTypes out_dtypes);
}  // namespace symmetricmemory
}  // namespace mindspore

#endif  // MS_KERNELS_SYMMETRIC_MEMORY_KERNEL_OP_CREATOR_H_
