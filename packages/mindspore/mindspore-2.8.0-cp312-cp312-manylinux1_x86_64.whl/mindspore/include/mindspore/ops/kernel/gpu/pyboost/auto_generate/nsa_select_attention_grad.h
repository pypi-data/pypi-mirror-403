/**
 * Copyright 2023 Huawei Technologies Co., Ltd
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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_NSASELECTATTENTIONGRAD_GPU_H_
#define MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_NSASELECTATTENTIONGRAD_GPU_H_

#include "include/pynative/utils/pyboost/auto_generate/nsa_select_attention_grad.h"
#include "ir/tensor.h"
#include "ir/scalar.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class NsaSelectAttentionGradGPU : public pyboost::NsaSelectAttentionGrad {
 public:
  NsaSelectAttentionGradGPU(PrimitivePtr primitive, const DeviceContext *device_context)
    : NsaSelectAttentionGrad(std::move(primitive), device_context) {}
  ~NsaSelectAttentionGradGPU() = default;

  std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &grad_tensor, const mindspore::tensor::TensorPtr &query_tensor, const mindspore::tensor::TensorPtr &key_tensor, const mindspore::tensor::TensorPtr &value_tensor, const mindspore::tensor::TensorPtr &attention_out_tensor, const mindspore::tensor::TensorPtr &softmax_max_tensor, const mindspore::tensor::TensorPtr &softmax_sum_tensor, const mindspore::tensor::TensorPtr &topk_indices_tensor, const mindspore::FP32ImmPtr &scale_value, const mindspore::Int64ImmPtr &head_num, const mindspore::Int64ImmPtr &select_block_size, const mindspore::Int64ImmPtr &select_block_count, const std::optional<mindspore::tensor::TensorPtr> &atten_mask_tensor, const std::optional<mindspore::ValueTuplePtr> &actual_seq_qlen, const std::optional<mindspore::ValueTuplePtr> &actual_seq_kvlen) override;
};
}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PLUGIN_DEVICE_GPU_KERNEL_PYBOOST_NSASELECTATTENTIONGRAD_GPU_H_
