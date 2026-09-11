# Production weight downloads

These scripts use GNU `wget` for weight transfer. Hugging Face downloads are
pinned to immutable commit hashes and use API-provided byte sizes as their
manifest authority. Completed files are skipped. Incomplete files remain as
`.part` files and continue with `wget --continue` on the next invocation.

Run all production downloads only after at least 230 GiB is free:

```bash
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_all_production_weights.sh
```

Or run one model at a time:

```bash
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_qwen3_vl_32b_production.sh
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_wan22_s2v.sh
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_seedvr2_7b_production.sh
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_latentsync_1_6_production.sh
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_codeformer_production.sh
/Users/oldowl/PycharmProjects/little_planet_wonders/scripts/models/download_practical_rife_production.sh
```

Approximate pinned payloads before filesystem and runtime overhead:

- Qwen3-VL 32B Instruct: 62.14 GiB
- Wan 2.2 S2V 14B BF16 bundle: 42.60 GiB
- SeedVR2 7B base, sharp, and VAE: 62.32 GiB
- LatentSync 1.6 and auxiliary weights: 8.97 GiB
- CodeFormer and face helpers: additional download
- Practical-RIFE v4.25: additional download

The known Hugging Face payload is approximately 176 GiB. The aggregate script
requires 230 GiB free to leave room for archives, extraction, manifests, and a
safety margin.

Set `HF_TOKEN` when a repository requires authenticated access. Individual
destination paths can be overridden with the `LPW_*_PRODUCTION_DIR` variables
declared in each wrapper. `LPW_WGET` and `LPW_PYTHON` override executable paths.
The hardware-neutral Wan entry point uses `LPW_WAN_S2V_MODEL_DIR` and defaults
to `runtime/models/Wan2.2-S2V-14B`, matching the episode render launchers.

The scripts never replace a valid completed file with a partial response. A
download is first written to `<filename>.part`, checked against the pinned remote
byte count, and atomically renamed only after validation. The aggregate command
runs the production pipeline check after all transfers finish.
