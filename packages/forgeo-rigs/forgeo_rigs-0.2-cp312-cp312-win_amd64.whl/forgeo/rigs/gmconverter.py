from copy import copy
from dataclasses import dataclass

import numpy as np

import rigs.utils
from forgeo.gmlib.common import OrientedEvaluation
from forgeo.gmlib.GeologicalModel3D import pypotential
from forgeo.gmlib.topography_reader import ImplicitHorizontalPlane
from rigs import BSPTree, Discontinuities, Side

# FIXME: only formations are supposed to be discontinuous


def _topological_sort(limits):
    # topological sorting of faults according to "stops on" relation
    left = np.ones((len(limits),), dtype=bool)
    order = []
    while np.any(left):
        removed = []
        for k in np.nonzero(left)[0]:
            if not any(left[limits[k]]):
                order.append(k)
                removed.append(k)
        left[np.array(removed)] = False
    order = np.array(order)
    rank = np.argsort(order)
    assert all(all(rank[k] > rank[li] for li in limits[k]) for k in range(len(limits)))
    return rank


def _select_parent(limits, rank=None):
    if rank is None:
        rank = _topological_sort(limits)
    parent = {}
    for k, l in enumerate(limits):
        if l.size != 0:
            # we chose the limit that maximize the ranking (lowest position in tree)
            parent[k] = l[np.argmax(rank[l])]
    return parent


def convert(
    model,
    as_functor=None,
    with_topography=True,
    faults_only=False,
    verbose=False,
    keep_interfaces=None,
    skip_interfaces=None,
):
    if as_functor is None:
        as_functor = rigs.utils.as_functor

    # FIXME: should be more robust to count signs on data points
    def find_side(field, limit):
        if limit(field.data_centroid()) <= 0:
            return Side.first
        return Side.second

    def boundary_name(s):
        return s + "-boundary"

    surface_id = {}
    surface_names = []
    surface_field = []
    functors = []
    colors = []

    def register(name, field, value=None, color=None):
        sid = len(functors)
        assert len(surface_field) == sid
        assert len(colors) == sid
        surface_id[name] = sid
        surface_names.append(name)
        functors.append(as_functor(field, value))
        surface_field.append((field, value))
        colors.append(color)
        return sid

    faults = model.faults
    data = model.faults_data
    is_finite = model.is_finite_fault
    ellipsoid = model.fault_ellipsoids

    fault_names = list(faults.keys())
    fault_id = {name: k for k, name in enumerate(fault_names)}
    limits = [
        np.unique(np.array([fault_id[name] for name in data[fault].stops_on], int))
        for fault in faults
    ]
    rank = _topological_sort(limits)
    stops_on = _select_parent(limits, rank)

    boundaries = {}
    for fk in np.argsort(rank):
        name = fault_names[fk]
        sid = register(name, faults[name], color=data[name].color)
        if is_finite(name):
            boundaries[sid] = register(boundary_name(name), ellipsoid[name])

    tree = BSPTree()
    tree.minimum_number_of_nodes(len(functors))
    assert tree.number_of_nodes() == len(functors)
    for sid, bid in boundaries.items():
        tree.set_boundary(sid, bid)
    for fk, lk in stops_on.items():
        fid = surface_id[fault_names[fk]]  # fault
        lid = surface_id[fault_names[lk]]  # limit
        side = find_side(surface_field[fid][0], surface_field[lid][0])
        tree.add_child(lid, side, fid)

    number_of_fault_elements = tree.number_of_nodes()

    def is_fault(i):
        return i < number_of_fault_elements

    # the geology
    topoid = None
    if with_topography:
        if (
            isinstance(model.topography, ImplicitHorizontalPlane)
            and model.topography.z == model.getbox().zmax
        ):
            pass
        else:
            topoid = register("topography", model.topography)

    # set topography above faults
    if topoid is not None:
        roots = tree.roots()
        for sid in roots:
            if sid != topoid:
                tree.add_child(topoid, Side.first, sid)
    assert tree.consistent_trees(verbose=verbose)

    skipped_interfaces = set()

    if not faults_only:
        # FIXME: what if a base serie with erode relation at the bottom has reverse values ?
        pile = model.pile
        units = model.collect_pile_information()
        interfaces = []
        all_series_names = [s.name for s in model.pile.all_series]
        for serie, info in model.series_info.items():
            k = all_series_names.index(serie)
            interfaces.extend(
                [(name, info.field, value, k) for name, value in info.interfaces]
            )
        assert len(units) == len(interfaces) + 1
        if pile.reference == "base":
            del units[0]

        assert keep_interfaces is None or skip_interfaces is None
        ravel_interfaces = not (keep_interfaces is None and skip_interfaces is None)

        if not ravel_interfaces:
            current_serie = None
            relations = []
            for unit, interface in zip(units, interfaces, strict=False):
                name, field, value, serie = interface
                if current_serie != serie:  # start a new serie
                    values = []
                current_serie = serie
                assert f"{pile.reference}-{unit.name}" == name
                if np.isnan(value):
                    continue
                si = register(name, field, value, color=unit.color)
                if unit.relation == "erode" or len(values) == 0:
                    relations.append((si, unit.relation, None))
                else:
                    assert unit.relation == "onlap"  # inside serie
                    assert value != values[-1]
                    if value < values[-1]:
                        assert all(value < vk for vk in values)
                        relations.append((si, model.relations[k], Side.first))
                    else:
                        assert all(value > vk for vk in values)
                        relations.append((si, model.relations[k], Side.second))
                values.append(value)

            tree.minimum_number_of_nodes(len(functors))
            assert tree.number_of_nodes() == len(functors)

            highest_node = topoid
            onlaps = []
            for info in reversed(relations):
                si, relation, side = info
                if relation == "onlap":
                    onlaps.append((si, side))
                elif relation == "erode":
                    if highest_node is not None:
                        tree.add_child(highest_node, Side.first, si)
                    highest_node = si
                    if onlaps:
                        node = highest_node
                        assert node is not None
                        for si, side in onlaps[::-1]:
                            tree.add_child(node, side or Side.second, si)
                            node = si
                        onlaps.clear()
                else:
                    msg = "unknown relation"
                    raise AssertionError(msg)
            if len(onlaps) > 0:
                parent = highest_node
                si, _ = onlaps.pop()
                if parent is not None:  # parent is topography or erode
                    tree.add_child(parent, Side.first, si)
                parent = si
                for si, _ in onlaps[::-1]:
                    tree.add_child(parent, Side.second, si)
                    parent = si

        else:  # ravel interfaces
            if skip_interfaces:
                for k in skip_interfaces:
                    if k < 0 or k >= len(interfaces):
                        skipped_interfaces.add(interfaces[k][0])
            else:
                for k in keep_interfaces:
                    if k < 0 or k >= len(interfaces):
                        pass
                for k, interface in enumerate(interfaces):
                    name, *_ = interface
                    if k not in keep_interfaces:
                        skipped_interfaces.add(name)

            interfaces_ids = []
            for k, (unit, interface) in enumerate(zip(units, interfaces, strict=False)):
                name, field, value, serie = interface
                assert f"{pile.reference}-{unit.name}" == name
                if np.isnan(value):
                    continue
                if name not in skipped_interfaces:
                    interfaces_ids.append(
                        register(name, field, value, color=unit.color)
                    )
            tree.minimum_number_of_nodes(len(functors))
            if topoid is not None:
                for si in interfaces_ids:
                    tree.add_child(topoid, Side.first, si)

    assert tree.number_of_nodes() == len(functors)

    # FIXME: check side consitency of fault tree
    @dataclass
    class DiscInfo:
        along: dict
        drifts: list

    discinfo = {}
    discontinuities = Discontinuities(tree.number_of_nodes())
    if not faults_only:  # faults are supposed to be continuous
        for serie, info in model.series_info.items():
            active_faults = info.active_faults
            if active_faults:
                di = DiscInfo(
                    {
                        surface_id[fault]: drift
                        for fault, drift in active_faults.items()
                    },
                    info.drifts,
                )
                for name, value in info.interfaces:
                    if np.isnan(value) or name in skipped_interfaces:
                        continue  # field has been discarded
                    sid = surface_id[name]
                    for along in di.along:
                        discontinuities.add(sid, along)
                    discinfo[sid] = di

    nb_unextended_functors = len(functors)

    def get_fault(sid):
        field, value = surface_field[sid]
        assert isinstance(field, pypotential.Fault)
        assert value is None
        return field

    def get_ellipsoid(sid):
        field, value = surface_field[sid]
        assert isinstance(field, pypotential.Ellipsoid)
        assert value is None
        return field

    def scheme_enum(s):
        return {
            Side.first: OrientedEvaluation.always_negative,
            Side.second: OrientedEvaluation.always_positive,
        }[s]

    def extension(i, sides):
        def other_side(s):
            if s == Side.first:
                return Side.second
            assert s == Side.second
            return Side.first

        assert i < nb_unextended_functors
        assert len(sides) > 0
        di = discinfo[i]
        assert len(sides) <= len(di.along)
        ext_drifts = copy(di.drifts)
        # present_discontinuities = tuple(s[0] for s in sides)
        for j, s in sides:
            assert ext_drifts[di.along[j]].is_fault_drift
            ext_drifts[di.along[j]] = ext_drifts[di.along[j]].change_evaluation(
                scheme_enum(s)
            )
            for k in tree.descendance(j, other_side(s)):
                if k in di.along:
                    ext_drifts[di.along[k]] = ext_drifts[di.along[k]].change_evaluation(
                        OrientedEvaluation.always_outside
                    )
            assert s in (Side.first, Side.second)
            for k in tree.descendance(j, s):
                if k in di.along:
                    unbounded_fault = get_fault(k).remove_boundary(get_fault(j))
                    scheme = ext_drifts[di.along[k]].evaluation().scheme
                    eid = boundaries.get(k)
                    if eid is not None:  # finite fault
                        new_drift = pypotential.make_finite_drift(
                            unbounded_fault, get_ellipsoid(eid), scheme
                        )
                    else:
                        new_drift = pypotential.make_drift(unbounded_fault, scheme)
                    ext_drifts[di.along[k]] = new_drift

        field, value = surface_field[i]
        f = as_functor(pypotential.alternate_drifts(field, ext_drifts), value)
        register(f, value)  # keeps reference to prevent gc
        return f

    if verbose:
        for sid, name in surface_id.items():
            pass
        tree.dump()
        discontinuities.dump()

    assert tree.consistent_trees(verbose=verbose)
    assert discontinuities.consistent_with(tree, verbose=verbose)
    assert len(faults) == 0 or all(
        tree.evaluation_order(
            surface_id[fault_names[l]], surface_id[fault_names[f]], strict=False
        )
        for f, lims in enumerate(limits)
        for l in lims
    )

    assert len(functors) == len(colors)

    return {
        "names": surface_names,
        "functors": functors,
        "topography": topoid,
        "is_fault": is_fault,
        "tree": tree,
        "discontinuities": discontinuities,
        "extension_factory": extension,
        "colors": colors,
    }
