# game/map_manager.py
import pygame
from .settings import (
    TILE_SIZE,
    COLOR_GRASS,
    COLOR_WATER,
    COLOR_DIRT,
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
)


class MapManager:
    def __init__(self):
        # 0 = Hierba, 1 = Agua (Bloqueo), 2 = Camino
        self.world_map = [
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
            [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 2, 2, 2, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 2, 0, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 0, 0, 0, 0, 0, 0, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
            [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        ]

        self.colors = {0: COLOR_GRASS, 1: COLOR_WATER, 2: COLOR_DIRT}

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        start_col = max(0, camera_x // TILE_SIZE)
        end_col = min(
            len(self.world_map[0]), (camera_x + SCREEN_WIDTH) // TILE_SIZE + 1
        )

        start_row = max(0, camera_y // TILE_SIZE)
        end_row = min(len(self.world_map), (camera_y + SCREEN_HEIGHT) // TILE_SIZE + 1)

        for row in range(start_row, end_row):
            for col in range(start_col, end_col):
                tile_type = self.world_map[row][col]
                color = self.colors.get(tile_type, COLOR_GRASS)
                rect = pygame.Rect(
                    col * TILE_SIZE - camera_x,
                    row * TILE_SIZE - camera_y,
                    TILE_SIZE,
                    TILE_SIZE,
                )
                pygame.draw.rect(surface, color, rect)
