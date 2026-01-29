from fmot.fqir.writer import FQIRWriter, new_fqir_graph, fftlib
import numpy as np
import pytest


@pytest.mark.parametrize(
    ["channels", "order", "loopmethod", "perm_lmax"],
    [
        # perm-lmax only needs to be tested on inputs longer than 512
        [128, 3, True, None],
        [128, 3, False, None],
        [640, 3, False, 512],
        [640, 3, False, None],
        [640, 3, True, 512],
        [640, 3, True, None],
    ],
)
def test_rfft(channels, order, loopmethod, perm_lmax):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)
    x = writer.add_input(channels, quanta=-15, precision="int16")
    re, im = fftlib.rfft(
        writer, x, order, quanta=None, loopmethod=loopmethod, perm_lmax=perm_lmax
    )
    writer.add_outputs([re, im])

    # print(graph)

    x = np.random.randint(-(2**15), 2**15, size=(10, channels))
    re_fqir, im_fqir = graph.run(x)
    re_fqir = re_fqir * 2 ** (re.quanta)
    im_fqir = im_fqir * 2 ** (im.quanta)
    y_fqir = re_fqir + 1j * im_fqir

    y_np = np.fft.rfft(x.astype(np.float32) * 2**-15)

    nmse = np.mean(np.abs(y_fqir - y_np) ** 2)
    nmse = nmse / np.mean(np.abs(y_np) ** 2)
    print(f"{nmse=}")
    print(graph.footprint_bytes())
    assert nmse < 1e-4


if __name__ == "__main__":
    n_fft = 512
    n_stages = 4
    print("LOOPMETHOD=False")
    test_rfft(n_fft, n_stages, False, None)
    print("\n\n\n")
    print("LOOPMETHOD=True")
    test_rfft(n_fft, n_stages, True, None)
