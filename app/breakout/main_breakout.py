#Import the pygame library and initialise the game engine
from random import random, randint
import pygame
from pygame.locals import *

#Let's import the Paddle Class & the Ball Class
from paddle import Paddle
from ball import Ball
from brick import Brick
from DB.DECTMessagingDb import DECTMessagingDb
import update_all_devices as ud
import config as cf
 
pygame.init()

# Define some colors
BLACK   = (100, 100, 100)
WHITE   = (255, 255, 255)
RED     = (255,   0,   0)
ORANGE = (255,100,0)
GREEN   = (  0, 255,   0)
BLUE    = ( 20,  20, 255)
DARKBLUE = (36,90,190)
LIGHTBLUE = (0,176,240)
YELLOW  = (255, 205,   0)
CYAN    = (  0, 255, 255)
PURPLE  = (255,   0, 255)

colors = [RED, GREEN, BLUE, PURPLE, CYAN]

score = 0
lives = 30
 
# Open a new window
size = cf.size
x_width, y_height = size 
#screen = pygame.display.set_mode(size, FULLSCREEN)
screen = pygame.display.set_mode(size, RESIZABLE)

pygame.display.set_caption("Breakout Game")
 
#This will be a list that will contain all the sprites we intend to use in our game.
all_sprites_list = pygame.sprite.Group()
 
#Create the Paddle
#paddle = Paddle(LIGHTBLUE, 100, 10)
paddles = []
# paddle = Paddle(LIGHTBLUE, size[0]/cf.num_m9bs, size[1]/30)

#paddle.rect.x = size[0]/2
#paddle.rect.y = size[1]*0.95

# dict contains all currently exsting paddles / players and current colors
# example: {"0328D7830E": "ORANGE"} 
active_paddles = {}
 
#Create the ball sprite
ball = Ball(colors[0],10,10)
ball.rect.x = 345
ball.rect.y = cf.size[1] / 2 
 
all_bricks = pygame.sprite.Group()
range_val = (size[0]-60)/100
for i in range(int(range_val)):
    brick = Brick(RED,80,30)
    brick.rect.x = 60 + i* 100
    brick.rect.y = 60
    all_sprites_list.add(brick)
    all_bricks.add(brick)
for i in range(int(range_val)):
    brick = Brick(ORANGE,80,30)
    brick.rect.x = 60 + i* 100
    brick.rect.y = 100
    all_sprites_list.add(brick)
    all_bricks.add(brick)
for i in range(int(range_val)):
    brick = Brick(YELLOW,80,30)
    brick.rect.x = 60 + i* 100
    brick.rect.y = 140
    all_sprites_list.add(brick)
    all_bricks.add(brick)
for i in range(int(range_val)):
    brick = Brick(WHITE,80,30)
    brick.rect.x = 60 + i* 100
    brick.rect.y = 180
    all_sprites_list.add(brick)
    all_bricks.add(brick)
 
# Add the paddle to the list of sprites
#all_sprites_list.add(paddle)
all_sprites_list.add(ball)
 
# The loop will carry on until the user exit the game (e.g. clicks the close button).
carryOn = True
 
# The clock will be used to control how fast the screen updates
clock = pygame.time.Clock()

# get access to the DB
# DB reuse and type
ODBC_=False
INITDB_=False
msgDb = DECTMessagingDb(odbc=ODBC_, initdb=INITDB_)
 
# -------- Main Program Loop -----------
while carryOn:
    # --- Main event loop
    for event in pygame.event.get(): # User did something
        if event.type == pygame.QUIT: # If user clicked close
              carryOn = False # Flag that we are done so we exit this loop
 
    #Moving the paddle when the use uses the arrow keys
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        if paddles: 
            paddles[0].moveLeft(5)
    if keys[pygame.K_RIGHT]:
        if paddles: 
            paddles[0].moveRight(5)
    if keys[pygame.K_UP]:
        carryOn = False # Flag that we are done so we exit this loop
 
    # --- Game logic should go here
    all_sprites_list.update()
 
    #Check if the ball is bouncing against any of the 4 walls:
    if ball.rect.x>=size[0]*0.99:
        ball.velocity[0] = -ball.velocity[0]
    if ball.rect.x<=0:
        ball.velocity[0] = -ball.velocity[0]
    if ball.rect.y>size[1]*0.99:
        ball.velocity[1] = -ball.velocity[1]
        lives -= 1
        ball.rect.x = (size[0] / 2 )
        ball.rect.y = (size[1] / 2 )
        ball.velocity[0] = randint(-4,4)
        if lives == 0:
            #Display Game Over Message for 3 seconds
            font = pygame.font.Font(None, 74)
            text = font.render("GAME OVER", 1, WHITE)
            screen.blit(text, (250,300))
            pygame.display.flip()
            pygame.time.wait(3000)
 
            #Stop the Game
            carryOn=False
 
    if ball.rect.y<40:
        ball.velocity[1] = -ball.velocity[1]
        # modify agle a bit to avoid straight shots for ever.
        ball.velocity[0] = -ball.velocity[0] + randint(-1,1)
        if ball.velocity[1] > 4:
            ball.velocity[1] = 4 
            # make sure position is before collision. 
            ball.rect.y = 40
 
    #Detect collisions between the ball and the paddles
    more_than_one = False
    for idx, single_pad in enumerate(paddles):
        if single_pad and pygame.sprite.collide_mask(ball, single_pad):
            print(single_pad.color)
            # check if there is more than one paddle on the same position - this is not allowed to bounce
            xpos = 9999
            for idx, single_pad in enumerate(paddles):
                if xpos == single_pad.rect.x:
                    print('more than one paddle in the same position - NOT VALID - hahaha')
                    more_than_one = True
                else: 
                    xpos = single_pad.rect.x
            if not more_than_one:
                if ball.color != single_pad.color and False:
                    print(single_pad.color)
                    font = pygame.font.Font(None, 50)
                    text = font.render("Wrong color - re-organize next time!", 1, ORANGE)
                    screen.blit(text, (250,300))
                    pygame.display.flip()
                    pygame.time.wait(10)
                    ball.rect.y += ball.velocity[1]

                else: 
                    ball.rect.x -= ball.velocity[0]
                    ball.rect.y -= ball.velocity[1]

                    if False:
                        # make a big ball with random color 
                        color_idx = randint(0,len(paddles)-1)
                        ball.update_color(colors[color_idx])
                        ball.update_size(30, 30)
                        ball.rect.y -= 50
                    ball.bounce()
                    break
            else:
                # Display more then one paddle 
                font = pygame.font.Font(None, 50)
                text = font.render("Invalid - Ha Ha Ha", 1, ORANGE)
                screen.blit(text, (250,300))
                pygame.display.flip()
                pygame.time.wait(10)
        
    
    #Check if there is the ball collides with any of bricks
    brick_collision_list = pygame.sprite.spritecollide(ball,all_bricks,False)
    for brick in brick_collision_list:
      ball.bounce()
      score += 1
      brick.kill()
      if len(all_bricks)==0:
           #Display Level Complete Message for 3 seconds
            font = pygame.font.Font(None, 74)
            text = font.render("LEVEL COMPLETE", 1, WHITE)
            screen.blit(text, (200,300))
            pygame.display.flip()
            pygame.time.wait(3000)
 
            #Stop the Game
            carryOn=False
 
    # --- Drawing code should go here
    # First, clear the screen to dark blue.
    screen.fill(DARKBLUE)
    pygame.draw.line(screen, WHITE, [0, 38], [size[0], 38], 2)
 
    #Display the score and the number of lives at the top of the screen
    font = pygame.font.Font(None, 34)
    text = font.render("Score: " + str(score), 1, WHITE)
    screen.blit(text, (20,10))
    text = font.render("Lives: " + str(lives), 1, WHITE)
    screen.blit(text, (size[0]*0.85,10))
 
    #Now let's draw all the sprites in one go. (For now we only have 2 sprites!)
    all_sprites_list.draw(screen)
 
    # --- Go ahead and update the screen with what we've drawn.
    pygame.display.flip()

    # get all the device positions
    if (pygame.time.get_ticks() % 500) < 20 :
        if False:
            # make a small ball
            ball.update_size(10,10)

        print(pygame.time.get_ticks())
        positions = ud.update_all_devices(msgDb)
        if len(positions) > 0:
            for pos in positions:
                if pos['btmac'] not in active_paddles:
                    new_color = colors[len(active_paddles)]
                    # add paddle
                    print('NEW PADDLE - NEW PLAYER')
                    paddle = Paddle(new_color, size[0]/cf.num_m9bs, size[1]/30)
                    paddles.append(paddle)
                    all_sprites_list.add(paddle)

                    # add in dict
                    active_paddles[pos['btmac']] = len(active_paddles)
            
                # move the right paddle to its position
                pos['y'] = size[1]*0.90 - (active_paddles[pos['btmac']] * (size[1]/30 + 5))
                paddles[active_paddles[pos['btmac']]].movePos(pos)


    # --- Limit to 60 frames per second
    clock.tick(60)
 
#Once we have exited the main program loop we can stop the game engine:
pygame.quit()
