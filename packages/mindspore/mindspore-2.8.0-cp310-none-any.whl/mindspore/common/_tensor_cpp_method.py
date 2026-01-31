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

tensor_cpp_methods = ['scatter_', 'add_', '__iadd__', 'min', 'transpose', 'index_copy_', 'square', 'eq', 'imag', 'addcdiv', 'topk', 'log_', 'sqrt', 'histc', 'true_divide', 'index', 'sin', 'sigmoid_', 'addbmm', 'outer', 'scatter', 'baddbmm', 'std', 'view_as', 'repeat', 'unique', 'inverse', 'minimum', 'log10', 'copy_', 'median', 'atanh', 'arctanh', 'greater', 'gt', 'less_equal', 'le', 'pow', '__pow__', 'new_ones', 't', 'gather', 'lerp', 'put_', 'cosh', 'fmod', 'dot', 'narrow', 'remainder', 'exp_', 'log1p', 'div_', '__itruediv__', 'bitwise_not', 'repeat_interleave', 'new_zeros', 'broadcast_to', 'to', 'roll', 'ceil', 'isneginf', 'gcd', 'var', 'abs', '__abs__', 'absolute', 'greater_equal', 'ge', 'real', 'bincount', 'reshape', 'scatter_add', 'xlogy', 'exp', 'erfc', 'all', 'tan', 'squeeze', 'count_nonzero', 'isinf', 'take', 'permute', 'triu', 'nansum', 'logical_or', 'isfinite', 'fill_diagonal_', 'argmin', 'flatten', 'bitwise_and', '__and__', 'sigmoid', 'acosh', 'arccosh', 'round', 'sinh', 'tril', 'addmm', 'select', 'sub_', '__isub__', 'allclose', 'bitwise_or', '__or__', 'argmax', 'logaddexp', 'logical_and', 'logical_not', 'mean', 'mm', 'frac', 'index_add', 'clamp', 'clip', 'floor_divide', 'reciprocal', 'split', 'asin', 'arcsin', 'less', 'lt', 'sinc', 'type_as', 'expm1', 'chunk', 'where', 'view', 'masked_scatter_', 'rsqrt', 'div', 'divide', 'sort', 'log', 'argsort', 'log2', 'prod', 'any', 'logaddexp2', 'acos', 'arccos', 'tile', 'erf', 'isclose', 'max', 'cos', 'fill_', 'mul_', '__imul__', '__mod__', 'index_fill_', 'new_full', 'mul', '__mul__', 'floor', 'kthvalue', 'add', '__add__', 'sum', 'diag', 'hardshrink', 'unbind', 'clone', 'atan', 'arctan', 'unsqueeze', 'asinh', 'arcsinh', 'trunc', 'index_select', 'floor_divide_', '__ifloordiv__', 'remainder_', '__imod__', 'addmv', 'cumsum', 'expand_as', 'subtract', 'bitwise_xor', '__xor__', 'neg', 'negative', 'not_equal', 'ne', 'atan2', 'arctan2', 'masked_fill_', 'matmul', 'tanh', 'logsumexp', 'sub', '__sub__', 'logical_xor', 'masked_select', 'nan_to_num', 'new_empty', 'masked_fill', 'masked_scatter', 'maximum']
