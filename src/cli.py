
import click
import yaml
from pathlib import Path

from .ndwi import compute_ndwi_rasters
from .change_detection import change_difference
from .stats import summarize_water
from .viz import save_quicklook

def load_cfg(path):
    with open(path, 'r') as f:
        return yaml.safe_load(f)

@click.group()
@click.option('--config', default='config/config.yaml', help='Path to config YAML.')
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj['cfg'] = load_cfg(config) if Path(config).exists() else {}

@cli.command('ndwi')
@click.option('--input', required=True, help='Path to green-band raster (or pre-stacked).')
@click.option('--nir', required=True, help='Path to NIR-band raster if separate.')
@click.option('--out', required=True, help='Output NDWI GeoTIFF.')
@click.pass_context
def ndwi_cmd(ctx, input, nir, out):
    cfg = ctx.obj['cfg']
    compute_ndwi_rasters(input, nir, out, cfg=cfg)
    click.echo(f"Saved NDWI to {out}")

@cli.command('change-detect')
@click.option('--t1', required=True, help='NDWI raster at time 1')
@click.option('--t2', required=True, help='NDWI raster at time 2')
@click.option('--out', required=True, help='Output change raster (GeoTIFF)')
@click.option('--threshold', default=None, type=float, help='Optional absolute threshold')
@click.pass_context
def change_cmd(ctx, t1, t2, out, threshold):
    cfg = ctx.obj['cfg']
    change_difference(t1, t2, out, threshold=threshold, cfg=cfg)
    click.echo(f"Saved change map to {out}")

@cli.command('summarize')
@click.option('--mask', required=True, help='Water mask raster (0/1).')
@click.option('--out_csv', required=True, help='CSV output path.')
@click.pass_context
def summarize_cmd(ctx, mask, out_csv):
    summarize_water(mask, out_csv)
    click.echo(f"Saved stats to {out_csv}")

@cli.command('quicklook')
@click.option('--raster', required=True, help='Raster path to visualize.')
@click.option('--out_png', required=True, help='PNG path to save.')
@click.pass_context
def quicklook_cmd(ctx, raster, out_png):
    save_quicklook(raster, out_png)
    click.echo(f"Saved preview to {out_png}")

if __name__ == '__main__':
    cli()
