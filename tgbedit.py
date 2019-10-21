#!/usr/bin/env python3
"""TGBEDIT: Troy's GameBoy graphics EDITor
"""

def bin2hex(binary):
    """Convert a binary number to hexadecimal number.
    """
    return format(int(binary, base=2), "x")


def checknum(value):
    """Return True if value is int or float, False if not.
    """
    if isinstance(value, list):
        check = False
        for entry in value:
            check = check or checknum(entry)
        return check
    return isinstance(value, (float, int))

def newbitmap():
    """Returns an empty bitmap dictionary. Format is (x,y): int from 0-3.

    x,y in range 0-7 inclusive.
    """
    bitmap = dict()

    for xpos in range(0, 8):
        for ypos in range(0, 8):
            bitmap[(xpos, ypos)] = 0

    return bitmap


class Char:
    """A graphics character (8x8 pixels, 2bpp depth).
    """
    def __init__(self):
        self.bitmap = newbitmap()

    def getpixel(self, xpos, ypos):
        """Return the 0-3 value of the pixel at that position.
        """
        if not checknum([xpos, ypos]):
            raise TypeError("X, Y must be a number.")

        if xpos > 7 or ypos > 7 or xpos < 0 or ypos < 0:
            raise ValueError("X, Y must be from 0-7.")

        return self.bitmap[(xpos, ypos)]

    def setpixel(self, xpos, ypos, value):
        """Set the value of the pixel for this character.
        """
        if not checknum([xpos, ypos, value]):
            raise TypeError("All arguments must be numbers.")

        if value > 3 or value < 0:
            raise ValueError("Value must be in range 0-3.")

        if xpos < 0 or xpos > 7 or ypos < 0 or ypos > 7:
            raise ValueError("X and Y pos must be in range 0-7.")

        self.bitmap[(xpos, ypos)] = value
        self.bounds()
        return value

    def bounds(self):
        """Make sure every entry in our bitmap dictionary is in range 0-3.
        """
        for xpos in range(0, 8):
            for ypos in range(0, 8):
                if self.bitmap[(xpos, ypos)] > 3:
                    self.bitmap[(xpos, ypos)] = 3
                elif self.bitmap[(xpos, ypos)] < 0:
                    self.bitmap[(xpos, ypos)] = 0

    def tobin(self):
        """Return this character in gameboy binary format, in a bytes object.
        """
        self.bounds()

        byte1 = ['0', '1', '0', '1']
        byte2 = ['0', '0', '1', '1']

        hexbyte = ''
        for ypos in range(0, 8):
            curline = [''] * 2
            for xpos in range(0, 8):
                pixel = self.getpixel(xpos, ypos)
                curline[0] += byte1[pixel]
                curline[1] += byte2[pixel]
            for line in range(0, 2):
                hexbyte += bin2hex(curline[line][0:4])
                hexbyte += bin2hex(curline[line][4:8])
        return bytes.fromhex(hexbyte)

    def frombin(self, bitbytes):
        """Set this object's bitmap via a bytes object.
        """
        if not isinstance(bitbytes, bytes):
            raise TypeError("bitbytes must be bytes object.")

        hexbytes = bitbytes.hex()
        conversion = {
            '0': '0000',
            '1': '0001',
            '2': '0010',
            '3': '0011',
            '4': '0100',
            '5': '0101',
            '6': '0110',
            '7': '0111',
            '8': '1000',
            '9': '1001',
            'a': '1010',
            'b': '1011',
            'c': '1100',
            'd': '1101',
            'e': '1110',
            'f': '1111'
        }
        pixels = ['00', '01', '10', '11']

        lines = []
        while hexbytes != '':
            twobytes = hexbytes[:4]
            hexbytes = hexbytes[4:]
            if len(twobytes) != 4:
                raise ValueError("Not enough bytes in {0}".format(twobytes))
            binary = ''
            for digit in twobytes:
                try:
                    binary += conversion[digit]
                except KeyError:
                    raise ValueError("Invalid hex digit in: {0}".format(hexbytes))
            lines.append([binary[:8], binary[8:]])


        if len(lines) != 8:
            raise ValueError("Must equate 8 lines of tiles.")

        self.bitmap = newbitmap()

        ypos = 0
        for line in lines:
            for xpos in range(0, 8):
                pixel = line[1][xpos] + line[0][xpos]
                pixel = pixels.index(pixel)
                self.setpixel(xpos, ypos, pixel)
            ypos += 1

        self.bounds()

        return self.bitmap

    def draw(self):
        """Return a string of this object.
        """
        output = "  01234567\n\n"
        for ypos in range(0, 8):
            output += str(ypos) + " "
            for xpos in range(0, 8):
                output += str(self.getpixel(xpos, ypos))
            output += "\n"
        return output

def mainloop():
    """The main loop for the editor.
    """
    tiles = []
    for curtile in range(0, 256):
        tiles.append(Char())

    curtile = 0
    quitting = False

    while not quitting:
        print("CURRENT TILE: {0}".format(curtile))
        print(tiles[curtile].draw())
        command = input(">")
        if command[0] == 'q':
            quitting = True
        elif command[0] == 'd':
            command = command[1:]
            try:
                command = command.split(',')
                if len(command) != 3:
                    raise ValueError
                for entry in enumerate(command):
                    command[entry[0]] = int(entry[1])
                tiles[curtile].setpixel(command[0], command[1], command[2])
            except (ValueError, TypeError) as err:
                print("ERROR WITH DRAW COMMAND: {0}".format(err))
        elif command[0] == 's':
            try:
                command = command[1:]
                savefile = open(command, 'wb')
                for tile in tiles:
                    savefile.write(tile.tobin())
                savefile.close()
            except TypeError as err:
                try:
                    savefile.close()
                except NameError:
                    pass
                print("ERROR WRITING FILE {0}: {1}".format(command, err))

        elif command[0] == 'l':
            try:
                command = command[1:]
                loadfile = open(command, "rb")
                for tile in tiles:
                    twobytes = loadfile.read(16)
                    tile.frombin(twobytes)
                loadfile.close()
            except FileNotFoundError:
                print("ERROR FILE NOT FOUND: ", command)
            except ValueError as err:
                print("ERROR LOADING: {0}".format(err))
                loadfile.close()

        elif command[0] == 't':
            command = command[1:]
            try:
                tileno = int(command)
            except ValueError:
                print("ERROR: tile number must be int")
            if tileno > 255 or tileno < 0:
                print("ERROR: tile number must be 0-255")
            curtile = tileno

        elif command[0] == '?':
            print("COMMANDS:")
            print("dx,y,p draws the pixel")
            print("tx switches to tile x")
            print("lfile loads file")
            print("sfile saves file")
            print("nx1,y1,x2,y2,pixel will draw a line from (x1,y1) to")
            print(" (x2,y2) in pixel color pixel.")

        elif command[0] == 'n':
            command = command[1:]
            command = command.split(',')
            if len(command) != 5:
                print("ERROR: must have 4 points and a color")
                continue

            for entry in enumerate(command):
                try:
                    command[entry[0]] = int(entry[1])
                except ValueError:
                    print("ERROR: invalid number {0}".format(entry[1]))

            check = False
            for entry in enumerate(command):
                for entry2 in enumerate(command):
                    if entry[0] == entry2[0]:
                        continue
                    if entry[1] == entry2[1]:
                        check = True
            if not check:
                print("ERROR: either horizontal or vertical lines")

            if command[0] == command[2]:
                line = 'v'
                start = command[1]
                end = command[3]
                constant = command[0]
            else:
                line = 'h'
                start = command[0]
                end = command[2]
                constant = command[1]

            points = []
            for pos in range(start, end+1):
                points.append(pos)
            for point in enumerate(points):
                if line == 'v':
                    new = (constant, point[1])
                elif line == 'h':
                    new = (point[1], constant)
                points[point[0]] = new

            color = command[4]

            for point in points:
                tiles[curtile].setpixel(point[0], point[1], color)


if __name__ == "__main__":
    mainloop()
