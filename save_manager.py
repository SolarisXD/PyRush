import pygame
import json
import os
from datetime import datetime
from pathlib import Path

class SaveManager:
	"""Manages save and load functionality for levels and game state with multiple save slots"""
	
	def __init__(self, num_slots=3):
		self.num_slots = num_slots
		self.save_directory = Path('save_data')
		self.save_directory.mkdir(exist_ok=True)
		
		# Separate directories for levels and game states
		self.level_directory = self.save_directory / 'levels'
		self.gamestate_directory = self.save_directory / 'gamestates'
		self.level_directory.mkdir(exist_ok=True)
		self.gamestate_directory.mkdir(exist_ok=True)
	
	def get_level_save_path(self, slot):
		"""Get the file path for a level save slot"""
		return self.level_directory / f'level_slot_{slot}.json'
	
	def get_gamestate_save_path(self, slot):
		"""Get the file path for a game state save slot"""
		return self.gamestate_directory / f'gamestate_slot_{slot}.json'
	
	def save_level(self, slot, level_data, level_name="Custom Level"):
		"""
		Save level data to a specific slot
		
		Args:
			slot (int): Save slot number (0 to num_slots-1)
			level_data (dict): Level grid data from editor
			level_name (str): Name of the level
		
		Returns:
			bool: True if save was successful
		"""
		if not 0 <= slot < self.num_slots:
			print(f"Invalid slot number: {slot}")
			return False
		
		try:
			# Prepare save data
			save_data = {
				'level_name': level_name,
				'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
				'level_data': self._serialize_level_data(level_data)
			}
			
			# Write to file
			save_path = self.get_level_save_path(slot)
			with open(save_path, 'w') as f:
				json.dump(save_data, f, indent=4)
			
			print(f"Level saved successfully to slot {slot}")
			return True
			
		except Exception as e:
			print(f"Error saving level: {e}")
			return False
	
	def load_level(self, slot):
		"""
		Load level data from a specific slot
		
		Args:
			slot (int): Save slot number (0 to num_slots-1)
		
		Returns:
			dict or None: Level data if successful, None otherwise
		"""
		if not 0 <= slot < self.num_slots:
			print(f"Invalid slot number: {slot}")
			return None
		
		save_path = self.get_level_save_path(slot)
		
		if not save_path.exists():
			print(f"No save found in slot {slot}")
			return None
		
		try:
			with open(save_path, 'r') as f:
				save_data = json.load(f)
			
			# Deserialize and return level data
			return self._deserialize_level_data(save_data['level_data'])
			
		except Exception as e:
			print(f"Error loading level: {e}")
			return None
	
	def save_game_state(self, slot, player_data, level_progress):
		"""
		Save game state (player progress, coins, etc.)
		
		Args:
			slot (int): Save slot number
			player_data (dict): Player stats (health, coins collected, etc.)
			level_progress (dict): Level completion data
		
		Returns:
			bool: True if save was successful
		"""
		if not 0 <= slot < self.num_slots:
			print(f"Invalid slot number: {slot}")
			return False
		
		try:
			save_data = {
				'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
				'player_data': player_data,
				'level_progress': level_progress
			}
			
			save_path = self.get_gamestate_save_path(slot)
			with open(save_path, 'w') as f:
				json.dump(save_data, f, indent=4)
			
			print(f"Game state saved to slot {slot}")
			return True
			
		except Exception as e:
			print(f"Error saving game state: {e}")
			return False
	
	def load_game_state(self, slot):
		"""
		Load game state from a specific slot
		
		Args:
			slot (int): Save slot number
		
		Returns:
			dict or None: Game state data if successful
		"""
		if not 0 <= slot < self.num_slots:
			print(f"Invalid slot number: {slot}")
			return None
		
		save_path = self.get_gamestate_save_path(slot)
		
		if not save_path.exists():
			print(f"No game state found in slot {slot}")
			return None
		
		try:
			with open(save_path, 'r') as f:
				return json.load(f)
		except Exception as e:
			print(f"Error loading game state: {e}")
			return None
	
	def get_slot_info(self, slot, save_type='level'):
		"""
		Get information about a save slot without loading it
		
		Args:
			slot (int): Save slot number
			save_type (str): 'level' or 'gamestate'
		
		Returns:
			dict or None: Save slot info (name, timestamp, etc.)
		"""
		if save_type == 'level':
			save_path = self.get_level_save_path(slot)
		else:
			save_path = self.get_gamestate_save_path(slot)
		
		if not save_path.exists():
			return None
		
		try:
			with open(save_path, 'r') as f:
				data = json.load(f)
			
			return {
				'slot': slot,
				'timestamp': data.get('timestamp', 'Unknown'),
				'level_name': data.get('level_name', f'Slot {slot}'),
				'exists': True
			}
		except Exception as e:
			print(f"Error reading slot info: {e}")
			return None
	
	def delete_save(self, slot, save_type='level'):
		"""
		Delete a save from a specific slot
		
		Args:
			slot (int): Save slot number
			save_type (str): 'level' or 'gamestate'
		
		Returns:
			bool: True if deletion was successful
		"""
		if save_type == 'level':
			save_path = self.get_level_save_path(slot)
		else:
			save_path = self.get_gamestate_save_path(slot)
		
		try:
			if save_path.exists():
				save_path.unlink()
				print(f"Deleted save in slot {slot}")
				return True
			else:
				print(f"No save to delete in slot {slot}")
				return False
		except Exception as e:
			print(f"Error deleting save: {e}")
			return False
	
	def get_all_slots_info(self, save_type='level'):
		"""
		Get information about all save slots
		
		Args:
			save_type (str): 'level' or 'gamestate'
		
		Returns:
			list: List of slot info dictionaries
		"""
		slots_info = []
		for slot in range(self.num_slots):
			info = self.get_slot_info(slot, save_type)
			if info is None:
				info = {
					'slot': slot,
					'timestamp': None,
					'level_name': f'Empty Slot {slot + 1}',
					'exists': False
				}
			slots_info.append(info)
		return slots_info
	
	def _serialize_level_data(self, level_data):
		"""
		Convert level data to JSON-serializable format
		
		Args:
			level_data (dict): Level grid data with tuples as keys
		
		Returns:
			dict: Serialized level data
		"""
		serialized = {}
		
		for layer_name, layer_data in level_data.items():
			serialized[layer_name] = {}
			for pos, value in layer_data.items():
				# Convert tuple keys to string
				key = f"{pos[0]},{pos[1]}"
				serialized[layer_name][key] = value
		
		return serialized
	
	def _deserialize_level_data(self, serialized_data):
		"""
		Convert serialized level data back to original format
		
		Args:
			serialized_data (dict): Serialized level data
		
		Returns:
			dict: Deserialized level data with tuple keys
		"""
		deserialized = {}
		
		for layer_name, layer_data in serialized_data.items():
			deserialized[layer_name] = {}
			for key_str, value in layer_data.items():
				# Convert string keys back to tuples
				x, y = map(int, key_str.split(','))
				deserialized[layer_name][(x, y)] = value
		
		return deserialized


class SaveSlotUI:
	"""UI for displaying and selecting save slots"""
	
	def __init__(self, save_manager, mode='save'):
		self.display_surface = pygame.display.get_surface()
		self.save_manager = save_manager
		self.mode = mode  # 'save' or 'load'
		self.selected_slot = 0
		self.active = False
		
		# UI settings
		self.slot_height = 100
		self.slot_margin = 20
		self.ui_width = 600
		self.ui_height = (self.slot_height + self.slot_margin) * save_manager.num_slots + 100
		
		# Colors
		self.bg_color = (50, 50, 50, 200)
		self.slot_color = (70, 70, 70)
		self.selected_color = (100, 100, 150)
		self.text_color = (255, 255, 255)
		self.empty_color = (90, 90, 90)
		
		# Font
		pygame.font.init()
		self.title_font = pygame.font.Font(None, 48)
		self.slot_font = pygame.font.Font(None, 32)
		self.info_font = pygame.font.Font(None, 24)
	
	def show(self, save_type='level'):
		"""
		Display the save slot UI
		
		Args:
			save_type (str): 'level' or 'gamestate'
		
		Returns:
			int or None: Selected slot number, or None if cancelled
		"""
		self.active = True
		clock = pygame.time.Clock()
		
		while self.active:
			dt = clock.tick(60) / 1000
			
			for event in pygame.event.get():
				if event.type == pygame.QUIT:
					return None
				
				if event.type == pygame.KEYDOWN:
					if event.key == pygame.K_ESCAPE:
						return None
					elif event.key == pygame.K_UP:
						self.selected_slot = (self.selected_slot - 1) % self.save_manager.num_slots
					elif event.key == pygame.K_DOWN:
						self.selected_slot = (self.selected_slot + 1) % self.save_manager.num_slots
					elif event.key == pygame.K_RETURN:
						return self.selected_slot
					elif event.key == pygame.K_DELETE or event.key == pygame.K_d:
						# Delete the selected slot
						slot_info = self.save_manager.get_slot_info(self.selected_slot, save_type)
						if slot_info:
							self.save_manager.delete_save(self.selected_slot, save_type)
				
				if event.type == pygame.MOUSEBUTTONDOWN:
					result = self.handle_click(event.pos, save_type)
					if result is not None:
						return result
			
			self.draw(save_type)
			pygame.display.update()
		
		return None
	
	def handle_click(self, mouse_pos, save_type):
		"""Handle mouse clicks on save slots"""
		window_width = self.display_surface.get_width()
		window_height = self.display_surface.get_height()
		
		ui_x = (window_width - self.ui_width) // 2
		ui_y = (window_height - self.ui_height) // 2
		
		start_y = ui_y + 80
		
		for i in range(self.save_manager.num_slots):
			slot_y = start_y + i * (self.slot_height + self.slot_margin)
			slot_rect = pygame.Rect(ui_x + 50, slot_y, self.ui_width - 100, self.slot_height)
			
			if slot_rect.collidepoint(mouse_pos):
				return i
		
		return None
	
	def draw(self, save_type='level'):
		"""Draw the save slot UI"""
		window_width = self.display_surface.get_width()
		window_height = self.display_surface.get_height()
		
		# Semi-transparent background
		overlay = pygame.Surface((window_width, window_height))
		overlay.set_alpha(180)
		overlay.fill((0, 0, 0))
		self.display_surface.blit(overlay, (0, 0))
		
		# UI box
		ui_x = (window_width - self.ui_width) // 2
		ui_y = (window_height - self.ui_height) // 2
		
		pygame.draw.rect(self.display_surface, self.bg_color, 
						(ui_x, ui_y, self.ui_width, self.ui_height))
		pygame.draw.rect(self.display_surface, self.text_color, 
						(ui_x, ui_y, self.ui_width, self.ui_height), 3)
		
		# Title
		title_text = "Save Level" if self.mode == 'save' else "Load Level"
		title_surf = self.title_font.render(title_text, True, self.text_color)
		title_rect = title_surf.get_rect(center=(window_width // 2, ui_y + 40))
		self.display_surface.blit(title_surf, title_rect)
		
		# Get slot info
		slots_info = self.save_manager.get_all_slots_info(save_type)
		
		# Draw slots
		start_y = ui_y + 80
		
		for i, slot_info in enumerate(slots_info):
			slot_y = start_y + i * (self.slot_height + self.slot_margin)
			
			# Slot background
			color = self.selected_color if i == self.selected_slot else self.slot_color
			if not slot_info['exists']:
				color = self.empty_color
			
			pygame.draw.rect(self.display_surface, color,
							(ui_x + 50, slot_y, self.ui_width - 100, self.slot_height))
			pygame.draw.rect(self.display_surface, self.text_color,
							(ui_x + 50, slot_y, self.ui_width - 100, self.slot_height), 2)
			
			# Slot number
			slot_text = f"Slot {i + 1}"
			slot_surf = self.slot_font.render(slot_text, True, self.text_color)
			self.display_surface.blit(slot_surf, (ui_x + 70, slot_y + 15))
			
			# Slot info
			if slot_info['exists']:
				name_surf = self.info_font.render(slot_info['level_name'], True, self.text_color)
				time_surf = self.info_font.render(slot_info['timestamp'], True, (180, 180, 180))
				self.display_surface.blit(name_surf, (ui_x + 70, slot_y + 50))
				self.display_surface.blit(time_surf, (ui_x + 70, slot_y + 75))
			else:
				empty_surf = self.info_font.render("Empty", True, (150, 150, 150))
				self.display_surface.blit(empty_surf, (ui_x + 70, slot_y + 50))
		
		# Instructions
		instructions = "↑↓: Navigate  |  ENTER: Select  |  DEL/D: Delete  |  ESC: Cancel"
		instr_surf = self.info_font.render(instructions, True, self.text_color)
		instr_rect = instr_surf.get_rect(center=(window_width // 2, ui_y + self.ui_height - 30))
		self.display_surface.blit(instr_surf, instr_rect)
