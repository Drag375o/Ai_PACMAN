import sys
import pygame

print("Python:", sys.version)
print("Pygame:", pygame.version.ver)

pygame.init()
screen = pygame.display.set_mode((300, 200))
pygame.display.set_caption("Env Check")
screen.fill((30, 30, 40))
pygame.display.flip()

pygame.time.wait(2000)  # keep the window up for 2 seconds
pygame.quit()
print("Window opened and closed cleanly.")