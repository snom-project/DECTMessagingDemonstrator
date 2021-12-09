import pygame
from random import randint

BLACK = (0, 0, 0)
 
class Ball(pygame.sprite.Sprite):
    #This class represents a ball. It derives from the "Sprite" class in Pygame.
    
    def __init__(self, color, width, height):
        # Call the parent class (Sprite) constructor
        super().__init__()
        
        # Pass in the color of the ball, and its x and y position, width and height.
        # Set the background color and set it to be transparent
        self.image = pygame.Surface([width, height])
        self.image.fill(BLACK)
        self.image.set_colorkey(BLACK)
 
        # Draw the ball (a rectangle!)
        pygame.draw.rect(self.image, color, [0, 0, width, height])
        
        # expose the ball color
        self.color = color
        self.width = width
        self.height = height

        self.velocity = [randint(2,4),randint(-4,4)]
        if self.velocity[0] == 0:
            self.velocity[0] = 2
        if self.velocity[1] == 0:
            self.velocity[1] = 2
        
        # Fetch the rectangle object that has the dimensions of the image.
        self.rect = self.image.get_rect()
    
    def update_size(self, width, height):
        self.width = width
        self.height = height
        self.image = pygame.Surface([width, height])
        pygame.draw.rect(self.image, self.color, [0, 0, self.width, self.height])

    def update_color(self, color):
        self.color = color
        pygame.draw.rect(self.image, color, [0, 0, self.width, self.height])

    def update(self):
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]
          
    def bounce(self):
        self.velocity[0] = -self.velocity[0]
        self.velocity[1] = randint(-2,2)
        if self.velocity[1] == 0:
            self.velocity[1] = 2
        if self.velocity[1] < 0:
            self.velocity[1] *= 8

