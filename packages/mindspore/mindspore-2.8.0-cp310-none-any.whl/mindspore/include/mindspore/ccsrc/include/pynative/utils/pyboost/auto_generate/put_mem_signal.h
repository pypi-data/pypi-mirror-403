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

#ifndef MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_PUTMEMSIGNAL_H_
#define MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_PUTMEMSIGNAL_H_

#include "include/pynative/utils/pyboost/op_runner.h"
#include "include/pynative/utils/pyboost/op_register.h"

namespace mindspore {
namespace kernel {
namespace pyboost {
class PYBOOST_API PutMemSignal : public pyboost::OpRunner {
 public:
  PutMemSignal(PrimitivePtr primitive, const DeviceContext *device_context)
      : OpRunner(std::move(primitive), device_context) {}
  ~PutMemSignal() override = default;

  virtual std::tuple<mindspore::tensor::TensorPtr,mindspore::tensor::TensorPtr> Call(const mindspore::tensor::TensorPtr &target_tensor, const mindspore::tensor::TensorPtr &target_offset_tensor, const mindspore::tensor::TensorPtr &src_tensor, const mindspore::tensor::TensorPtr &src_offset_tensor, const mindspore::tensor::TensorPtr &size_tensor, const mindspore::tensor::TensorPtr &signal_tensor, const mindspore::tensor::TensorPtr &signal_offset_tensor, const mindspore::tensor::TensorPtr &signal_value_tensor, const mindspore::Int64ImmPtr &signal_op, const mindspore::Int64ImmPtr &target_pe, const mindspore::BoolImmPtr &non_blocking) = 0;
  bool output_is_tuple() const override { return true; }

 protected:
  static const std::string &op_name() {return op_name_;}

  inline static std::string op_name_ = "PutMemSignal";
};

}  // namespace pyboost
}  // namespace kernel
}  // namespace mindspore
#endif  // MINDSPORE_MINDSPORE_CCSRC_PIPELINE_PYNATIVE_FORWARD_PYBOOST_OP_PUTMEMSIGNAL_H_
