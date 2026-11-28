# T-018A1 baseline report (WE-03A, headless)

All values are MEASURED_HEADLESS: CPU submission time of `animate()` in software GL (SwiftShader, 2 vCPU shared host). They are not device FPS and not VRAM. Texture bytes are an RGBA8 + mip estimate, not VRAM.

- 153.0.8010.12 / playwright 1.63.0 / commit 8e07db622991 / CACHE vh-2026-11-27-02; combinations 48/48, repeat sessions 16/16
- method: fresh Chrome per session, 20 warm-up + 120 recorded frames, dt 1/60, dayCycle off, fpsCap 0, 800x450; frame time = CPU time of one `animate()` call

| preset/location/time | draw calls | triangles (all passes) | shadow tri | frame ms P50/P95/P99/max | bodies | shapes |
|---|---|---|---|---|---|---|
| DESKTOP_HIGH/B1/12:00 | 61 | 545,183 | 522,224 | 21.6/35/68.5/77 | 625 | 4153 |
| DESKTOP_HIGH/B1/23:00 | 45 | 45,711 | 22,752 | 23/32.9/55.7/82.4 | 625 | 4153 |
| DESKTOP_HIGH/B2/12:00 | 95 | 2,136,015 | 1,520,776 | 22.4/38/47.1/85.2 | 625 | 4153 |
| DESKTOP_HIGH/B2/23:00 | 105 | 2,150,331 | 1,535,092 | 20.1/33/50.8/82.3 | 625 | 4153 |
| DESKTOP_HIGH/B3/12:00 | 1291 | 7,243,986 | 1,936,732 | 40.9/64.8/71.7/80.1 | 633 | 4161 |
| DESKTOP_HIGH/B3/23:00 | 1315 | 7,056,478 | 1,744,520 | 33.9/51.7/60.6/63.6 | 633 | 4161 |
| DESKTOP_HIGH/CBD/12:00 | 889 | 6,138,350 | 2,434,028 | 41.5/75.3/83.1/89 | 648 | 4176 |
| DESKTOP_HIGH/CBD/23:00 | 1041 | 6,390,532 | 2,681,506 | 31.8/64/77.3/94.1 | 648 | 4176 |
| DESKTOP_HIGH/SiteA/12:00 | 1369 | 6,931,130 | 1,800,604 | 35.1/55.7/67/75.2 | 632 | 4160 |
| DESKTOP_HIGH/SiteA/23:00 | 1373 | 6,699,802 | 1,564,572 | 33.4/54.8/62.7/63 | 632 | 4160 |
| DESKTOP_HIGH/Suburbs/12:00 | 418 | 4,485,441 | 1,660,348 | 51.3/93.5/121.9/6123.1 | 722 | 4250 |
| DESKTOP_HIGH/Suburbs/23:00 | 520 | 4,725,857 | 1,896,060 | 43.1/59.6/72.4/77.1 | 722 | 4250 |
| PHONE_LOW/B1/12:00 | 16 | 7,050 | 5,516 | 8.8/14.4/19.1/19.3 | 505 | 4040 |
| PHONE_LOW/B1/23:00 | 14 | 2,386 | 852 | 9.4/18.1/19.8/20 | 505 | 4040 |
| PHONE_LOW/B2/12:00 | 22 | 171,526 | 7,544 | 8.2/16.8/22/23.8 | 505 | 4040 |
| PHONE_LOW/B2/23:00 | 29 | 185,096 | 21,114 | 8.3/14.1/18.5/33.3 | 505 | 4040 |
| PHONE_LOW/B3/12:00 | 474 | 779,584 | 63,818 | 17.6/34.8/49.5/50.7 | 508 | 4043 |
| PHONE_LOW/B3/23:00 | 480 | 789,172 | 71,054 | 15.6/26.4/35.2/37.9 | 508 | 4043 |
| PHONE_LOW/CBD/12:00 | 317 | 672,908 | 107,354 | 16.3/35.3/50.6/61.6 | 533 | 4068 |
| PHONE_LOW/CBD/23:00 | 319 | 678,120 | 110,214 | 15.6/33.1/40.6/51.1 | 533 | 4068 |
| PHONE_LOW/SiteA/12:00 | 495 | 790,076 | 63,818 | 15.6/32.4/36.5/42.1 | 507 | 4042 |
| PHONE_LOW/SiteA/23:00 | 488 | 748,646 | 20,036 | 20.7/35.1/42.6/45 | 507 | 4042 |
| PHONE_LOW/Suburbs/12:00 | 150 | 676,106 | 50,480 | 17.8/31.1/42.6/49.7 | 549 | 4084 |
| PHONE_LOW/Suburbs/23:00 | 169 | 725,912 | 97,934 | 16.8/30.5/44.3/46 | 549 | 4084 |
| PHONE_MED/B1/12:00 | 31 | 27,526 | 16,040 | 12.3/24.4/35.2/38 | 524 | 4069 |
| PHONE_MED/B1/23:00 | 29 | 22,862 | 11,376 | 13.6/25.2/28.5/31.2 | 524 | 4069 |
| PHONE_MED/B2/12:00 | 45 | 584,650 | 410,128 | 12.8/25.4/27/27.4 | 524 | 4069 |
| PHONE_MED/B2/23:00 | 48 | 590,956 | 416,434 | 11.5/22/23.2/27.8 | 524 | 4069 |
| PHONE_MED/B3/12:00 | 590 | 2,324,502 | 463,986 | 18.4/35/48.4/66.8 | 529 | 4074 |
| PHONE_MED/B3/23:00 | 608 | 2,325,610 | 462,742 | 20.1/36.7/41.7/46.1 | 529 | 4074 |
| PHONE_MED/CBD/12:00 | 372 | 2,051,716 | 722,486 | 21.2/41.1/48.9/50.6 | 552 | 4097 |
| PHONE_MED/CBD/23:00 | 386 | 2,059,806 | 728,224 | 23/38.3/43.4/46.8 | 552 | 4097 |
| PHONE_MED/SiteA/12:00 | 594 | 2,069,366 | 459,490 | 18.7/35.8/47.3/57.1 | 529 | 4074 |
| PHONE_MED/SiteA/23:00 | 635 | 2,236,168 | 417,850 | 18.8/36.3/44.6/48.5 | 529 | 4074 |
| PHONE_MED/Suburbs/12:00 | 150 | 1,216,921 | 58,628 | 26.8/44.3/62.3/63.1 | 568 | 4113 |
| PHONE_MED/Suburbs/23:00 | 193 | 1,659,181 | 498,536 | 18/33.1/43.3/45.5 | 568 | 4113 |
| TABLET_MED/B1/12:00 | 31 | 27,526 | 16,040 | 14.2/23.9/48.9/52.7 | 526 | 4075 |
| TABLET_MED/B1/23:00 | 29 | 22,862 | 11,376 | 12.5/23.8/38.1/48.7 | 526 | 4075 |
| TABLET_MED/B2/12:00 | 45 | 584,650 | 410,128 | 12.2/21.7/30/44.3 | 526 | 4075 |
| TABLET_MED/B2/23:00 | 48 | 590,956 | 416,434 | 12.2/19.2/23.8/24.5 | 526 | 4075 |
| TABLET_MED/B3/12:00 | 590 | 2,324,502 | 463,986 | 21.7/41.7/52.2/55.3 | 530 | 4079 |
| TABLET_MED/B3/23:00 | 601 | 2,324,278 | 461,410 | 23.1/42.1/46.6/55.6 | 530 | 4079 |
| TABLET_MED/CBD/12:00 | 374 | 2,100,828 | 771,598 | 23.1/43.1/12778.7/12953 | 554 | 4103 |
| TABLET_MED/CBD/23:00 | 387 | 2,059,808 | 728,226 | 20.2/37.4/47/28599.8 | 554 | 4103 |
| TABLET_MED/SiteA/12:00 | 633 | 2,275,452 | 459,490 | 24.1/58.8/68.2/75.9 | 531 | 4080 |
| TABLET_MED/SiteA/23:00 | 640 | 2,238,200 | 419,882 | 21.6/41.1/50.5/51.3 | 531 | 4080 |
| TABLET_MED/Suburbs/12:00 | 150 | 1,216,921 | 58,628 | 18.9/30.9/34.7/40.9 | 569 | 4118 |
| TABLET_MED/Suburbs/23:00 | 178 | 1,655,235 | 494,590 | 20.2/33.4/41.5/48.7 | 569 | 4118 |

## Physics self-control (two fresh sessions of the same commit, 5 alternating pairs per preset, band 0.909..1.100)

| preset | ratio min | ratio max | status |
|---|---|---|---|
| PHONE_LOW | 0.89474 | 1.05376 | INCONCLUSIVE |
| PHONE_MED | 0.96087 | 1.09434 | STABLE |
| TABLET_MED | 0.93651 | 1.35088 | INCONCLUSIVE |
| DESKTOP_HIGH | 0.9702 | 0.99012 | STABLE |

## Repeat sessions (B3 and CBD, day/night, 4 presets)

- draw calls and triangles identical in every repeat: True
- frame-time P50 repeat ratio range [0.6944, 1.1902]; usable as a hard gate: False (INCONCLUSIVE otherwise)
- longest frames [ms, key]: [[28599.8, 'TABLET_MED/CBD/23:00'], [26742.1, 'TABLET_MED/CBD/23:00'], [24962.2, 'TABLET_MED/CBD/12:00']]

## Resource estimate ranges across the 12 scenes per preset

- PHONE_LOW: geometry [18.9, 22.4] MiB, texture [33.4, 49.4] MiB, bodies [505, 549]
- PHONE_MED: geometry [109.0, 111.9] MiB, texture [388.3, 388.3] MiB, bodies [524, 568]
- TABLET_MED: geometry [109.6, 109.6] MiB, texture [388.3, 388.3] MiB, bodies [526, 569]
- DESKTOP_HIGH: geometry [279.7, 279.7] MiB, texture [388.3, 388.3] MiB, bodies [625, 722]
