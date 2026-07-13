"""PNG asset loading tests."""

import pygame

import config
from utils.assets import clear_asset_cache, load_image, load_sprite_grid, load_sprite_sheet


def test_load_image_returns_cached_alpha_surface():
    clear_asset_cache()

    first = load_image("sprites/moonspace/laurel_tree.png")
    second = load_image("sprites/moonspace/laurel_tree.png")

    assert first is second
    assert first.get_flags() & pygame.SRCALPHA
    assert first.get_size() == (176, 220)


def test_load_sprite_sheet_slices_player_frames():
    clear_asset_cache()

    frames = load_sprite_sheet("sprites/moonspace/player_envoy.png", 16, 24)

    assert len(frames) == 8
    assert {frame.get_size() for frame in frames} == {(16, 24)}


def test_load_sprite_grid_slices_large_player_frames():
    clear_asset_cache()

    frames = load_sprite_grid("sprites/moonspace/player_envoy_large.png", 42, 62, 4, 4)

    assert len(frames) == 4
    assert {len(row) for row in frames} == {4}
    assert {frame.get_size() for row in frames for frame in row} == {(42, 62)}


def test_scene_background_assets_match_game_surface():
    clear_asset_cache()

    menu = load_image("sprites/moonspace/main_menu_bg.png")
    transition = load_image("sprites/moonspace/scene_transition_screen.png")
    found_face = load_image("sprites/moonspace/transition_found_you_face.png")
    courtyard = load_image("sprites/moonspace/courtyard_bg_large.png")

    assert menu.get_size() == (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    assert transition.get_size() == (config.SCREEN_WIDTH, config.SCREEN_HEIGHT)
    assert found_face.get_size() == (92, 112)
    assert courtyard.get_size() == (config.MAP_WIDTH, config.MAP_HEIGHT)


def test_user_confirmed_gate_and_transition_reference_assets_load():
    clear_asset_cache()

    gate_closed = load_image("sprites/moonspace/backgrounds/courtyard_gate_closed.png")
    gate_open = load_image("sprites/moonspace/backgrounds/courtyard_gate_open.png")
    monitor_sheet = load_image("sprites/moonspace/sheets/scene_transition_monitor_24frames.png")
    moon_pool = load_image("sprites/moonspace/moon_pool_large.png")

    assert gate_closed.get_size() == (1672, 941)
    assert gate_open.get_size() == (1672, 941)
    assert monitor_sheet.get_size() == (1448, 1086)
    assert moon_pool.get_size() == (144, 144)
    assert all(moon_pool.get_at(point).a == 0 for point in ((0, 0), (143, 0), (0, 143), (143, 143)))


def test_user_reference_assets_are_preserved_byte_for_byte():
    from pathlib import Path

    reference_dir = Path("assets/source/user_references/2026-07-10")
    pairs = [
        ("yutu_be_cg.png", "assets/sprites/moonspace/cg/be_yutu_pollution.png"),
        ("courtyard_gate_closed_reference.png", "assets/sprites/moonspace/backgrounds/courtyard_gate_closed.png"),
        ("courtyard_gate_open_reference.png", "assets/sprites/moonspace/backgrounds/courtyard_gate_open.png"),
        (
            "scene_transition_monitor_24frames_reference.png",
            "assets/sprites/moonspace/sheets/scene_transition_monitor_24frames.png",
        ),
    ]

    for reference_name, runtime_path in pairs:
        assert (reference_dir / reference_name).read_bytes() == Path(runtime_path).read_bytes()

    assert (reference_dir / "moon_pool_model_reference.png").stat().st_size > 100_000


def test_user_reference_assets_are_preserved_without_visual_edits():
    from pathlib import Path

    reference_dir = Path("assets/source/user_references/2026-07-10")
    exact_pairs = [
        ("yutu_be_cg.png", "assets/sprites/moonspace/cg/be_yutu_pollution.png"),
        ("courtyard_gate_closed_reference.png", "assets/sprites/moonspace/backgrounds/courtyard_gate_closed.png"),
        ("courtyard_gate_open_reference.png", "assets/sprites/moonspace/backgrounds/courtyard_gate_open.png"),
        (
            "scene_transition_monitor_24frames_reference.png",
            "assets/sprites/moonspace/sheets/scene_transition_monitor_24frames.png",
        ),
    ]

    assert (reference_dir / "moon_pool_model_reference.png").stat().st_size > 100_000
    for reference_name, runtime_path in exact_pairs:
        assert (reference_dir / reference_name).read_bytes() == Path(runtime_path).read_bytes()


def test_courtyard_sky_has_no_red_moon_glow():
    clear_asset_cache()

    courtyard = load_image("sprites/moonspace/courtyard_bg_large.png")
    red_sky_pixels = 0
    sampled = 0
    sky_height = 80
    for x in range(0, courtyard.get_width(), 4):
        for y in range(0, sky_height, 4):
            r, g, b, _ = courtyard.get_at((x, y))
            sampled += 1
            if r > 80 and r > g * 1.7 and r > b * 1.25:
                red_sky_pixels += 1

    assert red_sky_pixels / sampled < 0.01


def test_home_tutorial_sky_has_no_red_moon_glow():
    clear_asset_cache()
    home = load_image("sprites/moonspace/home_tutorial_bg.png")
    red_sky_pixels = 0
    sampled = 0
    for x in range(0, home.get_width(), 2):
        for y in range(0, min(120, home.get_height()), 2):
            r, g, b, _ = home.get_at((x, y))
            sampled += 1
            if r > 100 and r > g * 1.45 and r > b * 1.25:
                red_sky_pixels += 1
    assert red_sky_pixels / sampled < 0.002


def test_imagegen_source_atlases_are_preserved():
    scene = config.__file__
    _ = scene
    from pathlib import Path

    source_dir = Path("assets/source/imagegen")

    assert (source_dir / "moonspace_scene_atlas.png").stat().st_size > 1_000_000
    assert (source_dir / "moonspace_sprite_atlas.png").stat().st_size > 500_000


def test_confirmed_mainline_visual_resources_load():
    clear_asset_cache()

    resource_paths = [
        "sprites/moonspace/portraits/chang_e_dialog.png",
        "sprites/moonspace/portraits/wugang_dialog.png",
        "sprites/moonspace/portraits/yutu_dialog.png",
        "sprites/moonspace/portraits/dialog_portraits_large.png",
        "sprites/moonspace/props/registration_desk.png",
        "sprites/moonspace/sheets/chang_e_16frames.png",
        "sprites/moonspace/sheets/chang_e_16frames_transparent.png",
        "sprites/moonspace/backgrounds/guanghan_hall.png",
        "sprites/moonspace/backgrounds/guanghan_hall_curtain.png",
        "sprites/moonspace/backgrounds/courtyard_expanded_closed.png",
        "sprites/moonspace/backgrounds/courtyard_expanded_open.png",
        "sprites/moonspace/home_tutorial_bg_open.png",
        "sprites/moonspace/props/broken_jade_slip.png",
        "sprites/moonspace/cg/report_staging.png",
        "sprites/moonspace/cg/he_earth_return.png",
        "sprites/moonspace/cg/be_wugang_pollution.png",
        "sprites/moonspace/cg/be_yutu_pollution.png",
        "sprites/moonspace/cg/be_double_pollution.png",
        "sprites/moonspace/cg/be_wait_trap.png",
    ]

    for path in resource_paths:
        image = load_image(path)
        assert image.get_width() > 0
        assert image.get_height() > 0


def test_confirmed_expanded_scene_backgrounds_match_scene_world_sizes():
    courtyard = load_image("sprites/moonspace/backgrounds/courtyard_expanded_closed.png")
    hall = load_image("sprites/moonspace/backgrounds/guanghan_hall_curtain.png")

    assert courtyard.get_size() == (config.COURTYARD_WIDTH, config.COURTYARD_HEIGHT)
    assert hall.get_size() == (config.GUANGHAN_WIDTH, config.GUANGHAN_HEIGHT)


def test_confirmed_registration_desk_has_transparent_background():
    desk = load_image("sprites/moonspace/props/registration_desk.png")

    assert desk.get_flags() & pygame.SRCALPHA
    assert desk.get_at((0, 0)).a == 0
    assert desk.get_bounding_rect(min_alpha=8).width > desk.get_width() // 2


def test_chang_e_world_sheet_has_real_transparency_and_no_green_screen():
    sheet = load_image("sprites/moonspace/sheets/chang_e_16frames_transparent.png")

    assert sheet.get_at((0, 0)).a == 0
    assert sheet.get_bounding_rect(min_alpha=8).height > sheet.get_height() // 2
    green_pixels = sum(
        1
        for y in range(0, sheet.get_height(), 8)
        for x in range(0, sheet.get_width(), 8)
        if (color := sheet.get_at((x, y))).a > 0
        and color.g > 120
        and color.g > color.r + 40
        and color.g > color.b + 40
    )
    assert green_pixels == 0


def test_confirmed_mainline_imagegen_sources_are_preserved():
    from pathlib import Path

    source_dir = Path("assets/source/imagegen/candidates")
    confirmed_sources = [
        "candidate_mainline_chang_e_dialog_confirmed_v1.png",
        "candidate_mainline_wugang_dialog_confirmed_v1.png",
        "candidate_mainline_yutu_dialog_confirmed_v1.png",
        "candidate_mainline_chang_e_16frames_confirmed_v1.png",
        "candidate_mainline_guanghan_hall_confirmed_v1.png",
        "candidate_mainline_report_staging_confirmed_v1.png",
        "candidate_mainline_he_earth_return_confirmed_v1.png",
        "candidate_mainline_be_wugang_pollution_confirmed_v1.png",
        "candidate_mainline_be_yutu_pollution_confirmed_v1.png",
        "candidate_mainline_be_double_pollution_confirmed_v1.png",
        "candidate_mainline_be_wait_trap_confirmed_v1.png",
    ]

    for filename in confirmed_sources:
        assert (source_dir / filename).stat().st_size > 100_000
