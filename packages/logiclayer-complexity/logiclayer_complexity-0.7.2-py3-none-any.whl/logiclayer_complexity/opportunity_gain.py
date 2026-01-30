"""Opportunity Gain derivate calculations."""

__all__ = (
    "prepare_opportunity_gain_params",
    "OpportunityGainParameters",
)

from dataclasses import dataclass
from typing import Optional

import economic_complexity as ec
import pandas as pd
from fastapi import Depends, Query
from typing_extensions import Annotated

from .rca import RcaParameters, prepare_rca_params


@dataclass
class OpportunityGainParameters:
    """Parameters for Opportunity Gain calculation."""

    rca_params: RcaParameters
    cutoff: float = 1
    iterations: int = 20
    rank: bool = False
    sort_ascending: Optional[bool] = None

    @property
    def column_name(self) -> str:
        """Return the name of the opportunity gain column."""
        return f"{self.rca_params.measure} Opportunity Gain"

    def _calculate(self, rca: pd.Series) -> pd.Series:
        """Calculate opportunity gain from RCA values."""
        df_rca = rca.unstack()
        eci, pci = ec.complexity(df_rca, cutoff=self.cutoff, iterations=self.iterations)
        df_opgain = ec.opportunity_gain(df_rca, pci=pci, cutoff=self.cutoff)
        opgain = df_opgain.stack()
        assert isinstance(opgain, pd.Series), "Calculation did not yield a pandas.Series"
        return opgain.rename(self.column_name)

    def calculate(self, df: pd.DataFrame) -> pd.DataFrame:
        """Execute opportunity gain calculations on the provided DataFrame."""
        sort_ascending = self.sort_ascending
        name = self.column_name

        df_pivot = self.rca_params.pivot(df)
        columns = df_pivot.index.name, df_pivot.columns.name

        rca = self.rca_params._calculate(df_pivot)
        opgain = self._calculate(rca)

        ds = pd.concat([rca, opgain], axis=1).reset_index()

        if sort_ascending is not None:
            ds = ds.sort_values(by=name, ascending=sort_ascending)

        if sort_ascending is not None or self.rank:
            ds[f"{name} Ranking"] = ds[name].rank(ascending=False, method="max").astype(int)

        return df.merge(ds, how="left", on=columns)


def prepare_opportunity_gain_params(
    rca_params: RcaParameters = Depends(prepare_rca_params),
    ascending: Annotated[
        Optional[bool],
        Query(
            description=(
                "Outputs the results in ascending or descending order. "
                "If not defined, results will be returned sorted by level member."
            ),
        ),
    ] = None,
    cutoff: Annotated[
        float,
        Query(
            description=(
                "The threshold value at which a country's RCA is considered "
                "relevant for an economic activity, for the purpose of calculating "
                "the Complexity Indicators."
            ),
        ),
    ] = 1,
    rank: Annotated[
        bool,
        Query(
            description=(
                "Adds a 'Ranking' column to the data. "
                "This value represents the index in the whole result list, sorted by value."
            ),
        ),
    ] = False,
) -> OpportunityGainParameters:
    """Prepare and validate Opportunity Gain parameters from query dependencies."""
    return OpportunityGainParameters(
        rca_params=rca_params,
        cutoff=cutoff,
        rank=rank,
        sort_ascending=ascending,
    )
