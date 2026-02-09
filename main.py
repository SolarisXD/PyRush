import pygame
from pygame.math import Vector2 as vector
from settings import *
from support import *

from pygame.image import load

from editor import Editor
from level import Level
from main_menu import MainMenu

from os import walk
import sys

class Main:
	def __init__(self):
		pygame.init()
		pygame.display.set_caption('PyRush - 2D Platformer')
		self.display_surface = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
		self.clock = pygame.time.Clock()
		self.imports()

		# Game states: 'menu', 'editor', 'level'
		self.game_state = 'menu'
		self.transition = Transition(self.toggle)
		
		# Initialize menu first
		self.main_menu = MainMenu(self.switch_to_editor, self.switch_to_level, self.quit_game)
		
		# Editor and level will be initialized when needed
		self.editor = None
		self.level = None

		# Default cursor (will change in editor)
		pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)

	def imports(self):
		# terrain
		self.land_tiles = import_folder_dict('graphics/terrain/land')
		self.water_bottom = load('graphics/terrain/water/water_bottom.png').convert_alpha()
		self.water_top_animation = import_folder('graphics/terrain/water/animation')

		# coins
		self.gold = import_folder('graphics/items/gold')
		self.silver = import_folder('graphics/items/silver')
		self.diamond = import_folder('graphics/items/diamond')
		self.particle = import_folder('graphics/items/particle')

		# palm trees
		self.palms = {folder: import_folder(f'graphics/terrain/palm/{folder}') for folder in list(walk('graphics/terrain/palm'))[0][1]}

		# enemies
		self.spikes = load('graphics/enemies/spikes/spikes.png').convert_alpha()
		self.tooth = {folder: import_folder(f'graphics/enemies/tooth/{folder}') for folder in list(walk('graphics/enemies/tooth'))[0][1]}
		self.shell = {folder: import_folder(f'graphics/enemies/shell_left/{folder}') for folder in list(walk('graphics/enemies/shell_left/'))[0][1]}
		self.pearl = load('graphics/enemies/pearl/pearl.png').convert_alpha()

		# player
		self.player_graphics = {folder: import_folder(f'graphics/player/{folder}') for folder in list(walk('graphics/player/'))[0][1]}

		# clouds
		self.clouds = import_folder('graphics/clouds')

		# sounds
		self.level_sounds = {
			'coin': pygame.mixer.Sound('audio/coin.wav'),
			'hit': pygame.mixer.Sound('audio/hit.wav'),
			'jump': pygame.mixer.Sound('audio/jump.wav'),
			'music': pygame.mixer.Sound('audio/SuperHero.ogg'),
		}
		# Initial volume will be set when switching to level

	def toggle(self):
		# Toggle between editor and level
		if self.game_state == 'editor':
			self.game_state = 'level'
		elif self.game_state == 'level':
			self.game_state = 'editor'
			if self.editor:
				self.editor.editor_music.play()
	
	def switch_to_menu(self):
		"""Return to main menu"""
		self.game_state = 'menu'
		pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
		# Update volumes in case they were changed
		self.update_volumes()
	
	def switch_to_editor(self):
		"""Switch to level editor"""
		if not self.editor:
			self.editor = Editor(self.land_tiles, self.switch, self.switch_to_menu)
			# Set custom cursor for editor
			surf = load('graphics/cursors/mouse.png').convert_alpha()
			cursor = pygame.cursors.Cursor((0,0), surf)
			pygame.mouse.set_cursor(cursor)
		
		# Always apply volume settings (in case they changed in settings)
		volumes = self.main_menu.get_volumes()
		self.editor.editor_music.set_volume(volumes['music'])
		
		self.game_state = 'editor'
		if self.editor:
			self.editor.editor_music.play()
	
	def switch_to_level(self, grid=None):
		"""Switch to gameplay level"""
		if grid:
			# Get volume settings from menu
			volumes = self.main_menu.get_volumes()
			
			# Apply volume to sound effects
			self.level_sounds['coin'].set_volume(volumes['sfx'])
			self.level_sounds['hit'].set_volume(volumes['sfx'])
			self.level_sounds['jump'].set_volume(volumes['sfx'])
			self.level_sounds['music'].set_volume(volumes['music'])
			
			self.level = Level(
				grid, 
				self.switch,{
					'land': self.land_tiles,
					'water bottom': self.water_bottom,
					'water top': self.water_top_animation,
					'gold': self.gold,
					'silver': self.silver,
					'diamond': self.diamond,
					'particle': self.particle,
					'palms': self.palms,
					'spikes': self.spikes,
					'tooth': self.tooth,
					'shell': self.shell,
					'player': self.player_graphics,
					'pearl': self.pearl,
					'clouds': self.clouds},
				self.level_sounds,
				return_to_menu=self.switch_to_menu)
		self.game_state = 'level'
		pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_ARROW)
	
	def quit_game(self):
		"""Quit the game"""
		pygame.quit()
		sys.exit()
	
	def update_volumes(self):
		"""Update volume for all active audio based on menu settings"""
		volumes = self.main_menu.get_volumes()
		
		# Update editor music if editor exists
		if self.editor:
			self.editor.editor_music.set_volume(volumes['music'])
		
		# Update level sounds
		self.level_sounds['coin'].set_volume(volumes['sfx'])
		self.level_sounds['hit'].set_volume(volumes['sfx'])
		self.level_sounds['jump'].set_volume(volumes['sfx'])
		self.level_sounds['music'].set_volume(volumes['music'])
		
		# Update level audio if level exists
		if self.level:
			self.level.bg_music.set_volume(volumes['music'])
			self.level.coin_sound.set_volume(volumes['sfx'])
			self.level.hit_sound.set_volume(volumes['sfx'])

	def switch(self, grid = None):
		"""Switch between editor and level with transition effect"""
		self.transition.active = True
		if grid:
			# Get volume settings from menu and apply to sounds
			volumes = self.main_menu.get_volumes()
			self.level_sounds['coin'].set_volume(volumes['sfx'])
			self.level_sounds['hit'].set_volume(volumes['sfx'])
			self.level_sounds['jump'].set_volume(volumes['sfx'])
			self.level_sounds['music'].set_volume(volumes['music'])
			
			# Pass return_to_menu callback when creating level
			self.level = Level(
				grid, 
				self.switch,{
					'land': self.land_tiles,
					'water bottom': self.water_bottom,
					'water top': self.water_top_animation,
					'gold': self.gold,
					'silver': self.silver,
					'diamond': self.diamond,
					'particle': self.particle,
					'palms': self.palms,
					'spikes': self.spikes,
					'tooth': self.tooth,
					'shell': self.shell,
					'player': self.player_graphics,
					'pearl': self.pearl,
					'clouds': self.clouds},
				self.level_sounds,
				return_to_menu=self.switch_to_menu)

	def run(self):
		while True:
			dt = self.clock.tick() / 1000
			
			# Handle different game states
			if self.game_state == 'menu':
				self.main_menu.run(dt)
			elif self.game_state == 'editor':
				if self.editor:
					self.editor.run(dt)
			elif self.game_state == 'level':
				if self.level:
					result = self.level.run(dt)
					if result == 'menu':
						self.switch_to_menu()
			
			self.transition.display(dt)
			pygame.display.update()


class Transition:
	def __init__(self, toggle):
		self.display_surface = pygame.display.get_surface()
		self.toggle = toggle
		self.active = False

		self.border_width = 0
		self.direction = 1
		self.center = (WINDOW_WIDTH /2, WINDOW_HEIGHT / 2)
		self.radius = vector(self.center).magnitude()
		self.threshold = self.radius + 100

	def display(self, dt):
		if self.active:
			self.border_width += 1000 * dt * self.direction
			if self.border_width >= self.threshold:
				self.direction = -1
				self.toggle()
			
			if self.border_width < 0:
				self.active = False
				self.border_width = 0
				self.direction = 1
			pygame.draw.circle(self.display_surface, 'black',self.center, self.radius, int(self.border_width))

if __name__ == '__main__':
	main = Main()
	main.run() 