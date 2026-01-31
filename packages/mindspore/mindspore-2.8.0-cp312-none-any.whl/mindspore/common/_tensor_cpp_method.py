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

tensor_cpp_methods = ['logical_and', 'tan', 'diag', 'floor_divide', 'topk', 'lerp', 'div', 'divide', 'bincount', 'less_equal', 'le', 'flatten', 'narrow', 'addmm', 'min', 'reciprocal', 'addcdiv', 'sqrt', 'argsort', 'unique', 'masked_fill_', 'median', 'addbmm', 'bitwise_xor', '__xor__', 'logical_not', 'hardshrink', 'triu', 'sinh', 'floor', 'index_add', 'nan_to_num', 'view', 'scatter_', 'mean', 'type_as', 'logaddexp', 'select', 'clone', 'argmax', 'squeeze', 'new_zeros', 'repeat', 'split', 'any', 'permute', 'eq', 'exp', 'allclose', 'expm1', 'index', 'reshape', 'logaddexp2', 'argmin', 'floor_divide_', '__ifloordiv__', 'index_fill_', 'isneginf', 'cumsum', 'isclose', 'tril', 'expand_as', 'masked_scatter_', 'bitwise_not', 'sinc', 'trunc', 'greater', 'gt', 'true_divide', 'transpose', 'ceil', 'abs', 'absolute', '__abs__', 'not_equal', 'ne', 'unbind', 'sub_', '__isub__', 'masked_fill', 'greater_equal', 'ge', 'sigmoid_', 'mul_', '__imul__', 'to', 'fill_', 'repeat_interleave', 'logsumexp', 'unsqueeze', 'log1p', 'scatter', 'erf', 'subtract', 'imag', 'round', 'broadcast_to', 'cosh', 'tanh', 'neg', 'negative', 'roll', 'clamp', 'clip', 'bitwise_and', '__and__', 'asinh', 'arcsinh', 'gather', 'atan', 'arctan', 'baddbmm', 'fill_diagonal_', 'view_as', 'logical_xor', 'log10', 'sort', 'pow', '__pow__', 'tile', 'frac', 'copy_', 'add_', '__iadd__', 'isinf', 'index_copy_', 'kthvalue', 'bitwise_or', '__or__', 'maximum', 'log2', 'new_empty', '__mod__', 'sub', '__sub__', 'exp_', 'mul', '__mul__', 'matmul', 'sigmoid', 'asin', 'arcsin', 'isfinite', 'histc', 'scatter_add', 'acosh', 'arccosh', 'new_full', 'atan2', 'arctan2', 'div_', '__itruediv__', 'count_nonzero', 'nansum', 'real', 'sum', 'sin', 'inverse', 'fmod', 'take', 'cos', 't', 'max', 'index_select', 'new_ones', 'atanh', 'arctanh', 'addmv', 'prod', 'mm', 'masked_select', 'where', 'less', 'lt', 'var', 'outer', 'xlogy', 'remainder_', '__imod__', 'log', 'dot', 'erfc', 'gcd', 'chunk', 'put_', 'square', 'masked_scatter', 'log_', 'remainder', 'minimum', 'acos', 'arccos', 'add', '__add__', 'rsqrt', 'all', 'std', 'logical_or']
