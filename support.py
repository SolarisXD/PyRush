import pygame
from os import walk

def import_folder(path):
	surface_list = []

	for folder_name, sub_folders, img_files in walk(path):
		for image_name in img_files:
			full_path = path + '/' + image_name
			image_surf = pygame.image.load(full_path).convert_alpha()
			surface_list.append(image_surf)
	return surface_list

def import_folder_dict(path):
	surface_dict = {}

	for folder_name, sub_folders, img_files in walk(path):
		for image_name in img_files:
			full_path = path + '/' + image_name
			image_surf = pygame.image.load(full_path).convert_alpha()
			surface_dict[image_name.split('.')[0]] = image_surf
			
	return surface_dict


class Transition:
	"""Handles transitions between editor and game modes"""
	def __init__(self, toggle_callback):
		self.display_surface = pygame.display.get_surface()
		self.toggle_callback = toggle_callback
		self.active = False
		self.border_width = 0
		self.direction = 1
		self.center = (self.display_surface.get_width() // 2, self.display_surface.get_height() // 2)
		self.radius = self.display_surface.get_width()
		self.threshold = self.radius + 100
	
	def display(self, dt):
		if self.active:
			self.border_width += 1000 * dt * self.direction
			if self.border_width >= self.threshold:
				self.direction = -1
				self.toggle_callback()
			
			if self.border_width < 0:
				self.active = False
				self.border_width = 0
				self.direction = 1
			
			pygame.draw.circle(self.display_surface, 'black', self.center, self.radius, int(self.border_width))
