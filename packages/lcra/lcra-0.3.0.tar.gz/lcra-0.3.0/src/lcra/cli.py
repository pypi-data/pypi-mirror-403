"""
LCRA Flood Status CLI

Command-line interface for extracting LCRA flood status data.
"""

import asyncio
import json
import os
from datetime import datetime

import click
import uvicorn
from rich.console import Console

from scraper import LCRAFloodDataScraper

console = Console()


@click.group()
def cli():
    """LCRA Flood Status CLI"""
    pass


@cli.command(name="get")
@click.option("--report", is_flag=True, help="Extract the full flood operations report")
@click.option("--lake-levels", is_flag=True, help="Extract current lake levels")
@click.option("--river-conditions", is_flag=True, help="Extract current river conditions")
@click.option("--floodgate-operations", is_flag=True, help="Extract floodgate operations")
@click.option(
    "--saveas",
    default=None,
    help="Store result as JSON in reports/<filename>.json. If no filename provided after --saveas, uses timestamp.",
)
@click.option(
    "--save",
    is_flag=True,
    help="Save result as JSON with auto-generated timestamp filename.",
)
def get(report, lake_levels, river_conditions, floodgate_operations, saveas, save):
    """Extract LCRA flood status data and print to stdout or file"""

    async def run_extract():
        os.makedirs("reports", exist_ok=True)
        result = None
        label = None
        async with LCRAFloodDataScraper() as scraper:
            if report:
                result = await scraper.scrape_all_data()
                label = "report"
            elif lake_levels:
                result = await scraper.scrape_lake_levels()
                label = "lake_levels"
            elif river_conditions:
                result = await scraper.scrape_river_conditions()
                label = "river_conditions"
            elif floodgate_operations:
                result = await scraper.scrape_floodgate_operations()
                label = "floodgate_operations"

            if result is not None:
                data = (
                    result.model_dump()
                    if hasattr(result, "model_dump")
                    else [r.model_dump() for r in result]
                )
                if saveas or save:
                    now = datetime.now().isoformat(timespec="seconds").replace(":", "-")
                    if save or not saveas:
                        filename = f"{label}_{now}"
                    else:
                        filename = saveas
                    out_path = os.path.join("reports", f"{filename}.json")
                    with open(out_path, "w") as f:
                        json.dump(data, f, indent=2, default=str)
                    console.print(f"[green]Saved {label} to {out_path}[/green]")
                else:
                    console.print(data, soft_wrap=True)
            else:
                console.print(
                    "[yellow]Specify at least one data type to extract. Use --help for options.[/yellow]"
                )

    asyncio.run(run_extract())


@cli.command()
@click.option("--host", default="0.0.0.0", help="Host to serve the API on")
@click.option("--port", default=8080, help="Port to serve the API on")
def serve(host, port):
    """Serve the LCRA Flood Status API"""
    uvicorn.run("api:app", host=host, port=port, reload=True)


if __name__ == "__main__":
    cli()
