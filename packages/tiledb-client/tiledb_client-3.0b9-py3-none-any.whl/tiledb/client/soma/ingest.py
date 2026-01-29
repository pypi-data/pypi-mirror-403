import fnmatch
import logging
import os.path
import pathlib
from functools import partial
from typing import ContextManager, Dict, Optional
from unittest import mock

import tiledb
from tiledb.client import dag
from tiledb.client.utilities import as_batch
from tiledb.client.utilities import get_logger_wrapper
from tiledb.client.utilities import run_dag

_DEFAULT_DAG_FACTORY = partial(dag.DAG, workspace=None, mode=dag.Mode.BATCH)
"""Default factory for ingestion DAGs."""


def run_ingest_workflow_udf(
    *,
    output_uri: str,
    input_uri: str,
    measurement_name: str,
    pattern: Optional[str] = None,
    extra_tiledb_config: Optional[Dict[str, object]] = None,
    platform_config: Optional[Dict[str, object]] = None,
    ingest_mode: str = "write",
    ingest_resources: Optional[Dict[str, object]] = None,
    acn: Optional[str] = None,
    logging_level: int = logging.INFO,
    dry_run: bool = False,
    dag_factory=None,
    dag_kwargs: Optional[Dict[str, object]] = None,
    **kwargs,
) -> dag.DAG:
    """
    This is the highest-level ingestor component that runs on-node. Only
    here can we do VFS with access_credentials_name -- that does not
    work correctly on the client.
    """
    dag_factory = dag_factory or _DEFAULT_DAG_FACTORY

    # Some kwargs are eaten by the tiledb.client package, and won't reach
    # our child. In order to propagate these to a _grandchild_ we need to
    # package these up with different names. We use a dict as a single bag.
    carry_along: Dict[str, str] = kwargs.pop("carry_along", {})

    # For more information on "that does not work correctly on the client" please see
    # https://github.com/TileDB-Inc/TileDB-Cloud-Py/pull/512

    logger = get_logger_wrapper(level=logging_level)
    vfs = tiledb.VFS(config=extra_tiledb_config)

    input_files = []

    if vfs.is_dir(input_uri):
        for input_item in vfs.ls(input_uri):
            logger.debug(
                "Filtering directory items: input_uri=%r, input_item=%r, pattern=%r",
                input_uri,
                input_item,
                pattern,
            )

            # Subdirectories/subfolders can't be ingested.
            # Use the pattern "*.h5ad" to select only .h5ad files.
            if not vfs.is_dir(input_item) and (
                not pattern or fnmatch.fnmatch(input_item, pattern)
            ):
                logger.debug("Identified input file: input_item=%r", input_item)
                input_files.append(input_item)

    elif vfs.is_file(input_uri):
        input_files.append(input_uri)
    else:
        raise ValueError("input_uri %r is neither a file nor a directory", input_uri)

    logger.info(
        "Building DAG for SOMA ingestion: input_files=%r, dag_factory=%r",
        input_files,
        dag_factory,
    )
    grf = dag_factory(
        name=f"{'dry-run' if dry_run else 'ingest'}-h5ad-files",
        **dag_kwargs,
    )

    for input_file in input_files:
        stem = pathlib.Path(input_file).stem
        output_group_uri = os.path.join(output_uri, stem)
        logger.info(
            "Building task for h5ad file: input_file=%r, output_group_uri=%r",
            input_file,
            output_group_uri,
        )
        _ = grf.submit(
            ingest_h5ad,
            output_uri=output_group_uri,
            input_uri=input_file,
            measurement_name=measurement_name,
            extra_tiledb_config=extra_tiledb_config,
            ingest_mode=ingest_mode,
            platform_config=platform_config,
            resources=ingest_resources,  # Apply propagated resources here.
            access_credentials_name=carry_along.get("access_credentials_name", acn),
            logging_level=logging_level,
            name=f"H5ad ingestion: {stem}",
            dry_run=dry_run,
        )

    logger.info("Computing DAG: grf=%r", grf)

    try:
        grf.compute()
    except Exception:
        logger.exception(f"Graph compute failed: {grf=}")

    return grf


def _hack_patch_anndata() -> ContextManager[object]:
    from anndata._core import file_backing

    @file_backing.AnnDataFileManager.filename.setter
    def filename(self, filename) -> None:
        self._filename = filename

    return mock.patch.object(file_backing.AnnDataFileManager, "filename", filename)


def ingest_h5ad(
    *,
    output_uri: str,
    input_uri: str,
    measurement_name: str,
    extra_tiledb_config: Optional[Dict[str, object]] = None,
    platform_config: Optional[Dict[str, object]] = None,
    ingest_mode: str = "write",
    logging_level: int = logging.INFO,
    dry_run: bool = False,
    **kwargs,
) -> None:
    """Ingests H5AD data by calling tiledbsoma.io.from_anndata

    Parameters
    ----------
    output_uri : str
        The output URI to write to. This will probably look like
        "tiledb://workspace/teamspace/path/to/soma".
    input_uri : str
        The URI of the H5AD file to read from. This file is read using
        TileDB VFS, so any path supported (and accessible) will work.
    measurement_name : str
        The name of the Measurement within the Experiment to store the
        data.
    extra_tiledb_config : dict, optional
        Extra configuration for TileDB.
    platform_config : dict, optional
        The SOMA ``platform_config`` value to pass in, if any.
    ingest_mode : str, optional
        One of the ingest modes supported by `tiledbsoma.io.read_h5ad`.
    logging_level : int, optional
        Set a logging level for this function.
    dry_run : bool, optional
        If provided and set to `True`, does the input-path traversals
        without ingesting data.

    """

    import anndata
    import tiledbsoma
    import tiledbsoma.logging
    from tiledbsoma import io

    # Should be using a context manager for this so that
    # we revert to the previous level after the function
    # finishes.
    logging.basicConfig(level=logging_level)

    if logging_level <= logging.DEBUG:
        tiledbsoma.logging.debug()
    elif logging_level <= logging.INFO:
        tiledbsoma.logging.info()

    # While h5ad supports any file-like object, annndata specifically
    # wants only an `os.PathLike` object. The only thing it does with
    # the PathLike is to use it to get the filename.
    class _FSPathWrapper:
        """Tricks anndata into thinking a file-like object is an os.PathLike.

        While h5ad supports any file-like object, anndata specifically
        wants an os.PathLike object, which it uses *exclusively* to get
        the "filename" of the opened file.

        We need to provide `__fspath__` as a real class method, so
        simply setting `some_file_obj.__fspath__ = lambda: "some/path"`
        won't work, so here we just proxy all attributes except
        `__fspath__`.
        """

        def __init__(self, obj: object, path: str) -> None:
            self._obj = obj
            self._path = path

        def __fspath__(self) -> str:
            return self._path

        def __getattr__(self, name: str) -> object:
            return getattr(self._obj, name)

    soma_ctx = tiledbsoma.SOMATileDBContext()

    if extra_tiledb_config:
        soma_ctx = soma_ctx.replace(tiledb_config=extra_tiledb_config)

    with tiledb.VFS(ctx=soma_ctx.tiledb_ctx).open(input_uri) as input_file:
        if dry_run:
            logging.info("Dry run for %r to %r", input_uri, output_uri)
            return

        logging.info("Ingesting data from %r to %r", input_uri, output_uri)

        with _hack_patch_anndata():
            try:
                input_data = anndata.read_h5ad(
                    _FSPathWrapper(input_file, input_uri), "r"
                )
            except Exception as h5exc:
                raise RuntimeError(
                    f"Failed to read file {input_file!r} wrapping {input_uri!r}"
                ) from h5exc

        output_uri = io.from_anndata(
            experiment_uri=output_uri,
            anndata=input_data,
            measurement_name=measurement_name,
            context=soma_ctx,
            ingest_mode=ingest_mode,
            platform_config=platform_config,
        )


def run_ingest_workflow(
    *,
    output_uri: str,
    input_uri: str,
    measurement_name: str,
    pattern: Optional[str] = None,
    extra_tiledb_config: Optional[Dict[str, object]] = None,
    platform_config: Optional[Dict[str, object]] = None,
    ingest_mode: str = "write",
    ingest_resources: Optional[Dict[str, object]] = None,
    acn: Optional[str] = None,
    logging_level: int = logging.INFO,
    dry_run: bool = False,
    dag_factory=None,
    dag_kwargs: Optional[Dict[str, object]] = None,
    return_inner_graph: bool = False,
    **kwargs,
) -> Dict[str, str]:
    """Starts a workflow to ingest H5AD data into SOMA.

    Parameters
    ----------
    output_uri : str
        Output URI.
    input_uri : str
        The URI of the H5AD file(s) to read from. These are read using
        TileDB VFS, so any path supported (and accessible) will work.
        If the `input_uri` passes `vfs.is_file`, it is ingested.  If the
        `input_uri` passes `vfs.is_dir`, then all first-level entries
        are ingested .  In the latter, directory case, an input file is
        skipped if `pattern` is provided and doesn't match the input
        file. As well, in the directory case, each entry's basename is
        appended to the `output_uri` to form the entry's output URI.
        For example, if "a.h5ad" and "b.h5ad" are present within
        `input_uri` of "s3://bucket/h5ads/" and `output_uri` is
        "tiledb://workspace/teamspace/somas", then
        "tiledb://workspace/teamspace/somas/a" and
        "tiledb://workspace/teamspace/somas/b" are written.
    measurement_name : str
        The name of the measurement within the experiment to store the
        data.
    pattern : str
        As described for `input_uri`.
    extra_tiledb_config
        Extra configuration for TileDB.
    platform_config
        The SOMA `platform_config` value to pass in, if any.
    ingest_mode
        One of the ingest modes supported by `tiledbsoma.io.read_h5ad`.
    ingest_resources : dict
        A specification for the amount of resources to provide to the
        UDF executing the ingestion process, to override the default.
    acn : str
        The name of the credentials to pass to the executing UDF.
    dry_run : bool
        If provided and set to `True`, does the input-path traversals
        without ingesting data.
    dag_factory : callable
        Allows custom DAG classes to be used in tests.  Defaults to
        dag.DAG.
    dag_kwargs : dict
        Keyword arguments for the dag_factory.
    return_inner_graph : bool
        Returns the inner graph object itself as well as its UUID.
        Defaults to False.

    Returns
    -------
    dict
        A dictionary of `{"status": "started", "graph_id": ...}`, with
        the UUID of the graph on the server side, which can be used to
        manage execution and monitor progress.

    """
    dag_factory = dag_factory or _DEFAULT_DAG_FACTORY

    # Graph init
    grf = dag_factory(name="ingest-h5ad-launcher", **dag_kwargs)

    # Step 1: Ingest workflow UDF
    carry_along: Dict[str, str] = {
        "access_credentials_name": acn,
    }

    grf.submit(
        run_ingest_workflow_udf,
        output_uri=output_uri,
        input_uri=input_uri,
        measurement_name=measurement_name,
        pattern=pattern,
        extra_tiledb_config=extra_tiledb_config,
        platform_config=platform_config,
        ingest_mode=ingest_mode,
        ingest_resources=ingest_resources,
        access_credentials_name=acn,
        carry_along=carry_along,
        logging_level=logging_level,
        dry_run=dry_run,
        dag_factory=dag_factory,
        dag_kwargs=dag_kwargs,
    )

    # Start the ingestion process
    verbose = logging_level == logging.DEBUG
    run_dag(grf, debug=verbose)

    # Get the inner graph and UUID.
    the_node = next(iter(grf.nodes.values()))
    inner_graph = the_node.result()

    retval = {
        "status": inner_graph.status,
        "graph_id": str(inner_graph.server_graph_uuid),
    }

    if return_inner_graph:
        retval["inner_graph"] = inner_graph

    return retval


ingest = as_batch(run_ingest_workflow)
