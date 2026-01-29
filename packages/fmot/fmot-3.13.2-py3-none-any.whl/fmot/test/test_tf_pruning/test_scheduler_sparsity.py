import os

os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "2")
os.environ.setdefault("CUDA_VISIBLE_DEVICES", "")

import numpy as np
import pytest


tf = pytest.importorskip("tensorflow")

from fmot.tf.sparse.prune import PruneHelper, strip_all_pruning


def _layer_weight_sparsities(layer):
    weights = [w for w in layer.weights if w.shape.ndims >= 2 and "bias" not in w.name]
    if not weights:
        return []
    sparsities = []
    for w in weights:
        arr = w.numpy()
        zeros = arr == 0.0
        sparsities.append(float(np.sum(zeros)) / float(arr.size))
    return sparsities


def _train_and_measure(
    build_model,
    input_shape,
    prune_layer_cls,
    output_dim,
    target_sparsity,
    prune_scheduler,
    power=None,
):
    tf.keras.backend.clear_session()
    np.random.seed(0)
    tf.random.set_seed(0)

    model = build_model()
    pruned_layer = model.get_layer("pruned")
    initial_bias = None
    if hasattr(pruned_layer, "bias") and pruned_layer.bias is not None:
        initial_bias = pruned_layer.bias.numpy().copy()

    helper = PruneHelper(
        pencil_size=4,
        prune_scheduler=prune_scheduler,
        min_parameter_thresh=0,
    )

    batch_size = 4
    steps_per_epoch = 30
    epochs = 10
    total_steps = steps_per_epoch * epochs

    pruned_kwargs = {}
    if power is not None:
        pruned_kwargs["power"] = power

    pruned = helper(
        model,
        layers_to_prune=[prune_layer_cls],
        initial_sparsity=0.0,
        final_sparsity=target_sparsity,
        begin_step=0,
        end_step=total_steps - 1,
        prune_frequency=1,
        **pruned_kwargs,
    )

    pruned.compile(optimizer=tf.keras.optimizers.SGD(learning_rate=0.0), loss="mse")

    num_samples = batch_size * steps_per_epoch
    x = np.random.randn(num_samples, *input_shape).astype(np.float32)
    y = np.random.randn(num_samples, output_dim).astype(np.float32)

    pruned.fit(
        x,
        y,
        batch_size=batch_size,
        epochs=epochs,
        verbose=0,
        callbacks=[helper.get_pruning_callback()],
    )

    stripped = strip_all_pruning(pruned)
    pruned_layer = stripped.get_layer("pruned")

    bias_ok = True
    if (
        hasattr(pruned_layer, "bias")
        and pruned_layer.bias is not None
        and initial_bias is not None
    ):
        bias_ok = np.allclose(pruned_layer.bias.numpy(), initial_bias, atol=1e-6)

    return _layer_weight_sparsities(pruned_layer), bias_ok


def _build_dense(output_dim):
    inputs = tf.keras.Input(shape=(64,))
    x = tf.keras.layers.Dense(
        32,
        activation="relu",
        use_bias=True,
        bias_initializer="ones",
        name="pruned",
    )(inputs)
    outputs = tf.keras.layers.Dense(output_dim)(x)
    return tf.keras.Model(inputs, outputs)


def _build_dense_out_dim(out_dim, use_bias=True):
    inputs = tf.keras.Input(shape=(64,))
    x = tf.keras.layers.Dense(32, activation="relu", use_bias=use_bias, name="pruned")(
        inputs
    )
    outputs = tf.keras.layers.Dense(out_dim, use_bias=use_bias)(x)
    return tf.keras.Model(inputs, outputs)


def _build_conv1d(output_dim):
    inputs = tf.keras.Input(shape=(32, 8))
    x = tf.keras.layers.Conv1D(
        filters=16,
        kernel_size=4,
        padding="same",
        activation="relu",
        use_bias=True,
        bias_initializer="ones",
        name="pruned",
    )(inputs)
    x = tf.keras.layers.Flatten()(x)
    outputs = tf.keras.layers.Dense(output_dim)(x)
    return tf.keras.Model(inputs, outputs)


def _build_conv2d(output_dim):
    inputs = tf.keras.Input(shape=(16, 16, 4))
    x = tf.keras.layers.Conv2D(
        filters=16,
        kernel_size=(3, 3),
        padding="same",
        activation="relu",
        use_bias=True,
        bias_initializer="ones",
        name="pruned",
    )(inputs)
    x = tf.keras.layers.Flatten()(x)
    outputs = tf.keras.layers.Dense(output_dim)(x)
    return tf.keras.Model(inputs, outputs)


def _build_rnn(output_dim):
    inputs = tf.keras.Input(shape=(10, 16))
    x = tf.keras.layers.Dense(16, activation="relu", name="pre_dense")(inputs)
    x = tf.keras.layers.SimpleRNN(
        32,
        use_bias=True,
        bias_initializer="ones",
        name="pruned",
    )(x)
    outputs = tf.keras.layers.Dense(output_dim)(x)
    return tf.keras.Model(inputs, outputs)


def _build_gru(output_dim):
    inputs = tf.keras.Input(shape=(10, 16))
    x = tf.keras.layers.Dense(16, activation="relu", name="pre_dense")(inputs)
    x = tf.keras.layers.GRU(
        128,
        use_bias=True,
        bias_initializer="ones",
        name="pruned",
    )(x)
    outputs = tf.keras.layers.Dense(output_dim)(x)
    return tf.keras.Model(inputs, outputs)


def _build_lstm(output_dim):
    inputs = tf.keras.Input(shape=(10, 16))
    x = tf.keras.layers.Dense(16, activation="relu", name="pre_dense")(inputs)
    x = tf.keras.layers.LSTM(
        32,
        use_bias=True,
        bias_initializer="ones",
        name="pruned",
    )(x)
    outputs = tf.keras.layers.Dense(output_dim)(x)
    return tf.keras.Model(inputs, outputs)


@pytest.mark.parametrize(
    "build_model,input_shape,prune_layer_cls,output_dim",
    [
        (lambda: _build_conv1d(output_dim=5), (32, 8), tf.keras.layers.Conv1D, 5),
        (lambda: _build_dense(output_dim=5), (64,), tf.keras.layers.Dense, 5),
        (lambda: _build_conv2d(output_dim=5), (16, 16, 4), tf.keras.layers.Conv2D, 5),
        (lambda: _build_rnn(output_dim=5), (10, 16), tf.keras.layers.SimpleRNN, 5),
        (lambda: _build_gru(output_dim=5), (10, 16), tf.keras.layers.GRU, 5),
        (lambda: _build_lstm(output_dim=5), (10, 16), tf.keras.layers.LSTM, 5),
    ],
)
@pytest.mark.parametrize(
    "prune_scheduler,power",
    [
        ("linear", None),
        ("poly_decay", 3),
        ("constant", None),
        ("sine", None),
    ],
)
def test_schedule_reaches_target_sparsity(
    build_model, input_shape, prune_layer_cls, output_dim, prune_scheduler, power
):
    target_sparsity = 0.7
    sparsity_tol = 0.05

    sparsities, bias_ok = _train_and_measure(
        build_model,
        input_shape,
        prune_layer_cls,
        output_dim,
        target_sparsity,
        prune_scheduler=prune_scheduler,
        power=power,
    )
    assert (
        sparsities
    ), "Expected pruned layer to have at least one prunable weight matrix."
    for sparsity in sparsities:
        assert sparsity >= target_sparsity - sparsity_tol
        assert sparsity <= target_sparsity + sparsity_tol
    assert bias_ok, "Bias values should remain unchanged by pruning."


def test_dense_out_dim_le_pencil_size_raises():
    target_sparsity = 0.7

    tf.keras.backend.clear_session()
    np.random.seed(0)
    tf.random.set_seed(0)

    model = _build_dense_out_dim(out_dim=4, use_bias=False)
    helper = PruneHelper(
        pencil_size=4,
        prune_scheduler="linear",
        min_parameter_thresh=0,
    )

    pruned = helper(
        model,
        layers_to_prune=[tf.keras.layers.Dense],
        initial_sparsity=0.0,
        final_sparsity=target_sparsity,
        begin_step=0,
        end_step=1,
        prune_frequency=1,
    )
    pruned.compile(optimizer="adam", loss="mse")

    x = np.random.randn(8, 64).astype(np.float32)
    y = np.random.randn(8, 4).astype(np.float32)

    with pytest.raises(ValueError, match="Input tensor must be rank 2"):
        pruned.fit(
            x,
            y,
            batch_size=4,
            epochs=1,
            verbose=0,
            callbacks=[helper.get_pruning_callback()],
        )
