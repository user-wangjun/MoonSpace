"""开场像素 CG。"""

from __future__ import annotations

import math

import pygame

import config
from core.input_manager import InputManager
from utils import palette
from utils.assets import load_image
from utils.font import render_text
from utils.pixel_art import draw_filled_rect, draw_line, draw_rect


class OpeningCG:
    """第三视角开场 CG：电脑下载、回头望月、血月出云、月光照入房间。"""

    TOTAL_DURATION = 15.0
    # 正式 8 镜序列；时间段保持原开场总时长与字幕节拍不变。
    SHOT_ASSETS = (
        (0.0, 1.8, "cg/opening_01_download_start.png"),
        (1.8, 3.2, "cg/opening_02_download_finish.png"),
        (3.2, 4.8, "cg/opening_03_turn_to_window.png"),
        (4.8, 6.0, "cg/opening_04_blood_moon_emerges.png"),
        (6.0, 7.8, "cg/opening_05_blood_moon_full.png"),
        (7.8, 9.4, "cg/opening_06_moonlight_corrupts_screen.png"),
        (9.4, 12.6, "cg/opening_07_screen_shatters.png"),
        (12.6, TOTAL_DURATION, "cg/opening_08_blackout_crescent.png"),
    )
    CAPTIONS = (
        (0.0, 3.2, "新下载的 MoonSpace，进度条停在了最后一格。"),
        (3.2, 6.0, "窗外升起血月，房间里没有风。"),
        (6.0, 9.4, "云层被红光撕开，月亮像一只睁开的眼。"),
        (9.4, 12.6, "红光照到电脑，也照到你的影子。"),
        (12.6, 14.0, "屏幕开始呼吸，MoonSpace 在里面反过来看你。"),
        (14.0, TOTAL_DURATION, "醒来时，月宫的规条已经刻在面前。"),
    )
    AUDIO_CUES = (
        (0.0, "cg_download_start"),
        (1.8, "cg_download_complete"),
        (4.8, "cg_blood_moon"),
        (9.4, "cg_screen_crack"),
    )

    def __init__(self, audio=None) -> None:
        self.audio = audio
        self.active = False
        self.finished = False
        self.time = 0.0
        self._audio_tokens: set[str] = set()

    def start(self) -> None:
        """开始播放开场 CG。"""
        if self.audio is not None:
            self.audio.begin_cg_cycle()
        self.active = True
        self.finished = False
        self.time = 0.0
        self._audio_tokens.clear()
        self._emit_audio_cues()

    def skip(self) -> None:
        """跳过开场。"""
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
        """Trigger every crossed shot cue once, even when dt skips a boundary."""
        if self.audio is None:
            return
        for boundary, key in self.AUDIO_CUES:
            if self.time >= boundary:
                token = f"opening:{boundary}:{key}"
                if token in self._audio_tokens:
                    continue
                self._audio_tokens.add(token)
                self.audio.play_cg_cue(key, token=token)

    def draw(self, surface: pygame.Surface) -> None:
        """根据时间绘制正式 8 镜序列，缺失时保留原代码绘制回退。"""
        surface.fill(palette.BLACK)

        if not self._draw_formal_shot(surface):
            if self.time < 3.2:
                self._draw_download_shot(surface)
            elif self.time < 6.0:
                self._draw_turn_to_window(surface)
            elif self.time < 9.4:
                self._draw_blood_moon_reveal(surface)
            elif self.time < 12.6:
                self._draw_pull_back_moonlight(surface)
            elif self.time < 14.0:
                self._draw_screen_distortion(surface)
            else:
                self._draw_blackout(surface)

        self._draw_caption(surface)
        render_text(surface, "E / Esc 跳过", 390, 10, 11, palette.ASH_GRAY)

    def current_caption(self) -> str:
        """返回当前剧情节拍字幕。"""
        for start, end, caption in self.CAPTIONS:
            if start <= self.time < end:
                return caption
        return self.CAPTIONS[-1][2]

    def _draw_download_shot(self, surface: pygame.Surface) -> None:
        """背后第三视角：主角面对电脑，游戏图标正在下载。"""
        progress = min(1.0, self.time / 3.0)
        if self._draw_asset_background(surface, "opening_cg_room.png"):
            return
        self._draw_room_shell(surface)
        self._draw_window(surface, 46, 28, moon_visible=0.0)
        self._draw_player_back(surface, 224, 126, head_turn=0.0)
        self._draw_desk(surface, 170, 154)
        self._draw_computer(surface, 196, 91, progress)

    def _draw_turn_to_window(self, surface: pygame.Surface) -> None:
        """下载完成后，主角看向窗外，镜头也随之转向窗。"""
        local_t = (self.time - 3.2) / 2.8
        if self._draw_asset_background(surface, "opening_cg_room.png"):
            self._draw_moonlight(surface, strength=local_t * 0.25)
            return
        pan = int(local_t * 42)
        self._draw_room_shell(surface, pan_x=pan)
        self._draw_window(surface, 46 - pan, 28, moon_visible=0.12 + local_t * 0.12)
        self._draw_player_back(surface, 224 - pan // 5, 126, head_turn=local_t)
        self._draw_desk(surface, 170 - pan // 4, 154)
        self._draw_computer(surface, 196 - pan // 3, 91, 1.0)

    def _draw_blood_moon_reveal(self, surface: pygame.Surface) -> None:
        """镜头转到窗外，血月逐渐冲出云层。"""
        local_t = (self.time - 6.0) / 3.4
        if self._draw_asset_background(surface, "opening_cg_blood_moon.png"):
            return
        self._draw_clouded_sky(surface, local_t)
        moon_y = int(112 - 58 * local_t)
        moon_radius = int(10 + 18 * local_t)
        pygame.draw.circle(surface, palette.DARK_BLOOD, (240, moon_y), moon_radius + 5)
        pygame.draw.circle(surface, palette.BLOOD_RED, (240, moon_y), moon_radius)
        self._draw_clouds(surface, base_x=58, base_y=76, offset=int(local_t * 92))
        self._draw_window_frame_closeup(surface)

    def _draw_pull_back_moonlight(self, surface: pygame.Surface) -> None:
        """镜头后拉，血色月光照到主角和电脑。"""
        local_t = (self.time - 9.4) / 3.2
        if self._draw_asset_background(surface, "opening_cg_moonlight.png"):
            self._draw_moonlight(surface, strength=local_t)
            return
        pull = int(local_t * 18)
        self._draw_room_shell(surface, camera_pull=pull)
        self._draw_window(surface, 42 - pull, 24 - pull // 3, moon_visible=1.0)
        self._draw_moonlight(surface, strength=local_t)
        self._draw_player_back(surface, 224 + pull // 4, 128 + pull // 5, head_turn=1.0)
        self._draw_desk(surface, 170 + pull // 4, 154 + pull // 5)
        self._draw_computer(surface, 200 + pull // 3, 92 + pull // 6, 1.0, corrupted=local_t)

    def _draw_screen_distortion(self, surface: pygame.Surface) -> None:
        """电脑图标与血月红光共振，画面扭曲。"""
        local_t = self.time - 12.6
        if not self._draw_asset_background(surface, "opening_cg_moonlight.png"):
            surface.fill(palette.NIGHT_BLACK)

        # 以现有月光母版为底，只叠加暗色屏幕噪声和月影错位；不再使用成排红/青色条。
        veil = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        veil.fill((3, 6, 14, 112))
        surface.blit(veil, (0, 0))
        for i in range(16):
            y = 34 + i * 13 + int(math.sin(local_t * 7.0 + i * 0.8) * 3)
            start = 54 + int(math.cos(local_t * 5.0 + i) * 18)
            length = 96 + ((i * 47) % 188)
            color = palette.DEEP_BLUE if i % 3 else palette.GROUND_MID
            draw_filled_rect(surface, (start, y, length, 1), color)

        moon_x = 240 + int(math.sin(local_t * 3.0) * 6)
        moon_y = 124 + int(math.cos(local_t * 2.5) * 3)
        pygame.draw.circle(surface, palette.MOON_WHITE, (moon_x, moon_y), 24)
        pygame.draw.circle(surface, palette.NIGHT_BLACK, (moon_x + 10, moon_y - 7), 24)
        for i in range(9):
            x1 = moon_x - 28 + ((i * 17 + int(local_t * 24)) % 58)
            y1 = moon_y - 30 + i * 7
            color = palette.DARK_BLOOD if i % 3 == 0 else palette.ASH_GRAY
            draw_line(surface, (x1, y1), (x1 + 10 + i * 2, y1 + ((i % 2) * 2 - 1)), color)

    def _draw_blackout(self, surface: pygame.Surface) -> None:
        """黑屏转入月宫。"""
        if not self._draw_asset_background(surface, "opening_cg_blackout.png"):
            surface.fill(palette.BLACK)
        if int(self.time * 8) % 2 == 0:
            draw_filled_rect(surface, (232, 130, 16, 2), palette.BLOOD_RED)

    def _draw_asset_background(self, surface: pygame.Surface, filename: str) -> bool:
        """绘制开场 CG 的项目 PNG 背景；缺失时回退到代码绘制。"""
        try:
            background = load_image(f"sprites/moonspace/{filename}")
        except (FileNotFoundError, pygame.error):
            return False
        surface.blit(background, (0, 0))
        return True

    def _draw_formal_shot(self, surface: pygame.Surface) -> bool:
        """按当前时间绘制已批准的正式开场镜头。"""
        for index, (start, end, filename) in enumerate(self.SHOT_ASSETS):
            is_last_shot = index == len(self.SHOT_ASSETS) - 1
            if start <= self.time < end or (is_last_shot and self.time >= end):
                return self._draw_asset_background(surface, filename)
        return False

    def _draw_caption(self, surface: pygame.Surface) -> None:
        """绘制带轻微淡入淡出的剧情字幕。"""
        caption = self.current_caption()
        local_start = 0.0
        local_end = self.TOTAL_DURATION
        for start, end, text in self.CAPTIONS:
            if text == caption:
                local_start, local_end = start, end
                break

        fade_in = min(1.0, max(0.0, (self.time - local_start) / 0.5))
        fade_out = min(1.0, max(0.0, (local_end - self.time) / 0.5))
        strength = min(fade_in, fade_out)
        alpha = int(185 * strength)
        if alpha <= 0:
            return

        panel = pygame.Surface((config.SCREEN_WIDTH, 28), pygame.SRCALPHA)
        panel.fill((*palette.BLACK, alpha))
        surface.blit(panel, (0, config.SCREEN_HEIGHT - 36))
        render_text(surface, caption, 28, config.SCREEN_HEIGHT - 29, 13, palette.PALE_MOON)

    def _draw_room_shell(self, surface: pygame.Surface, camera_pull: int = 0, pan_x: int = 0) -> None:
        """绘制房间背景，不包含会互相遮挡的前景物体。"""
        draw_filled_rect(surface, (0, 0, config.SCREEN_WIDTH, config.SCREEN_HEIGHT), palette.NIGHT_BLACK)
        draw_filled_rect(surface, (0, 176 + camera_pull, config.SCREEN_WIDTH, 94), palette.GROUND_DARK)
        for i in range(5):
            y = 188 + i * 16 + camera_pull
            draw_line(surface, (0, y), (config.SCREEN_WIDTH, y + 18), palette.DEEP_BLUE)
        # 后墙暗纹，辅助表现镜头横移。
        for i in range(4):
            x = 36 + i * 110 - pan_x // 2
            draw_filled_rect(surface, (x, 42, 38, 2), palette.DEEP_BLUE)

    def _draw_desk(self, surface: pygame.Surface, x: int, y: int) -> None:
        """绘制桌子前景，放在主角身体前，避免穿模。"""
        draw_filled_rect(surface, (x, y, 140, 14), palette.WOOD_BROWN)
        draw_rect(surface, x, y, 140, 14, palette.WOOD_DARK)
        draw_filled_rect(surface, (x + 10, y + 14, 8, 40), palette.WOOD_DARK)
        draw_filled_rect(surface, (x + 122, y + 14, 8, 40), palette.WOOD_DARK)

    def _draw_window(self, surface: pygame.Surface, x: int, y: int, moon_visible: float) -> None:
        """绘制窗户和可见血月。"""
        draw_filled_rect(surface, (x, y, 104, 76), (8, 8, 14))
        if moon_visible > 0:
            radius = int(8 + moon_visible * 14)
            pygame.draw.circle(surface, palette.BLOOD_RED, (x + 70, y + 28), radius)
            self._draw_clouds(surface, base_x=x + 18, base_y=y + 22, offset=int(moon_visible * 20))
        draw_rect(surface, x, y, 104, 76, palette.MOON_WHITE)
        draw_line(surface, (x + 52, y), (x + 52, y + 76), palette.DEEP_BLUE)
        draw_line(surface, (x, y + 38), (x + 104, y + 38), palette.DEEP_BLUE)

    def _draw_window_frame_closeup(self, surface: pygame.Surface) -> None:
        """绘制近景窗框，让血月镜头仍像从房间里看出去。"""
        draw_rect(surface, 36, 24, 408, 206, palette.MOON_WHITE)
        draw_filled_rect(surface, (236, 24, 6, 206), palette.DEEP_BLUE)
        draw_filled_rect(surface, (36, 126, 408, 6), palette.DEEP_BLUE)

    def _draw_computer(
        self,
        surface: pygame.Surface,
        x: int,
        y: int,
        progress: float,
        corrupted: float = 0.0,
    ) -> None:
        """绘制电脑屏幕，屏幕上是 MoonSpace 游戏图标。"""
        draw_filled_rect(surface, (x + 39, y + 56, 12, 8), palette.WOOD_DARK)
        draw_filled_rect(surface, (x + 28, y + 64, 34, 4), palette.WOOD_DARK)
        draw_filled_rect(surface, (x, y, 90, 56), palette.BLACK)
        draw_rect(surface, x, y, 90, 56, palette.MOON_WHITE)
        screen_color = palette.DEEP_BLUE if corrupted < 0.4 else palette.DARK_BLOOD
        draw_filled_rect(surface, (x + 6, y + 6, 78, 36), screen_color)
        pygame.draw.circle(surface, palette.MOON_WHITE, (x + 45, y + 22), 9)
        pygame.draw.circle(surface, screen_color, (x + 49, y + 19), 8)
        draw_line(surface, (x + 45, y + 11), (x + 49, y + 33), palette.BLOOD_RED)
        bar_width = int(70 * progress)
        draw_rect(surface, x + 10, y + 46, 70, 5, palette.ASH_GRAY)
        draw_filled_rect(surface, (x + 10, y + 46, bar_width, 5), palette.BLOOD_RED if progress >= 1 else palette.POOL_HIGHLIGHT)
        if progress >= 1:
            draw_filled_rect(surface, (x + 37, y + 34, 16, 2), palette.PALE_MOON)

    def _draw_player_back(self, surface: pygame.Surface, x: int, y: int, head_turn: float) -> None:
        """绘制背后视角主角。"""
        draw_filled_rect(surface, (x + 7, y, 18, 16), palette.SKIN_PALE)
        hair_shift = int(head_turn * 4)
        draw_filled_rect(surface, (x + 5 + hair_shift, y - 2, 22, 8), palette.BLACK)
        draw_filled_rect(surface, (x, y + 15, 32, 48), palette.PLAYER_ROBE)
        draw_filled_rect(surface, (x - 7, y + 24, 7, 28), palette.PLAYER_ROBE)
        draw_filled_rect(surface, (x + 32, y + 24, 7, 28), palette.PLAYER_ROBE)
        draw_filled_rect(surface, (x + 8, y + 63, 6, 14), palette.DEEP_BLUE)
        draw_filled_rect(surface, (x + 20, y + 63, 6, 14), palette.DEEP_BLUE)

    def _draw_clouded_sky(self, surface: pygame.Surface, local_t: float) -> None:
        """绘制红月出现前的云层天幕。"""
        surface.fill((8, 8, 14))
        for y in range(0, 180, 18):
            shade = (16 + y // 12, 18 + y // 10, 28 + y // 8)
            draw_filled_rect(surface, (0, y, config.SCREEN_WIDTH, 18), shade)
        red_alpha = int(45 * local_t)
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*palette.BLOOD_RED, red_alpha))
        surface.blit(overlay, (0, 0))

    def _draw_clouds(self, surface: pygame.Surface, base_x: int = 70, base_y: int = 70, offset: int = 0) -> None:
        """绘制厚重云层。"""
        for i in range(5):
            x = base_x + i * 72 - offset
            y = base_y + (i % 2) * 14
            draw_filled_rect(surface, (x, y, 74, 18), palette.DEEP_BLUE)
            draw_filled_rect(surface, (x + 14, y - 8, 46, 12), palette.GROUND_MID)

    def _draw_moonlight(self, surface: pygame.Surface, strength: float) -> None:
        """绘制从窗外照入房间的血色月光。"""
        alpha = int(95 * strength)
        overlay = pygame.Surface((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.SRCALPHA)
        points = [(82, 78), (154, 40), (386, 270), (202, 270)]
        pygame.draw.polygon(overlay, (*palette.BLOOD_RED, alpha), points)
        surface.blit(overlay, (0, 0))
