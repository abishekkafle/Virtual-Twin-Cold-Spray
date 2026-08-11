# CEL-P4 qualified production DOE protocol

The production matrix contains 44 cases: 11 uniformly spaced velocities for
each of four velocity-qualified material pairs. Eleven valid CEL-P3 anchors are
reused by immutable ODB path and 33 new cases are generated.

| Pair | Range (m/s) | Levels | Reused anchors |
|---|---:|---:|---:|
| Cu -> Cu | 300-850 | 11 | 300, 575, 850 |
| Al6061 -> SS304 | 500-725 | 11 | 500, 725 |
| Ti6Al4V -> Ti6Al4V | 500-1150 | 11 | 500, 825, 1150 |
| Inconel718 -> Ti6Al4V | 500-1150 | 11 | 500, 825, 1150 |

Every new case uses the frozen 24-EPD, 80-ns, 15D-substrate, 1.5D-deep and
1.5D-lateral Eulerian geometry with combined hourglass weight 0.5 and no mass
scaling. The failed 950 m/s Al point and excluded SS316L-on-Al6061 pair are
outside the design space.

All numerical gates apply case by case. At-or-above-melt cases are excluded
from ML; near-melt and PEEQ review flags remain attached. A production pass
requires at least 9 ML candidates per pair and 36 overall, and authorizes only
a simulation surrogate with grouped material-pair validation.
