"""MoonSpace Pygame 入口。"""

from core.game import Game


def main() -> None:
    """启动游戏主循环。"""
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
