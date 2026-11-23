# Data versions

The main statewide code uses only these unmodified Rachel/FairVote CSVs:

| File | SHA-256 |
| --- | --- |
| Alaska_20261103_US_Governor_11_11.csv | 3d76cd612870025d9c470f78a60d0bde0cd274aeb9a4e57d575704b588f4b8b3 |
| Alaska_20261103_US_House_11_11.csv | b57fad2ef5a8845ba5b3da1eeb3c5e7cfb036c1c174af640b3acee65e45f8b48 |
| Alaska_20261103_US_Senate_11_11.csv | 3f0a1a946f23d2d1195f98c5ee5f123916d5f91ede334397465692d5e7f2d972 |

The files are not redistributed in this code release. Place copies you are
authorized to use in the respective pipeline's `inputs/` directory. The
interpreters check their hashes. Do not replace a snapshot silently or use old
official-JSON extracts to fill names hidden by overvote tokens.

Saved candidate axes, consistency summaries, aggregate ranking profiles,
randomized profiles and diagnostics in `axis_models/` are November 11
derivatives. They contain pattern counts rather than individual ballot IDs.
They do not make every notebook self-contained without the original inputs.

The separate `alaska_presentation_20261117/nov16_house_check/` code uses a later
official House CVR export and a separately archived benchmark. It must not be
mixed with the main November 11 candidate axes. Its archive path, URL and source
hash are explicit in the script; the archive itself is not included here.

Bryan's `CVR_11_18.zip` is a distinct prospective legislative data source. It is
not included or analyzed in this release. Legislative experiments remain pending.
