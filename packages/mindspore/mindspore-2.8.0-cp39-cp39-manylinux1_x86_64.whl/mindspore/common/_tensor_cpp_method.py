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

tensor_cpp_methods = ['masked_scatter_', 'remainder', 'masked_select', 'fill_diagonal_', 'ceil', 'erf', 'atanh', 'arctanh', 'addbmm', 'rsqrt', 'argmin', 'abs', '__abs__', 'absolute', 'dot', '__mod__', 'neg', 'negative', 'pow', '__pow__', 'log2', 'take', 'acosh', 'arccosh', 'scatter_add', 'remainder_', '__imod__', 'sub_', '__isub__', 'maximum', 'mul_', '__imul__', 'kthvalue', 'allclose', 'scatter', 'atan2', 'arctan2', 'mm', 'clamp', 'clip', 'bitwise_xor', '__xor__', 'logaddexp', 'addcdiv', 'floor_divide', 'nansum', 'isclose', 'hardshrink', 't', 'logical_and', 'scatter_', 'greater', 'gt', 'repeat', 'cos', 'isneginf', 'atan', 'arctan', 'square', 'xlogy', 'exp_', 'new_zeros', 'round', 'count_nonzero', 'put_', 'isinf', 'broadcast_to', 'new_full', 'asin', 'arcsin', 'sum', 'floor_divide_', '__ifloordiv__', 'copy_', 'tile', 'nan_to_num', 'index_select', 'bincount', 'triu', 'all', 'greater_equal', 'ge', 'logical_xor', 'frac', 'addmv', 'add', '__add__', 'min', 'less', 'lt', 'matmul', 'permute', 'true_divide', 'unique', 'clone', 'argsort', 'div', 'divide', 'argmax', 'masked_fill', 'sub', '__sub__', 'bitwise_or', '__or__', 'exp', 'histc', 'addmm', 'sin', 'real', 'minimum', 'transpose', 'view', 'prod', 'mean', 'roll', 'chunk', 'repeat_interleave', 'split', 'topk', 'new_empty', 'add_', '__iadd__', 'masked_scatter', 'mul', '__mul__', 'diag', 'logsumexp', 'cosh', 'index_copy_', 'sigmoid', 'sinc', 'inverse', 'reciprocal', 'reshape', 'expm1', 'less_equal', 'le', 'log', 'var', 'asinh', 'arcsinh', 'floor', 'sqrt', 'trunc', 'unsqueeze', 'sort', 'index_add', 'div_', '__itruediv__', 'sigmoid_', 'type_as', 'sinh', 'cumsum', 'view_as', 'log_', 'squeeze', 'std', 'index_fill_', 'new_ones', 'lerp', 'gather', 'logaddexp2', 'tan', 'to', 'imag', 'fmod', 'outer', 'log10', 'not_equal', 'ne', 'select', 'logical_or', 'any', 'gcd', 'isfinite', 'unbind', 'where', 'expand_as', 'fill_', 'bitwise_not', 'log1p', 'max', 'tanh', 'narrow', 'eq', 'index', 'baddbmm', 'flatten', 'erfc', 'acos', 'arccos', 'logical_not', 'median', 'bitwise_and', '__and__', 'subtract', 'tril', 'masked_fill_']
