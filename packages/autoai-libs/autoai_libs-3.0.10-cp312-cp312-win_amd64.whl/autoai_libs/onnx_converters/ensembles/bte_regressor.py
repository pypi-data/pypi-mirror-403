################################################################################
# IBM Confidential
# OCO Source Materials
# 5737-H76, 5725-W78, 5900-A1R, 5737-L65
# (c) Copyright IBM Corp. 2025-2026. All Rights Reserved.
# The source code for this program is not published or otherwise divested of its trade secrets,
# irrespective of what has been deposited with the U.S. Copyright Office.
################################################################################

from onnxconverter_common import apply_cast
from skl2onnx import update_registered_converter
from skl2onnx.algebra.onnx_operator import OnnxSubEstimator
from skl2onnx.common._container import ModelComponentContainer
from skl2onnx.common._topology import Operator, Scope
from skl2onnx.common.data_types import guess_proto_type
from skl2onnx.proto import onnx_proto
from snapml import BatchedTreeEnsembleRegressor


def bte_regressor_shape_calculator(operator: Operator) -> None:
    pass


def bte_regressor_converter(scope: Scope, operator: Operator, container: ModelComponentContainer) -> None:
    input_tensor = operator.inputs[0]
    input_type = operator.inputs[0].type
    op: BatchedTreeEnsembleRegressor = operator.raw_operator

    if base_ensemble_fitted := getattr(op, "base_ensemble_fitted_", False):
        sub = OnnxSubEstimator(
            base_ensemble_fitted,
            input_tensor,
            op_version=container.target_opset,
            output_names=[operator.outputs[0].full_name],
        )
        sub.add_to(scope, container)
    else:
        base_score = getattr(op, "base_score_", None)
        ensembles = getattr(op, "ensembles_", None)
        learning_rate = getattr(op, "learning_rate", None)
        n_classes = 1

        base_score_name = scope.get_unique_variable_name("base_score")
        container.add_initializer(base_score_name, guess_proto_type(input_type), [], [base_score])

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

        container.add_node(
            "Squeeze", [margin], [operator.outputs[0].full_name], name=scope.get_unique_operator_name("squeeze_predict")
        )


update_registered_converter(
    BatchedTreeEnsembleRegressor,
    "AutoLibsBatchedTreeEnsembleRegressor",
    bte_regressor_shape_calculator,
    bte_regressor_converter,
)
