# game/game_engine.py
import sys
import random
import pygame
from .settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    COLOR_UI_BG,
    COLOR_TEXT,
    COLOR_WHITE,
)
from .player import Player
from .npc import NPC
from .map_manager import MapManager
from .battle import BattleSystem


class GameEngine:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("RPG Retro - Windows 7 / 2GB RAM Edition")

        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 14)

        self.player = Player(tile_x=2, tile_y=2)
        self.map_manager = MapManager()

        # Aldeanos / NPCs distribuidos en el mapa
        self.npcs = [
            NPC(
                3,
                2,
                "Anciano",
                [
                    "¡Bienvenido aventurero!",
                    "Cuidado con la hierba alta.",
                    "Hay monstruos cerca.",
                ],
            ),
            NPC(
                7,
                4,
                "Mercader",
                ["¿Buscas provisiones?", "Usa la tecla [H] para curarte."],
            ),
        ]

        self.current_battle = None
        self.notification = (
            "Mover: [WASD] | Hablar: [E] | Poción: [H] | Guardar: [G] | Cargar: [C]"
        )
        self.running = True

    def check_npc_interaction(self):
        # Buscar si hay un NPC adyacente al personaje
        for npc in self.npcs:
            if (
                abs(self.player.tile_x - npc.tile_x)
                + abs(self.player.tile_y - npc.tile_y)
                == 1
            ):
                self.notification = npc.get_current_dialogue()
                return
        self.notification = "No hay nadie cerca para hablar."

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False

                # Gestión de entrada durante Combate
                if self.current_battle and self.current_battle.active:
                    self.current_battle.handle_input(event.key)
                else:
                    # Gestión de entrada en Mapa
                    moved = False
                    if event.key in (pygame.K_LEFT, pygame.K_a):
                        moved = self.player.move(
                            -1, 0, self.map_manager.world_map, self.npcs
                        )
                    elif event.key in (pygame.K_RIGHT, pygame.K_d):
                        moved = self.player.move(
                            1, 0, self.map_manager.world_map, self.npcs
                        )
                    elif event.key in (pygame.K_UP, pygame.K_w):
                        moved = self.player.move(
                            0, -1, self.map_manager.world_map, self.npcs
                        )
                    elif event.key in (pygame.K_DOWN, pygame.K_s):
                        moved = self.player.move(
                            0, 1, self.map_manager.world_map, self.npcs
                        )

                    # Interacciones y accesos directos
                    elif event.key == pygame.K_e:
                        self.check_npc_interaction()
                    elif event.key == pygame.K_h:
                        self.notification = self.player.use_potion()
                    elif event.key == pygame.K_g:
                        self.player.save_data()
                        self.notification = "¡Partida guardada!"
                    elif event.key == pygame.K_c:
                        if self.player.load_data():
                            self.notification = "¡Partida cargada!"
                        else:
                            self.notification = "No existe archivo de guardado."

                    # Probabilidad de combate aleatorio en hierba alta (Tile 0)
                    if (
                        moved
                        and self.map_manager.world_map[self.player.tile_y][
                            self.player.tile_x
                        ]
                        == 0
                    ):
                        if random.random() < 0.15:
                            self.current_battle = BattleSystem(
                                self.screen, self.font, self.player
                            )

    def draw_ui(self):
        ui_rect = pygame.Rect(0, 0, SCREEN_WIDTH, 35)
        pygame.draw.rect(self.screen, COLOR_UI_BG, ui_rect)

        stats = f"HP: {self.player.hp}/{self.player.max_hp} | Oro: {self.player.gold} | Pociones: {self.player.potions}"
        stats_surf = self.font.render(stats, True, COLOR_TEXT)
        self.screen.blit(stats_surf, (10, 8))

        noti_surf = self.font.render(self.notification, True, COLOR_WHITE)
        self.screen.blit(noti_surf, (SCREEN_WIDTH - noti_surf.get_width() - 10, 8))

    def run(self):
        while self.running:
            self.handle_events()

            if self.current_battle and self.current_battle.active:
                self.current_battle.update_enemy_turn()
                self.current_battle.draw()
            else:
                camera_x = self.player.x - (SCREEN_WIDTH // 2) + (32 // 2)
                camera_y = self.player.y - (SCREEN_HEIGHT // 2) + (32 // 2)

                self.map_manager.draw(self.screen, camera_x, camera_y)

                # Dibujar NPCs
                for npc in self.npcs:
                    npc.draw(self.screen, camera_x, camera_y)

                self.player.draw(self.screen, camera_x, camera_y)
                self.draw_ui()

            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()
