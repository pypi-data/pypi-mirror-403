import numpy as np
from fmot.fqir.writer import FQIRWriter, new_fqir_graph
from fmot.fqir.writer.graph_splitting import (
    get_fqir_between,
    MissingFQIRDependencyError,
)
import pytest


def test_simplecase():
    """very simple program without assign nodes:
    x -> A -> y -> B -> z

    subgraph between [x] and [y] should yield A
    subgraph between [y] and [z] should yield B
    """
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15, name="x")
    # A
    i0 = writer.add(x, 3)
    i1 = writer.add(x, 2)
    i3 = writer.multiply(i0, i1)
    y = writer.sign(i3)

    # B
    i4 = writer.multiply(y, 0.2)
    z = writer.add(i4, y)
    writer.add_outputs([y, z])

    subA = get_fqir_between(fqir, [x], [y])
    subB = get_fqir_between(fqir, [y], [z])
    subAB = get_fqir_between(fqir, [x], [z])

    x_vals = np.random.randint(low=-(2**15), high=2**15 - 1, size=(10, 32))
    y_vals, z_vals = fqir.run(x_vals)

    subA_yvals = subA.run(x_vals)
    assert np.array_equal(y_vals, subA_yvals)

    subB_zvals = subB.run(y_vals)
    assert np.array_equal(z_vals, subB_zvals)

    subAB_zvals = subAB.run(x_vals)
    assert np.array_equal(z_vals, subAB_zvals)


def test_buff_inside():
    """this program includes a buffer, but this buffer is fully maintained within the subgraph between
    x and y

    x -> A -> y -> B -> z
        ( )
       buff

    subgraph between [x] and [y] should yield A and buffer updates
    subgraph between [y] and [z] should yield B
    """
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15, name="x")
    buff = writer.add_zeros_buffer(32, -15)

    i0 = writer.add(x, buff)
    writer.assign(buff, x)
    y = writer.multiply(x, i0)
    z = writer.add(y, 3)
    writer.add_outputs([y, z])

    subA = get_fqir_between(fqir, [x], [y])
    subB = get_fqir_between(fqir, [y], [z])
    subAB = get_fqir_between(fqir, [x], [z])

    x_vals = np.random.randint(low=-(2**15), high=2**15 - 1, size=(10, 32))
    y_vals, z_vals = fqir.run(x_vals)

    subA_yvals = subA.run(x_vals)
    assert np.array_equal(y_vals, subA_yvals)

    subB_zvals = subB.run(y_vals)
    assert np.array_equal(z_vals, subB_zvals)

    subAB_zvals = subAB.run(x_vals)
    assert np.array_equal(z_vals, subAB_zvals)

    print("FQIR_ORIG:")
    print(fqir)
    print("subA:")
    print(subA)
    print("subB:")
    print(subB)


def test_buffer_outside_post():
    """More complex case with assign buffers

    x -> A -> y -> B -> z
        (       -> C
      buff <- - - -)

    buffer is used in A, but updated in C. Therefore, we need to include C in the subgraph (x) -> (y)

    subgraph between [x] and [y] should yield A and C (C is needed for buffer updates)
    subgraph between [y] and [z] should yield B (C is not a part of these updates)
    """
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15, name="x")
    # A: (x, buff) -> (y)
    buff = writer.add_zeros_buffer(32, -15)
    y = writer.add(x, buff)

    # B: (y) -> (z)
    z = writer.multiply(y, 0.3)

    # C: (y, buff) -> (buff')
    new_buff = writer.multiply(y, buff, quanta=buff.quanta)
    writer.assign(buff, new_buff)

    writer.add_outputs([y, z])

    subA = get_fqir_between(fqir, [x], [y])
    subB = get_fqir_between(fqir, [y], [z])
    subAB = get_fqir_between(fqir, [x], [z])

    x_vals = np.random.randint(low=-(2**15), high=2**15 - 1, size=(10, 32))
    y_vals, z_vals = fqir.run(x_vals)

    subA_yvals = subA.run(x_vals)
    assert np.array_equal(y_vals, subA_yvals)

    subB_zvals = subB.run(y_vals)
    assert np.array_equal(z_vals, subB_zvals)

    subAB_zvals = subAB.run(x_vals)
    assert np.array_equal(z_vals, subAB_zvals)

    print("FQIR_ORIG:")
    print(fqir)
    print("subA:")
    print(subA)
    print("subB:")
    print(subB)


def test_raises_missing_dependency_exception():
    """If there is a dependency not satisfied, we should raise a MissingFQIRDependencyError"""
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15, name="x")
    i0 = writer.add(x, 1.1)
    y = writer.multiply(x, i0)
    i1 = writer.add(y, 1.1)
    z = writer.multiply(i1, i0)
    writer.add_outputs([z])

    with pytest.raises(MissingFQIRDependencyError):
        # should raise an error because z depends on i0, which is not inside of the
        # subgraph between y and z
        get_fqir_between(fqir, [y], [z])


if __name__ == "__main__":
    test_buffer_outside_post()
