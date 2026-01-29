import numpy as np
from fmot.fqir.writer import FQIRWriter, new_fqir_graph
import pytest


@pytest.mark.parametrize(["eps", "pos_only", "quanta"], [[1e-3, True, -6]])
def test_divide_i16(eps: float, pos_only: bool, quanta: int, plot=False):
    np.random.seed(0)
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    x = writer.add_input(32, quanta=-15, precision="int16")
    y = writer.add_input(32, quanta=-15, precision="int16")

    z = writer.divide(x, y, eps=eps, quanta=quanta, pos_only=pos_only)

    writer.add_outputs([z])

    x = np.random.randint(-(2**14), 2**14, size=(100, 32))
    y = np.random.randint(-(2**14), 2**14, size=(100, 32))
    if pos_only:
        y = np.abs(y)
    z_fqir = graph.run(x, y)

    x = x * 2**-15
    y = y * 2**-15
    sign = np.sign(y)
    sign[sign == 0] = 1
    y = y + eps * sign
    z_expected = x / y

    z_fqir = z_fqir * 2**quanta

    if plot:
        import matplotlib.pyplot as plt

        plt.plot(np.abs(z_expected.flatten()), np.abs(z_fqir.flatten()), ".")
        plt.xscale("log", base=2)
        plt.yscale("log", base=2)
        plt.grid()
        plt.title("int16 divide")
        plt.xlabel("numpy output")
        plt.ylabel("FQIR output")
        plt.show()

    mse = np.nanmean((z_expected - z_fqir) ** 2)
    mse /= np.nanmean(z_expected**2)
    print(f"mse: {mse}")
    assert mse < 1e-1


@pytest.mark.parametrize(["eps", "pos_only", "quanta"], [[1e-5, True, -6]])
def test_divide_i24(eps: float, pos_only: bool, quanta: int, plot=False):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    x = writer.add_input(32, quanta=-23, precision="int24")
    y = writer.add_input(32, quanta=-23, precision="int24")

    with writer.with_precision("int24") as pwriter:
        z = pwriter.divide(x, y, eps=eps, quanta=quanta, pos_only=pos_only)

    writer.add_outputs([z])

    x = np.random.randint(1, 2**22, size=(100, 32))
    y = np.random.randint(1, 2**22, size=(100, 32))
    if pos_only:
        y = np.abs(y)
    z_fqir = graph.run(x, y)

    x = x * 2**-23
    y = y * 2**-23
    sign = np.sign(y)
    sign[sign == 0] = 1
    y = y + eps * sign
    z_expected = x / y
    z_expected[np.isinf(z_expected)] = float("nan")

    z_fqir = z_fqir * 2**quanta

    if plot:
        import matplotlib.pyplot as plt

        plt.plot(z_expected.flatten(), z_fqir.flatten(), ".")
        plt.xscale("log", base=2)
        plt.yscale("log", base=2)
        plt.title("int24 divide")
        plt.xlabel("numpy output")
        plt.ylabel("FQIR output")
        plt.grid()
        plt.show()

    mse = np.nanmean((z_expected - z_fqir) ** 2)
    mse /= np.nanmean(z_expected**2)
    print(f"mse: {mse}")

    # higher error tolerance due to lack of interpolation
    assert mse < 1e-1


@pytest.mark.parametrize("precision", ["int16", "int24"])
def test_divide_from_components(precision):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    if precision == "int24":
        q_unity = -23
    else:
        q_unity = -15

    x = writer.add_input(32, q_unity, precision=precision)
    y = writer.add_input(32, q_unity, precision=precision)

    with writer.with_precision(precision) as pwriter:
        recip0, components = pwriter.divide(
            num=x, den=y, quanta=-15, eps=1e-3, pos_only=False, return_components=True
        )
        recip1 = pwriter.divide_by_components(num=x, components=components, quanta=-15)

    writer.add_outputs([recip0, recip1])

    x = np.random.randint(-(2 ** (-q_unity)), 2 ** (-q_unity) - 1, (10, 32))
    y = np.random.randint(-(2 ** (-q_unity)), 2 ** (-q_unity) - 1, (10, 32))
    z0, z1 = graph.run(x, y)

    assert np.array_equal(z0, z1)


@pytest.mark.parametrize("precision", ["int16", "int24"])
def test_clampdivide(precision):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph)

    if precision == "int24":
        q_unity = -23
    else:
        q_unity = -15

    x = writer.add_input(32, q_unity, precision=precision)
    y = writer.add_input(32, q_unity, precision=precision)

    with writer.with_precision(precision) as pwriter:
        y = writer.maximum(y, 1e-3)
        recip = pwriter.divide(num=x, den=y, quanta=-15, eps=0, pos_only=False)

    writer.add_outputs([recip])


if __name__ == "__main__":
    test_divide_i16(1e-2, True, -7, plot=True)
    test_divide_i24(5e-6, True, -13, plot=True)
    test_clampdivide("int16")
