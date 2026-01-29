import random
import pygame

class visualize_list:
    def __init__(self, WIDTH=400, HEIGHT=600, window_name="list_visualizer", scale=1):
      self.WIDTH = WIDTH
      self.HEIGHT = HEIGHT
      self.list = []
      self.scale = scale
      self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
      self.list_length = 0
      self.matching_list = []
      self.clock = pygame.time.Clock()
      pygame.display.set_caption(window_name)
    def attach_list(self, list):
        self.list = list
        self.list_length = len(list)
    def list_compare(self, list):
        self.matching_list = list
    def update_screen(self):
        if self.list:
            self.screen.fill((0, 0, 0))    
            for i in range(self.list_length):
                current_x = int(i * self.WIDTH / self.list_length)
                next_x = int((i + 1) * self.WIDTH / self.list_length)
                width = next_x - current_x 
                if not self.matching_list:
                    color = (255, 255, 255)
                else:
                    color = (0, 255, 0) if self.matching_list[i] == self.list[i] else (255, 0, 0)
                pygame.draw.rect(
                    self.screen, 
                    color, 
                    (
                        current_x, 
                        self.HEIGHT - (self.list[i] * self.scale), 
                        width, 
                        self.list[i] * self.scale
                    )
                )
            pygame.display.flip()
        else:
            print("List not intilized")

