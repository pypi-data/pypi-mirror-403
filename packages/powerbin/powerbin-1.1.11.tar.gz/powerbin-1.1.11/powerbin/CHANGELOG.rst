Changelog
---------

V1.1.11: Oxford, 26 January 2026
++++++++++++++++++++++++++++++++

- Fixed possible program stop due to a plotting ``alpha > 1`` bug.

V1.1.10: Oxford, 17 November 2025
+++++++++++++++++++++++++++++++++

- Updated citation information to reflect publication in MNRAS.

V1.1.9: Oxford, 09 October 2025
+++++++++++++++++++++++++++++++

- Added a fast, vectorized code path for additive (array) capacities; callable
  capacities remain supported.
- Improved bin‑accretion (incremental centroid and r^2 updates) for lower
  runtime and memory use.
- Renamed and clarified key attributes (capacity_spec, pixel_capacity,
  bin_capacity) and updated docs/examples.
- Miscellaneous bug fixes and robustness improvements.

V1.0.6: Oxford, 17 September 2025
+++++++++++++++++++++++++++++++++

- Initial release.

