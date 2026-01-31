from typing import Any

import polars as pl


def parse_record(record: dict[str, Any]) -> pl.DataFrame:
    """Records 解析器

    平台大量的返回数据都是 schema + records 格式, 可统一用
    该函数返回

    Record Example
    --------------
    {
      'schema': {
        'name' / 'title' /
        'properties': [{'name' / 'title', 'type'}] # 列名
      },
      'records': [
        [], [], [], # 行数据
      ]
    }
    """
    schema_mapping = {
        "date": pl.String,
        "amount": pl.Float64,
        "integer": pl.Int64,
        "percent": pl.Float64,
        "decimal": pl.Float64,
        "permyriad": pl.Float64,
    }

    schema = {p["name"]: schema_mapping.get(p["type"]) or pl.String for p in record["schema"]["properties"]}
    data = pl.DataFrame(data=record["records"], schema=schema, orient="row")

    for f in filter(lambda x: x["type"] == "date", record["schema"]["properties"]):
        data = data.with_columns(pl.col(f["name"]).str.to_date())
    return data
