################################################################################
# image.py       Version 1.0     30-Jan-2025
# Taj Ballinger, Trevor Ritchie, and Bill Manaris
#
##############################################################
##################

from gui import Display, Icon

class Image():
   """
   Display window for rendering images.
   """
   def __init__(self, filename, height=None):
      """
      Creates a new image display.
      """
      # Since Python doesn't allow true overloaded constructors,
      # filename may actually be a filename to load, or 
      # a width for creating a blank canvas.

      if isinstance(filename, str) and (height is None):
         self._filename = filename
         self._icon = Icon(filename)  # load image

      elif isinstance(filename, (int, float)) and isinstance(height, (int, float)):
         self._filename = "Image"                # store default filename
         self._icon = Icon("", filename, height)  # create a blank image

      else:
         if height is None:
            raise TypeError(f'Image(): filename must be a string (it was {type(filename)})')
         else:
            raise TypeError(f'Image(): width and height must be numbers (they were {type(filename)}, {type(height)})')
      
      width, height = self._icon.getSize()
      self._display = Display(self._filename, width, height)
      self._display.add(self._icon)

   def __str__(self):
      string = "Image("

      if self._filename == "Image":
         # started with a blank file, so copy width/height
         string += f'filename = {self.getWidth()}, height = {self.getHeight()})'
      else:
         # started with a real filename, so copy that
         string += f'filename = {self._filename})'

      return string

   def __repr__(self):
      return str(self)

   @staticmethod
   def _fromPNGBytes(data):
      """
      Returns a new Image object built from raw PNG data.
      Used by music.View to render images from Verovio.
      """
      icon = Icon._fromPNGBytes(data)  # generate icon from data
      width, height = icon.getSize()   # get icon dimensions
      image = Image(width, height)     # create scaled, blank Image
      image._display.remove(image._icon)  # remove blank icon
      image._icon = icon                  # replace with new icon
      image._display.add(icon)            # and add to image display

   def show(self):
      """
      Shows the display window.
      """
      self._display.show()

   def hide(self):
      """
      Hides the display window.
      """
      self._display.hide()

   def getWidth(self):
      """
      Returns the display's canvas width (in pixels).
      """
      return self._icon.getWidth()

   def getHeight(self):
      """
      Returns the display's canvas height (in pixels).
      """
      return self._icon.getHeight()

   def getPixel(self, col, row):
      """
      Returns the [r, g, b] color of a given pixel in the image.
      """
      return self._icon.getPixel(col, row)

   def setPixel(self, col, row, RGBList):
      """
      Sets the [r, g, b] color of a given pixel in the image.
      """
      self._icon.setPixel(col, row, RGBList)

   def getPixels(self):
      """
      Returns the [r, g, b] color of all pixels in the icon as a 2-dimensional array.
      """
      return self._icon.getPixels()

   def setPixels(self, pixels):
      """
      Sets the [r, g, b] color of all pixels in the icon from a 2-dimensional array.
      """
      self._icon.setPixels(pixels)

   def write(self, filename):
      """
      Writes the image to the given filename.
      Supports JPG, JPEG, PNG, ICO, BMP, CUR, JFIF, PBM, PGM, PPM, XBM, and XPM formats.
      Read more: https://doc.qt.io/qt-6/qpixmap.html#reading-and-writing-image-files
      """
      self._display.setTitle(filename)
      self._filename = filename
      self._icon._pixmap.save(filename)

###### Unit Tests ###################################

if __name__ == "__main__":
   pass