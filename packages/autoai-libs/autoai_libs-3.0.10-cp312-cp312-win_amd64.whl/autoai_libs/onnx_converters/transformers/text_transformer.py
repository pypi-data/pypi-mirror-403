################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import numpy as np
from onnxconverter_common import apply_cast, apply_reshape
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import FloatTensorType
from skl2onnx.proto import onnx_proto

from autoai_libs.transformers.text_transformers import TextTransformer

PREFIX = "TEXT_TRANSFORMER_"


def text_transformer_shape_calculator(operator: Operator):
    op = operator.raw_operator
    column_headers_list = op.column_headers_list
    columns_to_be_deleted = op.columns_to_be_deleted
    for idx in range(len(column_headers_list)):
        if idx not in columns_to_be_deleted:
            original_list = [i for i in range(len(operator.inputs)) if i not in columns_to_be_deleted]
            if idx < (len(original_list)):
                operator.outputs[idx].type = operator.inputs[original_list[idx]].type.__class__((None, 1))
            else:
                operator.outputs[idx].type = FloatTensorType(shape=[None, 1])


def text_transformer_converter(scope: Scope, operator: Operator, container: ModelComponentContainer):
    op = operator.raw_operator
    inputs = operator.inputs
    text_columns = op.text_columns
    transformer_objs = op.transformer_objs
    activate_flag = op.activate_flag
    columns_to_be_deleted = op.columns_to_be_deleted

    target_type = onnx_proto.TensorProto.FLOAT

    if activate_flag and len(text_columns) > 0:
        split_outputs_total = []
        for trans_obj in transformer_objs:
            tfidf_models_list = trans_obj.tfidf_models
            truncated_svd_list = trans_obj.truncated_svd

            for idx, col in enumerate(text_columns):
                truncated_svd_n_dims = int(truncated_svd_list[idx].n_components)
                if tfidf_models_list[idx] is not None:
                    tfidf_model_output = scope.declare_local_variable(
                        f"tfidf_model_output_{idx}_{col}",
                        FloatTensorType([None, tfidf_models_list[idx].vocabulary_.__len__()]),
                    )
                    tfidf_model = OnnxSubEstimator(
                        tfidf_models_list[idx],
                        inputs[col].full_name,
                        op_version=container.target_opset,
                        output_names=[tfidf_model_output],
                    )
                    tfidf_model.add_to(scope, container)

                    is_nan = scope.get_unique_variable_name("is_nan")
                    is_pos_inf = scope.get_unique_variable_name("is_pos_inf")
                    is_neg_inf = scope.get_unique_variable_name("is_neg_inf")

                    zero_name = scope.get_unique_variable_name("zero_scalar")
                    pos_inf_name = scope.get_unique_variable_name("pos_inf")
                    neg_inf_name = scope.get_unique_variable_name("neg_inf")
                    max_val_name = scope.get_unique_variable_name("max_val")
                    min_val_name = scope.get_unique_variable_name("min_val")

                    container.add_initializer(zero_name, target_type, [1], [0.0])
                    container.add_initializer(pos_inf_name, target_type, [1], [float("inf")])
                    container.add_initializer(neg_inf_name, target_type, [1], [float("-inf")])
                    container.add_initializer(max_val_name, target_type, [1], [np.finfo(np.float32("inf")).max])
                    container.add_initializer(min_val_name, target_type, [1], [np.finfo(np.float32("inf")).min])

                    container.add_node(
                        "IsNaN", [tfidf_model_output.full_name], [is_nan], name=scope.get_unique_operator_name("IsNaN")
                    )

                    container.add_node(
                        "Equal",
                        [tfidf_model_output.full_name, pos_inf_name],
                        [is_pos_inf],
                        name=scope.get_unique_operator_name("IsPosInf"),
                    )

                    container.add_node(
                        "Equal",
                        [tfidf_model_output.full_name, neg_inf_name],
                        [is_neg_inf],
                        name=scope.get_unique_operator_name("IsNegInf"),
                    )

                    nan_cleaned = scope.get_unique_variable_name("nan_cleaned")
                    container.add_node(
                        "Where",
                        inputs=[is_nan, zero_name, tfidf_model_output.full_name],
                        outputs=[nan_cleaned],
                        name=scope.get_unique_operator_name("ReplaceNaN"),
                    )

                    pos_inf_cleaned = scope.get_unique_variable_name("pos_inf_cleaned")
                    container.add_node(
                        "Where",
                        inputs=[is_pos_inf, max_val_name, nan_cleaned],
                        outputs=[pos_inf_cleaned],
                        name=scope.get_unique_operator_name("ReplacePosInf"),
                    )

                    cleaned_output = scope.declare_local_variable(f"cleaned_col_{col}", FloatTensorType([None, None]))
                    container.add_node(
                        "Where",
                        inputs=[is_neg_inf, min_val_name, pos_inf_cleaned],
                        outputs=[cleaned_output.full_name],
                        name=scope.get_unique_operator_name("ReplaceNegInf"),
                    )

                    truncated_svd_output = scope.declare_local_variable(
                        f"truncated_svd_output_{idx}_{col}", FloatTensorType([None, truncated_svd_n_dims])
                    )
                    truncated_svd = OnnxSubEstimator(
                        truncated_svd_list[idx],
                        cleaned_output.full_name,
                        op_version=container.target_opset,
                        output_names=[truncated_svd_output],
                    )
                    truncated_svd.add_to(scope, container)

                    split_outputs = []
                    for i in range(truncated_svd_n_dims):
                        var = scope.declare_local_variable(
                            f"transformed_col_{idx}_{col}_{i}", FloatTensorType([None, 1])
                        )
                        split_outputs.append(var.full_name)
                        split_outputs_total.append(var.full_name)

                    container.add_node("Split", inputs=[truncated_svd_output.full_name], outputs=split_outputs, axis=1)
                else:
                    casted_name = scope.get_unique_variable_name("casted_input")
                    apply_cast(scope, inputs[col].full_name, casted_name, container, to=onnx_proto.TensorProto.FLOAT)
                    reshaped = scope.get_unique_variable_name(f"reshaped")
                    apply_reshape(scope, casted_name, reshaped, container, desired_shape=[-1, 1])

                    split_outputs_total.append(reshaped)

        original_outputs = [input.full_name for idx, input in enumerate(inputs) if idx not in columns_to_be_deleted]
        final_output_list = original_outputs + split_outputs_total

        for i, out in enumerate(operator.outputs):
            container.add_node(
                "Identity",
                inputs=[final_output_list[i]],
                outputs=[out.full_name],
                name=scope.get_unique_operator_name(f"Identity{i}"),
            )


def text_transformer_parser(
    scope: Scope, model: TextTransformer, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)

    this_operator.inputs.extend(inputs)
    op: TextTransformer = this_operator.raw_operator
    column_headers_list = op.column_headers_list
    columns_to_be_deleted = op.columns_to_be_deleted

    for idx in range(len(column_headers_list) + len(columns_to_be_deleted)):
        if idx not in columns_to_be_deleted:
            if idx < (len(this_operator.inputs)):
                this_operator.outputs.append(
                    scope.declare_local_variable(
                        this_operator.inputs[idx].raw_name,
                        type=this_operator.inputs[idx].type.__class__(shape=this_operator.inputs[idx].type.shape),
                    )
                )
            else:
                this_operator.outputs.append(
                    scope.declare_local_variable(
                        column_headers_list[idx - len(columns_to_be_deleted)], type=FloatTensorType(shape=[None, 1])
                    )
                )

    return list(this_operator.outputs)


transformer = TextTransformer
update_registered_converter(
    transformer,
    f"AutoAI{transformer.__name__}",
    text_transformer_shape_calculator,
    text_transformer_converter,
    parser=text_transformer_parser,
)
