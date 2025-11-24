import pygame
import os

def start_music(filename="Puzzle_Music_-_Lo_Fi.mp3"):
    pygame.mixer.init()
    path = os.path.join(os.path.dirname(__file__), filename)
    pygame.mixer.music.load(path)
    pygame.mixer.music.play(-1)

def stop_music():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except:
        pass