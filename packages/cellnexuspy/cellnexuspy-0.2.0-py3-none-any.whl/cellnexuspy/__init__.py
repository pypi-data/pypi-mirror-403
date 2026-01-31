import itertools
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Iterable, Literal

import anndata as ad
import numpy as np
import scipy.sparse as sp
import duckdb
import pandas as pd
import requests
from appdirs import user_cache_dir
from tqdm import tqdm

REMOTE_URL = "https://object-store.rc.nectar.org.au/v1/AUTH_06d6e008e3e642da99d806ba3ea629c5"
ASSAY_URL = "{}/cellNexus-anndata".format(REMOTE_URL)
METADATA_URL = "{}/cellNexus-metadata/metadata.1.3.0.parquet".format(REMOTE_URL)
MIN_EXPECTED_SIZE = 5000000

assay_map = {"counts": "counts", "cpm": "cpm"}

def is_parquet_valid(parquet_file):
    try:
        conn = duckdb.connect()
        conn.from_parquet(str(parquet_file))  # Try reading
        return True  # File is valid
    except Exception as e:
        print(f"Parquet file is corrupt: {e}")
        return False  # File is corrupt
        
def _get_default_cache_dir() -> Path:
    return Path(user_cache_dir("cellNexusPy"))

    # helper function to download file over http/https
def _sync_remote_file(full_url: str, output_file: Path):
    if not output_file.exists():
        output_dir = output_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        print(f"Downloading {full_url} to {output_file}", file=sys.stderr)
        req = requests.get(full_url, stream=True, allow_redirects=True)
        req.raise_for_status()
        pbar = tqdm(total=int(req.headers.get("Content-Length", 0)))
        with pbar.wrapattr(req.raw, "read") as src, output_file.open("wb") as dest:
            shutil.copyfileobj(src, dest)

# function to get metadata
def get_metadata(
    parquet_url: str = METADATA_URL,
    cache_dir: os.PathLike[str] = _get_default_cache_dir(),
) -> tuple[duckdb.DuckDBPyConnection, duckdb.DuckDBPyRelation]:
    r""" Downloads a parquet file with the Human Cell Atlas metadata into a cache 
    folder. This file is automatically imported into DuckDB for filtering and manipulation.

    Args:
        parquet_url (str): Provides the capability of using a customized URL for 
                           local server parquet files.
        cache_dir (str): Path to the folder to locate the parquet file.
    """


    
    parquet_local = Path(cache_dir) / parquet_url.split("/")[-1]

    if not parquet_local.exists() or not is_parquet_valid(parquet_local):
        print("File is missing or corrupted. Re-downloading...")
        parquet_local.unlink(missing_ok=True)  # Delete the corrupted file
        _sync_remote_file(parquet_url, parquet_local)  # Re-download
    
    _sync_remote_file(parquet_url, parquet_local)
    conn = duckdb.connect()
    return conn, conn.from_parquet(str(parquet_local))

def sync_assay_files(
    url: str = ASSAY_URL,
    cache_dir: Path = _get_default_cache_dir(),
    subdir: str = "",
    atlas: str = "",
    aggregation: str = "",
    files: Iterable[str] = [],
):
    for file in files:
        if aggregation == "single_cell":
            sub_url = f"{url}/{atlas}/{subdir}/{file}"
        else:
            sub_url = f"{url}/{atlas}/{aggregation}/{subdir}/{file}"
        output_filepath = cache_dir / atlas / aggregation / subdir / file

        if not output_filepath.exists() or os.path.getsize(output_filepath) < MIN_EXPECTED_SIZE:
            _sync_remote_file(sub_url, output_filepath)

        yield subdir, output_filepath
        
def filter_pseudobulk(file, data):
    cells = data.filter("file_id_cellNexus_pseudobulk ="  + "'"+str(file).split("/")[-1]+"'").fetchdf()
    cell_ids = cells["sample_id"].astype(str) + "___" + cells["cell_type_unified_ensemble"].astype(str)
    anndata = ad.read_h5ad(file)
    ann = anndata[cell_ids.unique()].copy()

    columns_to_remove = ["cell_id", "cell_type", "file_id_cellNexus_single_cell",
                         "cell_type_ontology_term_id",
                         "observation_joinid", "ensemble_joinid",
                         "nFeature_expressed_in_sample", "nCount_RNA", "data_driven_ensemble", "cell_type_unified",
                         "empty_droplet", "observation_originalid", "alive", "scDblFinder.class", "is_immune"]
    subdata = cells.drop(columns=[col for col in columns_to_remove if col in cells])
    pattern = '|'.join(re.escape(s) for s in ["metacell","azimuth","monaco","blueprint","subsets_","high_"])

    # Find matching columns and drop them
    cols_to_drop = subdata.columns[subdata.columns.str.contains(pattern, case=False, regex=True)]
    subdata = subdata.drop(columns=cols_to_drop)
    subdata = subdata.drop_duplicates(keep='last')
    subdata.index = subdata["sample_id"]+"___"+subdata["cell_type_unified_ensemble"]

    ann.obs = subdata.reindex(ann.obs.index)
    return ann

def filter_metacell(file, data):
    df = data.filter("file_id_cellNexus_single_cell ="  + "'"+str(file).split("/")[-1]+"'").fetchdf()
    df["file_id_cellNexus_metacell"] = df["sample_id"].astype(str) + "___" + df["metacell_2"].astype(int).astype(str)
    df.index = df["file_id_cellNexus_metacell"]
    filt_ad = ad.read_h5ad(file)[df["file_id_cellNexus_metacell"].unique()]
    filt_ad.obs = df[["dataset_id", "sample_id", "assay", "assay_ontology_term_id", 
     "development_stage", "development_stage_ontology_term_id", "disease", "disease_ontology_term_id", 
     "donor_id", "experiment___", "explorer_url", "feature_count", "is_primary_data", 
     "organism", "organism_ontology_term_id", "published_at", "raw_data_location", 
     "revised_at", "sample_heuristic", "schema_version", "self_reported_ethnicity", 
     "self_reported_ethnicity_ontology_term_id", "sex", "sex_ontology_term_id", "tissue", 
     "tissue_ontology_term_id", "tissue_type", "title", "tombstone", "url", "age_days", 
     "tissue_groups", "atlas_id", "sample_chunk", "file_id_cellNexus_single_cell","file_id_cellNexus_metacell"]].drop_duplicates()
    return filt_ad

def filter_single_cell(file, data):
    cells = data.filter("file_id_cellNexus_single_cell ="  + "'"+str(file).split("/")[-1]+"'").fetchdf()
    anndata = ad.read_h5ad(file)
    anndata.obs.index = anndata.obs.index.astype(str)
    cell_ids = cells["cell_id"].astype(str)
    ann = anndata[cell_ids]
    ann.obs = cells
    ann.obs.index = ann.obs["cell_id"]

    return ann
    
def get_anndata(
    data: duckdb.DuckDBPyRelation,
    assay: str = "counts",
    aggregation: str = "single_cell",
    cache_directory: Path = _get_default_cache_dir(),
    features: Iterable = slice(None, None, None)
) -> ad.AnnData:
    r""" Download and concatenate the .h5ad files with the gene expression and
         the observational data in a single :obj:`AnnData` object.

         Args:
             data (duckdb): Metadata filtered with information of experiments of interest.
             assay (str): Type of gene expression data `counts` (raw) or `cpm` (normalized).
             aggregation (str): Type of cell aggregation to be used: `pseudobulk` or `metacell`.
             cache_directory (str): Path to the folder to locate the parquet file.
             features (Iterable): List of Ensembl ids to subset the :obj:`AnnData` object to the
                                  specific genes of interest.
    """
    
    # error checking
    assert assay in (set(assay_map.keys()))
    assert isinstance(cache_directory, Path), "cache_directory must be a Path"
    
    cache_directory.mkdir(exist_ok=True, parents=True)

    if aggregation != "single_cell" and aggregation != "pseudobulk": data = data.filter(aggregation + " IS NOT NULL")
    
    if aggregation == "pseudobulk":
        files_to_read = (
            data.project("file_id_cellNexus_pseudobulk").distinct().fetchdf()["file_id_cellNexus_pseudobulk"]
        )
    else:
        files_to_read = (
            data.project("file_id_cellNexus_single_cell").distinct().fetchdf()["file_id_cellNexus_single_cell"]
        )
    
    atlas = data.project('"atlas_id"').distinct().fetchdf()["atlas_id"][0]                                                                                                                      
    
    synced = sync_assay_files(
        url=ASSAY_URL, cache_dir=cache_directory, atlas=atlas, subdir=assay, aggregation=aggregation, files=files_to_read
    )

    if aggregation == "pseudobulk":
        for _, files in itertools.groupby(synced, key=lambda x: x[0]):
            ads = [filter_pseudobulk(file[1], data) for file in files]
    elif aggregation == "metacell_2":
        for _, files in itertools.groupby(synced, key=lambda x: x[0]):
            ads = [filter_metacell(file[1], data) for file in files]
    else:
        for _, files in itertools.groupby(synced, key=lambda x: x[0]):
            ads = [filter_single_cell(file[1], data) for file in files]

    adatas = ad.concat(ads,index_unique="_")
    
    return adatas[:,features]
