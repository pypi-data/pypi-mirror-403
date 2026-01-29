from fmot.fqir.writer.graph_splitting import parse_fqir_to_digraph
from fmot.fqir.writer import FQIRWriter, new_fqir_graph
import networkx as nx


def test_parallel_chains():
    """Checks that two independent parallel chains are recognized
    as independent"""
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x0 = writer.add_input(32, -15)
    x1 = writer.add_input(32, -15)
    y0 = writer.add(x0, 3)
    y1 = writer.add(x1, -2)
    writer.add_outputs([y0, y1])

    G = parse_fqir_to_digraph(fqir)

    assert nx.has_path(G, x0, y0)
    assert nx.has_path(G, x1, y1)
    assert not nx.has_path(G, x0, y1)
    assert not nx.has_path(G, x1, y0)


def test_dependence_via_assign_dag():
    """Checks that a node that uses an updated assign value is
    seen as dependent on that update -- only if it comes afterward"""

    # y depends on buff *after* it has been updated via x
    # so there should be a path from x to y
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15)
    buff = writer.add_zeros_buffer(32, -15)
    writer.assign(buff, x)
    y = writer.add(buff, 3)
    writer.add_outputs([y])

    G = parse_fqir_to_digraph(fqir, dag_mode=True)

    assert nx.has_path(G, x, y)

    # y depends on buff *before* it has been updated via x
    # so there shouldn't be a path from x to y
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15)
    buff = writer.add_zeros_buffer(32, -15)
    y = writer.add(buff, 3)
    writer.assign(buff, x)
    writer.add_outputs([y])

    G = parse_fqir_to_digraph(fqir, dag_mode=True)

    assert not nx.has_path(G, x, y)


def test_non_dag_assign_loop():
    """
    - y is computed based on the buffer value
    - the buffer is later updated to z
    - we should see a dependency from z to y via a loop
    """
    fqir = new_fqir_graph()
    writer = FQIRWriter.from_fqir(fqir)

    x = writer.add_input(32, -15)
    buff = writer.add_zeros_buffer(32, -15)
    y = writer.add(buff, 3)

    z = writer.add(writer.multiply(buff, 0.5), writer.multiply(x, 0.5), quanta=-15)
    writer.assign(buff, z)

    writer.add_outputs([y])

    # check there's a path from z to y only in non_dag mode
    G = parse_fqir_to_digraph(fqir, dag_mode=False)
    assert nx.has_path(G, z, y)

    G = parse_fqir_to_digraph(fqir, dag_mode=True)
    assert not nx.has_path(G, z, y)
