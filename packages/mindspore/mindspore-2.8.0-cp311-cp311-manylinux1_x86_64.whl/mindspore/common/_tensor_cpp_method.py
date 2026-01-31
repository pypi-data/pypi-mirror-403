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

tensor_cpp_methods = ['nan_to_num', 'scatter_', 'square', 'pow', '__pow__', 'flatten', 'masked_fill_', 'repeat', 'log', 'exp_', 'log2', 'masked_scatter_', 'to', 'logical_not', 'new_full', 'div', 'divide', 'isclose', 'inverse', 'index_fill_', 'masked_fill', 'asin', 'arcsin', 'logical_or', 'logsumexp', 'histc', 'bincount', 'index_copy_', 'logical_xor', 'tile', 'exp', 'select', 'sin', 'expand_as', 'sigmoid', 'bitwise_or', '__or__', 'maximum', 'xlogy', 'tanh', 'allclose', 'new_ones', 'less_equal', 'le', 'add_', '__iadd__', 'addbmm', 'copy_', 'isinf', 'cosh', 'tril', 'real', 'remainder_', '__imod__', 'kthvalue', 'index', 'mul_', '__imul__', 'log10', 'atan2', 'arctan2', 'index_select', 'view', 'round', 'hardshrink', 'log1p', 'permute', 'asinh', 'arcsinh', 'unique', 'sub', '__sub__', 'masked_scatter', 'scatter_add', 'median', 'cumsum', 'atan', 'arctan', 'triu', 'lerp', 'true_divide', 'where', 'chunk', 'any', 'matmul', 'clone', 'take', 'dot', 'minimum', 'floor_divide_', '__ifloordiv__', 'argsort', 'argmin', 'sqrt', 'count_nonzero', 'argmax', 'not_equal', 'ne', 'ceil', 'erf', 'mul', '__mul__', 'bitwise_xor', '__xor__', 'log_', 'repeat_interleave', 'mm', 'sum', 'less', 'lt', 'prod', 'broadcast_to', 'neg', 'negative', 'new_empty', 'div_', '__itruediv__', 'fill_diagonal_', 'baddbmm', 'sigmoid_', 't', 'std', 'transpose', 'isneginf', 'acos', 'arccos', 'squeeze', 'erfc', 'gcd', 'roll', 'addmm', 'fill_', 'index_add', 'type_as', 'floor', 'outer', 'bitwise_not', 'imag', 'clamp', 'clip', 'topk', 'atanh', 'arctanh', 'var', 'unsqueeze', 'eq', 'isfinite', 'logaddexp', 'rsqrt', 'put_', 'sinh', 'mean', 'tan', '__mod__', 'diag', 'add', '__add__', 'abs', '__abs__', 'absolute', 'max', 'min', 'gather', 'fmod', 'expm1', 'sinc', 'addmv', 'new_zeros', 'unbind', 'nansum', 'frac', 'addcdiv', 'sub_', '__isub__', 'reshape', 'logical_and', 'bitwise_and', '__and__', 'greater', 'gt', 'cos', 'trunc', 'greater_equal', 'ge', 'subtract', 'scatter', 'all', 'floor_divide', 'remainder', 'reciprocal', 'acosh', 'arccosh', 'view_as', 'split', 'masked_select', 'narrow', 'sort', 'logaddexp2']
