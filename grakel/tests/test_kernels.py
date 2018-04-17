"""Tests for the kernel sub-module."""
import numpy as np

from time import time

from numpy.testing import assert_array_less

from sklearn.model_selection import train_test_split

from grakel.datasets import fetch_dataset
from grakel.datasets import get_dataset_info

from grakel.kernels import GraphletSampling
from grakel.kernels import RandomWalk
from grakel.kernels import RandomWalkLabeled
from grakel.kernels import ShortestPath
from grakel.kernels import ShortestPathAttr
from grakel.kernels import WeisfeilerLehman
from grakel.kernels import NeighborhoodHash
from grakel.kernels import PyramidMatch
from grakel.kernels import SubgraphMatching
from grakel.kernels import NeighborhoodSubgraphPairwiseDistance
from grakel.kernels import LovaszTheta
from grakel.kernels import SvmTheta
from grakel.kernels import OddSth
from grakel.kernels import Propagation
from grakel.kernels import PropagationAttr
from grakel.kernels import HadamardCode
from grakel.kernels import MultiscaleLaplacian
from grakel.kernels import MultiscaleLaplacianFast
from grakel.kernels import VertexHistogram
from grakel.kernels import EdgeHistogram
from grakel.kernels import GraphHopper
from grakel.kernels import CoreFramework

global verbose, main, development

default_eigvalue_precision = float("-1e-5")

if __name__ == '__main__':
    import argparse
    # Create an argument parser for the installer of pynauty
    parser = argparse.ArgumentParser(description='A test file for all kernels')

    parser.add_argument(
        '--verbose',
        help='print kernels with their outputs on stdout',
        action="store_true")
    parser.add_argument(
        '--problematic',
        help='allow execution of problematic test cases in development',
        action="store_true")
    parser.add_argument(
        '--slow',
        help='allow execution of slow test cases in development',
        action="store_true")
    parser.add_argument(
        '--ignore_warnings',
        help='ignore warnings produced by kernel executions',
        action="store_true")

    parser.add_argument(
        '--time',
        help='time the kernel computation (has effect only on verbose)',
        action="store_true")
    parser.add_argument(
        '--dataset',
        help='choose the dataset for tests requiring node/edge labels',
        type=str,
        default="MUTAG"
    )

    parser.add_argument(
        '--dataset_attr',
        help='choose the dataset for tests requiring node attributes',
        type=str,
        default="Cuneiform"
    )

    parser.add_argument('--normalize', help='normalize the kernel output',
                        action="store_true")

    meg = parser.add_mutually_exclusive_group()
    meg.add_argument(
        '--develop',
        help='execute only tests connected with current development',
        action="store_true")
    meg.add_argument(
        '--all',
        help='execute all tests',
        action="store_true")
    meg.add_argument(
        '--main',
        help='execute the main tests [default]',
        action="store_true")

    args = parser.parse_args()

    verbose = bool(args.verbose)
    if args.all:
        main, develop = True, True
    elif args.develop:
        main, develop = False, True
    else:
        main, develop = True, False
    problematic = bool(args.problematic)
    slow = bool(args.slow)

    if bool(args.ignore_warnings):
        import warnings
        warnings.filterwarnings('ignore', category=UserWarning)

    normalize = bool(args.normalize)
    time_kernel = bool(args.time)
    dataset_name = args.dataset
    dataset_attr_name = args.dataset_attr

else:
    import warnings
    warnings.filterwarnings('ignore', category=UserWarning)
    main, develop, problematic, slow = True, False, False, False
    normalize, verbose, time_kernel = False, False, False
    dataset_name = "MUTAG"
    dataset_attr_name = "Cuneiform"

# consistency check for the dataset
dinfo = get_dataset_info(dataset_name)
if dinfo is None:
    raise TypeError('dataset not found')
elif not dinfo["nl"] and not dinfo["el"]:
    raise TypeError('dataset must have either node and edge labels')

# consistency check for the attribute dataset
dinfo_attr = get_dataset_info(dataset_attr_name)
if dinfo is None:
    raise TypeError('dataset for attributes not found')
elif not dinfo_attr["nl"] and not dinfo_attr["el"]:
    raise TypeError('dataset must have node attributes')


# The baseline dataset for node, edge_labels
global dataset, dataset_tr, dataset_te
dataset = fetch_dataset(dataset_name, with_classes=False, verbose=verbose).data
dataset_tr, dataset_te = train_test_split(dataset,
                                          test_size=0.2,
                                          random_state=42)

# The baseline dataset for node/edge-attributes
global dataset_attr, dataset_attr_tr, dataset_attr_te
dataset_attr = fetch_dataset(dataset_attr_name, with_classes=False,
                             prefer_attr_nodes=True,
                             prefer_attr_edges=True,
                             verbose=verbose).data
dataset_attr_tr, dataset_attr_te = train_test_split(dataset_attr,
                                                    test_size=0.2,
                                                    random_state=42)


def test_random_walk():
    """Test the simple random walk kernel."""
    rw_kernel = RandomWalk(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Random Walk", rw_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(rw_kernel, dataset)

    rw_kernel_lab = RandomWalkLabeled(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Random Walk Labelled", rw_kernel_lab, dataset_tr, dataset_te)
    else:
        positive_eig(rw_kernel_lab, dataset)


def test_shortest_path():
    """Test Shortest Path kernel."""
    sp_kernel = ShortestPath(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Shortest Path", sp_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(sp_kernel, dataset)

    sp_kernel_attr = ShortestPathAttr(verbose=verbose, normalize=normalize)
    if verbose and slow:
        print_kernel("Shortest Path Attr", sp_kernel_attr, dataset_attr_tr, dataset_attr_te)
    elif not verbose and slow:
        positive_eig(sp_kernel_attr, dataset_attr)


def test_graphlet_sampling():
    """Test the Graphlet Sampling Kernel."""
    try:
        gs_kernel = GraphletSampling(verbose=verbose, normalize=normalize, sampling=dict(n_samples=150))
    except ImportError:
        return
    if verbose:
        print_kernel("Graphlet Sampling", gs_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(gs_kernel, dataset)


def test_weisfeiler_lehman():
    """Test the Weisfeiler Lehman kernel."""
    wl_st_kernel = WeisfeilerLehman(verbose=verbose, normalize=normalize,
                                    base_kernel=VertexHistogram)
    if verbose:
        print_kernel("WL/Subtree", wl_st_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(wl_st_kernel, dataset)


def test_pyramid_match():
    """Test the Pyramid Match kernel."""
    pm_kernel = PyramidMatch(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Pyramid Match", pm_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(pm_kernel, dataset)


def test_neighborhood_hash():
    """Test the Neighborhood Hash kernel."""
    nh_kernel = NeighborhoodHash(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Neighborhood Hash", nh_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(nh_kernel, dataset)


def test_subgraph_matching():
    """Test the subgraph_matching kernel."""
    sm_kernel = SubgraphMatching(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Subgraph Matching", sm_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(sm_kernel, dataset)


def test_neighborhood_subgraph_pairwise_distance():
    """Test the neighborhood subgraph pairwise distance kernel."""
    nspd_kernel = NeighborhoodSubgraphPairwiseDistance(
        verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("NSPD", nspd_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(nspd_kernel, dataset)


def test_lovasz_theta():
    """Test the Lovasz-theta distance kernel."""
    try:
        lt_kernel = LovaszTheta(verbose=verbose, normalize=normalize)
    except ImportError:
        return
    if verbose:
        print_kernel("Lovasz-theta", lt_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(lt_kernel, dataset)


def test_svm_theta():
    """Test the SVM-theta distance kernel."""
    svm_kernel = SvmTheta(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("SVM-theta", svm_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(svm_kernel, dataset)


def test_odd_sth():
    """Test the ODD-STh kernel."""
    odd_sth_kernel = OddSth(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("ODD-STh", odd_sth_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(odd_sth_kernel, dataset)


def test_propagation():
    """Test the Propagation kernel."""
    propagation_kernel = Propagation(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Propagation", propagation_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(propagation_kernel, dataset)

    propagation_kernel_attr = PropagationAttr(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Propagation", propagation_kernel_attr, dataset_attr_tr, dataset_attr_te)
    else:
        positive_eig(propagation_kernel_attr, dataset_attr)


def test_hadamard_code():
    """Test the Hadamard Code kernel."""
    hadamard_code_kernel = HadamardCode(verbose=verbose, normalize=normalize,
                                        base_kernel=VertexHistogram)
    if verbose:
        print_kernel("Hadamard-Code/VH [Simple]",
                     hadamard_code_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(hadamard_code_kernel, dataset)


def test_multiscale_laplacian():
    """Test the Multiscale Laplacian kernel."""
    # Intialise kernel
    ml_kernel = MultiscaleLaplacian(verbose=verbose, normalize=normalize)
    if verbose and slow:
        print_kernel("Multiscale Laplacian", ml_kernel,
                     dataset_attr_tr, dataset_attr_te)
    elif not verbose and slow:
        positive_eig(ml_kernel, dataset_attr)


def test_multiscale_laplacian_fast():
    """Test the Fast Multiscale Laplacian kernel."""
    # Initialise kernel
    mlf_kernel = MultiscaleLaplacianFast(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Multiscale Laplacian Fast", mlf_kernel,
                     dataset_attr_tr, dataset_attr_te)
    else:
        positive_eig(mlf_kernel, dataset_attr)


def test_vertex_histogram():
    """Test the Vertex Histogram Kernel."""
    vh_kernel = VertexHistogram(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Vertex Histogram", vh_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(vh_kernel, dataset)


def test_edge_histogram():
    """Test the Edge Histogram Kernel."""
    eh_kernel = EdgeHistogram(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Edge Histogram", eh_kernel, dataset_tr, dataset_te)
    else:
        positive_eig(eh_kernel, dataset)


def test_graph_hopper():
    """Test the Graph Hopper Kernel."""
    gh_kernel = GraphHopper(verbose=verbose, normalize=normalize)
    if verbose:
        print_kernel("Graph Hopper", gh_kernel, dataset_attr_tr, dataset_attr_te)
    else:
        positive_eig(gh_kernel, dataset_attr)


def test_core_framework():
    """Test the Graph Hopper Kernel."""
    base_kernel = (WeisfeilerLehman, dict(base_kernel=VertexHistogram))
    core_framework = CoreFramework(verbose=verbose, normalize=normalize, base_kernel=base_kernel)
    if verbose:
        print_kernel("Core Framework", core_framework, dataset_tr, dataset_te)
    else:
        positive_eig(core_framework, dataset)


def print_kernel(name, kernel, X, Y):
    """Print kernels in case of verbose execution."""
    if time_kernel:
        print(str(name) + ":\n" + (len(str(name)) * "-") + "-\n")
        print("fit_transform\n-------------")

        # [time] fit_transform
        start = time()
        Kft = kernel.fit_transform(X)
        ft_time = time() - start

        print(Kft)
        print("[TIME] fit_transform:", sec_to_time(ft_time))
        print("\ntransform\n---------")

        start = time()
        Kt = kernel.transform(Y)
        t_time = time() - start
        print(Kt)
        print("[TIME] transform:", sec_to_time(t_time))
        print("[TIME] total:", sec_to_time(ft_time+t_time))
        print("--------------------------------------" +
              "--------------------------------------\n")
    else:
        print(str(name) + ":\n" + (len(str(name)) * "-") + "-\n")
        print("fit_transform\n-------------")
        print(kernel.fit_transform(X))

        print("\ntransform\n---------")
        print(kernel.transform(Y))
        print("--------------------------------------" +
              "--------------------------------------\n")


def sec_to_time(sec):
    """Print time in a correct format."""
    dt = list()
    days = int(sec // 86400)
    if days > 0:
        sec -= 86400*days
        dt.append(str(days) + " d")

    hrs = int(sec // 3600)
    if hrs > 0:
        sec -= 3600*hrs
        dt.append(str(hrs) + " h")

    mins = int(sec // 60)
    if mins > 0:
        sec -= 60*mins
        dt.append(str(mins) + " m")

    if sec > 0:
        dt.append(str(round(sec, 2)) + " s")
    return " ".join(dt)


def positive_eig(kernel, X):
    """Assert true if the calculated kernel matrix is valid."""
    K = kernel.fit_transform(X)
    min_eig = np.real(np.min(np.linalg.eig(K)[0]))
    assert_array_less(default_eigvalue_precision, min_eig)


if verbose and main:
    test_random_walk()
    test_shortest_path()
    test_weisfeiler_lehman()
    test_neighborhood_hash()
    test_graphlet_sampling()
    test_lovasz_theta()
    test_svm_theta()
    test_odd_sth()
    test_propagation()
    test_hadamard_code()
    test_neighborhood_subgraph_pairwise_distance()
    test_pyramid_match()
    test_multiscale_laplacian_fast()
    test_edge_histogram()
    test_vertex_histogram()
    test_subgraph_matching()
    test_graph_hopper()
    test_core_framework()

if verbose and develop:
    if slow:
        test_multiscale_laplacian()
    if problematic:
        pass
