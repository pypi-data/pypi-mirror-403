# /// script
# dependencies = [
#     "duckdb==1.4.4",
#     "marimo",
#     "polars==1.37.1",
#     "pyarrow==23.0.0",
#     "sqlglot==28.6.0",
# ]
# requires-python = ">=3.12"
# ///

import marimo

__generated_with = "0.19.7"
app = marimo.App(width="medium", app_title="Test Notebook")


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Marimo test notebook
    Check conversion of notebooks.
    """)
    return


@app.cell
def _():
    import polars as pl
    return (pl,)


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(pl):
    df = pl.DataFrame(data=dict(a=(1,2,3),b=(4,5,6)))
    df
    return (df,)


@app.cell
def _(df, mo):
    _df = mo.sql(
        """
        SELECT a FROM df
        """
    )
    return


if __name__ == "__main__":
    app.run()
