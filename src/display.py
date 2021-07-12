# The MIT License (MIT)

# Copyright (c) 2021 Tom J. Sun

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import time
import math
import lcd
from machine import I2C

DEFAULT_PADDING = const(10)
MAX_BACKLIGHT = const(8)
MIN_BACKLIGHT = const(1)

class Display:
	def __init__(self, font_size=7):
		self.font_size = font_size
		self.initialize_lcd()
  		self.i2c = I2C(I2C.I2C0, freq=400000, scl=28, sda=29)
 		self.set_backlight(MAX_BACKLIGHT)

	def initialize_lcd(self):
		lcd.init(type=3)
		lcd.register(0x3A, 0x05)
		lcd.register(0xB2, [0x05, 0x05, 0x00, 0x33, 0x33])
		lcd.register(0xB7, 0x23)
		lcd.register(0xBB, 0x22)
		lcd.register(0xC0, 0x2C)
		lcd.register(0xC2, 0x01)
		lcd.register(0xC3, 0x13)
		lcd.register(0xC4, 0x20)
		lcd.register(0xC6, 0x0F)
		lcd.register(0xD0, [0xA4, 0xA1])
		lcd.register(0xD6, 0xA1)
		lcd.register(0xE0, [0x23, 0x70, 0x06, 0x0C, 0x08, 0x09, 0x27, 0x2E, 0x34, 0x46, 0x37, 0x13, 0x13, 0x25, 0x2A])
		lcd.register(0xE1,[0x70, 0x04, 0x08, 0x09, 0x07, 0x03, 0x2C, 0x42, 0x42, 0x38, 0x14, 0x14, 0x27, 0x2C])
		self.rot = 0
  
	def line_height(self):
		return self.font_size * 2

	def width(self):
		if self.rot == 0:
			return lcd.height()
		return lcd.width()

	def height(self):
		if self.rot == 0:
			return lcd.width()
		return lcd.height()

	def rotation(self, rot):
		lcd.rotation(rot)
		self.rot = rot
  
	def to_landscape(self):
		lcd.clear()
  		self.rotation(3)

	def to_portrait(self):
		lcd.clear()
		self.initialize_lcd()

	def to_lines(self, text, padding):
		screen_width = self.width() - padding * 2
		lines = []
		columns = math.ceil(screen_width / self.font_size)
		cur_column = 0
		for char in text:
			if char == '\n':
				cur_column = 0
			cur_column = (cur_column + 1) % columns
			if cur_column == 1:
				if char == ' ' or char == '\n':
					char = ''
				lines.append(char)
			else:
				lines[len(lines)-1] += char
		return lines

	def draw_hcentered_text(self, text, offset_y=DEFAULT_PADDING, color=lcd.WHITE, padding=DEFAULT_PADDING):
		screen_width = self.width() - padding * 2
		lines = self.to_lines(text, padding)
		for i, line in enumerate(lines):
			offset_x = max(0, (screen_width - (self.font_size * len(line))) // 2)
			lcd.draw_string(offset_x, offset_y + (i * self.line_height()), line, color, lcd.BLACK)
  
	def draw_centered_text(self, text, color=lcd.WHITE, padding=DEFAULT_PADDING):
		lines = self.to_lines(text, padding)
		screen_height = self.height() - padding * 2
		lines_height = len(lines) * self.line_height()
		offset_y = max(0, (screen_height - lines_height) // 2)
		self.draw_hcentered_text(text, offset_y, color, padding)
  
	def flash_text(self, text, color=lcd.WHITE, duration=3000):
		lcd.clear()
		self.draw_centered_text(text, color)
		time.sleep_ms(duration)
		lcd.clear()
		
	def draw_numpad(self, selected_key, digits, mask_digits=False, offset_y=DEFAULT_PADDING, color=lcd.WHITE):
		self.draw_hcentered_text(len(digits) * '*' if mask_digits else digits, offset_y, color)

		for x in range(3):
			for y in range(4):
				key = x + y * 3
				key_label = str(key)
				if key == 10:
					key_label = 'Del'
				elif key == 11:
					key_label = 'Go'
				lcd.draw_string(DEFAULT_PADDING + 10 + x * self.font_size * 6, offset_y + 40 + y * self.font_size * 4, key_label, color, lcd.BLACK)
				if key == selected_key:
					lcd.draw_string(DEFAULT_PADDING + x * self.font_size * 6, offset_y + 40 + y * self.font_size * 4, '>', color, lcd.BLACK)

	def draw_keypad(self, selected_key, letters, mask_letters=False, offset_y=DEFAULT_PADDING, color=lcd.WHITE):
		self.draw_hcentered_text(len(letters) * '*' if mask_letters else letters, offset_y, color)

		for x in range(5):
			for y in range(6):
				key = x + y * 5
				key_label = chr(ord('a') + key)
				if key == 26:
					key_label = 'Del'
				elif key == 27:
					key_label = 'Go'
				elif key > 27:
					continue
				lcd.draw_string(DEFAULT_PADDING - 5 + 10 + x * self.font_size * 4, offset_y + 40 + y * self.font_size * 3, key_label, color, lcd.BLACK)
				if key == selected_key:
					lcd.draw_string(DEFAULT_PADDING - 5 + x * self.font_size * 4, offset_y + 40 + y * self.font_size * 3, '>', color, lcd.BLACK)

	def draw_qr_code(self, offset_y, qr_code):
		# Add a 1px white border around the code before displaying
		qr_code = qr_code.strip()
		lines = qr_code.split('\n')
		size = len(lines)
		new_lines = ['0' * (size + 2)]
		for line in lines:
			new_lines.append('0' + line + '0')
		new_lines.append('0' * (size + 2))
		qr_code = '\n'.join(new_lines)
		lcd.draw_qr_code(offset_y, qr_code, self.width())
  
	def set_backlight(self, level):
		# Ranges from 0 to 8
		if level > 8:
			level = 8
		if level < 0:
			level = 0
		val = (level+7) << 4
		self.i2c.writeto_mem(0x34, 0x91, int(val))