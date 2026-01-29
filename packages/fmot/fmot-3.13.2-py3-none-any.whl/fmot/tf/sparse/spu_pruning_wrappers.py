"""
Block (pencil) pruning wrappers for TF/Keras Conv1D and Conv2D layers.

These wrappers implement block (pencil) pruning for Conv1D/Conv2D layers, which is not
supported by default TF pruning utilities. Masks are applied in the forward
pass (kernel * mask), ensuring gradients are masked consistently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import tensorflow as tf
from fmot.tf.sparse._tfmot.core.sparsity import keras as mot_keras


def _nparams_to_prune_round(amount: tf.Tensor, tensor_size: tf.Tensor) -> tf.Tensor:
    """
    Compute number of parameters to prune as round(amount * tensor_size).

    The result is clipped to [0, tensor_size].
    """
    amount = tf.clip_by_value(tf.cast(amount, tf.float32), 0.0, 1.0)
    tensor_size_i = tf.cast(tensor_size, tf.int32)
    k = tf.cast(tf.round(amount * tf.cast(tensor_size_i, tf.float32)), tf.int32)
    k = tf.clip_by_value(k, 0, tensor_size_i)
    return k


def _topk_smallest_indices(scores_1d: tf.Tensor, k: tf.Tensor) -> tf.Tensor:
    scores_1d = tf.cast(scores_1d, tf.float32)
    k = tf.cast(k, tf.int32)

    def _do():
        # smallest-k == topk of negative values
        _, idx = tf.math.top_k(-scores_1d, k=k, sorted=False)
        return idx

    return tf.cond(k > 0, _do, lambda: tf.zeros([0], dtype=tf.int32))


def _pencil_scores_mean_abs(flat_x: tf.Tensor) -> tf.Tensor:
    # flat_x: (n_pencils, pencil_size) -> (n_pencils,)
    return tf.reduce_mean(tf.abs(flat_x), axis=-1)


def _pencil_mask_2d_global(
    w_2d: tf.Tensor,
    default_mask_2d: tf.Tensor,
    amount: tf.Tensor,
    pencil_size: int,
) -> tf.Tensor:
    """Compute a pencil mask for a 2D tensor."""
    w_2d = tf.convert_to_tensor(w_2d)
    m_2d = tf.convert_to_tensor(default_mask_2d)

    nrows = tf.shape(w_2d)[0]
    ncols = tf.shape(w_2d)[1]

    # pad rows to multiple of pencil_size
    mod = tf.math.mod(nrows, pencil_size)
    padding = tf.math.mod(pencil_size - mod, pencil_size)  # (p - (n%p)) % p

    w_pad = tf.pad(w_2d, [[0, padding], [0, 0]])
    m_pad = tf.pad(m_2d, [[0, padding], [0, 0]])

    # transpose then flatten into (-1, pencil_size)
    wt = tf.transpose(w_pad)  # (ncols, nrows_pad)
    mt = tf.transpose(m_pad)

    flat_w = tf.reshape(wt, [-1, pencil_size])
    flat_m = tf.reshape(mt, [-1, pencil_size])

    scores = _pencil_scores_mean_abs(flat_w)
    n_pencils = tf.size(scores)

    k = _nparams_to_prune_round(amount, n_pencils)
    idx = _topk_smallest_indices(scores, k)

    # broadcast pruning to the full pencil: set those rows to zero
    row_mask = tf.ones([n_pencils], dtype=flat_m.dtype)
    row_mask = tf.tensor_scatter_nd_update(
        row_mask,
        indices=tf.expand_dims(idx, axis=1),
        updates=tf.zeros([tf.shape(idx)[0]], dtype=flat_m.dtype),
    )
    pruned_flat_m = flat_m * tf.expand_dims(row_mask, axis=1)

    # reshape back and unpad
    mt_new = tf.reshape(pruned_flat_m, tf.shape(mt))
    m_new_pad = tf.transpose(mt_new)  # (nrows_pad, ncols)
    m_new = m_new_pad[:nrows, :]
    return m_new


# ---- Keras kernel layout conversions ----


def _conv1d_to_torch_layout(kernel_tf: tf.Tensor) -> tf.Tensor:
    # Kernel layout is invariant to data_format (e.g., NWC vs NCW); only activation layout changes.
    # tf: (k, in, out) -> torch-like: (out, in, k)
    return tf.transpose(kernel_tf, [2, 1, 0])


def _conv1d_to_tf_layout(kernel_torch: tf.Tensor) -> tf.Tensor:
    # Kernel layout is invariant to data_format (e.g., NWC vs NCW); only activation layout changes.
    # torch-like: (out, in, k) -> tf: (k, in, out)
    return tf.transpose(kernel_torch, [2, 1, 0])


def _conv2d_to_torch_layout(kernel_tf: tf.Tensor) -> tf.Tensor:
    # Kernel layout is invariant to data_format (e.g., NHWC vs NCHW); only activation layout changes.
    # tf: (kh, kw, in, out) -> torch-like: (o, i, kw, kh)
    return tf.transpose(kernel_tf, [3, 2, 1, 0])


def _conv2d_to_tf_layout(kernel_torch: tf.Tensor) -> tf.Tensor:
    # Kernel layout is invariant to data_format (e.g., NHWC vs NCHW); only activation layout changes.
    # torch-like: (o, i, kw, kh) -> tf: (kh, kw, in, out)
    return tf.transpose(kernel_torch, [3, 2, 1, 0])


def _pencil_mask_conv1d(
    w_tf: tf.Tensor,
    default_mask_tf: tf.Tensor,
    amount: tf.Tensor,
    pencil_size: int,
) -> tf.Tensor:
    """Compute a pencil mask for Conv1D kernels in a flattened (out, in * k) view."""
    w_t = _conv1d_to_torch_layout(w_tf)  # (out, in, k)
    m_t = _conv1d_to_torch_layout(default_mask_tf)

    out_ch = tf.shape(w_t)[0]
    in_ch = tf.shape(w_t)[1]
    k = tf.shape(w_t)[2]

    w_2d = tf.reshape(w_t, [out_ch, in_ch * k])
    m_2d = tf.reshape(m_t, [out_ch, in_ch * k])

    new_m_2d = _pencil_mask_2d_global(w_2d, m_2d, amount, pencil_size)
    new_m_t = tf.reshape(new_m_2d, [out_ch, in_ch, k])

    return _conv1d_to_tf_layout(new_m_t)  # (k, in, out)


def _pencil_mask_conv2d(
    w_tf: tf.Tensor,
    default_mask_tf: tf.Tensor,
    amount: tf.Tensor,
    pencil_size: int,
) -> tf.Tensor:
    """Compute a pencil mask for Conv2D kernels."""
    w = _conv2d_to_torch_layout(w_tf)  # (o, i, kw, kh)
    m = _conv2d_to_torch_layout(default_mask_tf)

    o = tf.shape(w)[0]
    i = tf.shape(w)[1]

    # skip if i == 1 (depthwise)
    def _no_prune():
        return tf.ones_like(w_tf, dtype=default_mask_tf.dtype)

    def _do_prune():
        # put output last: (i, kw, kh, o)
        w_i_last = tf.transpose(w, [1, 2, 3, 0])
        m_i_last = tf.transpose(m, [1, 2, 3, 0])

        # pad output dim to multiple of pencil_size
        mod = tf.math.mod(o, pencil_size)
        pad_o = tf.math.mod(pencil_size - mod, pencil_size)

        w_pad = tf.pad(w_i_last, [[0, 0], [0, 0], [0, 0], [0, pad_o]])
        m_pad = tf.pad(m_i_last, [[0, 0], [0, 0], [0, 0], [0, pad_o]])

        flat_w = tf.reshape(w_pad, [-1, pencil_size])
        flat_m = tf.reshape(m_pad, [-1, pencil_size])

        scores = _pencil_scores_mean_abs(flat_w)
        n_pencils = tf.size(scores)

        k_prune = _nparams_to_prune_round(amount, n_pencils)
        idx = _topk_smallest_indices(scores, k_prune)

        row_mask = tf.ones([n_pencils], dtype=flat_m.dtype)
        row_mask = tf.tensor_scatter_nd_update(
            row_mask,
            indices=tf.expand_dims(idx, axis=1),
            updates=tf.zeros([tf.shape(idx)[0]], dtype=flat_m.dtype),
        )
        pruned_flat_m = flat_m * tf.expand_dims(row_mask, axis=1)

        m_pruned_pad = tf.reshape(pruned_flat_m, tf.shape(m_pad))  # (i, kw, kh, o+pad)
        m_pruned = m_pruned_pad[..., :o]  # slice output back

        # back to (o, i, kw, kh) then to TF layout
        m_torch = tf.transpose(m_pruned, [3, 0, 1, 2])
        return _conv2d_to_tf_layout(m_torch)

    return tf.cond(i == 1, _no_prune, _do_prune)


# ---- Wrappers + pruning callback ----


@dataclass
class SPUPruningConfig:
    """Configuration for SPU pruning wrappers."""

    pruning_schedule: mot_keras.PruningSchedule
    pencil_size: int


class _SPUBaseWrapper(tf.keras.layers.Wrapper):
    """Base wrapper with shared pruning schedule behavior."""

    def __init__(
        self, layer: tf.keras.layers.Layer, spu_cfg: SPUPruningConfig, **kwargs
    ):
        super().__init__(layer, **kwargs)
        self.spu_cfg = spu_cfg
        self._mask: Optional[tf.Variable] = None

    @property
    def mask(self) -> tf.Variable:
        if self._mask is None:
            raise RuntimeError("Mask not built yet.")
        return self._mask

    def update_mask(self, step: int) -> None:
        should_prune, sparsity = self.spu_cfg.pruning_schedule(step)
        should_prune = tf.cast(should_prune, tf.bool)

        def _do():
            new_mask = self._compute_new_mask(tf.cast(sparsity, tf.float32))
            self.mask.assign(tf.cast(new_mask, self.mask.dtype))
            return 0

        tf.cond(should_prune, _do, lambda: 0)

    def _compute_new_mask(self, amount: tf.Tensor) -> tf.Tensor:
        raise NotImplementedError


class SPUConv1DPruneWrapper(_SPUBaseWrapper):
    """Conv1D pruning wrapper using pencil pruning masks."""

    def _should_prune(self) -> bool:
        groups = getattr(self.layer, "groups", 1)
        input_shape = getattr(self.layer, "input_shape", None)
        if input_shape is None:
            return True
        in_channels = (
            input_shape[-1]
            if self.layer.data_format != "channels_first"
            else input_shape[1]
        )
        effective_groups = 1 if groups in (None, 1) else groups
        if effective_groups == in_channels:
            return False
        if effective_groups != 1:
            return False
        return True

    def build(self, input_shape):
        # self.layer.build(input_shape)
        self._mask = tf.Variable(
            initial_value=tf.ones_like(self.layer.kernel, dtype=tf.float32),
            trainable=False,
            name="spu_kernel_mask",
        )
        super().build(input_shape)

    def _compute_new_mask(self, amount: tf.Tensor) -> tf.Tensor:
        if not self._should_prune():
            return self.mask
        return _pencil_mask_conv1d(
            w_tf=self.layer.kernel,
            default_mask_tf=self.mask,
            amount=amount,
            pencil_size=self.spu_cfg.pencil_size,
        )

    def call(self, inputs, training=None):
        kernel_eff = tf.cast(self.layer.kernel, tf.float32) * tf.cast(
            self.mask, tf.float32
        )

        data_format = "NWC" if self.layer.data_format == "channels_last" else "NCW"
        stride = self.layer.strides[0]
        dil = self.layer.dilation_rate[0]

        y = tf.nn.conv1d(
            inputs,
            filters=tf.cast(kernel_eff, inputs.dtype),
            stride=stride,
            padding=self.layer.padding.upper(),
            data_format=data_format,
            dilations=dil,
        )

        if self.layer.use_bias:
            y = tf.nn.bias_add(y, self.layer.bias, data_format=data_format)

        if self.layer.activation is not None:
            y = self.layer.activation(y)

        return y


class SPUConv2DPruneWrapper(_SPUBaseWrapper):
    """Conv2D pruning wrapper using pencil pruning masks."""

    def _should_prune(self) -> bool:
        groups = getattr(self.layer, "groups", 1)
        input_shape = getattr(self.layer, "input_shape", None)
        if input_shape is None:
            return True
        in_channels = (
            input_shape[-1]
            if self.layer.data_format != "channels_first"
            else input_shape[1]
        )
        effective_groups = 1 if groups in (None, 1) else groups
        if effective_groups == in_channels:
            return False
        if effective_groups != 1:
            return False
        return True

    def build(self, input_shape):
        # self.layer.build(input_shape)
        self._mask = tf.Variable(
            initial_value=tf.ones_like(self.layer.kernel, dtype=tf.float32),
            trainable=False,
            name="spu_kernel_mask",
        )
        super().build(input_shape)

    def _compute_new_mask(self, amount: tf.Tensor) -> tf.Tensor:
        if not self._should_prune():
            return self.mask
        return _pencil_mask_conv2d(
            w_tf=self.layer.kernel,
            default_mask_tf=self.mask,
            amount=amount,
            pencil_size=self.spu_cfg.pencil_size,
        )

    def call(self, inputs, training=None):
        kernel_eff = tf.cast(self.layer.kernel, tf.float32) * tf.cast(
            self.mask, tf.float32
        )

        # TF expects different stride/dilation layouts depending on data_format
        if self.layer.data_format == "channels_last":
            data_format = "NHWC"
            strides = [1, self.layer.strides[0], self.layer.strides[1], 1]
            dil = [1, self.layer.dilation_rate[0], self.layer.dilation_rate[1], 1]
        else:
            data_format = "NCHW"
            strides = [1, 1, self.layer.strides[0], self.layer.strides[1]]
            dil = [1, 1, self.layer.dilation_rate[0], self.layer.dilation_rate[1]]

        y = tf.nn.conv2d(
            inputs,
            filters=tf.cast(kernel_eff, inputs.dtype),
            strides=strides,
            padding=self.layer.padding.upper(),
            data_format=data_format,
            dilations=dil,
        )

        if self.layer.use_bias:
            y = tf.nn.bias_add(y, self.layer.bias, data_format=data_format)

        if self.layer.activation is not None:
            y = self.layer.activation(y)

        return y


class FemtoTFPruningUpdateStep(tf.keras.callbacks.Callback):
    """
    Pruning callback that updates both internal and SPU pruning masks.

    Compatible with `model.fit(...)` and custom training loops.
    """

    def __init__(self):
        super().__init__()
        self._pruning_step = mot_keras.UpdatePruningStep()
        self._global_step = tf.Variable(0, dtype=tf.int64, trainable=False)

    def set_model(self, model):
        super().set_model(model)
        self._pruning_step.set_model(model)

    def on_train_begin(self, logs=None, **kwargs):
        self._global_step.assign(0)
        self._pruning_step.on_train_begin(logs=logs)
        self._update_spu_layers()

    def on_train_batch_begin(self, batch=None, logs=None, **kwargs):
        # prune before forward
        self._pruning_step.on_train_batch_begin(
            batch=batch if batch is not None else -1, logs=logs
        )
        self._update_spu_layers()
        self._global_step.assign_add(1)

    def on_epoch_end(self, epoch=None, logs=None, batch=None, **kwargs):
        # Support BOTH call styles.
        # If your loop passes batch=-1, forward that into the pruning callback.
        if batch is not None:
            self._pruning_step.on_epoch_end(batch=batch, logs=logs)
        else:
            # Some callback versions accept epoch; some accept batch. Be permissive:
            try:
                self._pruning_step.on_epoch_end(epoch=epoch, logs=logs)
            except TypeError:
                self._pruning_step.on_epoch_end(batch=-1, logs=logs)

        self._update_spu_layers()

    def _update_spu_layers(self):
        if self.model is None:
            return
        step_val = int(self._global_step.numpy())
        for layer in self.model.layers:
            if isinstance(layer, (SPUConv1DPruneWrapper, SPUConv2DPruneWrapper)):
                layer.update_mask(step_val)
