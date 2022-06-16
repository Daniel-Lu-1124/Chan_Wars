import sys
import time
import random
import math

from bin.classes.stopwatch import Timer
from bin.blit_tools import draw_text_left, draw_text_right, draw_rect_outline, center_blit_image
from bin.classes.buttons import ButtonTriangle
from bin.classes.health_bar import HealthBar
from bin.classes.level import Level
from bin.colours import *
from bin.classes.entities.enemy import Enemy
import bin.levels.minigames.Card_Game.player as card_pair
from bin.classes.entities.shopkeeper import ShopKeep


class EnemyLevel(Level):
    def __init__(self, width, height, surface, game_canvas, clock, fps, last_time, config):
        super().__init__(width, height, surface, game_canvas, clock, fps, last_time, config)
        self.back_button = ButtonTriangle(self.text_canvas, cw_blue)
        # ------------------------------------------------------------------------------------------------------------------
        # Card Game Attributes
        self.card_canvas = pg.Surface((self.width, self.height), flags=pg.HWACCEL and pg.DOUBLEBUF and pg.SRCALPHA).convert_alpha()
        self.card_canvas_y = self.height
        self.card_game = False
        self.game_transition_in = False
        self.game_transition_out = False  # Use this to stop the game
        # ------------------------------------------------------------------------------------------------------------------
        # Player Attributes
        self.hp_player_rect = pg.Rect(100, 545, 330, 35)
        self.hp_bar_player = None
        self.player = card_pair.Player(self.card_canvas, None)
        self.player_attack = 0
        self.player_statuses = []
        # ------------------------------------------------------------------------------------------------------------------
        # Enemy Attributes
        self.hp_enemy_rect = pg.Rect(1170, 545, 330, 35)
        self.hp_bar_enemy = None
        # ------------------------------------------------------------------------------------------------------------------
        self.size = None
        self.margins = (20, 30)
        self.cards = None
        self.background = None
        self.level = None
        self.action_stopwatch = Timer()
        self.update_stopwatch = Timer()
        self.transition_stopwatch = Timer()
        self.turn_counter = None
        self.card_stopwatch = Timer()
        self.death_stopwatch = Timer()
        self.card_complete = [0]
        self.enemy = Enemy(None)
        self.name = None
        self.face = None
        # ------------------------------------------------------------------------------------------------------------------
        # Shop Attributes
        self.shop_canvas = pg.Surface((self.width, self.height), flags=pg.HWACCEL and pg.DOUBLEBUF and pg.SRCALPHA).convert_alpha()
        self.shopkeeper = ShopKeep(self.shop_canvas)

    def reload(self):  # Set values here b/c `self.config = None` when the class is first initialized
        self.level = 1
        config = self.config.get_config("level")
        self.name = random.choice(list(config[0]["enemies"].keys()))
        self.player.metadata = config[self.level]["player"]
        self.enemy.metadata = config[self.level]["enemies"][self.name]
        self.size = self.config.chan_card_size
        self.turn_counter = 0
        self.enemy.initialize(self.name)
        self.player.initialize(self.config.img_chans)
        self.hp_bar_player = HealthBar(self.game_canvas, self.hp_player_rect, self.player.health, cw_green, white, 5, True, cw_dark_red, True, cw_yellow)
        self.hp_bar_enemy = HealthBar(self.game_canvas, self.hp_enemy_rect, self.enemy.health, cw_green, white, 5, True, cw_dark_red, True, cw_yellow)
        self.face = self.config.img_enemies[self.name]
        self.cards = self.player.generate_pairs(self.size, self.margins, self.width, self.height)
        self.shopkeeper.initialize(config[self.level]["player"]["cards"], self.player.deck, self.config.img_chans)
        self.shopkeeper.create_stock()


    def draw_bars(self, dt):  # Draw Health bars
        # Player Text & Health Bar
        draw_text_left(str(math.ceil(self.player.health)) + "HP", white, self.config.f_hp_bar_hp, self.text_canvas, self.hp_bar_player.x, self.hp_bar_player.y)
        draw_text_left("You", white, self.config.f_hp_bar_name, self.text_canvas, self.hp_bar_player.x, self.hp_bar_player.y + self.hp_bar_player.h * 2 + 5)
        self.hp_bar_player.render(self.player.health, 0.3, dt)
        # ------------------------------------------------------------------------------------------------------------------
        # Enemy Text & Health Bar
        draw_text_right(str(math.ceil(self.enemy.health)) + "HP", white, self.config.f_hp_bar_hp, self.text_canvas,
                        self.hp_bar_enemy.x + self.hp_bar_enemy.w + 10, self.hp_bar_enemy.y)
        draw_text_right(self.enemy.name, white, self.config.f_hp_bar_name, self.text_canvas,
                        self.hp_bar_enemy.x + self.hp_bar_enemy.w + 5, self.hp_bar_enemy.y + self.hp_bar_enemy.h * 2 + 5)
        self.hp_bar_enemy.render(self.enemy.health, 0.3, dt, True)

    def draw_enemy(self, time_elapsed):
        offset = 10 * math.sin(pg.time.get_ticks() / 500)  # VELOCITY FUNCTION HERE (SLOPE)
        center_blit_image(self.game_canvas, self.face, self.width / 2, self.height / 2 - 100 + offset)

    def run_card_game(self, click):
        mouse_pos = (0, 0)
        deck = ['flighty air_chan', 'bright angel_chan', 'earth_chan', 'avatar_chan', 'farquaad_chan', 'fire_chan', 'jackie_chan', 'jesus_chan', 'oni_chan', 'shrek_chan']
        if self.card_canvas_y != self.height:
            self.card_canvas.fill((255, 255, 255))
            # ------------------------------------------------------------------------------------------------------------------
            if self.player.energy and not self.game_transition_in and not self.game_transition_out:
                # This if statement prevents you from changing the state of the cards while the screen is moving or you don't have enough energy - Daniel
                if not self.cards:
                    self.cards = self.player.generate_pairs(self.size, self.margins, self.width, self.height, deck)
                if self.card_complete[0] != 2:
                    self.card_complete = self.player.complete()
                else:
                    if not self.card_stopwatch.activate_timer:
                        self.card_stopwatch.time_start()
                    if self.card_stopwatch.seconds > 0.25:
                        self.player.energy -= 1
                        self.player_attack += self.card_complete[1]
                        self.player_statuses.append(self.card_complete[2])
                        self.player.reset()
                        self.card_stopwatch.time_reset()
                        self.card_complete = self.player.complete()
                if click:
                    mouse_pos = tuple(pg.mouse.get_pos())
            self.player.draw_cards(mouse_pos, self.card_complete[0], self.config.img_levels["Card Game"], 0,
                                   self.player.energy and not self.card_stopwatch.seconds > 500 and not self.game_transition_in and not self.game_transition_out)
            self.shopkeeper.draw()
            # This is the running code made by Daniel. In order of appearance, the code generates the cards, checks to see if any pairs of choices have been made
            # starts a timer for the player to admire their choices if they have made two of them, does a bunch of stuff based on whether they chose right
            # and finally blits it all after getting the mouses position if a click has been made
            self.game_canvas.blit(self.card_canvas, (0, self.card_canvas_y))

    def run(self):
        self.reload()
        acted = True
        completed = True
        updated = True
        milliseconds = pg.USEREVENT
        time_elapsed = Timer()
        time_elapsed.time_start()
        pg.time.set_timer(milliseconds, 10)
        while True:
            # Framerate Independence
            dt = time.time() - self.last_time
            dt *= 60  # Delta time - 60fps physics
            self.last_time = time.time()
            self.click = False
            mx, my = pg.mouse.get_pos()  # Get mouse position
            # ----------------------------------------------------------------------------------------------------------
            for event in pg.event.get():
                pressed = pg.key.get_pressed()  # Gathers the state of all keys pressed
                if event.type == pg.QUIT or pressed[pg.K_ESCAPE]:
                    pg.quit()
                    sys.exit()
                if event.type == pg.MOUSEBUTTONDOWN:  # When Mouse Button Clicked
                    if event.button == 1:  # Left Mouse Button
                        self.click = True
                if event.type == milliseconds:
                    self.transition_stopwatch.stopwatch()
                    self.update_stopwatch.stopwatch()
                    self.action_stopwatch.stopwatch()
                    self.card_stopwatch.stopwatch()
                    self.death_stopwatch.stopwatch()
                    time_elapsed.stopwatch()
            # ------------------------------------------------------------------------------------------------------------------
            if not self.fade_out and not self.freeze:
                self.transition_in("game", self.game_canvas, dt)
            elif self.freeze:  # To prevent the transition from happening offscreen
                self.freeze = False
            # ------------------------------------------------------------------------------------------------------------------
            self.fill_screens()
            self.background = self.config.img_levels[self.level]
            self.game_canvas.blit(self.background, (0, 0))
            # ------------------------------------------------------------------------------------------------------------------
            if self.back_button.run(mx, my, cw_light_blue, self.click):
                self.fade_out = True
                self.next_level = 2
            # --------------------------------------------------------------------------------------------------------------
            if self.transition_out("game", self.game_canvas, dt):
                self.restore()
                return self.next_level
            # ------------------------------------------------------------------------------------------------------------------
            if self.click and self.enemy.health and self.player.health:
                if not self.card_game and completed and not self.game_transition_in and not self.game_transition_out:
                    # Daniel made it so that clicking won't interrupt the transitioning process
                    self.game_transition_in = True
                    self.game_transition_out = False
                elif self.card_game and self.player.energy == 0 and not self.game_transition_in and not self.game_transition_out:
                    # There should probably be a unified transitioning variable to shorten these if statements and the one above in run_card_game
                    self.game_transition_in = False
                    self.game_transition_out = True
            # Added energy and damage counter reset and only pulls down the card screen when energy is equal to 0
            # ------------------------------------------------------------------------------------------------------------------
            # Card Game Display Driver
            # Transition In
            if self.game_transition_in:
                if not self.transition_stopwatch.activate_timer:
                    self.transition_stopwatch.time_start()
                if self.card_canvas_y > 1:
                    self.card_canvas_y = card_pair.move_pos(True, self.transition_stopwatch.seconds, self.height, 25)
                    # Here, Daniel rejected velocity and returned to fixed values
                elif self.card_canvas_y <= 1:
                    self.card_canvas_y = 0
                    self.game_transition_in = False
                    self.card_game = True
                    self.transition_stopwatch.time_reset()
            # Transition Out
            if self.game_transition_out:
                if not self.transition_stopwatch.activate_timer:
                    self.transition_stopwatch.time_start()
                if self.card_canvas_y < self.height - 1:
                    self.card_canvas_y = card_pair.move_pos(False, self.transition_stopwatch.seconds, self.height, 25)
                    # Here, Daniel rejected velocity and returned to fixed values
                    self.card_game = False
                elif self.card_canvas_y >= self.height - 1:
                    self.card_canvas_y = self.height
                    self.game_transition_out = False
                    acted = False
                    completed = False
                    updated = False
                    self.transition_stopwatch.time_reset()
            # The stopwatch was used to do the transitions
            # I chose to just use fixed values because the impact of the framerate is practically negligible and it is so much easier to code with just the fixed values
            # Taking the derivative of the function is already a nightmare, let alone trying to implement it into the game.
            # ------------------------------------------------------------------------------------------------------------------
            if not self.card_game:  # Don't render if the card game is fully up
                if not self.update_stopwatch.activate_timer and not updated and not completed:
                    self.update_stopwatch.time_start()
                if not self.action_stopwatch.activate_timer and not completed:
                    self.action_stopwatch.time_start()
                if self.update_stopwatch.seconds > 1.5:
                    self.enemy.update(self.player_attack, self.player_statuses)
                    self.player_attack = 0
                    self.player_statuses = []
                    updated = True
                    self.update_stopwatch.time_reset()
                if self.action_stopwatch.seconds > 2.5 and not acted:
                    action = self.enemy.act(self.turn_counter)
                    acted = True
                    self.player.update(action[2], action[3])
                elif self.action_stopwatch.seconds > 4:
                    self.turn_counter += 1
                    self.action_stopwatch.time_reset()
                    completed = True
                self.draw_bars(dt)  # Draw Health Bars (See Method Above)
                self.draw_enemy(time_elapsed)  # Draw Enemy' Image (See Method Above)
                # Textbox
                pg.draw.rect(self.game_canvas, cw_dark_grey, pg.Rect(95, 650, self.width - 95 * 2, 175))
                draw_rect_outline(self.game_canvas, white, pg.Rect(95, 650, self.width - 95 * 2, 175), 10)
            if self.player.health <= 0:
                self.death_stopwatch.time_start()
                if self.death_stopwatch.seconds > 1:
                    self.config.img_end_screens[0].set_alpha((self.death_stopwatch.seconds - 1) * 250)
                    self.game_canvas.blit(self.config.img_end_screens[0], (0, 0))
            elif self.enemy.health <= 0:
                self.death_stopwatch.time_start()
                if self.death_stopwatch.seconds > 1:
                    self.config.img_end_screens[1].set_alpha((self.death_stopwatch.seconds - 1) * 250)
                    self.game_canvas.blit(self.config.img_end_screens[1], (0, 0))
            # ------------------------------------------------------------------------------------------------------------------
            if self.enemy.health and self.player.health:
                self.run_card_game(self.click)
            # ------------------------------------------------------------------------------------------------------------------
            self.blit_screens()
            self.clock.tick(self.FPS)
            pg.display.update()
            # print(self.clock.get_fps(), self.card_game, self.card_canvas_y, self.game_transition_in, self.game_transition_out)