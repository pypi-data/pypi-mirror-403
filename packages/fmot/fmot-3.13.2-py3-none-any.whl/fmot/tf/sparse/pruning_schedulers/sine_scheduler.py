import tensorflow as tf
from tensorflow import keras
import math
from fmot.tf.sparse._tfmot.core.sparsity.keras import PruningSchedule


class QuadrantSinePruningSchedule(PruningSchedule):
    def __init__(
        self,
        initial_sparsity: float,
        final_sparsity: float,
        begin_step: int,
        end_step: int,
        frequency: int = 100,
    ):
        """Sine Pruning Schedule class. Ramps from 0 to 1
        using the sine function over the first quadrant.

        Args:
            initial_sparsity (float): Sparsity (%) at which pruning begins.
            final_sparsity (float): Sparsity (%) at which pruning ends.
            begin_step (int): Step at which to begin pruning.
            end_step (int): Step at which to end pruning.
            frequency (int): Only apply pruning every `frequency` steps.
                                 Default: 100
        """
        super(QuadrantSinePruningSchedule, self).__init__()
        self.initial_sparsity = tf.cast(initial_sparsity, dtype=tf.float32)
        self.final_sparsity = tf.cast(final_sparsity, dtype=tf.float32)

        self.begin_step = tf.cast(begin_step, dtype=tf.float32)
        self.end_step = tf.cast(end_step, dtype=tf.float32)
        self.frequency = frequency

        self._validate_step(self.begin_step, self.end_step, self.frequency, False)
        self._validate_sparsity(initial_sparsity, "initial_sparsity")
        self._validate_sparsity(final_sparsity, "final_sparsity")

        self.pi = tf.constant(math.pi, dtype=tf.float32)

    def __call__(self, step):
        step = tf.cast(step, dtype=tf.float32)
        sine_mul = tf.math.sin(
            (self.pi / 2)
            * ((step - self.begin_step) / (self.end_step - self.begin_step))
        )
        sparsity = (
            self.final_sparsity - self.initial_sparsity
        ) * sine_mul + self.initial_sparsity

        return (
            self._should_prune_in_step(
                step, self.begin_step, self.end_step, self.frequency
            ),
            sparsity,
        )

    def get_config(self):
        return {
            "class_name": self.__class__.__name__,
            "config": {
                "initial_sparsity": self.initial_sparsity,
                "final_sparsity": self.final_sparsity,
                "begin_step": self.begin_step,
                "end_step": self.end_step,
                "frequency": self.frequency,
            },
        }
