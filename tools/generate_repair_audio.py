"""Generate workshop Foley and stage the approved CC0 scare vocal."""
from pathlib import Path
import math
import os
import random
import struct
import wave

RATE = 44100
ROOT = Path(__file__).resolve().parents[1] / "assets" / "audio"
SCARE_SOURCE = (
    Path(__file__).resolve().parents[1]
    / "assets" / "source" / "audio" / "freesound-442957-monster-attack-hq.mp3"
)


def save(name, duration, waveform, echoes=()):
    rng = random.Random(73)
    samples = [waveform(i / RATE, rng) for i in range(round(duration * RATE))]
    original = samples[:]
    for delay, gain in echoes:
        shift = round(delay * RATE)
        for i in range(shift, len(samples)):
            samples[i] += original[i - shift] * gain
    peak = max(abs(value) for value in samples) or 1
    pcm = b"".join(struct.pack("<h", round(value / peak * 0.62 * 32767)) for value in samples)
    with wave.open(str(ROOT / name), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm)


def stage_scare() -> None:
    """Convert the selected Freesound attack roar into an immediate mono cue."""
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
    import pygame

    pygame.mixer.init(frequency=RATE, size=-16, channels=1)
    try:
        raw = pygame.mixer.Sound(str(SCARE_SOURCE)).get_raw()
    finally:
        pygame.mixer.quit()

    samples = list(struct.unpack(f"<{len(raw) // 2}h", raw))
    peak = max(abs(sample) for sample in samples) or 1
    threshold = peak * .01
    onset = next(index for index, sample in enumerate(samples) if abs(sample) >= threshold)
    ending = len(samples) - next(
        index for index, sample in enumerate(reversed(samples)) if abs(sample) >= threshold
    )
    start = max(0, onset - round(RATE * .008))
    stop = min(len(samples), ending + round(RATE * .020))
    samples = samples[start:stop]

    gain = .68 * 32767 / peak
    fade_in = min(len(samples), round(RATE * .004))
    fade_out = min(len(samples), round(RATE * .020))
    for index in range(fade_in):
        samples[index] *= index / max(1, fade_in - 1)
    for index in range(fade_out):
        samples[-index - 1] *= index / max(1, fade_out - 1)
    pcm = b"".join(
        struct.pack("<h", max(-32768, min(32767, round(sample * gain))))
        for sample in samples
    )
    with wave.open(str(ROOT / "repair_scare.wav"), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(RATE)
        output.writeframes(pcm)


if __name__ == "__main__":
    save("repair_drip.wav", 1.25,
         lambda t, r: ((math.sin(2 * math.pi * (1280*t - 710*t*t)) * math.exp(-t*38)
                        + .18 * math.sin(2*math.pi*430*t) * math.exp(-t*19)
                        + r.uniform(-.11, .11)*math.exp(-t*140)) * min(1, t*1800)),
         ((.14, .24), (.31, .11), (.52, .045)))
    save("repair_chisel.wav", .85,
         lambda t, r: (r.uniform(-.8,.8)*math.exp(-t*120)
                       + .27*math.sin(2*math.pi*2370*t)*math.exp(-t*30)
                       + .18*math.sin(2*math.pi*960*t)*math.exp(-t*18)) * min(1,t*2000),
         ((.09, .16), (.23, .055)))
    stage_scare()
