"""Render the real repair-hall game flow with isolated disposable saves."""
from pathlib import Path
import os
import sys
import tempfile

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import pygame
from core.game import Game
from core.save_manager import SaveManager


def preview(destination: Path):
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="moon-repair-qa-") as save_dir:
        game = Game()
        game.save_manager = SaveManager(save_dir)
        game.current_slot_id = 1
        data = game.save_manager.default_save(1)
        data.update(opening_seen=True, home_tutorial_done=True, scene="playing")
        game._apply_save_data(data)
        game.mode = game.MODE_PLAYING
        game.player.rect.midbottom = game.repair_hall.COURTYARD_RETURN
        game.player.position.xy = game.player.rect.topleft
        game._save_checkpoint("qa_start")

        def snap(name):
            game.draw()
            pygame.image.save(pygame.transform.scale(game.game_surface, (960, 540)), destination / (name + ".png"))

        def at(zone):
            game.player.rect.midbottom = zone.center
            game.player.position.xy = game.player.rect.topleft

        def key(key):
            game.input_manager.begin_frame()
            game.input_manager.process_event(pygame.event.Event(pygame.KEYDOWN, key=key))
            game.update(1/60)
            game.input_manager.begin_frame()

        snap("01-courtyard-entrance")
        game.player.rect.midbottom = game.repair_door.RIGHT_ZONE.center
        game.player.position.xy = game.player.rect.topleft
        key(pygame.K_e)
        assert not game.repair_door.active
        snap("01-right-toad-static")
        game.player.rect.midbottom = game.repair_door.LEFT_ZONE.center
        game.player.position.xy = game.player.rect.topleft
        # The scripted preview places the player directly at the control;
        # seed the enter-zone state just as a real approach would do.
        game.tree_bow_zone.update(0.0, game.player.rect)
        key(pygame.K_e)
        assert game.repair_door.active
        snap("01a-lamp-initial")
        for _ in range(3):
            key(pygame.K_a)
        snap("01b-moon-aligned")
        # The existing Laurel rule is the second half of this puzzle. The
        # aligned shadow cannot be verified until its anomaly opens.
        game._on_tree_bleeding(source="qa")
        game.update(1 / 60)
        snap("01b-laurel-anomaly")
        game.update(.75)
        snap("01b-shadow-lag")
        game.update(.9)
        snap("01b-shadow-looking-back")
        game.update(.6)
        game.update(1.3)
        assert game.repair_door.unlocked
        assert game.current_save_data["checkpoint_id"] == "qa_start"
        snap("01c-open-lit-door")
        key(pygame.K_ESCAPE)
        game.player.rect.midbottom = game.repair_hall.COURTYARD_RETURN
        game.player.position.xy = game.player.rect.topleft
        snap("01d-west-open-world")
        key(pygame.K_e)
        assert game.mode == game.MODE_REPAIR
        assert game.repair_hall.trial.remaining == 60
        snap("02-entry")
        at(game.repair_hall.table_zone)
        key(pygame.K_e)
        snap("03-briefing")
        while game.dialog_box.active:
            key(pygame.K_e)
        key(pygame.K_e)
        snap("04-select")
        for _ in range(game.repair_hall.cracked_slot):
            key(pygame.K_d)
        key(pygame.K_e)
        at(game.repair_hall.light_zone)
        key(pygame.K_e)
        game.repair_hall.trial.set_orientation(
            game.repair_hall.trial.LIGHT_YAW,
            game.repair_hall.trial.LIGHT_PITCH,
        )
        game._observe_repair_piece()
        snap("05-inspect-cracked")
        key(pygame.K_e)
        at(game.repair_hall.statue_zone)
        key(pygame.K_e)
        snap("06-statue")
        while game.dialog_box.active:
            key(pygame.K_e)
        at(game.repair_hall.tray_zone)
        key(pygame.K_e)
        game.update(3.5)
        snap("07-sealing")
        game.update(2.1)
        snap("08-complete")
        assert game.mainline["repair_checked"]
        assert game.current_save_data["checkpoint_id"] == "repair_completed"
        game.mainline["repair_checked"] = False
        game._enter_repair_hall()
        game._begin_repair_trial()
        while game.dialog_box.active:
            key(pygame.K_e)
        game.repair_hall.trial.pick_up(0)
        game._submit_repair_piece()
        game.update(.65)
        snap("09-toad-death")
        game.update(1.6)
        assert game.mainline["repair_checked"]
        assert game.mode == game.MODE_REPAIR
        snap("10-checkpoint-restored")
        pygame.quit()
    print(f"Verified free-rotation examination, sealing, death and checkpoint recovery; previews: {destination.resolve()}")


if __name__ == "__main__":
    preview(Path(sys.argv[1]) if len(sys.argv) > 1 else Path("tmp/repair-hall-qa"))
