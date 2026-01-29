"""
Structured pruning utilities for TensorFlow/Keras models.

This module provides a helper to wrap eligible layers with pruning logic and
includes utilities to strip wrappers and bake pruning masks into weights.

Non-convolutional layers use internal pruning utilities. Conv1D and Conv2D use
custom block (pencil) pruning because default TF pruning does not support block-pruning
for Conv1D/Conv2D layers.
"""

import tensorflow as tf
from typing import Union, List, Callable

from fmot.tf.sparse._tfmot.core.sparsity import keras as mot_keras
from fmot.tf.sparse.pruning_schedulers.linear_scheduler import (
    LinearPruningSchedule,
)
from fmot.tf.sparse.pruning_schedulers.sine_scheduler import (
    QuadrantSinePruningSchedule,
)

from fmot.tf.sparse.spu_pruning_wrappers import (
    SPUPruningConfig,
    SPUConv1DPruneWrapper,
    SPUConv2DPruneWrapper,
    FemtoTFPruningUpdateStep,
)

import logging

logging.basicConfig(level=logging.INFO)


class PruneHelper:
    """
    Wraps selected layers with pruning behavior and provides pruning callbacks.

    Conv1D/Conv2D layers use custom block (pencil) pruning wrappers.
    All other layers use internal `prune_low_magnitude`.
    """

    def __init__(
        self,
        pencil_size: int = 4,
        pencil_pooling_type: str = "AVG",  # kept for non-conv block pruning; conv uses AVG (mean abs)
        prune_scheduler: str = "polynomial_decay",
        min_parameter_thresh: int = 200,
    ) -> None:
        assert pencil_size in (4, 8), "SPU supports pencil size 4 or 8."
        self.pencil_size = pencil_size
        self.block_size = (1, self.pencil_size)
        self.pencil_pooling_type = pencil_pooling_type
        self.min_parameter_thresh = min_parameter_thresh

        self.prune_scheduler = prune_scheduler
        self.prune_scheduler_map = {
            "poly_decay": mot_keras.PolynomialDecay,
            "constant": mot_keras.ConstantSparsity,
            "linear": LinearPruningSchedule,
            "sine": QuadrantSinePruningSchedule,
        }

    def get_pruning_callback(self) -> tf.keras.callbacks.Callback:
        """Return the FemtoTFPruningUpdateStep callback for model.fit or custom loops."""
        return FemtoTFPruningUpdateStep()

    def _prune_selected_layers_fn(
        self,
        pruning_params: dict,
        layers_to_prune: List[tf.keras.layers.Layer] = None,
        force_skip_layers: List[str] = [],
    ) -> Callable:
        if layers_to_prune is None:
            layers_to_prune = [
                tf.keras.layers.Dense,
                tf.keras.layers.Conv2D,
                tf.keras.layers.Conv1D,
                tf.keras.layers.SimpleRNN,
                tf.keras.layers.GRU,
                tf.keras.layers.LSTM,
            ]

        def _prune_layer(layer: tf.keras.layers.Layer):
            prune_layer_bool = any(
                isinstance(layer, layer_type) for layer_type in layers_to_prune
            )
            if prune_layer_bool is False:
                return layer

            weight_thresh_bool = any(
                tf.size(weight) > self.min_parameter_thresh
                for weight in layer.trainable_weights
            )
            if weight_thresh_bool is False:
                return layer

            force_skip_bool = any(
                weight.name in force_skip_layers for weight in layer.trainable_weights
            )
            if force_skip_bool is True:
                return layer

            # ---- Conv1D/Conv2D: use SPU wrappers ----
            if isinstance(layer, tf.keras.layers.Conv1D):
                spu_cfg = SPUPruningConfig(
                    pruning_schedule=pruning_params["pruning_schedule"],
                    pencil_size=self.pencil_size,
                )
                return SPUConv1DPruneWrapper(layer, spu_cfg)

            if isinstance(layer, tf.keras.layers.Conv2D):
                spu_cfg = SPUPruningConfig(
                    pruning_schedule=pruning_params["pruning_schedule"],
                    pencil_size=self.pencil_size,
                )
                return SPUConv2DPruneWrapper(layer, spu_cfg)

            # ---- Non-conv: use internal helper ----
            return mot_keras.prune_low_magnitude(layer, **pruning_params)

        return _prune_layer

    def _get_scheduler_params(
        self,
        begin_step: int,
        end_step: int,
        prune_frequency: int,
        power: int,
        initial_sparsity: float,
        final_sparsity: float,
    ):
        scheduler_params = {
            "begin_step": begin_step,
            "end_step": end_step,
            "frequency": prune_frequency,
        }
        if self.prune_scheduler == "poly_decay":
            scheduler_params.update(
                {
                    "power": power,
                    "initial_sparsity": initial_sparsity,
                    "final_sparsity": final_sparsity,
                }
            )
        elif self.prune_scheduler == "constant":
            scheduler_params.update({"target_sparsity": final_sparsity})
        elif self.prune_scheduler in ("linear", "sine"):
            scheduler_params.update(
                {"initial_sparsity": initial_sparsity, "final_sparsity": final_sparsity}
            )
        else:
            raise Exception(f"Unknown Prune Scheduler: {self.prune_scheduler}")
        return scheduler_params

    def _model_add_prune_wrappers(
        self,
        model: Union[tf.keras.Model, tf.keras.Sequential],
        initial_sparsity: float,
        final_sparsity: float,
        begin_step: int,
        end_step: int,
        prune_frequency: int,
        power: int = 3,
        layers_to_prune: List[tf.keras.layers.Layer] = None,
        force_skip_layers: List[str] = [],
    ) -> Union[tf.keras.Model, tf.keras.Sequential]:
        if layers_to_prune is None:
            layers_to_prune = [
                tf.keras.layers.Dense,
                tf.keras.layers.Conv2D,
                tf.keras.layers.Conv1D,
                tf.keras.layers.SimpleRNN,
                tf.keras.layers.GRU,
                tf.keras.layers.LSTM,
            ]

        scheduler_params = self._get_scheduler_params(
            begin_step=begin_step,
            end_step=end_step,
            prune_frequency=prune_frequency,
            power=power,
            initial_sparsity=initial_sparsity,
            final_sparsity=final_sparsity,
        )

        pruning_params = {
            "pruning_schedule": self.prune_scheduler_map[self.prune_scheduler](
                **scheduler_params
            ),
            # used for internal block pruning on non-conv layers
            "block_size": self.block_size,
            "block_pooling_type": self.pencil_pooling_type,
        }

        model_to_prune = tf.keras.models.clone_model(
            model,
            clone_function=self._prune_selected_layers_fn(
                pruning_params, layers_to_prune, force_skip_layers
            ),
        )
        return model_to_prune

    def __call__(self, *args, **kwargs):
        return self._model_add_prune_wrappers(*args, **kwargs)


def _strip_conv_pruning(model: tf.keras.Model) -> tf.keras.Model:
    """
    Remove SPU Conv1D/Conv2D wrappers and bake masks into kernels.

    Returns a new model graph (no in-place graph mutation).
    """

    def _clone_fn(layer: tf.keras.layers.Layer):
        # Always clone layers so weight names are re-created without wrapper scopes.
        if isinstance(layer, (SPUConv1DPruneWrapper, SPUConv2DPruneWrapper)):
            base = layer.layer  # the original Conv layer
            return base.__class__.from_config(base.get_config())

        return layer.__class__.from_config(layer.get_config())

    # 1) Clone graph, unwrapping SPU wrappers
    stripped = tf.keras.models.clone_model(model, clone_function=_clone_fn)

    # 2) Copy weights, baking kernel masks where needed
    # We match layers by name; SPU wrappers map to their inner conv layer names.
    old_by_name = {layer.name: layer for layer in model.layers}
    new_by_name = {layer.name: layer for layer in stripped.layers}

    for name, old_layer in old_by_name.items():
        new_layer = new_by_name.get(name)
        if isinstance(old_layer, (SPUConv1DPruneWrapper, SPUConv2DPruneWrapper)):
            base_old = old_layer.layer
            new_layer = new_by_name.get(base_old.name, new_layer)

        if new_layer is None:
            continue

        if isinstance(old_layer, (SPUConv1DPruneWrapper, SPUConv2DPruneWrapper)):
            base_old = old_layer.layer
            # Bake mask into kernel
            baked_kernel = tf.cast(base_old.kernel, tf.float32) * tf.cast(
                old_layer.mask, tf.float32
            )
            baked_kernel = tf.cast(baked_kernel, base_old.kernel.dtype)

            if base_old.use_bias:
                new_layer.set_weights([baked_kernel.numpy(), base_old.bias.numpy()])
            else:
                new_layer.set_weights([baked_kernel.numpy()])
        else:
            # Normal case: just copy weights
            try:
                new_layer.set_weights(old_layer.get_weights())
            except Exception:
                # Some layers have no weights or don't support set_weights cleanly
                pass

    return stripped


def strip_all_pruning(model_to_prune: tf.keras.Model) -> tf.keras.Model:
    """
    Remove all pruning wrappers and bake masks into weights.

    This strips both internal pruning wrappers and SPU Conv1D/Conv2D wrappers.
    """
    model_stripped = mot_keras.strip_pruning(model_to_prune)
    model_stripped = _strip_conv_pruning(model_stripped)
    return model_stripped
