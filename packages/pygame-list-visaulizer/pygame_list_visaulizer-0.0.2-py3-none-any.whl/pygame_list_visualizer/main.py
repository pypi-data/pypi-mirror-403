import random
import pygame

 
#"numbers" is a list, put in None matching list if you dont want to use that "feature"
class numbers_displayer:
  def __init__(self, WIDTH, HEIGHT, numbers, scale, window_name, matching_list):
    self.WIDTH = WIDTH
    self.HEIGHT = HEIGHT
    self.numbers = numbers
    self.scale = scale
    self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
    self.numbers_length = len(numbers)
    self.matching_list = matching_list
    self.clock = pygame.time.Clock()
    pygame.display.set_caption(window_name)
 
  def update_screen(self):
         self.screen.fill((0, 0, 0))    
         for i in range(self.numbers_length):
             current_x = int(i * self.WIDTH / self.numbers_length)
             next_x = int((i + 1) * self.WIDTH / self.numbers_length)
             width = next_x - current_x 
             if not self.matching_list:
                 color = (255, 255, 255)
             else:
                 color = (0, 255, 0) if self.matching_list[i] == self.numbers[i] else (255, 0, 0)
             pygame.draw.rect(
                 self.screen, 
                 color, 
                 (
                     current_x, 
                     self.HEIGHT - (self.numbers[i] * self.scale), 
                     width, 
                     self.numbers[i] * self.scale
                 )
             )
         pygame.display.flip()

