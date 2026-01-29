import logging
from pathlib import Path
import time
from typing import Literal

import click

from .animate_results import animate as animate_results
from .run import run_sim
from .save_results import write_multiframe_geotiff

logger = logging.getLogger('uvdat_flood_sim')


def _ensure_dir_exists(ctx, param, value):
    value.mkdir(parents=True, exist_ok=True)
    return value


@click.command(name='Dynamic Flood Simulation')
@click.option(
    '--initial-conditions-id', '-i',
    type=click.Choice(['001', '002', '003']),
    default='001',
    help='Initialization for real-world emissions scenarios to represent future climate conditions',
)
@click.option(
    '--time-period', '-t',
    type=click.Choice(['2031-2050', '2041-2060']),
    default='2031-2050',
    help='The 20 year time period in which to predict a flood'
)
@click.option(
    '--annual-probability', '-p',
    type=click.FloatRange(min=0, min_open=True, max=1, max_open=True),
    default=0.04,
    help='The probability that a flood of this magnitude will occur in any given year'
)
@click.option(
    '--hydrograph-name', '-n',
    type=click.Choice(['short_charles', 'long_charles']),
    default='short_charles',
    help=(
        'A selection of a 24-hour hydrograph. '
        '"short_charles" represents a hydrograph for the main river and '
        '"long_charles" represents a hydrograph for the main river plus additional upstream water sources.'
    )
)
@click.option(
    '--hydrograph', '-g',
    type=float,
    nargs=24,
    help='A hydrograph expressed as a list of numeric values where each value represents a proportion of total discharge'
)
@click.option(
    '--pet-percentile', '-e',
    type=click.IntRange(min=0, max=100),
    default=25,
    help='Potential evapotranspiration percentile'
)
@click.option(
    '--sm-percentile', '-s',
    type=click.IntRange(min=0, max=100),
    default=25,
    help='Soil moisture percentile'
)
@click.option(
    '--gw-percentile', '-w',
    type=click.IntRange(min=0, max=100),
    default=25,
    help='Ground water percentile'
)
@click.option(
    '--output-path', '-o',
    type=click.Path(writable=True, file_okay=False, path_type=Path),
    default=Path.cwd() / 'outputs',
    callback=_ensure_dir_exists,
    help='Directory to write the flood simulation outputs'
)
@click.option(
    '--animation/--no-animation',
    default=True,
    help='Display result animation via matplotlib'
)
@click.option(
    '--tiff-writer',
    type=click.Choice(['rasterio', 'large_image']),
    default='rasterio',
    help='Library to use for writing result tiff'
)
def main(
    initial_conditions_id: Literal['001', '002', '003'],
    time_period: Literal['2031-2050', '2041-2060'],
    annual_probability: float,
    hydrograph_name: Literal['short_charles', 'long_charles'],
    hydrograph: tuple[float, ...],
    pet_percentile: int,
    sm_percentile: int,
    gw_percentile: int,
    output_path: Path,
    animation: bool,
    tiff_writer: Literal['rasterio', 'large_image'],
) -> None:
    logging.basicConfig(level=logging.INFO)

    logger.info((
        f'Inputs: {initial_conditions_id=}, {time_period=}, {annual_probability=}, {hydrograph=}, '
        f'{pet_percentile=}, {sm_percentile=}, {gw_percentile=}, '
        f'{output_path=}, {animation=}'
    ))
    start = time.perf_counter()

    flood = run_sim(
        initial_conditions_id=initial_conditions_id,
        time_period=time_period,
        annual_probability=annual_probability,
        hydrograph_name=hydrograph_name,
        hydrograph=hydrograph if hydrograph else None,
        pet_percentile=pet_percentile,
        sm_percentile=sm_percentile,
        gw_percentile=gw_percentile,
    )

    write_multiframe_geotiff(
        flood_results=flood,
        output_path=output_path / 'flood_simulation.tif',
        writer=tiff_writer,
    )
    logger.info(f'Done in {time.perf_counter() - start} seconds.')

    if animation:
        animate_results(
            flood_results=flood,
            output_path=output_path / 'animation.gif',
        )


if __name__ == '__main__':
    main()
