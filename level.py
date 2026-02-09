import pygame, sys 
from pygame.math import Vector2 as vector

from settings import *
from support import *

from sprites import Generic, Block, Animated, Particle, Coin, Player, Spikes, Tooth, Shell, Cloud
from save_manager import SaveManager, SaveSlotUI

from random import choice, randint

class Level:
	def __init__(self, grid, switch, asset_dict, audio, return_to_menu=None):
		self.display_surface = pygame.display.get_surface()
		self.switch = switch
		self.return_to_menu = return_to_menu
		
		# Save manager for game state
		self.save_manager = SaveManager(num_slots=3)
		
		# Game state tracking
		self.coins_collected = 0
		self.total_coins = 0
		self.player_health = 100
		self.level_complete = False
		self.play_time = 0  # in seconds
		
		# Help overlay
		self.show_help = False
		pygame.font.init()
		self.help_font = pygame.font.Font(None, 28)
		self.help_title_font = pygame.font.Font(None, 40)

		# groups 
		self.all_sprites = CameraGroup()
		self.coin_sprites = pygame.sprite.Group()
		self.damage_sprites = pygame.sprite.Group()
		self.collision_sprites = pygame.sprite.Group()
		self.shell_sprites = pygame.sprite.Group()

		self.build_level(grid, asset_dict, audio['jump'])

		# level limits
		self.level_limits = {
		'left': -WINDOW_WIDTH,
		'right': sorted(list(grid['terrain'].keys()), key = lambda pos: pos[0])[-1][0] + 500
		}

		# additional stuff
		self.particle_surfs = asset_dict['particle']
		self.cloud_surfs = asset_dict['clouds']
		self.cloud_timer = pygame.USEREVENT + 2
		pygame.time.set_timer(self.cloud_timer, 2000)
		self.startup_clouds()

		# sounds (volumes are already set before Level is created)
		self.bg_music = audio['music']
		self.bg_music.play(loops = -1)

		self.coin_sound = audio['coin']
		self.hit_sound = audio['hit']
		
		# Death screen
		self.death_screen_active = False
		self.death_timer = 0
		self.death_font = pygame.font.Font(None, 100)
		self.death_subfont = pygame.font.Font(None, 50)

	def build_level(self, grid, asset_dict, jump_sound):
		for layer_name, layer in grid.items():
			for pos, data in layer.items():
				if layer_name == 'terrain':
					Generic(pos, asset_dict['land'][data], [self.all_sprites, self.collision_sprites])
				if layer_name == 'water':
					if data == 'top':
						Animated(asset_dict['water top'], pos, self.all_sprites, LEVEL_LAYERS['water'])
					else:
						Generic(pos, asset_dict['water bottom'], self.all_sprites, LEVEL_LAYERS['water'])

				match data:
					case 0: 
						self.player = Player(pos, asset_dict['player'], self.all_sprites, self.collision_sprites, jump_sound)
						self.player_start_pos = vector(pos)  # Store starting position for respawn
					case 1: 
						self.horizon_y = pos[1]
						self.all_sprites.horizon_y = pos[1]
					# coins
					case 4: Coin('gold', asset_dict['gold'], pos, [self.all_sprites, self.coin_sprites])
					case 5: Coin('silver', asset_dict['silver'], pos, [self.all_sprites, self.coin_sprites])
					case 6: Coin('diamond', asset_dict['diamond'], pos, [self.all_sprites, self.coin_sprites])

					# enemies
					case 7: Spikes(asset_dict['spikes'], pos, [self.all_sprites, self.damage_sprites])
					case 8: 
						Tooth(asset_dict['tooth'], pos, [self.all_sprites, self.damage_sprites], self.collision_sprites)
					case 9: 
						Shell(
							orientation = 'left', 
							assets = asset_dict['shell'], 
							pos =  pos, 
							group =  [self.all_sprites, self.collision_sprites, self.shell_sprites],
							pearl_surf = asset_dict['pearl'],
							damage_sprites = self.damage_sprites)
					case 10: 
						Shell(
							orientation = 'right', 
							assets = asset_dict['shell'], 
							pos =  pos, 
							group =  [self.all_sprites, self.collision_sprites, self.shell_sprites],
							pearl_surf = asset_dict['pearl'],
							damage_sprites = self.damage_sprites)

					# palm trees
					case 11: 
						Animated(asset_dict['palms']['small_fg'], pos, self.all_sprites)
						Block(pos, (76,50), self.collision_sprites)
					case 12: 
						Animated(asset_dict['palms']['large_fg'], pos, self.all_sprites)
						Block(pos, (76,50), self.collision_sprites)
					case 13: 
						Animated(asset_dict['palms']['left_fg'], pos, self.all_sprites)
						Block(pos, (76,50), self.collision_sprites)
					case 14: 
						Animated(asset_dict['palms']['right_fg'], pos, self.all_sprites)
						Block(pos + vector(50,0), (76,50), self.collision_sprites)
					
					case 15: Animated(asset_dict['palms']['small_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 16: Animated(asset_dict['palms']['large_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 17: Animated(asset_dict['palms']['left_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])
					case 18: Animated(asset_dict['palms']['right_bg'], pos, self.all_sprites, LEVEL_LAYERS['bg'])

		for sprite in self.shell_sprites:
			sprite.player = self.player
		
		# Count total coins
		self.total_coins = len(self.coin_sprites)

	def get_coins(self):
		collided_coins = pygame.sprite.spritecollide(self.player, self.coin_sprites, True)
		for sprite in collided_coins:
			self.coin_sound.play()
			Particle(self.particle_surfs, sprite.rect.center, self.all_sprites)
			self.coins_collected += 1
			
			# Check if all coins collected
			if self.coins_collected >= self.total_coins:
				self.level_complete = True

	def get_damage(self):
		collision_sprites = pygame.sprite.spritecollide(self.player, self.damage_sprites, False, pygame.sprite.collide_mask)
		if collision_sprites:
			self.hit_sound.play()
			self.player.damage()
	
	def check_death(self):
		"""Check if player fell off the level and respawn if needed"""
		# Death boundary - if player falls below level by 200 pixels
		death_y = WINDOW_HEIGHT + 200
		
		if self.player.rect.top > death_y:
			# Player fell off - respawn at start position
			self.hit_sound.play()
			self.player.rect.topleft = self.player_start_pos
			self.player.direction.y = 0  # Reset falling velocity
			self.player.on_ground = False
			self.player.damage()  # Take damage for falling off
		
		# Check if player died
		if self.player.is_dead and not self.death_screen_active:
			self.death_screen_active = True
			self.death_timer = 0
			self.bg_music.stop()

	def event_loop(self):
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					# Return to main menu
					if self.return_to_menu:
						self.bg_music.stop()
						self.return_to_menu()
					else:
						# Fallback to editor if no menu callback
						self.switch()
						self.bg_music.stop()
			
			# Save/Load hotkeys for game state
			if event.type == pygame.KEYDOWN:
				if event.key == pygame.K_h or event.key == pygame.K_F1:  # Toggle help
					self.show_help = not self.show_help
				elif event.key == pygame.K_F6:  # Quick save game state
					self.save_game_state(0)
				elif event.key == pygame.K_F7:  # Quick load game state
					self.load_game_state(0)
				elif pygame.key.get_pressed()[pygame.K_LCTRL] and event.key == pygame.K_s:  # Ctrl+S: Save with UI
					self.save_with_ui()
				elif pygame.key.get_pressed()[pygame.K_LCTRL] and event.key == pygame.K_l:  # Ctrl+L: Load with UI
					self.load_with_ui()

			if event.type == self.cloud_timer:
				surf = choice(self.cloud_surfs)
				surf = pygame.transform.scale2x(surf) if randint(0,5) > 3 else surf
				x = self.level_limits['right'] + randint(100,300)
				y = self.horizon_y - randint(-50,600)
				Cloud((x,y), surf, self.all_sprites, self.level_limits['left'])
	
	def draw_ui(self):
		"""Draw UI elements showing game state"""
		pygame.font.init()
		font = pygame.font.Font(None, 36)
		
		# Coins collected
		coins_text = f"Coins: {self.coins_collected}/{self.total_coins}"
		coins_surf = font.render(coins_text, True, (255, 215, 0))
		self.display_surface.blit(coins_surf, (10, 10))
		
		# Health
		health_text = f"Health: {self.player.health}"
		health_surf = font.render(health_text, True, (255, 100, 100))
		self.display_surface.blit(health_surf, (10, 50))
		
		# Play time
		minutes = int(self.play_time // 60)
		seconds = int(self.play_time % 60)
		time_text = f"Time: {minutes:02d}:{seconds:02d}"
		time_surf = font.render(time_text, True, (255, 255, 255))
		self.display_surface.blit(time_surf, (10, 90))
		
		# Help hint
		if not self.show_help:
			hint_surf = self.help_font.render("Press H for help", True, (255, 255, 255))
			hint_rect = hint_surf.get_rect(topright=(WINDOW_WIDTH - 10, 10))
			# Semi-transparent background
			bg_rect = hint_rect.inflate(20, 10)
			bg_surf = pygame.Surface(bg_rect.size)
			bg_surf.set_alpha(180)
			bg_surf.fill((0, 0, 0))
			self.display_surface.blit(bg_surf, bg_rect)
			self.display_surface.blit(hint_surf, hint_rect)
		
		# Level complete message
		if self.level_complete:
			complete_text = "LEVEL COMPLETE!"
			complete_surf = font.render(complete_text, True, (0, 255, 0))
			complete_rect = complete_surf.get_rect(center=(WINDOW_WIDTH // 2, 50))
			self.display_surface.blit(complete_surf, complete_rect)
	
	def draw_help_overlay(self):
		"""Draw help overlay with controls"""
		if not self.show_help:
			return
		
		# Full help overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.set_alpha(230)
		overlay.fill((20, 20, 40))
		self.display_surface.blit(overlay, (0, 0))
		
		# Title
		title = self.help_title_font.render("GAMEPLAY CONTROLS", True, (255, 215, 0))
		title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 60))
		self.display_surface.blit(title, title_rect)
		
		# Controls
		controls = [
			"",
			"MOVEMENT:",
			"  Arrow Keys / WASD - Move player",
			"  Space - Jump",
			"",
			"GAME:",
			"  ESC - Return to main menu",
			"  Collect all coins to complete level!",
			"  Don't fall off - you'll respawn with damage!",
			"",
			"SAVING PROGRESS:",
			"  F6 - Quick save game state",
			"  F7 - Quick load game state",
			"  Ctrl+S - Save with slot picker",
			"  Ctrl+L - Load with slot picker",
			"  DEL/D (in slot picker) - Delete save",
			"",
			"HELP:",
			"  H or F1 - Toggle this help screen",
			"",
			"Press H to close"
		]
		
		y = 130
		for line in controls:
			if line and not line.startswith("  "):
				# Section headers
				surf = self.help_title_font.render(line, True, (100, 200, 255))
			else:
				# Regular text
				surf = self.help_font.render(line, True, (255, 255, 255))
			
			rect = surf.get_rect(centerx=WINDOW_WIDTH // 2, top=y)
			self.display_surface.blit(surf, rect)
			y += 30 if line and not line.startswith("  ") else 26
	
	def draw_death_screen(self):
		"""Draw the 'You Died' screen overlay"""
		# Semi-transparent dark overlay
		overlay = pygame.Surface((WINDOW_WIDTH, WINDOW_HEIGHT))
		overlay.fill((0, 0, 0))
		overlay.set_alpha(200)
		self.display_surface.blit(overlay, (0, 0))
		
		# "YOU DIED" text
		death_text = "YOU DIED"
		death_surf = self.death_font.render(death_text, True, (255, 50, 50))
		death_rect = death_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 - 50))
		self.display_surface.blit(death_surf, death_rect)
		
		# "Returning to menu..." text
		sub_text = "Returning to menu..."
		sub_surf = self.death_subfont.render(sub_text, True, (200, 200, 200))
		sub_rect = sub_surf.get_rect(center=(WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 50))
		self.display_surface.blit(sub_surf, sub_rect)
	
	def startup_clouds(self):
		for i in range(40):
			surf = choice(self.cloud_surfs)
			surf = pygame.transform.scale2x(surf) if randint(0,5) > 3 else surf
			x = randint(self.level_limits['left'], self.level_limits['right'])
			y = self.horizon_y - randint(-50,600)
			Cloud((x,y), surf, self.all_sprites, self.level_limits['left'])
	
	# Save/Load game state functionality
	def save_game_state(self, slot=0):
		"""Save the current game state to a slot"""
		player_data = {
			'coins_collected': self.coins_collected,
			'health': self.player_health,
			'position': {'x': self.player.rect.x, 'y': self.player.rect.y},
			'play_time': self.play_time
		}
		
		level_progress = {
			'level_complete': self.level_complete,
			'total_coins': self.total_coins,
			'coins_remaining': len(self.coin_sprites)
		}
		
		success = self.save_manager.save_game_state(slot, player_data, level_progress)
		if success:
			print(f"Game state saved to slot {slot + 1}")
			return True
		return False
	
	def load_game_state(self, slot=0):
		"""Load a game state from a slot"""
		game_state = self.save_manager.load_game_state(slot)
		
		if game_state:
			# Restore player data
			player_data = game_state['player_data']
			self.coins_collected = player_data['coins_collected']
			self.player_health = player_data['health']
			self.play_time = player_data['play_time']
			
			# Restore player position
			self.player.rect.x = player_data['position']['x']
			self.player.rect.y = player_data['position']['y']
			self.player.pos = vector(self.player.rect.center)
			
			# Restore level progress
			level_progress = game_state['level_progress']
			self.level_complete = level_progress['level_complete']
			
			print(f"Game state loaded from slot {slot + 1}")
			return True
		return False
	
	def save_with_ui(self):
		"""Save game state with slot selection UI"""
		save_ui = SaveSlotUI(self.save_manager, mode='save')
		selected_slot = save_ui.show(save_type='gamestate')
		
		if selected_slot is not None:
			self.save_game_state(selected_slot)
	
	def load_with_ui(self):
		"""Load game state with slot selection UI"""
		save_ui = SaveSlotUI(self.save_manager, mode='load')
		selected_slot = save_ui.show(save_type='gamestate')
		
		if selected_slot is not None:
			self.load_game_state(selected_slot)

	def run(self, dt):
		# update
		self.event_loop()
		
		if self.death_screen_active:
			self.death_timer += dt
			if self.death_timer >= 3.0:  # Show death screen for 3 seconds
				return 'menu'  # Signal to return to main menu
		else:
			self.all_sprites.update(dt)
			self.get_coins()
			self.get_damage()
			self.check_death()  # Check if player fell off level
			
			# Track play time
			self.play_time += dt

		# drawing
		self.display_surface.fill(SKY_COLOR)
		self.all_sprites.custom_draw(self.player)
		
		# Display game state info
		self.draw_ui()
		
		# Draw death screen if active
		if self.death_screen_active:
			self.draw_death_screen()

class CameraGroup(pygame.sprite.Group):
	def __init__(self):
		super().__init__()
		self.display_surface = pygame.display.get_surface()
		self.offset = vector()

	def draw_horizon(self):
		horizon_pos = self.horizon_y - self.offset.y	

		if horizon_pos < WINDOW_HEIGHT:
			sea_rect = pygame.Rect(0,horizon_pos,WINDOW_WIDTH,WINDOW_HEIGHT - horizon_pos)
			pygame.draw.rect(self.display_surface, SEA_COLOR, sea_rect)

			# horizon line 
			# 3 extra rectangles 
			horizon_rect1 = pygame.Rect(0,horizon_pos - 10,WINDOW_WIDTH,10)
			horizon_rect2 = pygame.Rect(0,horizon_pos - 16,WINDOW_WIDTH,4)
			horizon_rect3 = pygame.Rect(0,horizon_pos - 20,WINDOW_WIDTH,2)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect1)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect2)
			pygame.draw.rect(self.display_surface, HORIZON_TOP_COLOR, horizon_rect3)
			pygame.draw.line(self.display_surface, HORIZON_COLOR, (0,horizon_pos), (WINDOW_WIDTH,horizon_pos), 3)

		if horizon_pos < 0:
			self.display_surface.fill(SEA_COLOR)

	def custom_draw(self, player):
		self.offset.x = player.rect.centerx - WINDOW_WIDTH / 2
		self.offset.y = player.rect.centery - WINDOW_HEIGHT / 2

		for sprite in self:
			if sprite.z == LEVEL_LAYERS['clouds']:
				offset_rect = sprite.rect.copy()
				offset_rect.center -= self.offset
				self.display_surface.blit(sprite.image, offset_rect)

		self.draw_horizon()
		for sprite in self:
			for layer in LEVEL_LAYERS.values():
				if sprite.z == layer and sprite.z != LEVEL_LAYERS['clouds']:
					offset_rect = sprite.rect.copy()
					offset_rect.center -= self.offset
					self.display_surface.blit(sprite.image, offset_rect)