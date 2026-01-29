import time

class LcdApi:
    LCD_CLR = 0x01
    LCD_HOME = 0x02
    LCD_ENTRY_MODE = 0x04
    LCD_ENTRY_INC = 0x02
    LCD_ON_CTRL = 0x08
    LCD_ON_DISPLAY = 0x04
    LCD_FUNCTION = 0x20
    LCD_FUNCTION_2LINES = 0x08
    LCD_FUNCTION_RESET = 0x30
    LCD_DDRAM = 0x80

    def __init__(self, num_lines, num_columns):
        self.num_lines = min(num_lines, 4)
        self.num_columns = min(num_columns, 40)
        self.cursor_x = 0
        self.cursor_y = 0
        self.backlight = True

        self.display_off()
        self.backlight_on()
        self.clear()
        self.hal_write_command(self.LCD_ENTRY_MODE | self.LCD_ENTRY_INC)
        self.display_on()

    def clear(self):
        self.hal_write_command(self.LCD_CLR)
        self.hal_write_command(self.LCD_HOME)

    def display_on(self):
        self.hal_write_command(self.LCD_ON_CTRL | self.LCD_ON_DISPLAY)

    def display_off(self):
        self.hal_write_command(self.LCD_ON_CTRL)

    def backlight_on(self):
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, x, y):
        addr = x & 0x3F
        if y & 1:
            addr += 0x40
        if y & 2:
            addr += self.num_columns
        self.hal_write_command(self.LCD_DDRAM | addr)

    def putchar(self, char):
        self.hal_write_data(ord(char))

    def putstr(self, string):
        for c in string:
            self.putchar(c)

    def hal_backlight_on(self): pass
    def hal_backlight_off(self): pass
    def hal_write_command(self, cmd): raise NotImplementedError
    def hal_write_data(self, data): raise NotImplementedError
