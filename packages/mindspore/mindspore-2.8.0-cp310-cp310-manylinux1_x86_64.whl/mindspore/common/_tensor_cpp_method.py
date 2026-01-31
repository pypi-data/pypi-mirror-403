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

tensor_cpp_methods = ['abs', '__abs__', 'absolute', 'mul', '__mul__', 'nan_to_num', 'bitwise_not', 'new_zeros', 'mul_', '__imul__', 'bitwise_and', '__and__', 'nansum', 'select', 'view_as', 'masked_fill_', 'atan', 'arctan', 'subtract', 'min', 'std', 'new_ones', 'repeat', 'allclose', 'sinc', 'scatter_add', 'fill_', 'triu', 'copy_', 'isfinite', 'kthvalue', 'atan2', 'arctan2', 'bitwise_xor', '__xor__', 'acosh', 'arccosh', 'index', 'diag', 'erfc', 'clamp', 'clip', 'neg', 'negative', 'sub', '__sub__', 'unbind', 'sinh', 'new_full', 'square', 'logical_or', 'remainder', 'all', 'acos', 'arccos', 'log2', 'log', 'logaddexp', 'sum', 'put_', 'logical_not', 'addmm', 'real', 'roll', 'cos', 'permute', 'round', 'tril', 'cumsum', 'floor', 'add', '__add__', 'histc', 'expand_as', 'masked_scatter', 'split', 'tanh', 'repeat_interleave', 'addbmm', 'sub_', '__isub__', 'floor_divide_', '__ifloordiv__', 'fmod', 'greater', 'gt', 'chunk', 'asin', 'arcsin', 'masked_select', 'prod', 'unique', 'sort', 'max', 'take', 'imag', 'new_empty', 'topk', 'isinf', 'unsqueeze', 'scatter_', 'flatten', 'count_nonzero', 'log1p', 'minimum', 'bincount', 'sqrt', 'masked_scatter_', 'not_equal', 'ne', 'dot', 'addmv', 'index_add', 'add_', '__iadd__', 'gcd', 'argmin', 'floor_divide', 'inverse', 'logaddexp2', 'addcdiv', 'broadcast_to', 'tile', 'mm', 'cosh', 'remainder_', '__imod__', 'true_divide', 'rsqrt', 'any', 'div', 'divide', 'outer', 'less', 'lt', 't', 'argmax', 'clone', 'var', 'log10', 'logsumexp', 'exp_', 'erf', 'ceil', 'reshape', 'div_', '__itruediv__', 'index_fill_', 'frac', 'pow', '__pow__', 'expm1', 'log_', 'gather', 'greater_equal', 'ge', 'mean', 'type_as', 'scatter', 'eq', 'baddbmm', 'sin', 'sigmoid', 'sigmoid_', 'argsort', 'less_equal', 'le', 'logical_xor', 'atanh', 'arctanh', 'exp', 'maximum', 'trunc', 'xlogy', '__mod__', 'logical_and', 'asinh', 'arcsinh', 'matmul', 'where', 'transpose', 'fill_diagonal_', 'isclose', 'hardshrink', 'narrow', 'squeeze', 'tan', 'index_select', 'reciprocal', 'isneginf', 'to', 'bitwise_or', '__or__', 'lerp', 'median', 'index_copy_', 'masked_fill', 'view']
