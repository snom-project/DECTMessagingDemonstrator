import pygame
import config as cf

BLACK = (0,0,0)

size = cf.size

class Paddle(pygame.sprite.Sprite):
    #This class represents a paddle. It derives from the "Sprite" class in Pygame.

    def __init__(self, color, width, height):
        # Call the parent class (Sprite) constructor
        super().__init__()

        # Pass in the color of the paddle, and its x and y position, width and height.
        # Set the background color and set it to be transparent
        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)

        # Draw the paddle (a rectangle!)
        pygame.draw.rect(self.image, color, [0, 0, width, height])

        # Fetch the rectangle object that has the dimensions of the image.
        self.rect = self.image.get_rect()
        # expose the color
        self.color = color

    def movePos(self, pos):
        x = pos['x']
        y = pos['y']
        self.rect.x = x
        self.rect.y = y

    def moveLeft(self, pixels):
        self.rect.x -= pixels
	    #Check that you are not going too far (off the screen)
        if self.rect.x < 0:
          self.rect.x = 0

    def moveRight(self, pixels):
        self.rect.x += pixels
        #Check that you are not going too far (off the screen)
        if self.rect.x > size[0]*0.90:
          self.rect.x = size[0]*0.90
