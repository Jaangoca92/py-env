# game/npc.py
import pygame
from .settings import TILE_SIZE, COLOR_NPC


class NPC:
    def __init__(self, tile_x: int, tile_y: int, name: str, dialogue: list):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.name = name
        self.dialogue = dialogue
        self.dialogue_index = 0
        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

    def get_current_dialogue(self) -> str:
        text = self.dialogue[self.dialogue_index]
        self.dialogue_index = (self.dialogue_index + 1) % len(self.dialogue)
        return f"{self.name}: {text}"

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        draw_rect = pygame.Rect(
            self.x - camera_x, self.y - camera_y, TILE_SIZE, TILE_SIZE
        )
        pygame.draw.rect(surface, COLOR_NPC, draw_rect)
