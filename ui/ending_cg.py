"""结局像素 CG。"""

from __future__ import annotations

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_image
from utils.font import render_text
from utils.pixel_art import draw_filled_rect, draw_line, draw_rect


class EndingCG:
    """结局 CG 播放器，承载 HE 与四个独立坏结局的正式三镜序列。"""

    TOTAL_DURATION = 8.0
    SHOT_RANGES = ((0.0, 2.4), (2.4, 5.2), (5.2, TOTAL_DURATION))
    AUDIO_CUES_BY_ENDING = {
        "he_return_earth": ((0.0, "cg_palace_transition"), (5.2, "cg_earth_arrival")),
        "be_wugang": (
            (0.0, "cg_moon_pool"),
            (2.4, "cg_wugang_axe"),
            (5.2, "cg_laurel_roots"),
        ),
        "be_yutu": ((0.0, "cg_moon_pool"), (2.4, "cg_yutu_pestle")),
        "be_double": (
            (0.0, "cg_moon_pool"),
            (2.4, "cg_wugang_axe"),
            (2.6, "cg_yutu_pestle"),
            (5.2, "cg_laurel_roots"),
        ),
        "be_laurel_mixed": (
            (0.0, "cg_moon_pool"),
            (2.4, "cg_wugang_axe"),
            (2.6, "cg_yutu_pestle"),
            (5.2, "cg_laurel_roots"),
        ),
        "be_change": ((0.0, "cg_palace_transition"), (5.2, "cg_earth_arrival")),
    }
    CAPTIONS_BY_ENDING = {
        "he_return_earth": (
            (0.0, 2.2, "月谷祭坛亮起，月宫的声音在身后合拢。"),
            (2.2, 4.8, "凌霄来使复命已毕，伪装也完成了它的职责。"),
            (4.8, TOTAL_DURATION, "晨光落在地球的房间里，归路终于抵达。"),
        ),
        "be_wugang": (
            (0.0, 2.6, "池水照见的，不再只是来使。"),
            (2.6, 5.2, "斧声从倒影里响起，替你答完了月宫的问题。"),
            (5.2, TOTAL_DURATION, "新的伐桂人，被月桂收下了。"),
        ),
        "be_yutu": (
            (0.0, 2.6, "池水照见的，不再只是来使。"),
            (2.6, 5.2, "杵声从腕骨里响起，药香替你留在了月宫。"),
            (5.2, TOTAL_DURATION, "新的捣药人，被药臼收下了。"),
        ),
        "be_double": (
            (0.0, 2.6, "两份差错在池边合成了一份记录。"),
            (2.6, 5.2, "月桂树伸出根须，把多余的来使拖回树下。"),
            (5.2, TOTAL_DURATION, "树皮上，缓缓多出一个流血的面孔。"),
        ),
        # 兼容旧存档和旧工具调用；新流程写入 be_double。
        "be_laurel_mixed": (
            (0.0, 2.6, "两份差错在池边合成了一份记录。"),
            (2.6, 5.2, "月桂树伸出根须，把多余的来使拖回树下。"),
            (5.2, TOTAL_DURATION, "树皮上，缓缓多出一个流血的面孔。"),
        ),
        "be_change": (
            (0.0, 2.6, "月光尽了，你还在宫中。"),
            (2.6, 5.2, "嫦娥没有催促，只看着流程完成。"),
            (5.2, TOTAL_DURATION, "广寒宫不缺月光，只缺一个留下来等的人。"),
        ),
    }
    SHOT_ASSETS_BY_ENDING = {
        "he_return_earth": (
            "cg/he_earth_return.png",
            "cg/he_02_depart_moon_palace.png",
            "cg/he_03_earth_arrival.png",
        ),
        "be_wugang": (
            "cg/be_wugang_01_pool_axe_reflection.png",
            "cg/be_wugang_02_roots_claim_envoy.png",
            "cg/be_wugang_03_new_lumberjack.png",
        ),
        "be_yutu": (
            "cg/be_yutu_01_rabbit_shadow.png",
            "cg/be_yutu_02_mortar_awakens.png",
            "cg/be_yutu_03_new_medicine_maker.png",
        ),
        "be_double": (
            "cg/be_double_01_records_overlap.png",
            "cg/be_double_02_roots_converge.png",
            "cg/be_double_03_bleeding_tree_face.png",
        ),
        # 兼容旧存档/工具调用，不创建新的正式结局 ID。
        "be_laurel_mixed": (
            "cg/be_double_01_records_overlap.png",
            "cg/be_double_02_roots_converge.png",
            "cg/be_double_03_bleeding_tree_face.png",
        ),
        "be_change": (
            "cg/be_change_01_empty_hall.png",
            "cg/be_change_02_chang_e_closes_path.png",
            "cg/be_change_03_left_under_moonlight.png",
        ),
    }
    ASSET_BY_ENDING = {
        "he_return_earth": "cg/he_earth_return.png",
        "be_wugang": "cg/be_wugang_pollution.png",
        "be_yutu": "cg/be_yutu_pollution.png",
        "be_double": "cg/be_double_pollution.png",
        "be_laurel_mixed": "cg/be_double_pollution.png",
        "be_change": "cg/be_wait_trap.png",
    }

    def __init__(self, audio=None) -> None:
        self.audio = audio
        self.active = False
        self.finished = False
        self.ending_id = ""
        self.time = 0.0
        self._audio_tokens: set[str] = set()

    def start(self, ending_id: str) -> None:
        """开始播放指定结局 CG。"""
        if self.audio is not None:
            self.audio.begin_cg_cycle()
        self.active = True
        self.finished = False
        self.ending_id = ending_id
        self.time = 0.0
        self._audio_tokens.clear()
        self._emit_audio_cues()

    def skip(self) -> None:
        """跳过结局 CG。"""
        self.active = False
        self.finished = True
        if self.audio is not None:
            self.audio.stop_cg_sounds()

    def update(self, dt: float, input_manager: InputManager) -> bool:
        """推进 CG；结束或跳过时返回 True。"""
        if not self.active:
            return self.finished

        if input_manager.was_pressed(config.ACTION_QUIT) or input_manager.was_pressed(config.ACTION_INTERACT):
            self.skip()
            return True

        self.time += max(0.0, dt)
        self._emit_audio_cues()
        if self.time >= self.TOTAL_DURATION:
            self.active = False
            self.finished = True
            if self.audio is not None:
                self.audio.stop_cg_sounds()
            return True
        return False

    def _emit_audio_cues(self) -> None:
        """Trigger every crossed ending-shot cue once."""
        if self.audio is None:
            return
        for boundary, key in self.AUDIO_CUES_BY_ENDING.get(self.ending_id, ()):
            if self.time >= boundary:
                token = f"ending:{self.ending_id}:{boundary}:{key}"
                if token in self._audio_tokens:
                    continue
                self._audio_tokens.add(token)
                self.audio.play_cg_cue(key, token=token)

    def draw(self, surface: pygame.Surface) -> None:
        """绘制结局 CG；优先使用确认后的 PNG 资源。"""
        surface.fill(palette.BLACK)
        if self._draw_sequence_asset(surface):
            pass
        elif self._draw_asset_background(surface):
            pass
        elif self.ending_id == "he_return_earth":
            self._draw_he_return(surface)
        else:
            self._draw_generic_ending(surface)
        self._draw_caption(surface)
        render_text(surface, "E / Esc 跳过", 390, 10, 11, palette.ASH_GRAY)

    def current_caption(self) -> str:
        """返回当前结局字幕。"""
        captions = self.CAPTIONS_BY_ENDING.get(
            self.ending_id,
            self.CAPTIONS_BY_ENDING["he_return_earth"],
        )
        for start, end, caption in captions:
            if start <= self.time < end:
                return caption
        return captions[-1][2]

    def _draw_asset_background(self, surface: pygame.Surface) -> bool:
        """绘制确认后的结局 PNG；缺失时由代码绘制降级。"""
        filename = self.ASSET_BY_ENDING.get(self.ending_id)
        if not filename:
            return False
        try:
            background = load_image(f"sprites/moonspace/{filename}")
        except (FileNotFoundError, pygame.error):
            return False
        if background.get_size() != surface.get_size():
            background = pygame.transform.smoothscale(background, surface.get_size())
        surface.blit(background, (0, 0))
        return True

    def _draw_sequence_asset(self, surface: pygame.Surface) -> bool:
        """按 8 秒节拍绘制当前结局的三个正式镜头。"""
        filenames = self.SHOT_ASSETS_BY_ENDING.get(self.ending_id)
        if not filenames:
            return False

        shot_index = self.shot_index_at(self.time)

        try:
            background = load_image(f"sprites/moonspace/{filenames[shot_index]}")
        except (FileNotFoundError, pygame.error):
            return False
        if background.get_size() != surface.get_size():
            background = pygame.transform.smoothscale(background, surface.get_size())
        surface.blit(background, (0, 0))
        return True

    @classmethod
    def shot_index_at(cls, timer: float) -> int:
        """Return the formal three-shot index for a timestamp."""
        if timer <= 0.0:
            return 0
        for index, (start, end) in enumerate(cls.SHOT_RANGES):
            if start <= timer < end:
                return index
        return len(cls.SHOT_RANGES) - 1

    def _draw_he_return(self, surface: pygame.Surface) -> None:
        """绘制月谷祭坛到地球屏幕的 HE 分镜。"""
        progress = min(1.0, self.time / self.TOTAL_DURATION)
        draw_filled_rect(surface, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.NIGHT_BLACK)
        for i in range(9):
            y = 38 + i * 18
            color = palette.DEEP_BLUE if i % 2 else palette.GROUND_DARK
            draw_line(surface, (18, y), (config.SCREEN_WIDTH - 18, y + int(progress * 12)), color)

        altar_x = config.SCREEN_WIDTH // 2 - 46
        altar_y = 158
        glow_width = int(36 + progress * 170)
        glow = pygame.Surface((glow_width, 28), pygame.SRCALPHA)
        glow.fill((*palette.PALE_MOON, int(42 + progress * 92)))
        surface.blit(glow, (config.SCREEN_WIDTH // 2 - glow_width // 2, altar_y - 10))
        draw_rect(surface, altar_x, altar_y, 92, 34, palette.MOON_WHITE)
        draw_filled_rect(surface, (altar_x + 8, altar_y + 10, 76, 4), palette.PALE_MOON)
        draw_filled_rect(surface, (altar_x + 18, altar_y + 20, 56, 2), palette.POOL_HIGHLIGHT)

        if self.time >= 4.8:
            screen_rect = pygame.Rect(160, 62, 160, 88)
            draw_filled_rect(surface, screen_rect, (10, 14, 20))
            draw_rect(surface, screen_rect.x, screen_rect.y, screen_rect.width, screen_rect.height, palette.MOON_WHITE)
            render_text(surface, "MoonSpace", screen_rect.x + 34, screen_rect.y + 26, 15, palette.PALE_MOON)
            draw_filled_rect(surface, (screen_rect.x + 52, screen_rect.y + 56, 56, 3), palette.DEEP_BLUE)

    def _draw_generic_ending(self, surface: pygame.Surface) -> None:
        """绘制未知结局的保底黑屏。"""
        draw_filled_rect(surface, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.BLACK)

    def _draw_caption(self, surface: pygame.Surface) -> None:
        """绘制底部 CG 字幕。"""
        caption = self.current_caption()
        panel = pygame.Surface((config.SCREEN_WIDTH, 34), pygame.SRCALPHA)
        panel.fill((*palette.BLACK, 180))
        surface.blit(panel, (0, config.SCREEN_HEIGHT - 34))
        render_text(surface, caption, 22, config.SCREEN_HEIGHT - 24, 13, palette.PALE_MOON)
