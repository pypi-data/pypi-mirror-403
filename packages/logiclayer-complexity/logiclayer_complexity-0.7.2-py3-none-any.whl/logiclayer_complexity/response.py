from __future__ import annotations

import os
import tempfile as tmp
from hashlib import md5
from typing import Optional

import orjson
import pandas as pd
from fastapi import HTTPException, Response
from fastapi.responses import FileResponse, PlainTextResponse
from starlette.background import BackgroundTask
from tesseract_olap.logiclayer import ResponseFormat

from .structs import TopkIntent


def serialize(
    extension: ResponseFormat,
    df: pd.DataFrame,
    aliases: dict[str, str],
    filters: dict[str, tuple[str, ...]],
    topk: Optional[TopkIntent] = None,
) -> Response:
    """Serialize a DataFrame to the requested response format.

    Applies filters, aliases, and top-k operations before converting to the specified format.
    """
    # filter which members will be sent in the response
    for key, values in filters.items():
        column_id = f"{key} ID"
        column_id = column_id if column_id in df.columns else key
        df = df.loc[df[column_id].astype(str).isin(values)]

    # apply aliases requested by the user
    df = df.rename(columns=aliases)

    # apply topk parameter
    if topk:
        if topk.order == "desc":
            applyfn = lambda x: x.nlargest(topk.amount, topk.measure)
        else:
            applyfn = lambda x: x.nsmallest(topk.amount, topk.measure)
        df = df.groupby(topk.level, group_keys=False).apply(applyfn)

    return data_response(df, extension)


TEMPDIR = os.getenv("TESSERACT_TEMPDIR", os.getcwd())


def data_response(
    df: pd.DataFrame,
    extension: ResponseFormat,
) -> Response:
    """Convert a DataFrame to a FastAPI Response in the specified format."""
    columns = tuple(df.columns)

    headers = {
        "X-Tesseract-Columns": ",".join(columns),
        "X-Tesseract-QueryRows": str(len(df.index)),
    }
    kwargs = {"headers": headers, "media_type": extension.get_mimetype()}

    if extension in (ResponseFormat.csv, ResponseFormat.csvbom):
        encoding = "utf-8-sig" if extension is ResponseFormat.csvbom else "utf-8"
        content = df.to_csv(sep=",", index=False, encoding=encoding)
        return PlainTextResponse(content, **kwargs)

    if extension in (ResponseFormat.tsv, ResponseFormat.tsvbom):
        encoding = "utf-8-sig" if extension is ResponseFormat.tsvbom else "utf-8"
        content = df.to_csv(sep="\t", index=False, encoding=encoding)
        return PlainTextResponse(content, **kwargs)

    if extension is ResponseFormat.jsonarrays:
        res = df.to_dict("tight")
        target = {"columns": columns, "data": res["data"]}
        content = orjson.dumps(target)
        return PlainTextResponse(content, **kwargs)

    if extension is ResponseFormat.jsonrecords:
        target = {"columns": columns, "data": df.to_dict("records")}
        content = orjson.dumps(target)
        return PlainTextResponse(content, **kwargs)

    if extension is ResponseFormat.excel:
        with tmp.NamedTemporaryFile(
            delete=False,
            dir=TEMPDIR,
            suffix=f".{extension}",
        ) as tmp_file:
            df.to_excel(tmp_file.name, engine="xlsxwriter")

        kwargs["filename"] = f"data_{shorthash(','.join(columns))}.{extension}"
        kwargs["background"] = BackgroundTask(os.unlink, tmp_file.name)
        return FileResponse(tmp_file.name, **kwargs)

    if extension is ResponseFormat.parquet:
        with tmp.NamedTemporaryFile(
            delete=False,
            dir=TEMPDIR,
            suffix=f".{extension}",
        ) as tmp_file:
            df.to_parquet(tmp_file.name)

        kwargs["filename"] = f"data_{shorthash(','.join(columns))}.{extension}"
        kwargs["background"] = BackgroundTask(os.unlink, tmp_file.name)
        return FileResponse(tmp_file.name, **kwargs)

    raise HTTPException(406, f"Requested format is not supported: {extension}")


def shorthash(string: str) -> str:
    """Generate a short hash (first 8 characters) of the MD5 hash of a string."""
    return str(md5(string.encode("utf-8"), usedforsecurity=False).hexdigest())[:8]
