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
BRICK_COLOR = (200, 200, 0)


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
        pygame.draw.circle(self.screen, self.colour,
                           (int(self.x), int(self.y)), self.size)

    def move(self):
        self.x += math.sin(self.angle) * self.speed
        self.y -= math.cos(self.angle) * self.speed

    def check_wall_colision(self):
        '''Returns true only if the ball colides with the floor.'''
        width = SCREEN_SIZE[0]

        if self.x >= width - self.size:
            self.x = 2 * (width - self.size) - self.x
            self.angle = - self.angle

        elif self.x <= self.size:
            self.x = 2 * self.size - self.x
            self.angle = - self.angle

        if self.y <= self.upper_limit + self.size:
            self.y = 2 * (self.upper_limit + self.size) - self.y
            self.angle = math.pi - self.angle

        elif self.y >= self.down_limit - self.size:
            self.y = 2 * (self.down_limit - self.size) - self.y
            self.angle = math.pi - self.angle
            return True

        return False

    def distance_to_line(self, a, b, c):
        ''' Distance from ball to a line = a * x + b * y + c.'''
        return abs(a * self.x + b * self.y + c)/math.sqrt(a**2 + b**2)

    def check_rect_colision(self, rect):

        left = rect.left
        right = rect.left + rect.width
        top = rect.top
        bottom = rect.top + rect.height

        dist_top = self.distance_to_line(0, 1, -top)
        dist_bottom = self.distance_to_line(0, 1, -bottom)
        dist_left = self.distance_to_line(1, 0, -left)
        dist_right = self.distance_to_line(1, 0, -right)
        
        x_intersec = (self.x + self.size >= left and self.x - self.size <= right)
        y_intersec = (self.y - self.size <= bottom and self.y + self.size >= top)
        # print x_intersec, y_intersec

        '''
        dist_bottom = self.distance_to_line((left + right)/2.0, bottom)
        dist_left = self.distance(left, (bottom + top)/2.0)
        dist_right = self.distance(right, (bottom + top)/2.0)
        '''
        a = [dist_top, dist_bottom, dist_left, dist_right]
        min_dist = min(a)
        colision = False
        count = 0

        if dist_bottom <= self.size and x_intersec:
            self.y = 2 * (bottom + self.size) - self.y
            self.angle = math.pi - self.angle
            print 'bottom up'
            colision = True
            count += 1
        elif dist_top <= self.size and x_intersec:
            self.y = 2 * (top - self.size) - self.y
            self.angle = math.pi - self.angle
            print 'top down'
            colision = True
            count += 1
        elif dist_left <= self.size and y_intersec:
            self.x = 2 * (left - self.size) - self.x
            self.angle = - self.angle
            colision = True
            print 'left right'
            count += 1
        elif dist_right <= self.size and y_intersec:
            self.x = 2 * (right + self.size) - self.x
            self.angle = - self.angle
            colision = True
            print 'right left'
            count += 1   
        '''

        # print left, right, bottom, top, self.x, self.y
        if self.x + self.size >= left and self.x - self.size <= right:
            # top down colision
            # if self.y >= top - self.size and self.y <= bottom:
            if dist_top == min_dist and self.y >= top - self.size and self.y <= bottom:
                self.y = 2 * (top - self.size) - self.y
                self.angle = math.pi - self.angle
                print 'top down'
                colision = True
                count += 1

            # bottom up colision
            elif dist_bottom == min_dist and self.y <= bottom + self.size and self.y >= top:
                self.y = 2 * (bottom + self.size) - self.y
                self.angle = math.pi - self.angle
                print 'bottom up'
                colision = True
                count += 1

        if self.y <= bottom - self.size and self.y >= top + self.size:
            # right left colision
            if dist_right == min_dist and self.x <= right + self.size and self.x >= left:
                self.x = 2 * (right + self.size) - self.x
                self.angle = - self.angle
                colision = True
                print 'right left'
                count += 1

            # left right colision
            elif dist_left == min_dist and self.x >= left + self.size and self.x <= right:
                self.x = 2 * (left + self.size) - self.x
                self.angle = - self.angle
                colision = True
                print 'left right'
                count += 1
        '''
        if count > 0:
            print count

        return colision

class Environment:
    '''Brick blast ball environment.
       This class not only has all the pygame code to physics and drawing, but
       also has what is needed to interact with an agent.
    '''
    def __init__(self):
        pygame.init()

        # create screen
        self.screen = pygame.display.set_mode(SCREEN_SIZE)
        # screen title
        pygame.display.set_caption("PLEASE WORK")

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
        self.init_game()

    def init_game(self):
        self.phase = 0
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
        self.ball = Ball((SCREEN_SIZE[0]/2.0, self.bottom_line.top - 16),
                         screen=self.screen,
                         upper_limit=self.top_line.top + line_height,
                         down_limit=self.bottom_line.top)

    def draw_lines(self):
        # Rect: left, top, width, height

        pygame.draw.rect(self.screen, WHITE, self.top_line)
        pygame.draw.rect(self.screen, WHITE, self.bottom_line)

    def random_row(self):
        '''For now let's keep this as simple as we can.'''

        # 0.6 of change of have some brick at each position of the row
        # if there's a brick then: 0.25 of chance of having value V
        # and 0.15 of chance of having value V * 2
        # obs: it can be full (no zeros) nor empty (only zeros)
        v = self.phase + 1
        row = np.random.choice([v, v * 2, 0],
                               self.bricks_matrix.shape[1],
                               p=[0.25, 0.15, 0.6])

        # if there are no zeros or is full of zeros then generate
        # another row
        zero_indexes = np.nonzero(row == 0)[0]
        if zero_indexes.size == 0 or zero_indexes.size == row.size:
            self.random_row()

        # generate a +1 ball in one of the empty spaces
        # row[np.random.choice(zero_indexes)] = -1

        return row

    def create_next_row(self):
        '''Bricks and +1 balls are created randomly.'''

        # generate a valid random row
        r = self.random_row()

        # roll the matrix (this will move everything one row below
        num_cols = self.bricks_matrix.shape[1]
        self.bricks_matrix = np.roll(self.bricks_matrix, num_cols)

        # add the row to the beginning
        self.bricks_matrix[1] = r

    def brick_pos(self, r, c):
        pos_x = c * BLOCK_SIZE
        pos_y = r * BLOCK_SIZE + BLOCK_SIZE
        return pos_x, pos_y

    def create_bricks(self):
        self.bricks = []
        row, col = np.nonzero(self.bricks_matrix != 0)
        for r, c in zip(row, col):
            pos_x, pos_y = self.brick_pos(r, c)
            brick = pygame.Rect(pos_x, pos_y,
                                self.BRICK_WIDTH, self.BRICK_HEIGHT)
            self.bricks.append((r, c, brick))

    def draw_brick(self, r, c, border_size=10):
        v = self.bricks_matrix[r][c]
        pos_x, pos_y = self.brick_pos(r, c)
        rect = pygame.Rect(pos_x + border_size/2.0,
                           pos_y + border_size/2.0,
                           self.BRICK_WIDTH - border_size,
                           self.BRICK_HEIGHT - border_size)
        border = pygame.Rect(pos_x, pos_y,
                             self.BRICK_WIDTH, self.BRICK_HEIGHT)
        pygame.draw.rect(self.screen, WHITE, border)
        pygame.draw.rect(self.screen, BRICK_COLOR, rect)

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

    def set_ball_angle(self, pos):
        # vector from ball to the cursor
        pos_x, pos_y = pos
        dx = pos_x - self.ball.x
        dy = pos_y - self.ball.y

        self.ball.angle = math.atan2(dy, dx) + 0.5 * math.pi

    def next_phase(self):
        self.waiting_input = True
        self.create_next_row()
        self.phase += 1

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

        floor_colision = self.ball.check_wall_colision()

        for i, element in enumerate(self.bricks):
            r, c, b = element
            if self.ball.check_rect_colision(b):
                # remove value from brick
                print self.bricks_matrix[r][c], r, c
                if self.bricks_matrix[r][c] > 0:
                    self.bricks_matrix[r][c] -= 1

        # print floor_colision
        if floor_colision:
            if np.nonzero(self.bricks_matrix[-1])[0].size:
                self.init_game()
            else:
                self.next_phase()

    def show_stats(self):
        if self.font:
            s = 'PHASE: ' + str(self.phase)
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

    def play(self):
        if not self.waiting_input:
            self.create_bricks()
            self.ball.move()
            self.handle_collisions()

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

            if self.state == GameState.HUMAN_PLAYING:
                self.play()
            elif self.state == GameState.MENU:
                self.show_message("PRESS SPACE TO LAUNCH THE BALL")
            elif self.state == GameState.GAME_OVER:
                self.show_message("GAME OVER. PRESS ENTER TO PLAY AGAIN")

            # draw everything
            self.draw()

            # updates display
            pygame.display.flip()


if __name__ == "__main__":
    Environment().run()
