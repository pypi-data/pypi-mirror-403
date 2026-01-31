################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

import numpy as np
from onnxconverter_common import apply_cast
from skl2onnx import get_model_alias, update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope, Variable
from skl2onnx.common.data_types import guess_data_type, guess_numpy_type, guess_proto_type
from skl2onnx.proto import onnx_proto
from snapml import BatchedTreeEnsembleClassifier


def bte_classifier_shape_calculator(operator: Operator) -> None:
    input_shape = operator.inputs[0].type.shape
    op: BatchedTreeEnsembleClassifier = operator.raw_operator
    classes = getattr(op, "classes_", None)
    num_classes = len(classes)

    operator.outputs[0].type = operator.outputs[0].type.__class__(
        [
            input_shape[0],
        ]
    )
    operator.outputs[1].type = operator.outputs[1].type.__class__([input_shape[0], num_classes])


def bte_classifier_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    input_tensor = operator.inputs[0]
    input_type = operator.inputs[0].type
    op: BatchedTreeEnsembleClassifier = operator.raw_operator

    if base_ensemble_fitted := getattr(op, "base_ensemble_fitted_", False):
        sub = OnnxSubEstimator(
            base_ensemble_fitted,
            input_tensor,
            op_version=container.target_opset,
            output_names=[operator.outputs[0].full_name, operator.outputs[1].full_name],
        )
        sub.add_to(scope, container)
    else:
        base_score = getattr(op, "base_score_", None)
        ensembles = getattr(op, "ensembles_", None)
        learning_rate = getattr(op, "learning_rate", None)
        n_classes = getattr(op, "n_classes_", None)
        classes = getattr(op, "classes_", None)

        if n_classes > 2:
            base_score_name = scope.get_unique_variable_name("base_score")
            container.add_initializer(
                base_score_name, guess_proto_type(input_type), base_score.shape, base_score.ravel().tolist()
            )

            n_classes_name = scope.get_unique_variable_name("n_classes")
            container.add_initializer(n_classes_name, onnx_proto.TensorProto.INT64, [], [n_classes])

            margin = scope.get_unique_variable_name("first_margin")
            container.add_node(
                op_type=(
                    "CustomMarginCreation_64"
                    if guess_proto_type(input_type) == onnx_proto.TensorProto.DOUBLE
                    else "CustomMarginCreation_32"
                ),
                inputs=[input_tensor.full_name, base_score_name, n_classes_name],
                outputs=[margin],
                name=scope.get_unique_operator_name("CustomMarginCreation"),
                op_domain="ai.onnx.contrib",
                op_version=1,
            )

            learning_rate_name = scope.get_unique_variable_name("learning_rate")
            container.add_initializer(learning_rate_name, guess_proto_type(input_type), [], [learning_rate])

            for i, ensemble in enumerate(ensembles):
                cls_ind = i % n_classes

                # create mask
                mask = np.zeros((1, n_classes), dtype=guess_numpy_type(input_type))
                mask[0, cls_ind] = 1.0
                mask_name = scope.get_unique_variable_name(f"cls_mask_name+{cls_ind}")
                container.add_initializer(mask_name, guess_proto_type(input_type), mask.shape, mask.ravel().tolist())

                sub_ensemble_output = scope.get_unique_variable_name("sub_ensemble_output")
                sub_ensemble = OnnxSubEstimator(
                    ensemble,
                    input_tensor.full_name,
                    op_version=container.target_opset,
                    output_names=[sub_ensemble_output],
                )
                sub_ensemble.add_to(scope, container)

                if guess_proto_type(input_type) == onnx_proto.TensorProto.DOUBLE:
                    casted_name = scope.get_unique_variable_name("casted_name")
                    apply_cast(scope, sub_ensemble_output, casted_name, container, to=guess_proto_type(input_type))
                    sub_ensemble_output = casted_name

                reshape_shape_name = scope.get_unique_variable_name("reshape")
                container.add_initializer(
                    reshape_shape_name, onnx_proto.TensorProto.INT64, [2], np.array([-1, 1], dtype=np.int64).tolist()
                )

                ensemble_cols = scope.get_unique_variable_name("estimator_reshape_cols")
                container.add_node(
                    "Reshape",
                    [sub_ensemble_output, reshape_shape_name],
                    [ensemble_cols],
                    name=scope.get_unique_operator_name("reshape_est"),
                )

                contrib = scope.get_unique_variable_name("contrib")
                container.add_node(
                    "MatMul",
                    [ensemble_cols, mask_name],
                    [contrib],
                    name=scope.get_unique_operator_name("MatMul_contrib"),
                )

                learning_and_sub_ensemble_output = scope.get_unique_variable_name("learning_and_sub_ensemble_output")
                container.add_node(
                    "Mul",
                    inputs=[learning_rate_name, contrib],
                    outputs=[learning_and_sub_ensemble_output],
                    name=scope.get_unique_operator_name("mul_learning_ensemble"),
                )

                updated_margin_output = scope.get_unique_variable_name("updated_margin_output")
                container.add_node(
                    "Add",
                    inputs=[margin, learning_and_sub_ensemble_output],
                    outputs=[updated_margin_output],
                    name=scope.get_unique_operator_name("add_margin_and_ensemble"),
                )
                margin = updated_margin_output

            arg_max_name = scope.get_unique_variable_name("argmax_name")
            container.add_node(
                "ArgMax",
                inputs=[margin],
                outputs=[arg_max_name],
                axis=1,
                keepdims=0,
                name=scope.get_unique_operator_name("argmax"),
            )
            if guess_proto_type(operator.outputs[0].type) == onnx_proto.TensorProto.STRING:
                label_encode_name = scope.get_unique_variable_name("label_encode_name")
                container.add_node(
                    "LabelEncoder",
                    [arg_max_name],
                    [label_encode_name],
                    "ai.onnx.ml",
                    keys_int64s=[i for i in range(len(classes))],
                    values_strings=classes,
                )
                container.add_node(
                    "Squeeze",
                    [label_encode_name],
                    [operator.outputs[0].full_name],
                    name=scope.get_unique_operator_name("squeeze_predict"),
                )
            else:
                container.add_node(
                    "Squeeze",
                    [arg_max_name],
                    [operator.outputs[0].full_name],
                    name=scope.get_unique_operator_name("squeeze_predict"),
                )

            container.add_node(
                "Softmax",
                inputs=[margin],
                outputs=[operator.outputs[1].full_name],
                name=scope.get_unique_operator_name("sigmoid"),
                axis=1,
            )
        else:
            base_score_name = scope.get_unique_variable_name("base_score")
            container.add_initializer(base_score_name, guess_proto_type(input_type), [], [base_score])

            n_classes_name = scope.get_unique_variable_name("n_classes")
            container.add_initializer(n_classes_name, onnx_proto.TensorProto.INT64, [], [1])

            margin = scope.get_unique_variable_name("first_margin")
            container.add_node(
                op_type=(
                    "CustomMarginCreation_64"
                    if guess_proto_type(input_type) == onnx_proto.TensorProto.DOUBLE
                    else "CustomMarginCreation_32"
                ),
                inputs=[input_tensor.full_name, base_score_name, n_classes_name],
                outputs=[margin],
                name=scope.get_unique_operator_name("CustomMarginCreation"),
                op_domain="ai.onnx.contrib",
                op_version=1,
            )

            learning_rate_name = scope.get_unique_variable_name("learning_rate")
            container.add_initializer(learning_rate_name, guess_proto_type(input_type), [], [learning_rate])

            for ensemble in ensembles:
                sub_ensemble_output = scope.get_unique_variable_name("sub_ensemble_output")
                sub_ensemble = OnnxSubEstimator(
                    ensemble,
                    input_tensor.full_name,
                    op_version=container.target_opset,
                    output_names=[sub_ensemble_output],
                )
                sub_ensemble.add_to(scope, container)

                if guess_proto_type(input_type) == onnx_proto.TensorProto.DOUBLE:
                    casted_name = scope.get_unique_variable_name("casted_name")
                    apply_cast(scope, sub_ensemble_output, casted_name, container, to=guess_proto_type(input_type))
                    sub_ensemble_output = casted_name

                learning_and_sub_ensemble_output = scope.get_unique_variable_name("learning_and_sub_ensemble_output")
                container.add_node(
                    "Mul",
                    inputs=[learning_rate_name, sub_ensemble_output],
                    outputs=[learning_and_sub_ensemble_output],
                    name=scope.get_unique_operator_name("mul_learning_ensemble"),
                )

                updated_margin_output = scope.get_unique_variable_name("updated_margin_output")
                container.add_node(
                    "Add",
                    inputs=[margin, learning_and_sub_ensemble_output],
                    outputs=[updated_margin_output],
                    name=scope.get_unique_operator_name("add_margin_and_ensemble"),
                )
                margin = updated_margin_output

            bool_name = scope.get_unique_variable_name("margin_gt_zero")
            zero_init_name = scope.get_unique_variable_name("zero_scalar")
            container.add_initializer(zero_init_name, guess_proto_type(input_type), [], [0.0])
            container.add_node(
                "Greater", [margin, zero_init_name], [bool_name], name=scope.get_unique_operator_name("greater")
            )
            cast_name = scope.get_unique_variable_name("cast_predict")
            container.add_node(
                "Cast",
                [bool_name],
                [cast_name],
                name=scope.get_unique_operator_name("cast_to_int64"),
                to=onnx_proto.TensorProto.INT64,
            )
            if guess_proto_type(operator.outputs[0].type) == onnx_proto.TensorProto.STRING:
                label_encode_name = scope.get_unique_variable_name("label_encode_name")
                container.add_node(
                    "LabelEncoder",
                    [cast_name],
                    [label_encode_name],
                    "ai.onnx.ml",
                    keys_int64s=[i for i in range(len(classes))],
                    values_strings=classes,
                )
                container.add_node(
                    "Squeeze",
                    [label_encode_name],
                    [operator.outputs[0].full_name],
                    name=scope.get_unique_operator_name("squeeze_predict"),
                )
            else:
                container.add_node(
                    "Squeeze",
                    [cast_name],
                    [operator.outputs[0].full_name],
                    name=scope.get_unique_operator_name("squeeze_predict"),
                )

            p1 = scope.get_unique_variable_name("proba_pos")
            container.add_node(
                "Sigmoid",
                inputs=[margin],
                outputs=[p1],
                name=scope.get_unique_operator_name("sigmoid"),
            )

            one_name = scope.get_unique_variable_name("one_cost")
            container.add_initializer(one_name, guess_proto_type(input_type), [], [1.0])

            p0 = scope.get_unique_variable_name("proba_neg")
            container.add_node("Sub", [one_name, p1], [p0], name=scope.get_unique_operator_name("one_minus"))
            container.add_node(
                "Concat",
                [p0, p1],
                [operator.outputs[1].full_name],
                name=scope.get_unique_operator_name("concat_proba"),
                axis=1,
            )


def bte_classifier_parser(
    scope: Scope, model: BatchedTreeEnsembleClassifier, inputs: list[Variable], custom_parsers=None
) -> list[Variable]:
    alias = get_model_alias(type(model))
    this_operator = scope.declare_local_operator(alias, model)
    op: BatchedTreeEnsembleClassifier = this_operator.raw_operator

    this_operator.inputs.append(inputs[0])

    classes = getattr(op, "classes_", None)
    label_type = guess_data_type(classes)[0][1].__class__

    val_label = scope.declare_local_variable("val_label", label_type())
    val_prob = scope.declare_local_variable("val_prob", inputs[0].type.__class__())
    this_operator.outputs.append(val_label)
    this_operator.outputs.append(val_prob)

    return list(this_operator.outputs)


update_registered_converter(
    BatchedTreeEnsembleClassifier,
    "AutoLibsBatchedTreeEnsembleClassifier",
    bte_classifier_shape_calculator,
    bte_classifier_converter,
    parser=bte_classifier_parser,
    options={"zipmap": [True, False, "columns"]},
)
