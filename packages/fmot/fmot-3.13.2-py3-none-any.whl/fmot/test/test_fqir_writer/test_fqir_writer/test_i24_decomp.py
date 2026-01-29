from fmot.fqir.passes.virtualize_high_precisions import virtualize_high_precisions
from fmot.fqir.writer import FQIRWriter, new_fqir_graph
from fmot.fqir.writer.utils import get_creation_node, find_fqir_tensor_with_name
import numpy as np
from fmot.fqir import GraphProto, TensorProto
import pytest
import matplotlib.pyplot as plt
from copy import deepcopy
from collections import defaultdict
import math

REL_TOL = 4e-2
ETOL_LO = 0
ETOL_HI = 0


@pytest.mark.parametrize("in_channels", [1, 32, 64])
@pytest.mark.parametrize("out_channels", [1, 32, 64])
def test_i24_matmul(in_channels: int, out_channels: int, plot: bool = False):
    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph, "int24")

    x = writer.add_input(channels=in_channels, quanta=-23)
    weight = writer.add_parameter(np.random.randn(out_channels, in_channels))
    y = writer.matmul(
        weight, x, quanta=weight.quanta - 15 + int(math.ceil(math.log2(in_channels)))
    )
    y_lo, y_hi = writer._precision_split(y, [13, 12], ["int16", "int16"])
    writer.add_outputs([y_lo, y_hi])

    print(graph)

    x_vals = np.random.randint(low=-(2**15), high=2**15 - 1, size=[10, in_channels])
    y_vals_lo, y_vals_hi = graph.run(x_vals, dequant=False)
    y_vals = y_vals_lo + 2**12 * y_vals_hi

    virtualize_high_precisions(graph)

    print(graph)

    y_vals_virt_lo, y_vals_virt_hi = graph.run(x_vals, dequant=False)
    y_vals_virt = y_vals_virt_lo + 2**12 * y_vals_virt_hi

    if plot:
        plt.hist(y_vals.flatten(), bins=100)
        plt.show()

        plt.plot(y_vals.flatten(), y_vals_virt.flatten(), ".")
        plt.show()


@pytest.mark.parametrize("round", [True, False])
@pytest.mark.parametrize(
    ["op", "const"],
    [
        ["add_float", 12.32],
        ["add_float", 0],
        ["multiply_float", 1],
        ["multiply_float", 3.1415926],
        ["split", 200],
        ["gt0", None],
        ["eq0", None],
        ["pow", 0.5],
        ["pow", -0.5],
        ["sub", None],
        ["add", None],
    ],
)
def test_i24_decomp_unary_op(
    op: str,
    const: float,
    round: bool,
    dual_input: bool = False,
    plot=False,
    compare_state=False,
):
    pos_only = False

    if dual_input:
        N = 10000
    else:
        N = 2**16

    graph = new_fqir_graph()
    writer = FQIRWriter.from_fqir(graph, "int24")
    if dual_input:
        x0 = writer.add_input(channels=N, quanta=-15, name="x0", precision="fqint16")
        x1 = writer.add_input(channels=N, quanta=-15, name="x1", precision="fqint16")
        x = writer.multiply(x0, x1, round=round)
        print(f"multiply-in (dual): {x0.quanta=} {x1.quanta=} {x.quanta=}")
    else:
        x0 = writer.add_input(channels=N, quanta=-15, name="x0", precision="fqint16")
        x = writer.multiply(x0, 0.972, round=round)
        print(f"multiply-in (single): {x0.quanta=} {x.quanta=}")

    if op == "add_float":
        y = writer._add_float(x, const, round=round)
    elif op == "multiply_float":
        y = writer.multiply(x, const, round=round)
    elif op == "square":
        y = writer.multiply(x, x, round=round)
    elif op == "split":
        y, _ = writer.split(x, [const, N - const])
    elif op == "gt0":
        y = writer.gt0(x)
    elif op == "eq0":
        y = writer.eq(x, 0)
    elif op == "pow":
        y = writer.pow(x, const)
        pos_only = True
    elif op == "add":
        x1 = writer.multiply(x, 0.73)
        y = writer.add(x, x1)
    elif op == "sub":
        x1 = writer.multiply(x, 0.73)
        y = writer.sub(x, x1)
    else:
        raise NotImplementedError(f"{op=} not recognized")

    print(f"{op}: {y.quanta=}")

    # precision-split for output
    ylo, yhi = writer._precision_split(y, [12, 13], ["fqint16", "fqint16"])
    print(f"precision_split: {ylo.quanta=} {yhi.quanta=}")

    writer.add_outputs([ylo, yhi])

    if dual_input:
        inputs = [np.random.randint(0, 2**15 - 1, size=(1, N)) for _ in range(2)]
        ivals = inputs[0] * inputs[1]
    else:
        inputs = [np.arange(-(2**15), 2**15, 1).reshape(1, -1)]
        if pos_only:
            inputs[0] = np.abs(inputs[0])
        ivals = inputs[0]

    (ylo_exp, yhi_exp), state_exp = graph.run(*inputs, dequant=False, return_objs=True)

    graph_orig = deepcopy(graph)

    print(graph)

    print("VIRTUALIZING...")
    virtualize_high_precisions(graph)

    print(graph)

    (ylo_dc, yhi_dc), state_dc = graph.run(*inputs, dequant=False, return_objs=True)

    y_vals_exp = ylo_exp[0] + 2**12 * yhi_exp[0]
    y_vals_dc = ylo_dc[0] + 2**12 * yhi_dc[0]

    if plot:
        if ylo_exp.shape == ivals.shape:
            fig, ax = plt.subplots(1, 2, figsize=(10, 4))
            ax[0].plot(ivals[0], y_vals_exp, ".", label="unvirtualized")
            ax[0].plot(ivals[0], y_vals_dc, ".", label="virtualized")
            ax[0].set_xlabel("inputs")
            ax[0].set_ylabel("outputs")
            ax[0].legend()
            ax[0].grid()
            ax = ax[1]
        else:
            fig, ax = plt.subplots()
        ax.plot(ylo_exp[0] + y_vals_exp, y_vals_dc, ".")
        ax.set_xlabel("unvirtualized")
        ax.set_ylabel("virtualized")
        plt.suptitle(f"Unary op: {op}, {dual_input=}")
        ax.grid()
        plt.show()

        if not dual_input:
            plt.plot(
                ivals[0], np.abs(y_vals_exp - y_vals_dc) / (np.abs(y_vals_exp) + 1), "."
            )
            plt.plot(ivals[0], np.abs(y_vals_exp), ".")
            plt.xscale("log")
            plt.yscale("log")
            plt.show()
            print(np.sort(np.abs(y_vals_exp - y_vals_dc) / (np.abs(y_vals_exp) + 1)))

    if compare_state:
        diffs = defaultdict(int)
        state_dc_reconst = {}
        for key in state_exp.keys():
            x_exp = state_exp[key]
            if key in state_dc:
                x_dc = state_dc[key]
            elif f"{key}_lo" in state_dc and f"{key}_hi" in state_dc:
                x_dc = state_dc[f"{key}_lo"] + 2**12 * state_dc[f"{key}_hi"]
            else:
                continue

            diffs[key] = np.sqrt(np.mean((x_exp - x_dc) ** 2))
            state_dc_reconst[key] = x_dc

        first_bad_node = None
        for node in graph_orig.subgraphs["ARITH"].nodes:
            valid_in = all(diffs[x.name] == 0 for x in node.inputs.values())
            valid_out = all(diffs[x.name] == 0 for x in node.outputs)

            if valid_in and valid_out:
                symbol = "✅  "
            elif valid_in:
                symbol = "❌❌"
                # THIS IS THE BAD NODE
                if first_bad_node is None:
                    first_bad_node = node

            else:
                symbol = "❌  "

            print(f"{symbol}  {node}")

        # bad node inspection
        if first_bad_node is not None:
            node = first_bad_node

            print(f"INVESTIGATING THE FIRST BAD NODE... {node}")
            print(f"{node.constants}")
            print(f"{node.name=}")

            names = [x.name for x in node.inputs.values()]
            oname = node.outputs[0].name

            if oname in state_dc:
                x_dc = find_fqir_tensor_with_name(graph.subgraphs["ARITH"], oname)
            else:
                x_dc = find_fqir_tensor_with_name(
                    graph.subgraphs["ARITH"], oname + "_lo"
                )

            node_virt = get_creation_node(graph.subgraphs["ARITH"], x_dc)
            print(f"{node_virt=}")
            print(f"{node_virt.constants=}")
            print(f"{node_virt.name=}")

            if plot:
                input1, input2 = [state_exp[name] for name in names]
                fig, ax = plt.subplots(2, sharex=True)
                ax[0].plot(input1.flatten(), input2.flatten(), ".")
                ax[0].set_xlabel(names[0])
                ax[0].set_ylabel(names[1])
                ax[0].grid()

                output_name = node.outputs[0].name
                output_exp = state_exp[output_name]
                output_dc = state_dc_reconst[output_name]

                ax[1].plot(
                    input1.flatten(), output_exp.flatten(), ".", label="expected"
                )
                ax[1].plot(
                    input1.flatten(), output_dc.flatten(), ".", label="virtualized"
                )
                ax[1].legend()
                ax[1].set_xlabel(names[0])
                ax[1].set_ylabel(output_name)
                ax[1].grid()
                plt.show()

    if ivals[0].shape == y_vals_exp.shape:
        diff = np.abs(y_vals_exp - y_vals_dc)
        rdiff = np.abs(y_vals_exp - y_vals_dc) / (np.abs(y_vals_exp) + 1)
        rdiff = rdiff[np.where(ivals[0] != 0)[0]]

        if np.any(rdiff > REL_TOL):
            raise ValueError(f"rdiff has max {np.max(rdiff)} > {REL_TOL}")

    else:
        diff_lo = ylo_exp - ylo_dc
        assert (
            np.max(np.abs(diff_lo)) <= ETOL_LO
        ), f"diff was {np.max(np.abs(diff_lo))=}"
        diff_hi = yhi_exp - yhi_dc
        assert (
            np.max(np.abs(diff_hi)) <= ETOL_HI
        ), f"diff was {np.max(np.abs(diff_hi))=}"


# if __name__ == "__main__":
#     import logging

#     # logging.basicConfig(level=logging.DEBUG)

#     ROUND = True

#     # test_i24_decomp_unary_op("square", 0.3, ROUND, dual_input=True, plot=True)
#     # test_i24_decomp_unary_op("eq0", None, ROUND, dual_input=False, plot=True)
#     # test_i24_decomp_unary_op("add_float", 0.3, ROUND, dual_input=False, plot=True)
#     # test_i24_decomp_unary_op("multiply_float", 0.3, ROUND, dual_input=False, plot=True)
#     # test_i24_decomp_unary_op("split", 100, ROUND, dual_input=False, plot=False)
#     # test_i24_decomp_unary_op(
#     #     "pow",
#     #     -0.5,
#     #     ROUND,
#     #     dual_input=False,
#     #     plot=True,
#     #     compare_state=False,
#     # )

#     test_i24_matmul(32, 64, True)
