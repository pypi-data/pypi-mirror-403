import os
import numpy as np
import healpy as hp
import matplotlib.pyplot as plt

from hicrafter.generator import HIGenerator

def plot_map(m, title, outpath):
    plt.figure(figsize=(8, 5))
    hp.mollview(
        m,
        fig=plt.gcf().number,
        title=title,
        unit="T_HI (arb.)",
        cmap="viridis",
        min=np.percentile(m, 1),
        max=np.percentile(m, 99),
    )
    hp.graticule()
    plt.savefig(outpath, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Saved {outpath}")

os.makedirs("tutorial_outputs", exist_ok=True)

gen = HIGenerator(
    nside=32,
    z_min=0.40,
    z_max=0.45,
    nbins=1,
    sigmaz0=1e-4,
    beam_deg=None,
    noise=False,
    zebras=False,
    seed=1,
)

hi_base = gen.generate_map()
plot_map(
    hi_base,
    title="Baseline HI Intensity Map",
    outpath="tutorial_outputs/step1_baseline.png",
)

gen_beam = HIGenerator(
    nside=32,
    z_min=0.40,
    z_max=0.45,
    nbins=1,
    sigmaz0=1e-4,
    beam_deg=1.5,   # degrees
    noise=False,
    zebras=False,
    seed=1,
)

hi_beam = gen_beam.generate_map()
plot_map(
    hi_beam,
    title="HI Map with Beam Smoothing (1.5°)",
    outpath="tutorial_outputs/step2_beam.png",
)

gen_noise = HIGenerator(
    nside=32,
    z_min=0.40,
    z_max=0.45,
    nbins=1,
    sigmaz0=1e-4,
    beam_deg=1.5,
    noise=True,
    noise_level=1.0,
    zebras=False,
    seed=1,
)

hi_noise = gen_noise.generate_map()
plot_map(
    hi_noise,
    title="HI Map with Beam + Noise",
    outpath="tutorial_outputs/step3_noise.png",
)

gen_zebra = HIGenerator(
    nside=32,
    z_min=0.40,
    z_max=0.45,
    nbins=1,
    sigmaz0=1e-4,
    beam_deg=1.5,
    noise=True,
    noise_level=1.0,
    zebras=True,
    seed=1,
)

hi_zebra = gen_zebra.generate_map()
plot_map(
    hi_zebra,
    title="HI Map with Beam + Noise + Zebras",
    outpath="tutorial_outputs/step4_zebras.png",
)
