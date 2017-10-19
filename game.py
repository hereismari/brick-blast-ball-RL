'''
Copyright 2017 Marianne Linhares Monteiro, @mari-linhares at github.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

# -------- Imports ------------
import copy
from enum import Enum
import math
import sys

import numpy as np
import pygame

# --------- Constants ---------
# screen
BLOCK_SIZE = 64
NUM_BLOCKS_Y = 10
NUM_BLOCKS_X = 7
SCREEN_SIZE = BLOCK_SIZE * NUM_BLOCKS_X, BLOCK_SIZE * NUM_BLOCKS_Y + 100

# color constants
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
BRICK_COLOR = {1: (221, 218, 94), 2: (90, 185, 186), 3: (1, 161, 247), 4: (237, 134, 186)}


# ------- Classes ----------
class GameState(Enum):
    '''These are the possible game states with different behaviours.
       This class is not related with the possible states that
       the agent considers.
    '''
    MENU = 0
    AGENT_PLAYING = 1
    HUMAN_PLAYING = 2
    GAME_OVER = 3


class Ball():
    '''Ball in the game.'''
    def __init__(self, (x, y), screen, upper_limit, down_limit, size=8,
                 speed=10):
        self.screen = screen
        self.x = x
        self.y = y
        self.size = size
        self.colour = WHITE
        self.speed = speed
        self.angle = 0

        self.upper_limit = upper_limit
        self.down_limit = down_limit

    def display(self):
        '''Draw circle.'''
        pygame.draw.circle(self.screen, self.colour,
                           (int(self.x), int(self.y)), self.size)

    def move(self):
        '''Move ball.'''
        self.x += math.sin(self.angle) * self.speed
        self.y -= math.cos(self.angle) * self.speed

    def set_angle(self, new_angle):
        '''Sets angle to new angle and ensures that angle is [-pi, pi].'''
        self.angle = new_angle
        aux_value = (self.angle + math.pi)/(2 * math.pi)  # avoids line > 80
        correction = 2 * math.pi * math.floor(aux_value)
        self.angle = self.angle - correction

    def check_wall_collision(self):
        '''Returns true only if the ball colides with the floor.'''
        width = SCREEN_SIZE[0]

        if self.x >= width - self.size:
            self.x = 2 * (width - self.size) - self.x
            self.set_angle(-1 * self.angle)

        elif self.x <= self.size:
            self.x = 2 * self.size - self.x
            self.set_angle(-1 * self.angle)

        if self.y <= self.upper_limit + self.size:
            self.y = 2 * (self.upper_limit + self.size) - self.y
            self.set_angle(math.pi - self.angle)

        elif self.y >= self.down_limit - self.size:
            self.y = 2 * (self.down_limit - self.size) - self.y
            self.set_angle(math.pi - self.angle)
            return True

        return False

    def distance_to_line(self, a, b, c):
        ''' Distance from ball to a line = a * x + b * y + c.'''
        return abs(a * self.x + b * self.y + c)/math.sqrt(a**2 + b**2)

    def check_rect_collision(self, rect):
        '''Check collision between ball and a rectangle (brick).'''
        # TODO: fix small bugs related to left right colisions
        # print self.angle
        # rect edges
        left = rect.left
        right = rect.left + rect.width
        top = rect.top
        bottom = rect.top + rect.height

        # distance between rect lines and ball
        dist_top = self.distance_to_line(0, 1, -top)
        dist_bottom = self.distance_to_line(0, 1, -bottom)
        dist_left = self.distance_to_line(1, 0, -left)
        dist_right = self.distance_to_line(1, 0, -right)
        
        # check x and y intersections
        x_intersec = (self.x + self.size >= left and self.x - self.size <= right)
        y_intersec = (self.y - self.size <= bottom and self.y + self.size >= top)
        
        colision = False
        # bottom up collision 
        if dist_bottom <= self.size and x_intersec and abs(self.angle) < math.pi/2.0:
            self.y = 2 * (bottom + self.size) - self.y
            self.set_angle(math.pi - self.angle)
            # print 'bottom up'
            colision = True
        # top down collision
        elif dist_top <= self.size and x_intersec and abs(self.angle) > math.pi/2.0:
            self.y = 2 * (top - self.size) - self.y
            self.set_angle(math.pi - self.angle)
            # print 'top down'
            colision = True
        # left right collision
        elif dist_left <= self.size and y_intersec and self.angle > 0:
            self.x = 2 * (left - self.size) - self.x
            self.set_angle(-1 * self.angle)
            colision = True
            # print 'left right'
        # right left collision
        elif dist_right <= self.size and y_intersec and self.angle < 0:
            self.x = 2 * (right + self.size) - self.x
            self.set_angle(-1 * self.angle)
            colision = True
            # print 'right left'
 
        return colision

class Environment:
    '''Brick blast ball environment.
       This class not only has all the pygame code to physics and drawing, but
       also has what is needed to interact with an agent.
    '''
    def __init__(self, ball_speed=10, state=GameState.MENU):
        pygame.init()

        # agent related attributes
        self.actions = np.arange(math.pi/2.0 * -1 + 0.1, math.pi/2.0, 0.1)
        self.number_of_actions = self.actions.shape[0]

        # create screen
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        # screen title
        pygame.display.set_caption("PLEASE WORK")

        # max phase the environement has ever seen
        self.max_phase = 0

        # create clock
        self.clock = pygame.time.Clock()

        # this will be used to draw on the screen
        self.font = pygame.font.Font(None, 30)

        # brick constants
        self.BRICK_WIDTH = BLOCK_SIZE
        self.BRICK_HEIGHT = BLOCK_SIZE

        # line constants
        self.LINE_HEIGHT = 2
        self.LINE_WIDTH = SCREEN_SIZE[0]

        # init game
        self.state = state       
        self.init_game(ball_speed)
        

    def init_game(self, ball_speed):
        '''Initialize main objects of the game accordingly with the game mode.'''
        self.phase = 0
        if self.state == GameState.HUMAN_PLAYING:
            self.state = GameState.MENU
            
        self.waiting_input = False

        # stores the bricks values
        self.bricks_matrix = np.zeros((NUM_BLOCKS_Y - 1, NUM_BLOCKS_X))

        # create display lines
        line_height = 10
        self.top_line = pygame.Rect(0, BLOCK_SIZE - line_height,
                                    SCREEN_SIZE[0], line_height)
        self.bottom_line = pygame.Rect(0,
                                       SCREEN_SIZE[1] - BLOCK_SIZE + line_height,
                                       SCREEN_SIZE[0], line_height)
        # ball
        self.ball_speed = ball_speed
        self.ball = Ball((SCREEN_SIZE[0]/2.0, self.bottom_line.top - 16),
                         screen=self.screen,
                         upper_limit=self.top_line.top + line_height,
                         down_limit=self.bottom_line.top,
                         speed=ball_speed)

    def set_ball_position(self):
        self.ball.x = SCREEN_SIZE[0]/2.0
        self.ball.y = self.bottom_line.top - 16
    
    def step(self, state, action):
        '''Interaction with the agent.
            
            Args:
                state (tensor): a tensor with the same shape as self.bricks_matrix.
                action (angle): index of an action in self.actions (ball initial angle).
            Returns:
                next_state (tensor): a tensor with the same shaoe as self.bricks_matrix.
                r (int): reward. -1 if lost, 0 otherwhise.
        '''
        self.ball.set_angle(self.actions[action])
        _, next_state, r = self.run()
        if r == -1:
            self.init_game(self.ball_speed)
        else:
            # unkown behaviour from the environment
            self.next_phase()
            next_state = copy.copy(self.bricks_matrix)   
        return next_state, r

    # ------------------ Create rows ------------------------
    def random_row(self):
        '''For now let's keep this as simple as we can.'''

        # TODO:
        # 0.6 of change of have some brick at each position of the row
        # if there's a brick then: 0.25 of chance of having value V
        # and 0.10 of chance of having value V * 2 and 0.05 of having V * 4
        # obs: it can be full (no zeros) nor empty (only zeros)

        # NOW: only bricks with v = 1
        v = 1  # let's make this as simple as possible, v is constant
        row = np.random.choice([v, 0],
                               self.bricks_matrix.shape[1],
                               p=[0.5, 0.5])

        # if there are no zeros or is full of zeros then generate
        # another row
        zero_indexes = np.nonzero(row == 0)[0]
        if zero_indexes.size == 0 or zero_indexes.size == row.size:
            return self.random_row()

        return row

    def create_next_row(self):
        '''Bricks are created randomly.'''

        # generate a valid random row
        r = self.random_row()

        # roll the matrix (this will move everything one row below
        num_cols = self.bricks_matrix.shape[1]
        self.bricks_matrix = np.roll(self.bricks_matrix, num_cols)

        # add the row to the beginning
        self.bricks_matrix[1] = r

    # ----------------- Bricks --------------------
    def brick_pos(self, r, c):
        '''Get a brick pos given its position at self.bricks_matrix.'''
        pos_x = c * BLOCK_SIZE
        pos_y = r * BLOCK_SIZE + BLOCK_SIZE
        return pos_x, pos_y

    def create_bricks(self):
        '''Create bricks that can collide with the ball.''' 
        self.bricks = []
        row, col = np.nonzero(self.bricks_matrix != 0)
        for r, c in zip(row, col):
            pos_x, pos_y = self.brick_pos(r, c)
            brick = pygame.Rect(pos_x, pos_y,
                                self.BRICK_WIDTH, self.BRICK_HEIGHT)
            self.bricks.append((r, c, brick))

    # ----------------- Drawing ---------------------
    def draw_brick(self, r, c, border_size=10):
        v = int(self.bricks_matrix[r][c])
        pos_x, pos_y = self.brick_pos(r, c)
        rect = pygame.Rect(pos_x + border_size/2.0,
                           pos_y + border_size/2.0,
                           self.BRICK_WIDTH - border_size,
                           self.BRICK_HEIGHT - border_size)
        border = pygame.Rect(pos_x, pos_y,
                             self.BRICK_WIDTH, self.BRICK_HEIGHT)
        pygame.draw.rect(self.screen, WHITE, border)
        pygame.draw.rect(self.screen, BRICK_COLOR[v], rect)

        # negative_corr = 3 if v < 0 else 0
        s = str(v)
        size = self.font.size(s)
        self.screen.blit(self.font.render(s, True, BLACK),
                         ((pos_x + (BLOCK_SIZE - size[0])/2.0,
                          (pos_y + (BLOCK_SIZE - size[1])/2.0))))

    def draw_bricks(self):
        row, col = np.nonzero(self.bricks_matrix != 0)
        for r, c in zip(row, col):
            self.draw_brick(r, c)
    
    def draw_lines(self):
        # Rect: left, top, width, height
        pygame.draw.rect(self.screen, WHITE, self.top_line)
        pygame.draw.rect(self.screen, WHITE, self.bottom_line)

    def show_stats(self):
        if self.font:
            s = 'LEVEL: ' + str(self.phase) + ' BEST : ' + str(self.max_phase) 
            size = self.font.size(s)
            font_surface = self.font.render(s, False, WHITE)
            self.screen.blit(font_surface, ((SCREEN_SIZE[0] - size[0])/2, 10))

    def show_message(self, message):
        if self.font:
            size = self.font.size(message)
            font_surface = self.font.render(message, False, WHITE)
            x = (SCREEN_SIZE[0] - size[0]) / 2
            y = (SCREEN_SIZE[1] - size[1]) / 2
            self.screen.blit(font_surface, (x, y))

    def draw(self):
        # draw all bricks
        self.draw_bricks()

        # draw ball
        self.ball.display()

        # write status
        self.show_stats()

        # draw lines
        self.draw_lines()

    # ----------------- Running game -----------------------
    def set_ball_angle(self, pos):
        # vector from ball to the cursor
        pos_x, pos_y = pos
        dx = pos_x - self.ball.x
        dy = pos_y - self.ball.y

        self.ball.set_angle(math.atan2(dy, dx) + 0.5 * math.pi)

    def next_phase(self):
        self.waiting_input = True
        self.create_next_row()
        self.phase += 1
        self.set_ball_position()

    def check_input(self, mouse_pos):
        keys = pygame.key.get_pressed()

        if self.state == GameState.MENU:
            if keys[pygame.K_SPACE]:
                self.state = GameState.HUMAN_PLAYING
                self.next_phase()
        elif self.state == GameState.HUMAN_PLAYING and self.waiting_input:
            if mouse_pos is not None:
                self.set_ball_angle(mouse_pos)
                self.waiting_input = False

    def handle_collisions(self):
        floor_collision = self.ball.check_wall_collision()

        for i, element in enumerate(self.bricks):
            r, c, b = element
            if self.ball.check_rect_collision(b):
                # remove value from brick
                # print self.bricks_matrix[r][c], r, c
                if self.bricks_matrix[r][c] > 0:
                    self.bricks_matrix[r][c] -= 1

        if self.state == GameState.AGENT_PLAYING:
            final_state = floor_collision and np.nonzero(self.bricks_matrix[-1])[0].size
            res = floor_collision, copy.copy(self.bricks_matrix), -1 if final_state else 0 
            if final_state: 
                self.max_phase = max(self.phase, self.max_phase)            
                self.init_game(self.ball_speed)
            return res
        else:            
            if floor_collision:
                if np.nonzero(self.bricks_matrix[-1])[0].size:
                    self.max_phase = max(self.phase, self.max_phase)
                    self.init_game(self.ball_speed)
                else:
                    self.next_phase()

        return floor_collision

    def play(self):
        if not self.waiting_input:
            self.create_bricks()
            self.ball.move()
            self.handle_collisions()

    def play_agent(self):
        '''Called only when an agent is playing.'''
        self.create_bricks()
        self.ball.move()
        return self.handle_collisions()

    def run(self):
        while 1:
            # check for events
            mouse_pos = None
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_pos = pygame.mouse.get_pos()

            # clock tick
            self.clock.tick(50)
            # make the background black
            self.screen.fill(BLACK)
            # check input
            self.check_input(mouse_pos)

            if self.state == GameState.AGENT_PLAYING:
                res = self.play_agent()
                if res[0]:
                    return res
            if self.state == GameState.HUMAN_PLAYING:
                self.play()
            elif self.state == GameState.MENU:
                message = 'PRESS SPACE TO PLAY THE GAME'
                self.show_message(message)
            elif self.state == GameState.GAME_OVER:
                self.show_message("GAME OVER. PRESS ENTER TO PLAY AGAIN")

            # draw everything
            self.draw()

            # updates display
            pygame.display.flip()


if __name__ == "__main__":
    Environment().run()
