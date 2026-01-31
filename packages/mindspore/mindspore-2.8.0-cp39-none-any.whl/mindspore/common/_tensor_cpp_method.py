# Copyright 2024 Huawei Technologies Co., Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ============================================================================
"""Add tensor cpp methods for stub tensor"""

tensor_cpp_methods = ['new_zeros', 'clone', 't', 'xlogy', 'bitwise_and', '__and__', 'kthvalue', 'diag', 'split', 'tril', 'remainder', 'log1p', 'pow', '__pow__', 'asinh', 'arcsinh', 'floor', 'nansum', 'unbind', 'topk', 'ceil', 'select', 'abs', 'absolute', '__abs__', 'masked_fill', 'take', 'min', 'logical_and', 'greater', 'gt', 'new_full', 'index_copy_', 'all', 'argsort', 'cumsum', 'mul', '__mul__', 'sum', 'sin', 'outer', 'reshape', 'sinh', 'bitwise_not', 'eq', 'remainder_', '__imod__', 'logsumexp', 'max', 'addmm', 'mm', 'scatter', 'expand_as', 'new_empty', 'baddbmm', 'less', 'lt', 'index_select', 'reciprocal', 'squeeze', 'not_equal', 'ne', 'floor_divide', 'fill_', 'where', 'expm1', 'round', 'floor_divide_', '__ifloordiv__', 'new_ones', 'subtract', 'div_', '__itruediv__', 'log_', 'trunc', 'masked_fill_', 'log2', 'logical_xor', 'view_as', 'sigmoid_', 'type_as', 'permute', 'transpose', 'rsqrt', 'asin', 'arcsin', 'bitwise_or', '__or__', 'cos', 'atan', 'arctan', 'prod', 'log', 'allclose', 'argmin', 'sub', '__sub__', 'isfinite', 'erf', 'sqrt', 'roll', 'exp', 'div', 'divide', 'any', 'bitwise_xor', '__xor__', 'broadcast_to', 'index_add', 'atan2', 'arctan2', 'mean', 'index', 'addcdiv', 'logaddexp', 'add_', '__iadd__', 'masked_scatter_', 'sub_', '__isub__', 'cosh', 'isclose', 'repeat_interleave', 'greater_equal', 'ge', 'count_nonzero', 'inverse', 'gather', 'scatter_add', 'sigmoid', 'masked_scatter', 'logical_not', 'maximum', 'narrow', 'matmul', 'fill_diagonal_', 'neg', 'negative', 'sinc', 'square', 'chunk', 'clamp', 'clip', 'lerp', 'put_', 'flatten', 'less_equal', 'le', 'copy_', 'dot', 'true_divide', 'imag', 'isinf', 'hardshrink', 'logaddexp2', 'masked_select', 'addmv', 'unsqueeze', 'mul_', '__imul__', 'tile', 'bincount', 'real', 'unique', 'std', 'logical_or', 'exp_', 'atanh', 'arctanh', 'erfc', 'fmod', 'argmax', 'minimum', 'to', 'addbmm', 'log10', 'gcd', 'tan', 'index_fill_', 'sort', 'tanh', 'median', '__mod__', 'frac', 'view', 'nan_to_num', 'triu', 'repeat', 'isneginf', 'scatter_', 'acosh', 'arccosh', 'histc', 'add', '__add__', 'acos', 'arccos', 'var']
