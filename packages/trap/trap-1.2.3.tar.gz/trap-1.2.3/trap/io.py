from os import PathLike
from pathlib import Path
from typing import List, Literal, Optional, Tuple, Union

import numpy as np
import pandas as pd
import sqlalchemy
from astropy.io import fits

from trap.log import logger

IMAGE_DTYPE_SCHEMA = {
    "id": sqlalchemy.Integer,
    "url": sqlalchemy.Text,
    # The pandas datetime is timezone-naive
    "acquisition_date": sqlalchemy.DateTime(timezone=False),
    "rejected": sqlalchemy.Boolean,
}

# Note on floating-point precision:
#    In PostgreSQL, precision=PRECISION_FLOAT_32 is a real/float32 and precision=PRECISION_FLOAT_64 is a double/float64.
#        In general we store position as a float64 and flux as a float32.
#    In SQLite, all floats are stored as 8-byte doubles and precision is ignored.
PRECISION_FLOAT_32 = 24
PRECISION_FLOAT_64 = 53
EXTRACTED_SOURCES_DTYPE_SCHEMA = {
    "ra": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "dec": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "ra_fit_err": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "dec_fit_err": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "peak_flux": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "peak_flux_err": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "int_flux": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "int_flux_err": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "significance_detection_level": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "semimajor_axis": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "semiminor_axis": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "parallactic_angle": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "error_radius": sqlalchemy.Float(precision=PRECISION_FLOAT_64),
    "chisq": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "reduced_chisq": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "ns_sys_err": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "ew_sys_err": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "gaussian_fit": sqlalchemy.Boolean,
    "uncertainty_ew": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
    "uncertainty_ns": sqlalchemy.Float(precision=PRECISION_FLOAT_32),
}


def is_fits(file: Path):
    """Check if the supplied file exists and is a .fits image.

    Parameters
    ----------
    file: :class:`Path`
        The path to the file of which we want to know if it is a valid fits file

    Returns
    -------
    bool
        Whether the file is a fits file or not
    """
    if not file.is_file():
        return False

    if file.suffix.lower() != ".fits":
        return False

    return True


def find_fits(path: Union[str, Path]) -> List[Path]:
    """Find the .fits files in the supplied directories.
    Only .fits images are supported.
    Both absolute and relative paths are allowed.
    Supported input style: \n
        - File (/data/im0.fits) \n
        - Directory (/data/im0.fits) \n
        - Glob (/data/*/im_*) \n
    In the case of a directory all fits files in the given directory are used. Any non-fits files are ignored.
    Same with the glob pattern.

    Parameters
    ----------
    fits_path: list
        A list of directories, glob patterns or file locations.

    Returns
    -------
    fits_path: numpy.ndarray
        A list of file paths for each .fits file found
    """

    def _expand_glob_path(path: Path):
        # Expand each * in the path.
        # E.g. /data/dummy_*/files would be turned into [/data/dummy_aaa/files, /data/dummy_bbb/files, ...]
        parent_dir = path.parent
        if "*" in str(parent_dir):
            matches = _expand_glob_path(parent_dir)
            return [match / path.name for match in matches]
        else:
            return parent_dir.glob(path.name)

    # The workflow below is as follows:
    # 1. If path is a fits file, add it to the list
    # 2. If path is a directory, call this function again for each item (file or sub-directory) in the given directory
    # 3. If there is a glob pattern (*) in the filename, find each file using that pattern
    # 4. If there is a glob pattern (*) in the directory, expand it into a list of directories using _expand_glob_path
    #    and call find_fits again for each directory found by expanding the glob patterns.
    search_path: Path = Path(path)
    fits_files = []
    if search_path.is_file():  # Step 1. add fits file to the list
        if not search_path.exists():
            raise FileNotFoundError(f"Cannot read {search_path}: file does not exist.")
        if is_fits(search_path):
            fits_files.append(search_path)
    elif search_path.is_dir():  # Step 2. find all fits files in directory
        for p in search_path.iterdir():
            fits_files.extend(find_fits(p))
    else:
        if "*" in str(
            search_path.parent
        ):  # Step 3. expand directories with '*' in the path
            paths = _expand_glob_path(search_path)
            for p in paths:
                fits_files.extend(find_fits(p))
        elif "*" in str(search_path):  # Step 4. find files with '*' in filename
            found_files_or_dirs = list(search_path.parent.glob(search_path.name))
            for p in found_files_or_dirs:
                if is_fits(p):
                    fits_files.append(p)
                elif p.is_dir():
                    fits_files.extend(find_fits(p))
        else:
            raise ValueError(
                f"Cannot interpret supplied path as directory or file: {search_path}. Does this location exist?"
            )
    return fits_files


def order_fits_by_time(fits_paths: List[Path]) -> Tuple[np.ndarray, np.ndarray]:
    """Order a list of paths to fits images by their acquisition time, as read from the metadata.

    Parameters
    ----------
    fits_path: list
        A list of .fits files.

    Returns
    -------
    fits_path: numpy.ndarray
        The ordered array of fits image paths
    datetimes: numpy.ndarray
        An array containing the datetimes to go along with the paths in fits_path
    """
    datetimes = np.empty(len(fits_paths), dtype="datetime64[ms]")
    for i, path in enumerate(fits_paths):
        with fits.open(path) as im:
            header = im[0].header
            date_time = header.get("DATE-OBS", None)
            datetimes[i] = np.datetime64(date_time, "s")

    order = np.argsort(datetimes)
    fits_paths = np.asarray(fits_paths)
    fits_paths = fits_paths[order]
    datetimes = datetimes[order]
    return fits_paths, datetimes


def init_db(
    db_backend: Literal["sqlite", "postgres"],
    db_name: str,
    db_user: Optional[str] = None,
    db_password: Optional[str] = None,
    db_host: Optional[str] = None,
    db_port: Optional[str] = None,
    db_overwrite: bool = False,
) -> sqlalchemy.engine.base.Engine:
    """Create a new database. An error is raised if the database already exists, except if ``db_overwrite`` is provided.
    In that case the original database will be removed before the new database is created.

    Parameters
    ----------
    db_backend: Literal["sqlite", "postgres"] (default: "sqlite")
        The database implementation to use.
    db_name: str
        If ``db_backend`` is "sqlite" this is the path to the database.
        If ``db_backend`` is "postgres" this is the name of database.
    db_user: str
        The username with which to log in to the database.
        Only used if ``db_backend`` is "postgres".
    db_password: str
        The password to go along with db_user.
        Only used if ``db_backend`` is "postgres".
    db_host: str
        The name of the host where the database is located.
        Only used if ``db_backend`` is "postgres".
    db_port: str
        The port at which to connect to the host. Goes along wht ``db_host``.
        Only used if ``db_backend`` is "postgres".
    db_overwrite: bool (default: False)
        Allow overwriting of an existing database.
        If `db_overwrite` is False, an error is raised if the database ``db_name`` already exists.
        If `db_overwrite` is True, the database ``db_name`` will be removed if it already exists.

    Returns
    -------
        A sqlalchemy database engine.
    """
    logger.info(f"Establishing {db_backend} database connection for '{db_name}'")
    match db_backend:
        case "sqlite":
            db_path: Path = Path(db_name)
            if db_path.exists():
                if db_overwrite:
                    db_path.unlink()
                else:
                    raise Exception(
                        f"SQLite database {db_name} already exists. Either run TraP with a different 'db_name' or supply '--db_overwrite'."
                    )

            db_engine = sqlalchemy.create_engine(f"sqlite:///{db_name}")
        case "postgres":
            # First connect to the default database to create the new database
            admin_engine = sqlalchemy.create_engine(
                f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/postgres",
                isolation_level="AUTOCOMMIT",
            )
            with admin_engine.connect() as conn:
                if db_overwrite:
                    try:
                        logger.warning(f"Dropping existing database '{db_name}'")
                        conn.execute(
                            sqlalchemy.text(f"DROP DATABASE IF EXISTS {db_name}")
                        )
                    except Exception as e:
                        raise Exception(
                            f"Problem dropping Postgres database '{db_name}', see above for original error"
                        ) from e
                try:
                    conn.execute(sqlalchemy.text(f"CREATE DATABASE {db_name}"))
                except sqlalchemy.exc.ProgrammingError as e:
                    if "already exists" in str(e):
                        raise Exception(
                            f"Postgres database '{db_name}' already exists. Either run TraP with a different 'db_name' or supply '--db_overwrite'."
                        ) from e
                    else:
                        raise Exception(
                            f"Problem connecting to Postgres database '{db_name}', see above for original error"
                        ) from e

            db_engine = sqlalchemy.create_engine(
                f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
            )
        case _:
            raise ValueError(
                f"Unsupported database backend: {db_backend}. Supported backends: ['sqlite', 'postgres']"
            )
    return db_engine


def open_db(
    db_backend: Literal["sqlite", "postgres"],
    db_name: str,
    db_user: Optional[str] = None,
    db_password: Optional[str] = None,
    db_host: Optional[str] = None,
    db_port: Optional[str] = None,
) -> sqlalchemy.engine.base.Engine:
    """Open a handle to a database for reading or appending to.

    Parameters
    ----------
    db_backend: Literal["sqlite", "postgres"] (default: "sqlite")
        The database implementation to use.
    db_name: str
        If ``db_backend`` is "sqlite" this is the path to the database.
        If ``db_backend`` is "postgres" this is the name of database.
    db_user: str
        The username with which to log in to the database.
        Only used if ``db_backend`` is "postgres".
    db_password: str
        The password to go along with db_user.
        Only used if ``db_backend`` is "postgres".
    db_host: str
        The name of the host where the database is located.
        Only used if ``db_backend`` is "postgres".
    db_port: str
        The port at which to connect to the host. Goes along wht ``db_host``.
        Only used if ``db_backend`` is "postgres".

    Returns
    -------
        A sqlalchemy database engine.
    """
    logger.info(f"Establishing {db_backend} database connection for '{db_name}'")
    match db_backend:
        case "sqlite":
            db_path: Path = Path(db_name)
            if not db_path.exists():
                raise Exception(f"SQLite database {db_name} not found.")

            db_engine = sqlalchemy.create_engine(f"sqlite:///{db_name}")
        case "postgres":
            try:
                db_engine = sqlalchemy.create_engine(
                    f"postgresql+psycopg2://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
                )
            except Exception as e:
                raise Exception(
                    f"Unable to connect to postgres database {db_host}:{db_port}/{db_name} as {db_user}."
                ) from e
        case _:
            raise ValueError(
                f"Unsupported database backend: {db_backend}. Supported backends: ['sqlite', 'postgres']"
            )
    return db_engine


def export_to_database(db_kwargs, im_id, im_meta, extracted_sources):
    """Write the data for time step ``im_id`` to the database.

    Parameters
    ----------
    db_kwargs: dict
        A dictionary containing the arguments for :func:`trap.io.open_db`
    im_id: int
        The index corresponding to the image
    im_meta: dict
        A dictionary containing the metadata corresponding to the image that is to be written to the database.
        # TODO: point to table in database description (yet to be documented)
    extracted_sources: dict
        A dictionary containing the information of each source that was fitted in the image (corresponding to the
        supplied ``im_id`` and ``im_meta``). These sources will be written to the database.
        # TODO: point to table in database description (yet to be documented)

    returns
    -------
    db_kwargs: dict
        Return the same database arguments, unaltered.
        This is exported such that this can be fed into the next call to export_database to enable the creation
        of a sequential Dask chain, which would prevent simultaneous execution of multiple `export_to_database`
        calls at once.
        # TODO: investigate if we can have parallel writes to the same table (I believe postgres supports this but sqlite less so)

    """
    db_engine = open_db(**db_kwargs)
    # Write image metadta table
    image_db = pd.DataFrame(
        {
            "id": [im_id],
            "rejected": [0],
            **im_meta,
        }
    )
    image_db.to_sql(
        "images", db_engine, if_exists="append", index=False, dtype=IMAGE_DTYPE_SCHEMA
    )
    # Write extracted sources table
    extracted_sources.index.name = "id"
    extracted_sources.to_sql(
        "extracted_sources",
        db_engine,
        if_exists="append",
        index=True,
        dtype=EXTRACTED_SOURCES_DTYPE_SCHEMA,
    )
    return db_kwargs


def source_list_from_db(
    db_backend: Literal["sqlite", "postgres"],
    db_name: str,
    db_user: Optional[str] = None,
    db_password: Optional[str] = None,
    db_host: Optional[str] = None,
    db_port: Optional[str] = None,
) -> pd.DataFrame:
    """
    Restore a source list from a TraP database as required for association.

    Parameters
    ----------
    db_backend : Literal["sqlite", "postgres"]
        The database implementation to use.
    db_name : str
        If ``db_backend`` is "sqlite", this is the filesystem path to the
        SQLite database file.
        If ``db_backend`` is "postgres", this is the name of the PostgreSQL database.
    db_user : str, optional
        The username used to authenticate with a PostgreSQL database.
        Ignored for SQLite.
    db_password : str, optional
        The password associated with ``db_user``.
        Ignored for SQLite.
    db_host : str, optional
        The hostname of the PostgreSQL database server.
        Ignored for SQLite.
    db_port : str, optional
        The port on which the PostgreSQL server is listening.
        Ignored for SQLite.

    Returns
    -------
    pandas.DataFrame
        A DataFrame indexed by ``src_id`` containing the following columns:

        - ``ra`` : float
            The most recently measured right ascension for the source.
        - ``dec`` : float
            The most recently measured declination for the source.
        - ``uncertainty_ns`` : float
            North–south positional uncertainty of the latest detection in degrees.
        - ``uncertainty_ew`` : float
            East–west positional uncertainty of the latest detection in degrees.
        - ``nr_consecutive_force_fits`` : int
            Number of consecutive null-detections where the source was force-fit.
        - ``latest_extracted_source_id`` : int
            The ID of the most recent measurement in ``extracted_sources`` corresponding
            to this source.

    Notes
    -----
    The function expects two tables in the database:
    ``extracted_sources`` and ``images``. The grouping and update logic assume
    the schema used by the TraP pipeline as documented here:
        https://transients-pipeline.readthedocs.io/en/latest/export_database/database_reference.html

    """
    db_handle = open_db(db_backend, db_name, db_user, db_password, db_host, db_port)

    columns = [
        "id",
        "src_id",
        "ra",
        "dec",
        "uncertainty_ns",
        "uncertainty_ew",
        "is_force_fit",
        "im_id",
    ]

    query = f"SELECT {', '.join(columns)} FROM extracted_sources"

    sources = pd.read_sql_query(query, db_handle).set_index("id", drop=True)
    images = pd.read_sql_query("SELECT id FROM images", db_handle).set_index(
        "id", drop=True
    )
    grouped = sources.groupby("src_id")
    src_id = grouped["src_id"].first().values
    restored_source_list = pd.DataFrame(
        index=src_id,
        data={
            "ra": np.full(len(src_id), np.nan, dtype=float),
            "dec": np.full(len(src_id), np.nan, dtype=float),
            "uncertainty_ns": np.full(len(src_id), np.nan, dtype=float),
            "uncertainty_ew": np.full(len(src_id), np.nan, dtype=float),
            "nr_consecutive_force_fits": np.zeros(len(src_id), dtype=int),
            "latest_extracted_source_id": np.zeros(len(src_id), dtype=int),
        },
    )
    for im_id in images.index:
        sources_slice = sources[sources.im_id == im_id]
        idx = sources_slice["src_id"].values

        restored_source_list.loc[idx, "ra"] = sources_slice["ra"].values
        restored_source_list.loc[idx, "dec"] = sources_slice["dec"].values
        restored_source_list.loc[idx, "uncertainty_ns"] = sources_slice[
            "uncertainty_ns"
        ].values
        restored_source_list.loc[idx, "uncertainty_ew"] = sources_slice[
            "uncertainty_ew"
        ].values

        # Add one to nr_consecutive_force_fits if is_force_fit, else set to zero
        is_force_fit = sources_slice["is_force_fit"].values
        restored_source_list.loc[idx, "nr_consecutive_force_fits"] += is_force_fit
        restored_source_list.loc[idx, "nr_consecutive_force_fits"] *= is_force_fit

        restored_source_list.loc[idx, "latest_extracted_source_id"] = (
            sources_slice.index
        )

    return restored_source_list
