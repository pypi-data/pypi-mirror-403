def test_tagged_fmot_example():
    import fmot
    import torch
    from torch import nn, Tensor
    import numpy as np

    class MelSpecFrontend(nn.Module):
        """
        Example mel-spectrogram frontend, using fmot.tag to label intermediate variables by name
        These tagged variables will be easily located in the FQIR
        """

        def __init__(self, hop: int, n_mels: int, sr=16000):
            super().__init__()
            self.stft = fmot.nn.STFT(
                n_fft=2 * hop, hop_size=hop, window_fn=torch.hann_window(2 * hop)
            )
            self.mag = fmot.nn.signal_processing.Magnitude()
            self.mel_tform = fmot.nn.signal_processing.MelFilterBank(
                sr=sr, n_fft=2 * hop, n_mels=n_mels
            )

        def forward(self, audio: Tensor):
            s_re, s_im = self.stft(audio)
            mag = self.mag(s_re, s_im)
            mels = self.mel_tform(mag)

            # tag intermediate variables so we can easily find them in the FQIR
            fmot.tag(mag, "stft_mag")
            fmot.tag(mels, "mels")
            return mels

    class MelClassifier(nn.Module):
        def __init__(
            self, hop: int, n_mels: int, d_hidden: int, n_classes: int, sr=16000
        ):
            super().__init__()
            self.mel_spec = MelSpecFrontend(hop, n_mels, sr)
            self.lstm = nn.LSTM(n_mels, d_hidden, batch_first=True)
            self.lin_out = nn.Linear(d_hidden, n_classes)

        def forward(self, audio):
            feats = self.mel_spec(audio)
            emb, _ = self.lstm(feats)
            return self.lin_out(emb)

    class STFTClassifier(nn.Module):
        def __init__(self, hop: int, d_hidden: int, n_classes: int):
            super().__init__()
            self.stft = fmot.nn.STFT(
                n_fft=2 * hop, hop_size=hop, window_fn=torch.hann_window(2 * hop)
            )
            self.mag = fmot.nn.signal_processing.Magnitude()
            self.lstm = nn.LSTM(hop + 1, d_hidden, batch_first=True)
            self.lin_out = nn.Linear(d_hidden, n_classes)

        def forward(self, audio):
            s_re, s_im = self.stft(audio)
            mag = self.mag(s_re, s_im)
            # tag features so we can find them easily in FQIR
            fmot.tag(mag, "stft_mag")

            emb, _ = self.lstm(mag)
            return self.lin_out(emb)

    HOP = 128
    N_MELS = 32
    model_a = MelClassifier(HOP, N_MELS, d_hidden=32, n_classes=4)
    model_b = MelClassifier(HOP, N_MELS, d_hidden=64, n_classes=24)
    model_c = STFTClassifier(HOP, d_hidden=24, n_classes=3)
    print("models defined...")

    # training goes here...

    cmodel_a = fmot.ConvertedModel(model_a, batch_dim=0, seq_dim=1)
    cmodel_b = fmot.ConvertedModel(model_b, batch_dim=0, seq_dim=1)
    cmodel_c = fmot.ConvertedModel(model_c, batch_dim=0, seq_dim=1)

    # replace with real calibration data...
    calib = [torch.randn(8, 20, HOP) for _ in range(4)]
    cmodel_a.quantize(calib)
    cmodel_b.quantize(calib)
    cmodel_c.quantize(calib)
    print("models quantized...")

    fqir_a = cmodel_a.trace()
    fqir_b = cmodel_b.trace()
    fqir_c = cmodel_c.trace()
    print("models_traced...")

    # now we have 3 FQIR graphs
    # fqir_a and fqir_b use identical MelSpectrogram frontends
    # fqir_c uses an STFT frontend, which uses the same STFT config as the MelFronted for fqir_a and fqir_b

    from fmot.fqir.writer import get_fqir_between, FQIRWriter, new_fqir_graph

    # step 1: extract feature extraction subgraphs:
    # * audio -> stft_magnitude
    # * stft_magnitude -> mels
    audio2mag = get_fqir_between(fqir_a, [0], ["stft_mag"])
    mag2mels = get_fqir_between(fqir_a, ["stft_mag"], ["mels"])
    # now, let's pull out the classifiers for each graph
    mels2logits_a = get_fqir_between(fqir_a, ["mels"], [0])
    mels2logits_b = get_fqir_between(fqir_b, ["mels"], [0])
    mag2logits_c = get_fqir_between(fqir_c, ["stft_mag"], [0])

    # finally, let's construct our end-to-end graph by inlining these together
    fqir_e2e = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir_e2e)

    (audio,) = writer.add_inputs_from_graph(audio2mag)
    (mag,) = writer.inline_fqir_graph(audio2mag, inputs=[audio])
    (mels,) = writer.inline_fqir_graph(mag2mels, inputs=[mag])
    (logits_a,) = writer.inline_fqir_graph(mels2logits_a, inputs=[mels])
    (logits_b,) = writer.inline_fqir_graph(mels2logits_b, inputs=[mels])
    (logits_c,) = writer.inline_fqir_graph(mag2logits_c, inputs=[mag])
    writer.add_outputs([logits_a, logits_b, logits_c])

    print("models combined...")

    # now, let's test our E2E graph against the individual graphs
    audio = np.random.randint(low=-1000, high=1000, size=(20, HOP))
    out_a0 = fqir_a.run(audio)
    out_b0 = fqir_b.run(audio)
    out_c0 = fqir_c.run(audio)

    out_a1, out_b1, out_c1 = fqir_e2e.run(audio)

    assert np.array_equal(out_a0, out_a1)
    assert np.array_equal(out_b0, out_b1)
    assert np.array_equal(out_c0, out_c1)

    print("passed runtime tests!")


def test_simpler_tagged_fmot_example():
    import torch
    import fmot
    from torch import nn

    class MelSpec(nn.Module):
        def __init__(self, hop: int, window: int, n_mels: int):
            super().__init__()

            self.stft = fmot.nn.STFT(window, hop, window_fn=torch.hann_window(window))
            self.mag = fmot.nn.signal.Magnitude()
            self.mel = fmot.nn.signal.MelFilterBank(16000, window, n_mels)

        def forward(self, audio):
            re, im = self.stft(audio)
            mag = self.mag(re, im)
            mels = self.mel(mag)
            fmot.tag(mels, "mels")
            return mels

    class LSTMClassifier(nn.Module):
        def __init__(self, n_mels: int, hidden_size: int, n_labels: int):
            super().__init__()
            self.lstm = nn.LSTM(n_mels, hidden_size, batch_first=True)
            self.proj_out = nn.Linear(hidden_size, n_labels)

        def forward(self, mels):
            feats, _ = self.lstm(mels)
            return self.proj_out(feats)

    N_MELS = 32
    HOP = 128
    WINDOW = 256
    D_HIDDEN = 64

    e2e_model_a = nn.Sequential(
        MelSpec(HOP, WINDOW, N_MELS), LSTMClassifier(N_MELS, D_HIDDEN, 5)
    )
    e2e_model_b = nn.Sequential(
        MelSpec(HOP, WINDOW, N_MELS), LSTMClassifier(N_MELS, D_HIDDEN, 7)
    )

    # -----------------------------#

    cmodel_a = fmot.ConvertedModel(e2e_model_a, batch_dim=0, seq_dim=1)
    cmodel_b = fmot.ConvertedModel(e2e_model_a, batch_dim=0, seq_dim=1)

    calib = [torch.randn(8, 10, HOP) for _ in range(10)]

    cmodel_a.quantize(calib)
    cmodel_b.quantize(calib)

    a_fqir = cmodel_a.trace()
    b_fqir = cmodel_b.trace()

    # -----------------------------#

    from fmot.fqir.writer import get_fqir_between

    # get_fqir_between returns an FQIR subgraph that produces the given set of inputs from the given
    # set of inputs.

    # if an input is an integer, then this refers to the index of the top-level graph input. Otherwise, a string
    # refers to the name of the given FQIR variable.

    # similarly, if an output is an integer, this refers to the index of the top-level graph output. Otherwise, a string
    # refers to the name of the given FQIR variable.
    frontend = get_fqir_between(a_fqir, inputs=[0], outputs=["mels"])

    dnn_a = get_fqir_between(a_fqir, inputs=["mels"], outputs=[0])
    dnn_b = get_fqir_between(b_fqir, inputs=["mels"], outputs=[0])

    # -----------------------------#

    from fmot.fqir.writer import new_fqir_graph, FQIRWriter

    # new_fqir_graph creates an empty graph object, and FQIRWriter.from_fqir attaches
    # a writer to it
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    # add input and inline the mel fqir
    (audio,) = writer.add_inputs_from_graph(frontend)
    (mels,) = writer.inline_fqir_graph(frontend, inputs=[audio])

    # inline the two classifiers, using the mel-features as input
    (out_a,) = writer.inline_fqir_graph(dnn_a, inputs=[mels])
    (out_b,) = writer.inline_fqir_graph(dnn_b, inputs=[mels])

    # add outputs
    writer.add_outputs([out_a, out_b])

    # -----------------------------#

    import numpy as np

    # run random integer data through the models
    x = np.random.randint(low=-(2**15), high=2**15 - 1, size=[10, HOP])

    # first, run each graph individually
    a_vals_0 = a_fqir.run(x, dequant=False)
    b_vals_0 = b_fqir.run(x, dequant=False)

    # now, run the end-to-end graph
    a_vals_1, b_vals_1 = graph.run(x, dequant=False)

    assert np.array_equal(a_vals_0, a_vals_1)
    assert np.array_equal(b_vals_0, b_vals_1)


if __name__ == "__main__":
    # test_tagged_fmot_example()
    test_simpler_tagged_fmot_example()
