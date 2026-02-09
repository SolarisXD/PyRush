import pygame
from settings import *
from save_manager import SaveManager
from os.path import exists
import json
from pathlib import Path

class MainMenu:
	def __init__(self, switch_to_editor, switch_to_level, quit_game):
		self.display_surface = pygame.display.get_surface()
		self.switch_to_editor = switch_to_editor
		self.switch_to_level = switch_to_level
		self.quit_game = quit_game
		self.save_manager = SaveManager()
		
		# Menu options
		self.menu_options = [
			'Start Game',
			'Level Editor', 
			'Saved Levels',
			'Load Custom Level',
			'Settings',
			'Quit'
		]
		self.selected_index = 0
		
		# Font setup
		self.title_font = pygame.font.Font(None, 85)
		self.option_font = pygame.font.Font(None, 48)
		self.subtitle_font = pygame.font.Font(None, 32)
		
		# Colors
		self.bg_color = (20, 30, 50)
		self.title_color = (255, 215, 0)
		self.selected_color = (255, 255, 100)
		self.normal_color = (180, 180, 180)
		self.hover_color = (255, 255, 255)
		
		# Animation
		self.pulse_offset = 0
		
		# Submenu states
		self.in_submenu = False
		self.submenu_type = None
		self.submenu_selected = 0
		
		# Settings menu states
		self.settings_menu_mode = 'main'  # 'main', 'sound', or 'controls'
		
		# Sound settings
		self.music_volume = 0.4
		self.sfx_volume = 0.3
		self.settings_option = 0  # For sound controls: 0=music, 1=sfx
		self.load_settings()
		self.apply_volume_settings()
		
	def handle_input(self):
		keys = pygame.key.get_pressed()
		
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				self.quit_game()
				
			if event.type == pygame.KEYDOWN:
				if self.in_submenu:
					self.handle_submenu_input(event.key)
				else:
					self.handle_main_menu_input(event.key)
					
	def handle_main_menu_input(self, key):
		if key == pygame.K_UP or key == pygame.K_w:
			self.selected_index = (self.selected_index - 1) % len(self.menu_options)
		elif key == pygame.K_DOWN or key == pygame.K_s:
			self.selected_index = (self.selected_index + 1) % len(self.menu_options)
		elif key == pygame.K_RETURN or key == pygame.K_SPACE:
			self.select_option()
		elif key == pygame.K_ESCAPE:
			self.quit_game()
			
	def handle_submenu_input(self, key):
		if key == pygame.K_ESCAPE:
			self.in_submenu = False
			self.submenu_type = None
			return
			
		if self.submenu_type == 'saved_levels':
			# Get available save slots
			available_slots = []
			for i in range(3):
				slot_data = self.save_manager.get_slot_info(i)
				if slot_data:
					available_slots.append(i)
			
			if not available_slots:
				if key == pygame.K_RETURN:
					self.in_submenu = False
				return
				
			if key == pygame.K_UP or key == pygame.K_w:
				self.submenu_selected = (self.submenu_selected - 1) % len(available_slots)
			elif key == pygame.K_DOWN or key == pygame.K_s:
				self.submenu_selected = (self.submenu_selected + 1) % len(available_slots)
			elif key == pygame.K_RETURN or key == pygame.K_SPACE:
				# Load the selected level
				slot_index = available_slots[self.submenu_selected]
				level_data = self.save_manager.load_level(slot_index)
				if level_data:
					self.switch_to_level(level_data)
			elif key == pygame.K_DELETE or key == pygame.K_d:
				# Delete the selected level
				slot_index = available_slots[self.submenu_selected]
				self.save_manager.delete_save(slot_index)
		
		elif self.submenu_type == 'settings':
			if self.settings_menu_mode == 'main':
				# Settings main menu navigation
				if key == pygame.K_ESCAPE:
					self.in_submenu = False
					return
					
				if key == pygame.K_UP or key == pygame.K_w:
					self.submenu_selected = (self.submenu_selected - 1) % 2  # 2 options: Sound, Controls
				elif key == pygame.K_DOWN or key == pygame.K_s:
					self.submenu_selected = (self.submenu_selected + 1) % 2
				elif key == pygame.K_RETURN or key == pygame.K_SPACE:
					if self.submenu_selected == 0:
						self.settings_menu_mode = 'sound'
						self.settings_option = 0
					elif self.submenu_selected == 1:
						self.settings_menu_mode = 'controls'
						
			elif self.settings_menu_mode == 'sound':
				# Sound controls submenu
				if key == pygame.K_ESCAPE:
					self.save_settings()
					self.settings_menu_mode = 'main'
					return
				elif key == pygame.K_RETURN:
					self.save_settings()
					self.settings_menu_mode = 'main'
					return
					
				if key == pygame.K_UP or key == pygame.K_w:
					self.settings_option = (self.settings_option - 1) % 2
				elif key == pygame.K_DOWN or key == pygame.K_s:
					self.settings_option = (self.settings_option + 1) % 2
				elif key == pygame.K_LEFT or key == pygame.K_a:
					if self.settings_option == 0:
						self.music_volume = max(0.0, self.music_volume - 0.1)
						self.apply_volume_settings()
					else:
						self.sfx_volume = max(0.0, self.sfx_volume - 0.1)
						self.apply_volume_settings()
				elif key == pygame.K_RIGHT or key == pygame.K_d:
					if self.settings_option == 0:
						self.music_volume = min(1.0, self.music_volume + 0.1)
						self.apply_volume_settings()
					else:
						self.sfx_volume = min(1.0, self.sfx_volume + 0.1)
						self.apply_volume_settings()
						
			elif self.settings_menu_mode == 'controls':
				# Controls reference (read-only)
				if key == pygame.K_ESCAPE or key == pygame.K_RETURN:
					self.settings_menu_mode = 'main'
					return
					
		elif self.submenu_type == 'custom_level':
			if key == pygame.K_ESCAPE:
				self.in_submenu = False
				return
				
			if not self.custom_level_files:
				if key == pygame.K_RETURN:
					self.in_submenu = False
				return
				
			if key == pygame.K_UP or key == pygame.K_w:
				self.submenu_selected = (self.submenu_selected - 1) % len(self.custom_level_files)
			elif key == pygame.K_DOWN or key == pygame.K_s:
				self.submenu_selected = (self.submenu_selected + 1) % len(self.custom_level_files)
			elif key == pygame.K_RETURN or key == pygame.K_SPACE:
				# Load the selected custom level
				file_path = self.custom_level_files[self.submenu_selected]
				level_data = self.load_custom_level(file_path)
				if level_data:
					self.switch_to_level(level_data)
				
	def select_option(self):
		option = self.menu_options[self.selected_index]
		
		if option == 'Start Game':
			# Check if there's a default level or use level editor's current level
			slot_data = self.save_manager.get_slot_info(0)
			if slot_data:
				level_data = self.save_manager.load_level(0)
				self.switch_to_level(level_data)
			else:
				# No saved level, go to editor first
				self.switch_to_editor()
				
		elif option == 'Level Editor':
			self.switch_to_editor()
			
		elif option == 'Saved Levels':
			self.in_submenu = True
			self.submenu_type = 'saved_levels'
			self.submenu_selected = 0
			
		elif option == 'Load Custom Level':
			self.in_submenu = True
			self.submenu_type = 'custom_level'
			self.custom_level_files = self.get_custom_level_files()
			self.submenu_selected = 0
			
		elif option == 'Settings':
			self.in_submenu = True
			self.submenu_type = 'settings'
			self.settings_menu_mode = 'main'
			self.submenu_selected = 0
			
		elif option == 'Quit':
			self.quit_game()
			
	def draw_main_menu(self, dt):
		# Pulse animation
		self.pulse_offset += dt * 2
		pulse = abs(pygame.math.Vector2(0, 10).rotate(self.pulse_offset * 360).y)
		
		# Title
		title_text = "PyRush"
		title_surf = self.title_font.render(title_text, True, self.title_color)
		title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 110))
		self.display_surface.blit(title_surf, title_rect)
		
		# Subtitle
		subtitle_text = "2D Platformer Adventure"
		subtitle_surf = self.subtitle_font.render(subtitle_text, True, self.normal_color)
		subtitle_rect = subtitle_surf.get_rect(center=(WINDOW_WIDTH // 2, 160))
		self.display_surface.blit(subtitle_surf, subtitle_rect)
		
		# Menu options
		start_y = 240
		spacing = 70
		
		for i, option in enumerate(self.menu_options):
			if i == self.selected_index:
				# Selected option with pulse effect
				color = self.selected_color
				y_offset = pulse
				prefix = "> "
			else:
				color = self.normal_color
				y_offset = 0
				prefix = "  "
			
			option_surf = self.option_font.render(prefix + option, True, color)
			option_rect = option_surf.get_rect(center=(WINDOW_WIDTH // 2, start_y + i * spacing + y_offset))
			self.display_surface.blit(option_surf, option_rect)
			
		# Controls hint
		hint_text = "↑↓ Navigate  |  Enter: Select  |  ESC: Quit"
		hint_surf = self.subtitle_font.render(hint_text, True, self.normal_color)
		hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
		self.display_surface.blit(hint_surf, hint_rect)
		
	def draw_saved_levels_submenu(self):
		# Semi-transparent overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(180)
		self.display_surface.blit(overlay, (0, 0))
		
		# Title
		title_text = "Saved Levels"
		title_surf = self.title_font.render(title_text, True, self.title_color)
		title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 100))
		self.display_surface.blit(title_surf, title_rect)
		
		# List saved levels
		available_slots = []
		slot_info = []
		
		for i in range(3):
			slot_data = self.save_manager.get_slot_info(i)
			if slot_data:
				available_slots.append(i)
				timestamp = slot_data.get('timestamp', 'Unknown')
				# Format timestamp
				if timestamp != 'Unknown':
					from datetime import datetime
					dt = datetime.fromisoformat(timestamp)
					timestamp = dt.strftime('%Y-%m-%d %H:%M')
				slot_info.append(f"Slot {i + 1}: {timestamp}")
		
		if not available_slots:
			# No saved levels
			text = "No saved levels found"
			surf = self.option_font.render(text, True, self.normal_color)
			rect = surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
			self.display_surface.blit(surf, rect)
			
			hint_text = "Press Enter or ESC to go back"
			hint_surf = self.subtitle_font.render(hint_text, True, self.normal_color)
			hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
			self.display_surface.blit(hint_surf, hint_rect)
		else:
			# Display available slots
			start_y = 250
			spacing = 80
			
			for i, info in enumerate(slot_info):
				if i == self.submenu_selected:
					color = self.selected_color
					prefix = "> "
				else:
					color = self.normal_color
					prefix = "  "
				
				surf = self.option_font.render(prefix + info, True, color)
				rect = surf.get_rect(center=(WINDOW_WIDTH // 2, start_y + i * spacing))
				self.display_surface.blit(surf, rect)
			
			# Controls hint
			hint_text = "↑↓ Navigate  |  Enter: Load  |  DEL/D: Delete  |  ESC: Back"
			hint_surf = self.subtitle_font.render(hint_text, True, self.normal_color)
			hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
			self.display_surface.blit(hint_surf, hint_rect)
			
	def draw_settings_submenu(self):
		"""Draw settings menu based on current mode"""
		if self.settings_menu_mode == 'main':
			self.draw_settings_main()
		elif self.settings_menu_mode == 'sound':
			self.draw_sound_controls()
		elif self.settings_menu_mode == 'controls':
			self.draw_controls_reference()
	
	def draw_settings_main(self):
		"""Draw main settings menu with options"""
		# Semi-transparent overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(180)
		self.display_surface.blit(overlay, (0, 0))
		
		# Title
		title_text = "Settings"
		title_surf = self.title_font.render(title_text, True, self.title_color)
		title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 120))
		self.display_surface.blit(title_surf, title_rect)
		
		# Game info
		info_items = [
			"Window Size: 1280x720",
			"Tile Size: 64x64",
			"Save Slots: 3"
		]
		
		info_y = 210
		for item in info_items:
			surf = self.subtitle_font.render(item, True, self.normal_color)
			rect = surf.get_rect(center=(WINDOW_WIDTH // 2, info_y))
			self.display_surface.blit(surf, rect)
			info_y += 35
		
		# Settings options
		options = ["Sound Controls", "View Controls"]
		start_y = 380
		spacing = 70
		
		for i, option in enumerate(options):
			if i == self.submenu_selected:
				color = self.selected_color
				prefix = "> "
			else:
				color = self.normal_color
				prefix = "  "
			
			surf = self.option_font.render(prefix + option, True, color)
			rect = surf.get_rect(center=(WINDOW_WIDTH // 2, start_y + i * spacing))
			self.display_surface.blit(surf, rect)
		
		# Instructions
		hint_text = "↑↓: Navigate  |  Enter: Select  |  ESC: Back"
		hint_surf = self.subtitle_font.render(hint_text, True, self.normal_color)
		hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
		self.display_surface.blit(hint_surf, hint_rect)
	
	def draw_sound_controls(self):
		"""Draw sound control sliders"""
		# Semi-transparent overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(180)
		self.display_surface.blit(overlay, (0, 0))
		
		# Title
		title_text = "Settings"
		title_surf = self.title_font.render(title_text, True, self.title_color)
		title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 100))
		self.display_surface.blit(title_surf, title_rect)
		
		# Game info
		info_items = [
			"Window Size: 1280x720",
			"Tile Size: 64x64",
			"Save Slots: 3"
		]
		
		info_y = 180
		for item in info_items:
			surf = self.subtitle_font.render(item, True, self.normal_color)
			rect = surf.get_rect(center=(WINDOW_WIDTH // 2, info_y))
			self.display_surface.blit(surf, rect)
			info_y += 40
		
		# Volume controls section
		volume_title = self.option_font.render("Sound Controls", True, self.title_color)
		volume_title_rect = volume_title.get_rect(center=(WINDOW_WIDTH // 2, 340))
		self.display_surface.blit(volume_title, volume_title_rect)
		
		# Music volume slider
		self.draw_volume_slider("Music Volume", self.music_volume, 420, self.settings_option == 0)
		
		# SFX volume slider
		self.draw_volume_slider("Sound Effects", self.sfx_volume, 500, self.settings_option == 1)
		
		# Instructions
		instructions = [
			"↑↓: Select  |  ←→: Adjust Volume  |  Enter/ESC: Back"
		]
		
		instr_y = WINDOW_HEIGHT - 60
		for instr in instructions:
			surf = self.subtitle_font.render(instr, True, self.normal_color)
			rect = surf.get_rect(center=(WINDOW_WIDTH // 2, instr_y))
			self.display_surface.blit(surf, rect)
			instr_y += 35
	
	def draw_volume_slider(self, label, volume, y_pos, selected):
		"""Draw a volume slider bar"""
		# Label
		color = self.selected_color if selected else self.normal_color
		prefix = "> " if selected else "  "
		label_surf = self.option_font.render(prefix + label, True, color)
		label_rect = label_surf.get_rect(center=(WINDOW_WIDTH // 2, y_pos))
		self.display_surface.blit(label_surf, label_rect)
		
		# Slider bar
		bar_width = 400
		bar_height = 30
		bar_x = (WINDOW_WIDTH - bar_width) // 2
		bar_y = y_pos + 40
		
		# Background
		pygame.draw.rect(self.display_surface, (60, 60, 60),
						(bar_x, bar_y, bar_width, bar_height))
		
		# Fill (volume level)
		fill_width = int(bar_width * volume)
		fill_color = self.selected_color if selected else (100, 150, 100)
		pygame.draw.rect(self.display_surface, fill_color,
						(bar_x, bar_y, fill_width, bar_height))
		
		# Border
		border_color = self.selected_color if selected else self.normal_color
		pygame.draw.rect(self.display_surface, border_color,
						(bar_x, bar_y, bar_width, bar_height), 3)
		
		# Percentage text
		percent_text = f"{int(volume * 100)}%"
		percent_surf = self.subtitle_font.render(percent_text, True, (255, 255, 255))
		percent_rect = percent_surf.get_rect(center=(WINDOW_WIDTH // 2, bar_y + bar_height // 2))
		self.display_surface.blit(percent_surf, percent_rect)
	
	def draw_controls_reference(self):
		"""Draw comprehensive controls reference"""
		# Semi-transparent overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(180)
		self.display_surface.blit(overlay, (0, 0))
		
		# Title
		title_text = "Keyboard Controls"
		title_surf = self.title_font.render(title_text, True, self.title_color)
		title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 50))
		self.display_surface.blit(title_surf, title_rect)
		
		# Controls organized in two columns
		left_column_x = 150
		right_column_x = 700
		start_y = 120
		line_spacing = 28
		section_spacing = 40
		
		# Font for text
		control_font = pygame.font.Font(None, 24)
		header_font = pygame.font.Font(None, 32)
		
		# Left Column - Main Menu & Editor
		y = start_y
		
		# Main Menu
		header = header_font.render("MAIN MENU:", True, self.title_color)
		self.display_surface.blit(header, (left_column_x, y))
		y += section_spacing
		
		menu_controls = [
			"↑↓ / W/S - Navigate menu",
			"Enter / Space - Select",
			"ESC - Quit game"
		]
		
		for control in menu_controls:
			surf = control_font.render(control, True, self.normal_color)
			self.display_surface.blit(surf, (left_column_x, y))
			y += line_spacing
		
		y += section_spacing - 5
		
		# Level Editor
		header = header_font.render("LEVEL EDITOR:", True, self.title_color)
		self.display_surface.blit(header, (left_column_x, y))
		y += section_spacing
		
		editor_controls = [
			"Left Click - Place tile",
			"Right Click - Delete tile",
			"← → - Change tile type",
			"Middle Mouse - Pan camera",
			"Mouse Wheel - Scroll",
			"Enter - Play level",
			"ESC - Main menu",
			"H / F1 - Toggle help",
			"F5 - Quick save",
			"F9 - Quick load",
			"Ctrl+S - Save slot picker",
			"Ctrl+L - Load slot picker",
			"Ctrl+N - Clear grid"
		]
		
		for control in editor_controls:
			surf = control_font.render(control, True, self.normal_color)
			self.display_surface.blit(surf, (left_column_x, y))
			y += line_spacing
		
		# Right Column - Gameplay
		y = start_y
		
		header = header_font.render("GAMEPLAY:", True, self.title_color)
		self.display_surface.blit(header, (right_column_x, y))
		y += section_spacing
		
		gameplay_controls = [
			"Arrow Keys / WASD - Move",
			"Space - Jump",
			"ESC - Main menu",
			"H / F1 - Toggle help",
			"F6 - Quick save state",
			"F7 - Quick load state",
			"Ctrl+S - Save state picker",
			"Ctrl+L - Load state picker"
		]
		
		for control in gameplay_controls:
			surf = control_font.render(control, True, self.normal_color)
			self.display_surface.blit(surf, (right_column_x, y))
			y += line_spacing
		
		y += section_spacing - 5
		
		# Save System
		header = header_font.render("SAVE SYSTEM:", True, self.title_color)
		self.display_surface.blit(header, (right_column_x, y))
		y += section_spacing
		
		save_controls = [
			"↑↓ - Navigate slots",
			"Enter - Select slot",
			"DEL / D - Delete save",
			"ESC - Cancel"
		]
		
		for control in save_controls:
			surf = control_font.render(control, True, self.normal_color)
			self.display_surface.blit(surf, (right_column_x, y))
			y += line_spacing
		
		# Instructions at bottom
		hint_text = "Press Enter or ESC to go back"
		hint_surf = self.subtitle_font.render(hint_text, True, self.selected_color)
		hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 40))
		self.display_surface.blit(hint_surf, hint_rect)
	
	def load_settings(self):
		"""Load volume settings from config file"""
		try:
			config_path = Path('game_settings.json')
			if config_path.exists():
				with open(config_path, 'r') as f:
					data = json.load(f)
					self.music_volume = data.get('music_volume', 0.4)
					self.sfx_volume = data.get('sfx_volume', 0.3)
		except Exception as e:
			print(f"Error loading settings: {e}")
	
	def save_settings(self):
		"""Save volume settings to config file"""
		try:
			config_path = Path('game_settings.json')
			data = {
				'music_volume': self.music_volume,
				'sfx_volume': self.sfx_volume
			}
			with open(config_path, 'w') as f:
				json.dump(data, f, indent=2)
			print(f"Settings saved: Music {int(self.music_volume*100)}%, SFX {int(self.sfx_volume*100)}%")
		except Exception as e:
			print(f"Error saving settings: {e}")
	
	def apply_volume_settings(self):
		"""Apply volume settings to pygame mixer"""
		try:
			# Set global music volume
			pygame.mixer.music.set_volume(self.music_volume)
			# Note: Individual sound effects volumes will be applied when they're loaded in editor/level
		except Exception as e:
			print(f"Error applying volume: {e}")
	
	def get_volumes(self):
		"""Get current volume settings for other modules"""
		return {'music': self.music_volume, 'sfx': self.sfx_volume}
	
	def draw_custom_level_submenu(self):
		"""Draw custom level loading submenu"""
		# Semi-transparent overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(180)
		self.display_surface.blit(overlay, (0, 0))
		
		# Title
		title_text = "Load Custom Level"
		title_surf = self.title_font.render(title_text, True, self.title_color)
		title_rect = title_surf.get_rect(center=(WINDOW_WIDTH // 2, 100))
		self.display_surface.blit(title_surf, title_rect)
		
		if not self.custom_level_files:
			# No custom levels found
			text = "No custom level files found"
			surf = self.option_font.render(text, True, self.normal_color)
			rect = surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2))
			self.display_surface.blit(surf, rect)
			
			text2 = "Place .json level files in game folder or save_data/"
			surf2 = self.subtitle_font.render(text2, True, self.normal_color)
			rect2 = surf2.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
			self.display_surface.blit(surf2, rect2)
			
			hint_text = "Press Enter or ESC to go back"
			hint_surf = self.subtitle_font.render(hint_text, True, self.normal_color)
			hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
			self.display_surface.blit(hint_surf, hint_rect)
		else:
			# Display available custom level files
			start_y = 200
			spacing = 60
			
			for i, file_path in enumerate(self.custom_level_files):
				if i == self.submenu_selected:
					color = self.selected_color
					prefix = "> "
				else:
					color = self.normal_color
					prefix = "  "
				
				filename = file_path.name
				surf = self.option_font.render(prefix + filename, True, color)
				rect = surf.get_rect(center=(WINDOW_WIDTH // 2, start_y + i * spacing))
				self.display_surface.blit(surf, rect)
			
			# Controls hint
			hint_text = "↑↓ Navigate  |  Enter: Load  |  ESC: Back"
			hint_surf = self.subtitle_font.render(hint_text, True, self.normal_color)
			hint_rect = hint_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT - 50))
			self.display_surface.blit(hint_surf, hint_rect)
		
	def get_custom_level_files(self):
		"""Get list of custom level JSON files in current directory"""
		level_files = []
		try:
			# Look for JSON files in current directory
			for file_path in Path('.').glob('*.json'):
				if file_path.stem.startswith('level_') or file_path.stem.startswith('custom_'):
					level_files.append(file_path)
			# Also check save_data directory
			save_dir = Path('save_data')
			if save_dir.exists():
				for file_path in save_dir.glob('*.json'):
					if not file_path.stem.startswith('gamestate_'):
						level_files.append(file_path)
			# Check save_data/levels directory
			levels_dir = Path('save_data/levels')
			if levels_dir.exists():
				for file_path in levels_dir.glob('*.json'):
					level_files.append(file_path)
		except Exception as e:
			print(f"Error scanning for custom levels: {e}")
		return sorted(level_files)
	
	def load_custom_level(self, file_path):
		"""Load a custom level from a JSON file"""
		try:
			with open(file_path, 'r') as f:
				data = json.load(f)
				level_data = data.get('level_data', None)
				
				if level_data:
					# Convert string keys back to tuples
					converted_data = {}
					for layer_name, layer_content in level_data.items():
						converted_layer = {}
						for pos_str, value in layer_content.items():
							# Convert "x,y" string to (x, y) tuple
							x, y = map(int, pos_str.split(','))
							converted_layer[(x, y)] = value
						converted_data[layer_name] = converted_layer
					return converted_data
				return None
		except Exception as e:
			print(f"Error loading custom level: {e}")
			return None
	
	def run(self, dt):
		self.handle_input()
		
		# Clear screen
		self.display_surface.fill(self.bg_color)
		
		if self.in_submenu:
			if self.submenu_type == 'saved_levels':
				self.draw_saved_levels_submenu()
			elif self.submenu_type == 'settings':
				self.draw_settings_submenu()
			elif self.submenu_type == 'custom_level':
				self.draw_custom_level_submenu()
		else:
			self.draw_main_menu(dt)
