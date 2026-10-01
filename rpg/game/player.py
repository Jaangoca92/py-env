# game/player.py
import json
import os
import pygame
from .settings import TILE_SIZE, COLOR_PLAYER


class Player:
    def __init__(self, tile_x: int = 2, tile_y: int = 2):
        self.tile_x = tile_x
        self.tile_y = tile_y
        self.hp = 100
        self.max_hp = 100
        self.gold = 0
        self.potions = 2

        self.x = tile_x * TILE_SIZE
        self.y = tile_y * TILE_SIZE

    def move(self, dx: int, dy: int, map_data, npcs: list) -> bool:
        new_x = self.tile_x + dx
        new_y = self.tile_y + dy

        # Comprobar límites de mapa
        if 0 <= new_y < len(map_data) and 0 <= new_x < len(map_data[0]):
            # Colisión con agua (Tile 1)
            if map_data[new_y][new_x] == 1:
                return False

            # Colisión con NPCs
            for npc in npcs:
                if npc.tile_x == new_x and npc.tile_y == new_y:
                    return False

            self.tile_x = new_x
            self.tile_y = new_y
            self.x = self.tile_x * TILE_SIZE
            self.y = self.tile_y * TILE_SIZE
            return True
        return False

    def use_potion(self) -> str:
        if self.potions > 0:
            if self.hp < self.max_hp:
                self.potions -= 1
                heal = 35
                self.hp = min(self.max_hp, self.hp + heal)
                return f"¡Usaste poción! Curaste {heal} HP."
            return "¡Salud al máximo!"
        return "¡Sin pociones!"

    def save_data(self, filename="savegame.json"):
        data = {
            "tile_x": self.tile_x,
            "tile_y": self.tile_y,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "gold": self.gold,
            "potions": self.potions,
        }
        with open(filename, "w") as f:
            json.dump(data, f)

    def load_data(self, filename="savegame.json") -> bool:
        if os.path.exists(filename):
            with open(filename, "r") as f:
                data = json.load(f)
                self.tile_x = data.get("tile_x", 2)
                self.tile_y = data.get("tile_y", 2)
                self.hp = data.get("hp", 100)
                self.max_hp = data.get("max_hp", 100)
                self.gold = data.get("gold", 0)
                self.potions = data.get("potions", 2)
                self.x = self.tile_x * TILE_SIZE
                self.y = self.tile_y * TILE_SIZE
            return True
        return False

    def draw(self, surface: pygame.Surface, camera_x: int, camera_y: int):
        draw_rect = pygame.Rect(
            self.x - camera_x, self.y - camera_y, TILE_SIZE, TILE_SIZE
        )
        pygame.draw.rect(surface, COLOR_PLAYER, draw_rect)
