# game/battle.py
import random
import pygame
from .settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BLACK,
    COLOR_WHITE,
    COLOR_UI_BG,
    COLOR_TEXT,
    COLOR_GREEN,
)


class BattleSystem:
    def __init__(self, screen, font, player):
        self.screen = screen
        self.font = font
        self.player = player

        self.enemy_name = random.choice(["Goblín", "Esqueleto", "Lobo"])
        self.enemy_hp = 40
        self.enemy_max_hp = 40
        self.enemy_attack = 9

        self.state = "PLAYER_TURN"
        self.log_message = f"¡Un {self.enemy_name} te ha atacado!"
        self.active = True

    def handle_input(self, key):
        if self.state == "PLAYER_TURN":
            if key == pygame.K_1:  # Atacar
                damage = random.randint(12, 22)
                self.enemy_hp = max(0, self.enemy_hp - damage)
                self.log_message = f"¡Infligiste {damage} de daño al {self.enemy_name}!"

                if self.enemy_hp == 0:
                    self.state = "VICTORY"
                    gold_reward = random.randint(10, 20)
                    self.player.gold += gold_reward
                    self.log_message = (
                        f"¡Ganaste! Obtenido: {gold_reward} de oro. Presiona [ENTER]"
                    )
                else:
                    self.state = "ENEMY_TURN"

            elif key == pygame.K_2:  # Usar Poción
                self.log_message = self.player.use_potion()
                self.state = "ENEMY_TURN"

            elif key == pygame.K_3:  # Huir
                if random.random() > 0.35:
                    self.log_message = "¡Lograste huir! Presiona [ENTER]"
                    self.state = "VICTORY"
                else:
                    self.log_message = "¡No pudiste escapar!"
                    self.state = "ENEMY_TURN"

        elif self.state in ("VICTORY", "DEFEAT"):
            if key == pygame.K_RETURN:
                self.active = False

    def update_enemy_turn(self):
        if self.state == "ENEMY_TURN":
            pygame.time.delay(400)
            damage = max(1, self.enemy_attack + random.randint(-2, 2))
            self.player.hp = max(0, self.player.hp - damage)

            if self.player.hp == 0:
                self.state = "DEFEAT"
                self.log_message = "¡Has sido derrotado! Presiona [ENTER]"
            else:
                self.log_message = f"El {self.enemy_name} te inflige {damage} de daño."
                self.state = "PLAYER_TURN"

    def draw(self):
        self.screen.fill(COLOR_BLACK)

        player_rect = pygame.Rect(100, 200, 64, 64)
        enemy_rect = pygame.Rect(SCREEN_WIDTH - 164, 200, 64, 64)

        pygame.draw.rect(self.screen, (220, 20, 60), player_rect)
        pygame.draw.rect(self.screen, (34, 139, 34), enemy_rect)

        # Barras HP
        pygame.draw.rect(self.screen, COLOR_UI_BG, (100, 180, 100, 10))
        pygame.draw.rect(
            self.screen,
            COLOR_GREEN,
            (100, 180, max(0, int(100 * (self.player.hp / self.player.max_hp))), 10),
        )

        pygame.draw.rect(self.screen, COLOR_UI_BG, (SCREEN_WIDTH - 164, 180, 100, 10))
        pygame.draw.rect(
            self.screen,
            COLOR_GREEN,
            (
                SCREEN_WIDTH - 164,
                180,
                max(0, int(100 * (self.enemy_hp / self.enemy_max_hp))),
                10,
            ),
        )

        # Cuadro de opciones
        panel_rect = pygame.Rect(10, SCREEN_HEIGHT - 120, SCREEN_WIDTH - 20, 110)
        pygame.draw.rect(self.screen, COLOR_UI_BG, panel_rect)
        pygame.draw.rect(self.screen, COLOR_WHITE, panel_rect, 2)

        log_surf = self.font.render(self.log_message, True, COLOR_TEXT)
        self.screen.blit(log_surf, (20, SCREEN_HEIGHT - 110))

        if self.state == "PLAYER_TURN":
            opts_text = f"[1] Atacar   [2] Poción ({self.player.potions})   [3] Huir"
            opts_surf = self.font.render(opts_text, True, COLOR_WHITE)
            self.screen.blit(opts_surf, (20, SCREEN_HEIGHT - 50))
