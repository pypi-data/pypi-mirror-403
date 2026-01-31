"""Functions for parallel processing."""

import concurrent.futures
import multiprocessing
import os
import sys

import numpy as np
from tqdm import tqdm

# set start method to 'fork' on Unix-like systems for better compatibility
if sys.platform != "win32":
    try:
        multiprocessing.set_start_method("fork", force=True)
    except RuntimeError:
        # start method already set
        pass


def get_no_processors(no_processors):
    """
    Find number of processors to use.

    Return minimum of no_processors and one less of the number of
    available processors.
    """
    max_no_processors = os.cpu_count()
    return np.min([no_processors, max_no_processors]), max_no_processors


def process_strains_parallel(
    one_strain_fn,
    params,
    all_strains,
    max_workers=None,
    use_tqdm=True,
):
    """
    Correct multiple strains in parallel.

    Assume one_strain_fn has arguments strain and params.
    """
    results = []
    with concurrent.futures.ProcessPoolExecutor(
        max_workers=max_workers
    ) as executor:
        # submit all tasks and collect futures as dict
        futures_dict = {
            executor.submit(one_strain_fn, s, params): s for s in all_strains
        }
        # process results as they complete
        if use_tqdm:
            all_futures = tqdm(
                concurrent.futures.as_completed(futures_dict),
                total=len(futures_dict),
                desc="Processing strains",
            )
        else:
            all_futures = concurrent.futures.as_completed(futures_dict)
        for future in all_futures:
            strain = futures_dict[future]
            try:
                result = future.result()
                if result is not None:
                    results.append(result)
            except Exception as exc:
                print(f"{strain} generated an exception: {exc}")
    return results
