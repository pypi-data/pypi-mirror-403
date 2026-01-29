import tensorflow as tf
from tensorflow import keras
import math
from fmot.tf.sparse._tfmot.core.sparsity.keras import PruningSchedule


class LinearPruningSchedule(PruningSchedule):
    def __init__(
        self,
        initial_sparsity: float,
        final_sparsity: float,
        begin_step: int,
        end_step: int,
        frequency: int = 100,
    ):
        """
        Linear Pruning Schedule class.

        Args:
            initial_sparsity (float): Sparsity (%) at which pruning begins.
            final_sparsity (float): Sparsity (%) at which pruning ends.
            begin_step (int): Step at which to begin pruning.
            end_step (int): Step at which to end pruning.
            frequency (int): Only apply pruning every `frequency` steps.
                                 Default: 100
        """
        super(LinearPruningSchedule, self).__init__()
        self.initial_sparsity = tf.cast(initial_sparsity, dtype=tf.float32)
        self.final_sparsity = tf.cast(final_sparsity, dtype=tf.float32)

        self.begin_step = tf.cast(begin_step, dtype=tf.float32)
        self.end_step = tf.cast(end_step, dtype=tf.float32)
        self.frequency = frequency

        self._validate_step(self.begin_step, self.end_step, self.frequency, False)
        self._validate_sparsity(initial_sparsity, "initial_sparsity")
        self._validate_sparsity(final_sparsity, "final_sparsity")

    def __call__(self, step):
        step = tf.cast(step, dtype=tf.float32)
        slope = (self.final_sparsity - self.initial_sparsity) / (
            self.end_step - self.begin_step
        )
        current_step = step - self.begin_step
        sparsity = tf.math.multiply(current_step, slope) + self.initial_sparsity
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
