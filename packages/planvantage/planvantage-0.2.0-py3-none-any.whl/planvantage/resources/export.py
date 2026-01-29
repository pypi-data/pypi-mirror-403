"""Export resource for bulk data downloads."""

from __future__ import annotations

from planvantage.resources.base import BaseResource


class ExportResource(BaseResource):
    """Resource for bulk data exports."""

    def plan_designs_csv(self) -> bytes:
        """Export all plan designs as CSV.

        Downloads all plan designs across all plan sponsors and scenarios
        for the authenticated user.

        Returns:
            CSV file bytes with all plan design data.

        Example:
            >>> csv_data = client.export.plan_designs_csv()
            >>> with open("plan_designs.csv", "wb") as f:
            ...     f.write(csv_data)
        """
        return self._http.get_raw("/export/plandesigns/csv")

    def rates_contributions_csv(self) -> bytes:
        """Export all rates and contributions as CSV.

        Downloads all rates and contributions across all plan sponsors
        and scenarios for the authenticated user.

        Returns:
            CSV file bytes with all rate and contribution data.

        Example:
            >>> csv_data = client.export.rates_contributions_csv()
            >>> with open("rates_contributions.csv", "wb") as f:
            ...     f.write(csv_data)
        """
        return self._http.get_raw("/export/ratescontributions/csv")
