# MoonSpace BGM provenance

This inventory contains the approved main-menu baseline, the three scene
tracks, and the two ending tracks selected for the current MoonSpace mapping.
The previous procedural route prototypes were removed from the project on
2026-09-02 at the project owner's request.

| File | Role | Format | SHA-256 |
| --- | --- | --- | --- |
| `bgm_main_menu.wav` | Approved main menu and save-menu baseline | 72.000 s, stereo, 44,100 Hz, 16-bit PCM WAV | `5aef2daebccf822f62d99584b6789ff88b89997ed7f0d0a9c4e66520f7492b49` |
| `bgm_home_dream_2_ambience.mp3` | `home` 教程 / 月谷归路（图一） | ~129.463 s, MP3 | `e0e92f82ceb608a2ec340daaa1649a860f5f44216cd0ecbe0219d825449c531` |
| `bgm_guanghan_square_the_surreal_truth.mp3` | 广寒宫广场（用户指定） | ~58.932 s, MP3 | `fe4a94a95aa8f281185f09818d1c9f4cb0da5cd70350bf13b43b5a3c779ce691` |
| `bgm_guanghan_palace_space_ambient.mp3` | 广寒宫殿内（图二） | ~600.033 s, MP3 | `2f9d8bfb789a3cca03376ebf480f7212e51ba8798176475c8dac3a2339f3a60f` |
| `bgm_ending_he_somnium.mp3` | 交接完成并抵达月谷后的 HE / `he_return_earth` | ~219.063 s, MP3 | `FE6055D9EB118FAAFEB2EBB30E453B2B288C0C22D67331200C922FEFB7D6A371` |
| `bgm_ending_be_insistent.ogg` | 交接完成后尚未离开月宫，以及全部 BE / `be_*` 结局 | ~128.693 s, OGG | `C5E0ECCB09379301C56E95C6B6586E842BE0EF363938B8D1062518280DA99CFB` |

## Active scene mapping

- `main_menu` and `save_menu` → `bgm_main_menu.wav`
- `home` → `bgm_home_dream_2_ambience.mp3`
- `playing` / 广寒宫广场 → `bgm_guanghan_square_the_surreal_truth.mp3`
- `guanghan` / 广寒宫殿内 → `bgm_guanghan_palace_space_ambient.mp3`
- 交接完成但仍在 `guanghan` / `playing` → `bgm_ending_be_insistent.ogg`
- 清白路线抵达 `home` / 月谷祭坛，以及 HE `ending_cg` → `bgm_ending_he_somnium.mp3`
- BE `ending_cg`（`be_wugang`、`be_yutu`、`be_double`、`be_change`，旧别名 `be_laurel_mixed`） → `bgm_ending_be_insistent.ogg`
- 污染标记不再切换到单独污染 BGM；所在场景继续使用上述场景音乐。
- `opening` → `bgm_home_dream_2_ambience.mp3`（与随后月谷教程连续播放，不重启）

## Selected external sources

### `bgm_home_dream_2_ambience.mp3`

- Title: `Dream 2 Ambience`
- Author: `TokyoGeisha`
- License: `CC0`; the source page says no credit is necessary.
- Source page: https://opengameart.org/content/dream-2-ambience
- Source file: `Dream 2 (Ambience)_0.mp3`

### `bgm_guanghan_square_the_surreal_truth.mp3`

- Title: `The Surreal Truth`
- Author: `Joth`
- License: `CC0`
- Source pack: https://opengameart.org/content/ambience-pack-1-sci-fi-horror
- Source file: `The Surreal Truth.mp3`
- Input: copied from the user-provided local selection on 2026-09-02.

### `bgm_guanghan_palace_space_ambient.mp3`

- Title: `Space ambient`
- Author: `Osmic`
- License: `CC-BY 3.0`; retain an attribution credit in the game credits.
- Source page: https://opengameart.org/content/space-ambient
- Source file: `ville_seppanen-1_g.mp3`

### `bgm_ending_he_somnium.mp3`

- Title: `Somnium`
- Author: `Adiutorium`
- License: `CC0`; the source page permits commercial and non-commercial use and says credit is optional.
- Source page: https://opengameart.org/content/somnium
- Source file: `somnium.mp3`
- Downloaded source SHA-256: `FE6055D9EB118FAAFEB2EBB30E453B2B288C0C22D67331200C922FEFB7D6A371`

### `bgm_ending_be_insistent.ogg`

- Title: `Insistent: background loop`
- Author: `yd`
- License: `CC0`; the source page says the work can be used by anyone for any reason.
- Source page: https://opengameart.org/content/insistent-background-loop
- Source file: `Insistent.ogg`
- Downloaded source SHA-256: `C5E0ECCB09379301C56E95C6B6586E842BE0EF363938B8D1062518280DA99CFB`

## Approved main-menu baseline and CC0 provenance

The project owner approved `bgm_main_menu.wav` on 2026-08-16 as the music for
the main page and as the overall tonal baseline for future MoonSpace music:
large empty space, distant danger, restrained horror, and an ethereal lunar
surface rather than dissonance or synthetic noise.

This file is a derivative edit of the following CC0 source, not a claim of a
wholly original composition:

- Title: `Lost in a bad place (horror ambience loop)`
- Author: `congusbongus`
- License: `CC0 1.0`
- Source page: https://opengameart.org/content/lost-in-a-bad-place-horror-ambience-loop
- Downloaded source file: `lost_2.ogg`
- Downloaded source SHA-256: `ad9a9f39240ef5862d3a6dc5220893926c6873aa0e08a641dadf3f1c0acc2cd4`

The MoonSpace edit reorders the source passages at 33-58, 69-97, and 103-132
seconds with three-second equal-power transitions, narrows excessive stereo
side energy, filters only sub-42 Hz rumble and content above 10.5 kHz, lowers
the mastered level for menu UI, and uses a four-second wrap transition to form
the final 72-second loop. It adds no newly synthesized music or noise layer.
Measured output peak is -9.37 dBFS, RMS is -24.68 dBFS, and no sample clips.

CC0 does not require attribution, but the recommended courtesy credit is:

> `"Lost in a bad place" by congusbongus, CC0 1.0, via OpenGameArt.`

## Repair-hall scare vocal provenance

`repair_scare.wav` is a trimmed and level-normalized derivative of this CC0
source. The edit removes MP3 encoder silence, keeps the complete short attack
vocal, adds only click-prevention fades, and converts it to 44.1 kHz mono PCM.

- Title: `Monster Attack`
- Author: `qubodup`
- License: `CC0 1.0`
- Source page: https://freesound.org/people/qubodup/sounds/442957/
- Downloaded preview: `assets/source/audio/freesound-442957-monster-attack-hq.mp3`
- Downloaded source SHA-256: `E79084B643688AE0B373ED0E3108749E969FFFC87BF7E1A0CDA19AF0E64B628F`
