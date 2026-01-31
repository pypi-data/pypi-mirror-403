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

tensor_cpp_methods = ['new_ones', 'cumsum', 'div_', '__itruediv__', 'mul_', '__imul__', 'transpose', 'erfc', 'scatter_add', 'topk', 'var', 'chunk', 'diag', 'bitwise_or', '__or__', 'fill_diagonal_', 'index_fill_', 'clone', 'unbind', 'new_full', 'new_zeros', 'tril', 'unique', 'ceil', 'square', 'log2', 'mm', 'sigmoid', 'std', 'baddbmm', 'reshape', 'index_select', 'exp_', 'addcdiv', 'outer', 'put_', 'masked_fill', 'add', '__add__', 'min', 'take', 'atan2', 'arctan2', 'unsqueeze', 'greater', 'gt', 'abs', 'absolute', '__abs__', 'remainder_', '__imod__', 'log10', 'isneginf', 'broadcast_to', 'prod', 'erf', 'minimum', 'less_equal', 'le', 'sinc', 'log1p', 'new_empty', 'where', 'squeeze', 'sub', '__sub__', 'subtract', 'scatter_', 'view_as', 'type_as', 'masked_fill_', 'roll', 'logical_not', 'atanh', 'arctanh', 'sinh', 'repeat_interleave', 'cos', 'reciprocal', 'max', 'mean', 'view', 'scatter', 'log', 'remainder', 'asinh', 'arcsinh', 'isinf', 't', 'less', 'lt', 'tile', 'repeat', 'gcd', 'logical_and', 'fill_', 'addmv', 'masked_scatter', 'acos', 'arccos', 'sin', 'bincount', 'narrow', 'index_copy_', 'select', 'floor_divide', 'fmod', 'split', 'nan_to_num', 'to', 'clamp', 'clip', 'trunc', 'neg', 'negative', 'addbmm', 'argmin', 'logical_or', 'permute', 'frac', 'rsqrt', 'histc', 'masked_scatter_', 'argsort', 'floor_divide_', '__ifloordiv__', 'atan', 'arctan', 'bitwise_not', 'sum', 'asin', 'arcsin', 'logsumexp', 'maximum', 'lerp', 'isfinite', 'xlogy', 'allclose', 'expm1', 'tan', 'hardshrink', 'true_divide', 'mul', '__mul__', 'median', 'imag', 'greater_equal', 'ge', 'masked_select', 'argmax', 'real', 'nansum', 'isclose', 'bitwise_and', '__and__', 'not_equal', 'ne', 'cosh', 'any', 'eq', 'index', 'kthvalue', 'gather', 'logical_xor', 'copy_', 'all', 'sqrt', 'add_', '__iadd__', 'inverse', 'exp', 'round', 'triu', 'logaddexp2', 'logaddexp', 'div', 'divide', '__mod__', 'dot', 'index_add', 'sub_', '__isub__', 'flatten', 'addmm', 'sort', 'expand_as', 'acosh', 'arccosh', 'sigmoid_', 'count_nonzero', 'tanh', 'pow', '__pow__', 'matmul', 'bitwise_xor', '__xor__', 'log_', 'floor']
