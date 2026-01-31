#######################################################################################
# gui.py       Version 1.0     15-Nov-2025
# Taj Ballinger, Trevor Ritchie, Bill Manaris, and Dana Hughes
#######################################################################################
import PySide6.QtWidgets as _QtWidgets
import PySide6.QtGui as _QtGui
import PySide6.QtCore as _QtCore
import PySide6.QtSvg as _QtSvg
import PySide6.QtOpenGLWidgets as _QtOpenGL
import PySide6.QtWebEngineCore as _QtWeb
import PySide6.QtWebEngineWidgets as _QtWebW
import PySide6.QtSvg as _QtSvg
import numpy as np
#######################################################################################

### QT
# PySide6 is a Python binding for Qt, a popular C++ framework for GUI
# development.  QApplication is the heart of this framework.

# In a typical GUI, the QApplication is created early in the main script,
#  and its .exec() method is called at the end of the program to start
#  the event loop.
# However, we want to allow the user to run and execute scripts dynamically,
#  so we can't call .exec() without occupying the main thread.  Fortunately,
#  Qt has an alternative event loop that runs in a separate thread, but only
#  while the Python interpreter is running.
# To hide the Qt event loop from the user, and allow dynamic scripting, we
#  require the user to run scripts with the -i option, which enables this
#  secondary, hidden event loop, and always makes the interpreter available.

if "_QTAPP_" not in globals():
   _QTAPP_ = None  # claim global variable for QApplication

if "_DISPLAYS_" not in globals():
   _DISPLAYS_ = []  # track all displays created


def _ensureApp():
   """Guarantee that a QApplication is running."""
   # this function is called whenever we create a new display,
   # or queue a function that modifies the display (or the display's items)
   global _QTAPP_
   if _QTAPP_ is None:
      # try to find an existing QApplication instance
      _QTAPP_ = _QtWidgets.QApplication.instance()
      if _QTAPP_ is None:
         # if no existing QApplication, create a new instance
         _QTAPP_ = _QtWidgets.QApplication([])
         _QTAPP_.setApplicationName("CreativePython")
         _QTAPP_.setStyleSheet(  # force ToolTip font color to black
            """
            QToolTip {
               color: black;
            }
            """)

_ensureApp()

#######################################################################################
# Virtual Key Constants
#######################################################################################
# Java 8 Virtual Keys -> Qt Virtual Key Codes
VK_A = _QtCore.Qt.Key.Key_A
VK_B = _QtCore.Qt.Key.Key_B
VK_C = _QtCore.Qt.Key.Key_C
VK_D = _QtCore.Qt.Key.Key_D
VK_E = _QtCore.Qt.Key.Key_E
VK_F = _QtCore.Qt.Key.Key_F
VK_G = _QtCore.Qt.Key.Key_G
VK_H = _QtCore.Qt.Key.Key_H
VK_I = _QtCore.Qt.Key.Key_I
VK_J = _QtCore.Qt.Key.Key_J
VK_K = _QtCore.Qt.Key.Key_K
VK_L = _QtCore.Qt.Key.Key_L
VK_M = _QtCore.Qt.Key.Key_M
VK_N = _QtCore.Qt.Key.Key_N
VK_O = _QtCore.Qt.Key.Key_O
VK_P = _QtCore.Qt.Key.Key_P
VK_Q = _QtCore.Qt.Key.Key_Q
VK_R = _QtCore.Qt.Key.Key_R
VK_S = _QtCore.Qt.Key.Key_S
VK_T = _QtCore.Qt.Key.Key_T
VK_U = _QtCore.Qt.Key.Key_U
VK_V = _QtCore.Qt.Key.Key_V
VK_W = _QtCore.Qt.Key.Key_W
VK_X = _QtCore.Qt.Key.Key_X
VK_Y = _QtCore.Qt.Key.Key_Y
VK_Z = _QtCore.Qt.Key.Key_Z

VK_0 = _QtCore.Qt.Key.Key_0
VK_1 = _QtCore.Qt.Key.Key_1
VK_2 = _QtCore.Qt.Key.Key_2
VK_3 = _QtCore.Qt.Key.Key_3
VK_4 = _QtCore.Qt.Key.Key_4
VK_5 = _QtCore.Qt.Key.Key_5
VK_6 = _QtCore.Qt.Key.Key_6
VK_7 = _QtCore.Qt.Key.Key_7
VK_8 = _QtCore.Qt.Key.Key_8
VK_9 = _QtCore.Qt.Key.Key_9

VK_NUMPAD0 = _QtCore.Qt.Key.Key_0
VK_NUMPAD1 = _QtCore.Qt.Key.Key_1
VK_NUMPAD2 = _QtCore.Qt.Key.Key_2
VK_NUMPAD3 = _QtCore.Qt.Key.Key_3
VK_NUMPAD4 = _QtCore.Qt.Key.Key_4
VK_NUMPAD5 = _QtCore.Qt.Key.Key_5
VK_NUMPAD6 = _QtCore.Qt.Key.Key_6
VK_NUMPAD7 = _QtCore.Qt.Key.Key_7
VK_NUMPAD8 = _QtCore.Qt.Key.Key_8
VK_NUMPAD9 = _QtCore.Qt.Key.Key_9

VK_F1  = _QtCore.Qt.Key.Key_F1
VK_F2  = _QtCore.Qt.Key.Key_F2
VK_F3  = _QtCore.Qt.Key.Key_F3
VK_F4  = _QtCore.Qt.Key.Key_F4
VK_F5  = _QtCore.Qt.Key.Key_F5
VK_F6  = _QtCore.Qt.Key.Key_F6
VK_F7  = _QtCore.Qt.Key.Key_F7
VK_F8  = _QtCore.Qt.Key.Key_F8
VK_F9  = _QtCore.Qt.Key.Key_F9
VK_F10 = _QtCore.Qt.Key.Key_F10
VK_F11 = _QtCore.Qt.Key.Key_F11
VK_F12 = _QtCore.Qt.Key.Key_F12

VK_ESCAPE        = _QtCore.Qt.Key.Key_Escape
VK_TAB           = _QtCore.Qt.Key.Key_Tab
VK_CAPS_LOCK     = _QtCore.Qt.Key.Key_CapsLock
VK_SHIFT         = _QtCore.Qt.Key.Key_Shift
VK_CONTROL       = _QtCore.Qt.Key.Key_Control
VK_ALT           = _QtCore.Qt.Key.Key_Alt
VK_SPACE         = _QtCore.Qt.Key.Key_Space
VK_ENTER         = _QtCore.Qt.Key.Key_Return
VK_BACK_SPACE    = _QtCore.Qt.Key.Key_Backspace
VK_DELETE        = _QtCore.Qt.Key.Key_Delete
VK_HOME          = _QtCore.Qt.Key.Key_Home
VK_END           = _QtCore.Qt.Key.Key_End
VK_PAGE_UP       = _QtCore.Qt.Key.Key_PageUp
VK_PAGE_DOWN     = _QtCore.Qt.Key.Key_PageDown
VK_UP            = _QtCore.Qt.Key.Key_Up
VK_DOWN          = _QtCore.Qt.Key.Key_Down
VK_LEFT          = _QtCore.Qt.Key.Key_Left
VK_RIGHT         = _QtCore.Qt.Key.Key_Right
VK_INSERT        = _QtCore.Qt.Key.Key_Insert
VK_PAUSE         = _QtCore.Qt.Key.Key_Pause
VK_PRINTSCREEN   = _QtCore.Qt.Key.Key_Print
VK_SCROLL_LOCK   = _QtCore.Qt.Key.Key_ScrollLock
VK_NUM_LOCK      = _QtCore.Qt.Key.Key_NumLock
VK_SEMICOLON     = _QtCore.Qt.Key.Key_Semicolon
VK_EQUALS        = _QtCore.Qt.Key.Key_Equal
VK_COMMA         = _QtCore.Qt.Key.Key_Comma
VK_MINUS         = _QtCore.Qt.Key.Key_Minus
VK_PERIOD        = _QtCore.Qt.Key.Key_Period
VK_SLASH         = _QtCore.Qt.Key.Key_Slash
VK_BACK_SLASH    = _QtCore.Qt.Key.Key_Backslash
VK_OPEN_BRACKET  = _QtCore.Qt.Key.Key_BracketLeft
VK_CLOSE_BRACKET = _QtCore.Qt.Key.Key_BracketRight
VK_QUOTE         = _QtCore.Qt.Key.Key_Apostrophe
VK_BACK_QUOTE    = _QtCore.Qt.Key.Key_QuoteLeft

# Arc Constants (in degrees)
PI      = 180
HALF_PI = 90
TWO_PI  = 360

# Arc Style Constants
PIE   = 0
OPEN  = 1
CHORD = 2

# Label Constants
LEFT   = _QtCore.Qt.AlignmentFlag.AlignLeft
CENTER = _QtCore.Qt.AlignmentFlag.AlignCenter
RIGHT  = _QtCore.Qt.AlignmentFlag.AlignRight

# Widget Orientation Constants
HORIZONTAL = _QtCore.Qt.Orientation.Horizontal
VERTICAL   = _QtCore.Qt.Orientation.Vertical

#######################################################################################
# Color
#######################################################################################
class Color:
   """
   Color constants and utilities.
   """
   def __init__(self, red=None, green=None, blue=None, alpha=255):
      """
      Creates a new Color object.
      """
      if None in (red, green, blue):
         # at least one color wasn't provided, so bring up color selection
         red, green, blue = _selectColor()


      # store color values as 0-255 integers
      self.red   = int(red)
      self.green = int(green)
      self.blue  = int(blue)
      self.alpha = int(alpha)

   def __str__(self):
      return f'Color(red = {self.getRed()}, green = {self.getGreen()}, blue = {self.getBlue()}, alpha = {self.getAlpha()})'

   def __repr__(self):
      return str(self)

   def getRed(self):
      """
      Returns the Color's red value (0-255).
      """
      return self.red

   def getGreen(self):
      """
      Returns the Color's green value (0-255).
      """
      return self.green

   def getBlue(self):
      """
      Returns the Color's blue value (0-255).
      """
      return self.blue

   def getAlpha(self):
      """
      Returns the Color's transparency value (0-255).
      """
      return self.alpha

   def getRGB(self):
      """
      Returns the Color's values (0-255) as a tuple.
      """
      return (self.red, self.green, self.blue)

   def getRGBA(self):
      """
      Returns the Color's values (0-255), including transparency, as a tuple.
      """
      return (self.red, self.green, self.blue, self.alpha)

   def getHex(self):
      """
      Returns the Color's values as a hex string (e.g. #FF00FF).  Includes transparency, if it's meaningful.
      """
      hex = f'#{self.red:02x}{self.green:02x}{self.blue:02x}'  # base hex string
      if self.alpha != 255:
         hex += f'{self.alpha:02x}'  # add alpha if not fully opaque
      return hex

   def brighter(self):
      """
      Returns a Color that's 10% brighter than this one.
      """
      return Color(
         min(255, int(self.red * 1.1)),
         min(255, int(self.green * 1.1)),
         min(255, int(self.blue * 1.1)),
         self.alpha
      )

   def darker(self):
      """
      Returns a Color that's 10% darker than this one.
      """
      return Color(
         max(0, int(self.red * 0.9)),
         max(0, int(self.green * 0.9)),
         max(0, int(self.blue * 0.9)),
         self.alpha
      )

   @staticmethod
   def _fromQColor(qColor):
      """
      Returns a new Color object from a QColor.
      """
      r = qColor.red()
      g = qColor.blue()
      b = qColor.red()
      a = qColor.alpha()
      return Color(r, g, b, a)

Color.BLACK      = Color(  0,   0,   0)
Color.BLUE       = Color(  0,   0, 255)
Color.CYAN       = Color(  0, 255, 255)
Color.DARK_GRAY  = Color( 44,  44,  44)
Color.GRAY       = Color(128, 128, 128)
Color.GREEN      = Color(  0, 255,   0)
Color.LIGHT_GRAY = Color(211, 211, 211)
Color.MAGENTA    = Color(255,   0, 255)
Color.ORANGE     = Color(255, 165,   0)
Color.PINK       = Color(255, 192, 203)
Color.RED        = Color(255,   0,   0)
Color.WHITE      = Color(255, 255, 255)
Color.YELLOW     = Color(255, 255,   0)
Color.CLEAR      = Color(  0,   0,   0,   0)

def _selectColor():
   """
   Opens up a color selection pane, and returns the RGB values.
   """
   defaultColor = _QtGui.QColor("white")
   color = _QtWidgets.QColorDialog.getColor(defaultColor)

   if color.isValid():
      r, g, b = color.getRgb()

   else:
      r, g, b = 0, 0, 0

   return r, g, b

#######################################################################################
# Color gradient
#
# A color gradient is a smooth color progression from one color to another,
# which creates the illusion of continuity between the two color extremes.
#
# The following auxiliary function may be used used to create a color gradient.
# This function returns a list of RGB colors (i.e., a list of lists) starting with color1
# (e.g., [0, 0, 0]) and ending (without including) color2 (e.g., [251, 147, 14], which is orange).
# The number of steps equals the number of colors in the list returned.
#
# For example, the following creates a gradient list of 12 colors:
#
# >>> colorGradient([0, 0, 0], [251, 147, 14], 12)
# [[0, 0, 0], [20, 12, 1], [41, 24, 2], [62, 36, 3], [83, 49, 4], [104, 61, 5], [125, 73, 7],
# [146, 85, 8], [167, 98, 9], [188, 110, 10], [209, 122, 11], [230, 134, 12]]
#
# Notice how the above excludes the final color (i.e.,  [251, 147, 14]).  This allows to
# create composite gradients (without duplication of colors).  For example, the following
#
# black = [0, 0, 0]         # RGB values for black
# orange = [251, 147, 14]   # RGB values for orange
# white = [255, 255, 255]   # RGB values for white
#
# cg = colorGradient(black, orange, 12) + colorGradient(orange, white, 12) + [white]
#
# creates a list of gradient colors from black to orange, and from orange to white.
# Notice how the final color, white, has to be included separately (using list concatenation).
# Now, gc contains a total of 25 unique gradient colors.
#
# For convenience, colorGradient() also works with Color objects, in which case
# it returns a list of Color objects.
#
#######################################################################################
def colorGradient(color1, color2, steps):
   """
   Returns a list of RGB colors creating a "smooth" gradient between 'color1'
   and 'color2'.  The amount of smoothness is determined by 'steps', which specifies
   how many intermediate colors to create. The result includes 'color1' but not
   'color2' to allow for connecting one gradient to another (without duplication
   of colors).
   """
   gradientList = []   # holds RGB lists of individual gradient colors

   # check if using Color objects
   if isinstance(color1, Color) and isinstance(color2, Color):
      # extract RGB values
      red1, green1, blue1 = color1.getRed(), color1.getGreen(), color1.getBlue()
      red2, green2, blue2 = color2.getRed(), color2.getGreen(), color2.getBlue()

   else:  # otherwise, assume RGB list
      # extract RGB values
      red1, green1, blue1 = color1
      red2, green2, blue2 = color2

   # find difference between color extremes
   differenceR = red2   - red1     # R component
   differenceG = green2 - green1   # G component
   differenceB = blue2  - blue1    # B component

   # interpolate RGB values between extremes
   for i in range(steps):
      gradientR = red1   + i * differenceR / steps
      gradientG = green1 + i * differenceG / steps
      gradientB = blue1  + i * differenceB / steps

      # ensure color values are integers
      gradientList.append([int(gradientR), int(gradientG), int(gradientB)])
   # now, gradient list contains all the intermediate colors, including color1
   # but not color2

   # if input was Color objects (e.g., Color.RED), return Color objects
   # otherwise, keep as RGB lists (e.g., [255, 0, 0]
   if isinstance(color1, Color):
      gradientList = [Color(rgb[0], rgb[1], rgb[2]) for rgb in gradientList]

   return gradientList


########################################################################################
# Font
########################################################################################
class Font:
   """
   Font descriptor for Label, TextField, and TextArea.
   """
   PLAIN      = (_QtGui.QFont.Weight.Normal, False)
   BOLD       = (_QtGui.QFont.Weight.Bold,   False)
   ITALIC     = (_QtGui.QFont.Weight.Normal, True)
   BOLDITALIC = (_QtGui.QFont.Weight.Bold,   True)

   def __init__(self, fontName, style=PLAIN, fontSize=-1):
      """
      Creates a new Font object.
      """
      self._name  = fontName
      self._style = style
      self._size  = fontSize

   def __str__(self):
      return f'Font(fontName = "{self.getName()}", style = {self.getStyle()}, fontSize = {self.getFontSize()})'

   def __repr__(self):
      return str(self)

   def _getQFont(self):
      """
      Returns a new QFont object with this Font's properties.
      """
      qFont = _QtGui.QFont(self._name, self._size)
      qFont.setWeight(self._style[0])
      qFont.setItalic(self._style[1])
      return qFont

   def getName(self):
      """
      Returns the Font's family name as a string.
      """
      return self._name

   def getStyle(self):
      """
      Returns the Font's style as a tuple.
      The first value represents the Font's weight.
      The second value represents whether the Font is italicized.
      """
      return self._style

   def getFontSize(self):
      """
      Returns the Font's point size.
      """
      return self._size


#######################################################################################
# Event Dispatcher
#######################################################################################
class Event():
   """
   Simple event object delivered by EventDispatcher to Interactables.
   """
   def __init__(self, type="", *args):
      """
      Creates a new Event object.
      """
      self.type    = str(type)
      self.args    = list(args)
      self.handled = False

   def __str__(self):
      return f'Event(type = {self.type}, args = {self.args})'


class EventDispatcher(_QtCore.QObject):
   """
   EventDispatchers are internal bridges between Qt's Events and JythonMusic's Events.
   You rarely instantiate this directly, as it is part of creating a Display or Group.
      QT EVENTS    -> JYTHONMUSIC EVENTS
      MousePress   -> onMouseDown
      MouseRelease -> onMouseUp + onMouseClick (if mouse didn't move)
      MouseMove    -> onMouseMove or onMouseDrag (if mouse is pressed)
      MouseEnter   -> onMouseEnter
      MouseLeave   -> onMouseExit
      KeyPress     -> onKeyDown + onKeyType
      KeyRelease   -> onKeyUp

   When an event occurs, the Display always sees the event first.
   Mouse events deliver to the topmost item at the event's position, that has a corresponding callback.
   Key events deliver to the most recent, topmost item that a mouseDown event occurred at
      ("the last item you clicked on").
   """

   def __init__(self, owner):
      """
      Creates a new EventDispatcher and attaches it to its owner Group or Display.
      """
      super().__init__()
      self.owner           = owner  # Group or Display this dispatcher listens for
      self.draggingItem    = None   # last item mouseDown was over (cleared on mouseUp)
      self.lastMouseDown   = None   # last mouseDown coordinates (cleared on mouseUp)
      self.lastMouseMove   = None   # last known mouse movement/position
      self.itemsUnderMouse = set()  # items currently under last known mouse position
      self.moveThreshold   = 5      # max distance (in pixels) for mouseClick to trigger

      if isinstance(owner, Display):
         self.owner._view.viewport().installEventFilter(self)  # redirect mouse events
         self.owner._view.installEventFilter(self)             # redirect key events

      # EventDispatcher tracks its owner's items that have event callbacks.
      # Each list corresponds to a type of event, sorted by z-order.
      # Lists are updated when an item is added or removed from the owner,
      # or when a new event callback is registered to an item in the group.
      # Maintaining these lists significantly speeds up event processing by reducing
      # the items searched to just the items who can actually handle the current event.
      self.eventHandlers = {
         'mouseDown':    [],
         'mouseUp':      [],
         'mouseClick':   [],
         'mouseMove':    [],
         'mouseDrag':    [],
         'mouseEnter':   [],
         'mouseExit':    [],
         'keyType':      [],
         'keyDown':      [],
         'keyUp':        []
      }

      # For convenience, each qEvent we listen for is paired with its handler method
      self._qMouseEventDict = {
         _QtCore.QEvent.Type.MouseButtonPress   : self._handleQMousePress,
         _QtCore.QEvent.Type.MouseButtonRelease : self._handleQMouseRelease,
         _QtCore.QEvent.Type.MouseMove          : self._handleQMouseMove,
         _QtCore.QEvent.Type.Enter              : self._handleQMouseEnter,
         _QtCore.QEvent.Type.Leave              : self._handleQMouseLeave
      }
      self._qKeyEventDict = {
         _QtCore.QEvent.Type.KeyPress           : self._handleQKeyPress,
         _QtCore.QEvent.Type.KeyRelease         : self._handleQKeyRelease
      }

   def add(self, item):
      """
      Adds an Interactable child to receive events.
      """
      if not isinstance(item, Interactable):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.add(): item should be an Interactable (it was {type(item).__name__}).')
      eventList   = item._callbackFunctions.keys()  # item's registered event types
      ownerItems  = self.owner._itemList            # list of owner's items
      objectIndex = ownerItems.index(item)          # item's index in owner's z-order

      for eventType in eventList:                        # for each event type,
         if eventType in self.eventHandlers.keys():      # ...that is a known event,
            handlerList = self.eventHandlers[eventType]  # ...get its handler list

            if item not in handlerList:  # skip if callback is already registered
               inserted = False

               if objectIndex == 0:      # object is on top, so insert in front
                  handlerList.insert(0, item)
                  inserted = True

               else:                     # otherwise, scan for its position
                  i = 0
                  while not inserted and i < len(handlerList) - 1:
                     neighbor = handlerList[i]
                     neighborIndex = self.owner.getOrder(neighbor)
                     if objectIndex < neighborIndex:
                        handlerList.insert(i, item)  # insert on top of neighbor
                        inserted = True
                     i = i + 1

               if not inserted:         # if we couldn't find a position, add to bottom
                  handlerList.append(item)

   def remove(self, item):
      """
      Removes a child item from event delivery.
      """
      for eventType in self.eventHandlers.keys():       # for each known event type,
         if item in self.eventHandlers[eventType]:      # ...if object is registered,
            self.eventHandlers[eventType].remove(item)  # ...unregister it

   def eventFilter(self, object, qEvent):
      """
      Filters Qt Events for delivery to Interactables.

      eventFilter is a Qt-defined method.  While attached to a Display,
      this method is how Qt reports events to us.
      We receive key events from Display's internal view object.
      We receive mouse events from that view object's internal viewport.
      (Mouse events from the view don't always have coordinates we need.)

      eventFilter extracts the necessary data from the QEvent and calls an
      appropriate handler method, which creates and delivers events to the
      EventDispatcher's owner and the owner's child objects.
      """
      eventHandled = False

      try:
         ##### MOUSE EVENTS #####
         if object == self.owner._view.viewport():  # viewport event, check mouse events
            if qEvent.type() in self._qMouseEventDict.keys():
               # mouse event, so we need to determine where it happened
               if hasattr(qEvent, 'position') and callable(qEvent.position):
                  x = int(qEvent.position().x())   # use qEvent coordinates, if possible
                  y = int(qEvent.position().y())
               elif self.lastMouseMove is not None:
                  x = self.lastMouseMove[0]        # fallback to last known mouse position
                  y = self.lastMouseMove[1]
               else:
                  x = 0                            # if no mouse position, use origin
                  y = 0

               handlerMethod = self._qMouseEventDict[qEvent.type()]  # find mouse handler
               eventHandled  = handlerMethod(x, y)                   # deliver coordinates

         ##### KEY EVENTS #####
         elif object == self.owner._view:  # _view event, check key events
            if qEvent.type() in self._qKeyEventDict.keys():
               # key event, so we need the key code and character typed
               if not qEvent.isAutoRepeat():  # skip held/repeated keys
                  key = qEvent.key()          # key code
                  if qEvent.text():           # character
                     char = qEvent.text()
                  else:                       # not all keys have a character (e.g. Shift)
                     char = ""
                  handlerMethod = self._qKeyEventDict[qEvent.type()]  # find key handler
                  eventHandled  = handlerMethod(key, char)            # deliver key + char

      except RuntimeError:
         # During shutdown, PySide may deliver late events to view and viewport after
         # the underlying C++ objects (e.g. QGraphicsView) are destroyed.  Since we
         # access view and viewport as part of event processing, we sometimes get
         # "RuntimeError: Internal C++ object already deleted."
         # Per PySide's maintainers, we can safely catch and ignore this for clean shutdown.
         pass

      # report results to Qt's event handler
      return eventHandled

   def deliverEvent(self, event, candidateList=None):
      """
      Delivers a JythonMusic Event to candidate recipients until Event is handled.
      """
      if (event.type in self.eventHandlers.keys()) and (not event.handled):
         if candidateList is None:  # get event's registered candidates, if needed
            candidateList = self.eventHandlers[event.type]

         if event.type.startswith('mouse'):
            x, y = event.args
            i = 0

            while not event.handled and (i < len(candidateList)):
               item = candidateList[i]
               if item.contains(x, y):   # event is within item boundaries, so...
                  if isinstance(item, Group):  # offer event to Group's children
                     item._eventDispatcher.deliverEvent(event)
                  item._receiveEvent(event)    # offer event to item
               i = i + 1

         else:
            i = 0

            while not event.handled and (i < len(candidateList)):
               item = candidateList[i]
               if isinstance(item, Group):  # offer event to Group's children
                  item._eventDispatcher.deliverEvent(event)
               item._receiveEvent(event)    # offer event to item
               i = i + 1

   def _handleQMousePress(self, x, y):
      """
      Delivers mouseDown events to the appropriate Interactable.
      """
      self.lastMouseDown = (x, y)  # store mouse down position

      i = 0  # find the topmost item with a mouseDrag callback at event coordinates
      while self.draggingItem is None and i < len(self.eventHandlers['mouseDrag']):
         item = self.eventHandlers['mouseDrag'][i]
         if item.contains(x, y):
            self.draggingItem = item  # store topmost item
         else:
            i = i + 1

      ##### MOUSE DOWN #####
      mouseDownEvent = Event('mouseDown', x, y)  # generate event
      self.deliverEvent(mouseDownEvent)          # send to items
      self.owner._receiveEvent(mouseDownEvent)   # send to owner

      return mouseDownEvent.handled

   def _handleQMouseRelease(self, x, y):
      """
      Delivers mouseUp and mouseClick events to the appropriate Interactable.
      """
      isMouseClick = False
      if self.lastMouseDown is not None:       # is the mouse down right now?
         dx = abs(x - self.lastMouseDown[0])   # yes, calculate how far mouse moved since it was pressed
         dy = abs(y - self.lastMouseDown[1])
         withinX = (dx <= self.moveThreshold)
         withinY = (dy <= self.moveThreshold)
         if withinX and withinY:               # is the movement under our moveThreshold?
            isMouseClick = True                # yes, this is also a mouseClick

      self.lastMouseDown = None  # clear mouse down position
      self.draggingItem  = None  # clear dragging item

      ##### MOUSE UP #####
      mouseUpEvent = Event('mouseUp', x, y)   # generate event
      self.deliverEvent(mouseUpEvent)         # send to items
      self.owner._receiveEvent(mouseUpEvent)  # send to owner

      ##### MOUSE CLICK #####
      if isMouseClick:
         mouseClickEvent = Event('mouseClick', x, y)  # generate event
         self.deliverEvent(mouseClickEvent)           # send to items
         self.owner._receiveEvent(mouseClickEvent)    # send to owner

      return mouseUpEvent.handled

   def _handleQMouseMove(self, x, y):
      """
      Delivers mouseMove, mouseDrag, events to the appropriate Interactable.
      Also delivers mouseEnter and mouseExit to the appropriate Drawable Interactable
      (mouseEnter and mouseExit for Displays have their own event handler).
      """
      self.lastMouseMove = (x, y)          # store current mouse position
      self._updateCoordinateTooltip(x, y)  # refresh tooltip coordinates (if needed)

      ##### MOUSE MOVE #####
      if self.lastMouseDown is None:       # mouse is up, so this is mouseMove
         mouseMoveEvent = Event('mouseMove', x, y)  # generate event
         self.deliverEvent(mouseMoveEvent)          # deliver to items
         self.owner._receiveEvent(mouseMoveEvent)   # deliver to owner

      ##### MOUSE DRAG #####
      else:                                # mouse is down, so this is mouseDrag
         mouseMoveEvent = Event('mouseDrag', x, y)  # generate event
         if self.draggingItem is not None:          # deliver to first item under mouse
            self.draggingItem._receiveEvent(mouseMoveEvent)
         self.owner._receiveEvent(mouseMoveEvent)   # deliver to owner

      ##### MOUSE ENTER/EXIT #####
      # Calculating mouseEnter and mouseExit for Drawables is somewhat expensive,
      # so we use sets for efficient difference calculations.  Sets aren't ordered,
      # so we can't promise z-order delivery, but this is rarely an issue in practice.
      itemsUnderMouseNow = set()  # determine which items are under the mouse
      for item in self.owner._itemList:
         if item.contains(x, y):
            itemsUnderMouseNow.add(item)

      # determine which of those items we're entering and exiting
      movedIntoSet  = itemsUnderMouseNow.difference(self.itemsUnderMouse)
      movedOutOfSet = self.itemsUnderMouse.difference(itemsUnderMouseNow)
      self.itemsUnderMouse = itemsUnderMouseNow

      # determine which items we're entering or exiting also have event callbacks
      enterHandlers = set(self.eventHandlers['mouseEnter']).intersection(movedIntoSet)
      exitHandlers  = set(self.eventHandlers['mouseExit']).intersection(movedOutOfSet)

      ##### MOUSE ENTER #####
      mouseEnterEvent = Event('mouseEnter', x, y)  # generate event
      for item in list(enterHandlers):             # deliver to all candidate items
         item._receiveEvent(mouseEnterEvent)

      ##### MOUSE EXIT #####
      mouseExitEvent = Event('mouseExit', x, y)    # generate event
      for item in list(exitHandlers):              # deliver to all candidate items
         item._receiveEvent(mouseExitEvent)

      return mouseMoveEvent.handled

   def _handleQMouseEnter(self, x, y):
      """
      Delivers mouseEnter events to a Display owner.
      """
      eventHandled = False

      if isinstance(self.owner, Display):
         mouseEnterEvent = Event("mouseEnter", x, y)  # generate event
         self.owner._receiveEvent(mouseEnterEvent)    # deliver to Display
         eventHandled = mouseEnterEvent.handled

      return eventHandled

   def _handleQMouseLeave(self, x, y):
      """
      Delivers mouseExit events to a Display owner.
      """
      eventHandled = False

      if isinstance(self.owner, Display):
         mouseExitEvent = Event("mouseExit", x, y)  # generate event
         self.owner._receiveEvent(mouseExitEvent)   # deliver to Display
         eventHandled = mouseExitEvent.handled

      return eventHandled

   def _handleQKeyPress(self, key, char):
      """
      Delivers keyDown and keyType events to the appropriate Interactable(s).
      """
      ##### KEY DOWN #####
      keyDownEvent = Event("keyDown", key)        # generate event
      for item in self.eventHandlers['keyDown']:  # deliver to all candidate items
         item._receiveEvent(keyDownEvent)
      self.owner._receiveEvent(keyDownEvent)      # deliver to owner

      ##### KEY TYPE #####
      keyTypeEvent = Event("keyType", char)       # generate event
      for item in self.eventHandlers['keyType']:  # deliver to all candidate items
         item._receiveEvent(keyTypeEvent)
      self.owner._receiveEvent(keyTypeEvent)      # deliver to owner

      return (keyDownEvent.handled or keyTypeEvent.handled)

   def _handleQKeyRelease(self, key, char):
      """
      Delivers keyUp events to the appropriate Interactable(s).
      """
      ##### KEY DOWN #####
      keyUpEvent = Event("keyUp", key)          # generate event
      for item in self.eventHandlers['keyUp']:  # deliver to all candidate items
         item._receiveEvent(keyUpEvent)
      self.owner._receiveEvent(keyUpEvent)      # deliver to owner

      return keyUpEvent.handled

   def _updateCoordinateTooltip(self, x, y):
      """
      Updates a Display owner's coordinate tooltip
      """
      if isinstance(self.owner, Display) and self.owner._showCoordinates:
         # override any set tooltips to show mouse coordinates instead
         # QToolTips have a delay before appearing, and automatically disappear
         # after a short time, so we force the tooltip to show immediately,
         # and refresh it whenever the mouse moves.
         globalPos   = self.owner._view.mapToGlobal(_QtCore.QPoint(x, y))
         toolTipText = f"({x}, {y})"
         _QtWidgets.QToolTip.showText(globalPos, toolTipText, self.owner._view, self.owner._view.rect(), 10000)


#######################################################################################
# Interactable
#######################################################################################
class Interactable:
   """
   Superclass that provides event/callback support for GUI events.
   """
   def __init__(self):
      self._parent = None
      self._callbackFunctions = {}

   def __str__( self ):
      return f'Interactable()'

   def __repr__( self ):
      return str(self)

   def _receiveEvent(self, event):
      """
      Receives a dispatched Event and triggers any registered callbacks.
      """
      if event.type in self._callbackFunctions:          # is event defined?
         callback = self._callbackFunctions[event.type]  # yes, get callback
         if callable(callback):                          # is callback callable?
            callback(*event.args)                        # yes, call it with args
            event.handled = True                         # mark event as handled

   def _registerCallback(self):
      """
      Internal helper to register a callback.
      """
      if isinstance(self._parent, (Display, Group)):
         self._parent._eventDispatcher.add(self)

   def onMouseClick(self, function):
      """
      Registers a callback function for mouse clicks events (down, then up).
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseClick'] = function
      self._registerCallback()

   def onMouseDown(self, function):
      """
      Registers a callback function for mouse button down events.
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseDown'] = function
      self._registerCallback()

   def onMouseUp(self, function):
      """
      Registers a callback function for mouse button up events.
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseUp'] = function
      self._registerCallback()

   def onMouseMove(self, function):
      """
      Registers a callback function for mouse move events.
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseMove'] = function
      self._registerCallback()

   def onMouseDrag(self, function):
      """
      Registers a callback function for mouse drag events (moving with mouse down).
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseDrag'] = function
      self._registerCallback()

   def onMouseEnter(self, function):
      """
      Registers a callback function for mouse enter events (enter the object's space).
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseEnter'] = function
      self._registerCallback()

   def onMouseExit(self, function):
      """
      Registers a callback function for mouse exit events (exit the object's space).
      The function should accept two parameters, an x and y coordinate.
      """
      self._callbackFunctions['mouseExit'] = function
      self._registerCallback()

   def onKeyType(self, function):
      """
      Registers a callback function for key type events.
      The function should accept one parameter, the typed character.
      """
      self._callbackFunctions['keyType'] = function
      self._registerCallback()

   def onKeyDown(self, function):
      """
      Registers a callback function for key down events.
      The function should accept one parameter, the key's code.
      """
      self._callbackFunctions['keyDown'] = function
      self._registerCallback()

   def onKeyUp(self, function):
      """
      Registers a callback function for key up events.
      The function should accept one parameter, the key's code.
      """
      self._callbackFunctions['keyUp'] = function
      self._registerCallback()


#######################################################################################
# Display
#######################################################################################
class Display(Interactable):
   """
   Top-level window and drawing canvas.  Use to draw shapes, images, text, and
   controls; handle mouse/keyboard events; and manage on-screen objects.
   """
   def __init__(self, title="", width=600, height=400, x=0, y=50, color=Color.WHITE):
      """
      Creates a new display window with given title, size, position, and background color.
      """
      _ensureApp()             # make sure Qt is running
      _DISPLAYS_.append(self)  # add to global display list

      # initialize internal properties
      self._itemList         = []     # list of items in this display (front=top)
      self._zCount           = 0.0    # float count of Qt z-orders (bottom=top)
      self._toolTipText      = None   # tooltip text for this display
      self._showCoordinates  = False  # show mouse coordinates in tooltip?

      self._localX = 0     # origin coordinates for Drawable coordinate calculations
      self._localY = 0     # (these should never change)
      self._parent = None

      Interactable.__init__(self)
      # TODO: Update these for EventDispatcher
      self._onClose     = None
      self._onPopupMenu = None

      # create display window
      window = _QtWidgets.QMainWindow()        # create window
      window.setWindowTitle(title)             # set window title
      window.setGeometry(x, y, width, height)  # set window position
      window.setFixedSize(width, height)       # prevent resizing
      window.setContextMenuPolicy( _QtCore.Qt.ContextMenuPolicy.CustomContextMenu)                       # disable default right-click menu
      window.show()

      # Display uses OpenGLWidget to render 2D graphics.  This moves graphics
      # processing to the graphics card, drastically improving performance.
      # Only Graphics are rendered this way; Controls are still rendered on the CPU.

      # set general rendering settings
      swapBehavior   = _QtGui.QSurfaceFormat.SwapBehavior.DoubleBuffer
      renderableType = _QtGui.QSurfaceFormat.RenderableType.OpenGL
      openGLProfile  = _QtGui.QSurfaceFormat.OpenGLContextProfile.CoreProfile

      format = _QtGui.QSurfaceFormat()
      format.setSwapBehavior(swapBehavior)
      format.setRenderableType(renderableType)
      format.setProfile(openGLProfile)
      _QtGui.QSurfaceFormat.setDefaultFormat(format)

      # create rendering objects
      # - scene is the canvas for Drawables
      # - view renders scene to the display window
      scene  = _QtWidgets.QGraphicsScene(0, 0, width, height)  # create canvas
      view   = _QtWidgets.QGraphicsView(scene)           # attach canvas to view
      openGL = _QtOpenGL.QOpenGLWidget()                 # create hardware accel widget
      view.setViewport(openGL)                           # attach hardware accel to view
      window.setCentralWidget(view)                      # attach view to window

      # set scene and view properties
      sceneIndex     = _QtWidgets.QGraphicsScene.ItemIndexMethod.NoIndex  # don't cache scene indices
      updateMode     = _QtWidgets.QGraphicsView.ViewportUpdateMode.MinimalViewportUpdate
      hoverTracking  = _QtCore.Qt.WidgetAttribute.WA_Hover                # track mouse movement
      mouseTracking  = _QtCore.Qt.WidgetAttribute.WA_MouseTracking        # track mouse location
      scrollPolicy   = _QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff      # disable scroll bars
      shapeAntiAlias = _QtGui.QPainter.RenderHint.Antialiasing            # smooth shapes
      pixmapSmooth   = _QtGui.QPainter.RenderHint.SmoothPixmapTransform   # smooth images
      textAntiAlias  = _QtGui.QPainter.RenderHint.TextAntialiasing        # smooth text rendering

      scene.setItemIndexMethod(sceneIndex)
      view.setViewportUpdateMode(updateMode)
      view.setAttribute(hoverTracking, True)
      view.setAttribute(mouseTracking, True)
      view.setHorizontalScrollBarPolicy(scrollPolicy)
      view.setVerticalScrollBarPolicy(scrollPolicy)
      view.setRenderHint(shapeAntiAlias, True)
      view.setRenderHint(pixmapSmooth, True)
      view.setRenderHint(textAntiAlias, True)

      # remember window, scene and view objects
      self._window = window
      self._scene  = scene
      self._view   = view

      # create event dispatcher
      self._eventDispatcher = EventDispatcher(self)
      self.setColor(color)  # set display background color

   def __str__( self ):
      return f'Display(title = "{self.getTitle()}", width = {self.getWidth()}, height = {self.getHeight()}, x = {self.getPosition()[0]}, y = {self.getPosition()[1]}, color = {self.getColor()})'

   def _getLocalCornerPosition(self):
      """
      Returns the local top-left corner for internal layout.
      """
      return self._localX, self._localY

   def show(self):
      """
      Shows the display window.
      """
      self._window.show()

   def hide(self):
      """
      Hides the display window.
      """
      self._window.hide()

   def close(self):
      """
      Closes the display window.
      """
      if 'onClose' in self._callbackFunctions:
         callback = self._callbackFunctions['onClose']
         if callable(callback):
            callback()         # call onClose function, if defined

      self._window.close()     # close window
      self.removeAll()         # remove all objects from display
      _DISPLAYS_.remove(self)  # remove from global display list

   def add(self, item, x=None, y=None):
      """
      Adds an item to the display at its current or specified position.
      Removes the item from other Groups or Displays first.
      """
      self.addOrder(item, 0, x, y)

   def place(self, item, x=None, y=None, order=0):
      """
      Places an item on the display at the specified order and position.
      Removes the item from other Groups or Displays first.
      """
      self.place(item, x, y, order)

   def addOrder(self, item, order, x, y):
      """
      Adds an item to the display at the specified order and position.
      Removes the item from other Groups or Displays first.
      """
      if not isinstance(item, Drawable):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.addOrder(): item should be a Drawable object (it was {type(item).__name__})')

      if item._parent is not None:
         item._parent.remove(item)  # remove item from any Group or Display
      item._parent = self           # tell item it is on this Display

      # add item in CreativePython
      order = max(0, min(len(self._itemList), order))  # clamp order to possible indices
      self._itemList.insert(order, item)               # insert to items list
      self._eventDispatcher.add(item)                  # register with event dispatcher

      # calculate Qt zValue
      if order == 0:                             # adding to top...
         qtZValue = 1.0
         if(len(self._itemList) > 1):
            neighbor = self._itemList[1]            # find previous topmost object
            qtZValue = neighbor._qZValue + 1.0      # get zValue above it

      elif order >= len(self._itemList) - 1:     # adding to bottom...
         qtZValue = 0.0
         if len(self._itemList) > 1:
            neighbor = self._itemList[-2]           # find previous bottommost object
            qtZValue = neighbor._qZValue - 1.0      # get zValue underneath it

      else:                                      # inserting somewhere in middle...
         frontNeighbor = self._itemList[order - 1]  # find front neighbor
         backNeighbor  = self._itemList[order + 1]  # find back neighbor
         zFront        = frontNeighbor._qZValue     # find their zValues
         zBack         = backNeighbor._qZValue
         qtZValue      = (zFront + zBack) / 2.0     # find average of neighbor zValues

      # add item in Qt
      if isinstance(item, (Graphics, Group)):  # add QGraphicsItem
         item._qZValue = qtZValue               # assign zValue
         item._qObject.setZValue(qtZValue)      # set qObject zValue
         self._scene.addItem(item._qObject)     # add to scene
         cacheMode = _QtWidgets.QGraphicsItem.CacheMode.DeviceCoordinateCache
         item._qObject.setCacheMode(cacheMode)  # set graphics caching strategy

      elif isinstance(item, Control):  # add QWidget
         item._qZValue = qtZValue               # assign zValue
         item._qObject.setParent(self._window)  # attach to window
         item._qObject.show()                   # ensure item is visible
         # NOTE: QWidgets sit on top of the Display, regardless of zValue.  However,
         # zValue plays a role in how objects receive events.

      # set item position, if needed
      if x is not None:
         item.setX(x)
      if y is not None:
         item.setY(y)

   def remove(self, item):
      """
      Removes an item from the display.
      """
      if item in self._itemList:  # skip if item not on Display
         # remove item in CreativePython
         item._parent = None                 # tell item it's not on this Display
         self._itemList.remove(item)         # remove from items list
         self._eventDispatcher.remove(item)  # de-register event callbacks

         # remove item in Qt
         if isinstance(item, (Graphics, Group)):  # remove QGraphicsItem
            self._scene.removeItem(item._qObject)    # remove from scene
         elif isinstance(item, Control):          # remove QWidget
            item._qObject.setParent(None)            # detach from window
            item._qObject.hide()                     # ensure item is hidden

   def removeAll(self):
      """
      Removes all items from the display.
      """
      self._view.setUpdatesEnabled(False)  # pause repainting
      for item in self._itemList:          # remove each item
         self.remove(item)
      self._view.setUpdatesEnabled(True)   # resume repainting
      self._view.viewport().update()       # repaint immediately

   def move(self, item, x, y):
      """
      Moves an item to the given coordinates.
      """
      if item in self._itemList:  # skip if item not on Display
         item.setPosition(x, y)   # move item

   def getOrder(self, item):
      """
      Returns the drawing order (z-index) for an item on the display.
      """
      order = None

      if item in self._itemList:  # skip if item not on Display
         order = self._itemList.index(item)

      return order

   def setOrder(self, item, order):
      """
      Sets the drawing order (z-index) for an item on the display.
      """
      if item in self._itemList:  # skip if item not on Display
         self.addOrder(item, order)  # remove and re-add item at desired order

   def setToolTipText(self, text=None):
      """
      Sets the display’s tooltip text (None clears it).
      """
      self._toolTipText = text
      self._view.setToolTip(text)

   def showMouseCoordinates(self):
      """
      Shows a tooltip with live mouse coordinates.
      """
      self._showCoordinates = True   # set flag to show coordinates
      self._view.setToolTip(None)    # remove any existing tooltip

      for item in self._itemList:    # silence item tooltips (but don't clear them)
         item._qObject.setToolTip(None)

   def hideMouseCoordinates(self):
      """
      Hides the mouse coordinate tooltip.
      """
      self._showCoordinates = False             # set flag to hide coordinates
      self._view.setToolTip(self._toolTipText)  # restore display tooltip

      for item in self._itemList:             # restore item tooltips
         item._qObject.setToolTip(item._toolTipText)

   def getColor(self):
      """
      Returns the display's background color.
      """
      qColor = self._scene.backgroundBrush().color()
      return Color._fromQColor(qColor)

   def setColor(self, color=None):
      """
      Sets the display's background color.
      """
      if isinstance(color, Color):
         r, g, b, a = color.getRGBA()

      elif color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         a = 255

      else:
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      qColor     = _QtGui.QColor(r, g, b, a)
      brush      = _QtGui.QBrush(qColor)
      self._scene.setBackgroundBrush(brush)  # on Mac
      self._view.setBackgroundBrush(brush)   # on Windows

   def getTitle(self):
      """
      Returns the display's window title.
      """
      return self._window.windowTitle()

   def setTitle(self, title):
      """
      Sets the display's  window title.
      """
      self._window.setWindowTitle(title)

   def getWidth(self):
      """
      Returns the display's canvas width (in pixels).
      """
      return int(self._scene.width())

   def getHeight(self):
      """
      Returns the display's canvas height (in pixels).
      """
      return int(self._scene.height())

   def setSize(self, width, height):
      """
      Sets the display's canvas dimensions (in pixels).
      """
      if (width <= 0) or (height <= 0):  # do some basic error checking
         print(f"{type(self).__name__}.setSize(): width and height should be positive, non-zero integers (they were {width} and {height}).")
      else:
         pos = self._window.pos()  # remember current window position

         self._scene.setSceneRect(0, 0, width, height)  # adjust scene canvas size
         self._window.setFixedSize(width, height)       # adjust window size
         self._window.move(pos)                         # ensure window doesn't move

   def getPosition(self):
      """
      Returns the display's window position on the screen.
      """
      return int(self._window.x()), int(self._window.y())

   def setPosition(self, x, y):
      """
      Moves the display's window on the screen.
      """
      self._window.setGeometry(int(x), int(y), self.getWidth(), self.getHeight())

   def getItems(self):
      """
      Returns a list of items in the display.
      """
      return self._itemList

   def addMenu(self, menu):
      """
      Attaches a top-level menu to the display.
      """
      if not isinstance(menu, Menu):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.addMenu(): menu should be a Menu object (it was {type(menu).__name__})')

      menuBar = self._window.menuBar()  # get or create this display's menuBar
      menuBar.addMenu(menu._qObject)    # add menu to the menuBar

   def addPopupMenu(self, menu):
      """
      Attaches a context (right-click) menu to the display.
      """
      if not isinstance(menu, Menu):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.addPopupMenu(): menu should be a Menu object (it was {type(menu).__name__})')

      # attach popup menu callback - this tells popup menu where to appear
      self._onPopupMenu = lambda pos: menu._qObject.exec(self._window.mapToGlobal(pos))  # set callback
      self._window.customContextMenuRequested.connect(self._onPopupMenu)  # connect to event signal

   def onClose(self, function):
      """
      Registers a callback function for window close events.
      The function should accept no parameters.
      """
      self._callbackFunctions['displayClose'] = function

   ##### CONVENIENCE METHODS
   def drawOval(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates and draws an Oval on the display; returns the object.
      """
      oval = Oval(x1, y1, x2, y2, color, fill, thickness, rotation)
      self.add(oval)
      return oval

   def drawCircle(self, x, y, radius, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates and draws a Circle on the display; returns the object.
      """
      circle = Circle(x, y, radius, color, fill, thickness, rotation)
      self.add(circle)
      return circle

   def drawPoint(self, x, y, color=Color.BLACK):
      """
      Creates and draws a Point on the display; returns the object.
      """
      point = Point(x, y, color)
      self.add(point)
      return point

   def drawArc(self, x1, y1, x2, y2, startAngle, endAngle, color = Color.BLACK, fill = False, thickness = 1):
      """
      Creates and draws an Arc on the display; returns the object.
      """
      arc = Arc(x1, y1, x2, y2, startAngle, endAngle, color, fill, thickness)
      self.add(arc)
      return arc

   def drawArcCircle(self, x, y, radius, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates and draws an ArcCircle on the display; returns the object.
      """
      arcCircle = ArcCircle(x, y, radius, startAngle, endAngle, style, color, fill, thickness, rotation)
      self.add(arcCircle)
      return arcCircle

   def drawPolyLine(self, xPoints, yPoints, color=Color.BLACK, thickness=1, rotation=0):
      """
      Creates and draws a PolyLine on the display; returns the object.
      """
      polyLine = PolyLine(xPoints, yPoints, color, thickness, rotation)
      self.add(polyLine)
      return polyLine

   def drawLine(self, x1, y1, x2, y2, color=Color.BLACK, thickness=1, rotation=0):
      """
      Creates and draws a Line on the display; returns the object.
      """
      line = Line(x1, y1, x2, y2, color, thickness, rotation)
      self.add(line)
      return line

   def drawPolygon(self, xPoints, yPoints, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates and draws a Polygon on the display; returns the object.
      """
      polygon = Polygon(xPoints, yPoints, color, fill, thickness, rotation)
      self.add(polygon)
      return polygon

   def drawRectangle(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates and draws a Rectangle on the display; returns the object.
      """
      rectangle = Rectangle(x1, y1, x2, y2, color, fill, thickness, rotation)
      self.add(rectangle)
      return rectangle

   def drawIcon(self, filename, x, y, width=None, height=None, rotation=0):
      """
      Creates and draws an Icon on the display; returns the object.
      """
      icon = Icon(filename, width, height, rotation)
      self.add(icon, x, y)
      return icon

   def drawImage(self, filename, x, y, width=None, height=None):
      """
      Creates and draws an image on the display; returns the object.
      """
      return self.drawIcon(filename, x, y, width, height)

   def drawLabel(self, text, x, y, color=Color.BLACK, font=None):
      """
      Creates and draws a Label on the display; returns the object.
      """
      label = Label(text, LEFT, color)
      if font is not None:
         label.setFont(font)
      self.add(label, x, y)
      return label

   def drawText(self, text, x, y, color=Color.BLACK, font=None):
      """
      Creates and draws text on the display; returns the object.
      """
      return self.drawLabel(text, x, y, color, font)


#######################################################################################
# GUI Superclasses (Drawable, Graphics, Group, MusicControl, and Control)
#######################################################################################
# Drawable:     items that can be rendered on a Display
# Graphics:     simple geometric shapes, icons, and text labels
# Group:        a collection of Graphics that are manipulated as one object
# MusicControl: user-styled widgets
# Control:      system-styled widgets
class Drawable:
   """
   Superclass for all items that can be added to a Display.
   Handles position, size, rotation, and hit testing.
   """
   def __init__(self):
      """
      Initializes drawable state (position, size, rotation).
      """
      self._qObject        = None  # underlying QGraphicsItem/QWidget object
      self._qZValue        = None  # qObject's order in Qt
      self._parent         = None  # Display or Group this object is on/in, if any
      self._localX         = 0     # local bounding box position, relative to parent
      self._localY         = 0     # ...
      self._width          = 0     # bounding box dimensions
      self._height         = 0     # ...
      self._originalWidth  = 0     # initial dimensions, used for rebuilding shapes
      self._originalHeight = 0     # ...
      self._rotation       = 0     # ...
      self._toolTipText    = None  # text to Display on mouse over (None == disabled)

   def __str__(self):
      return f'Drawable()'

   def __repr__(self):
      return str(self)

   ##### INTERNAL METHODS
   # These methods are hidden from the user, and do most of the work
   # for our user-facing class methods.
   # NOTE: These methods are the only way user-facing methods and
   # external classes should access or alter a Drawable's dimensions.
   # e.g. 'self._setLocalCornerPosition(x, y)' instead of 'self._localX = x'
   def _isInGroup(self):
      """
      Returns True if this item is currently in a Group.
      """
      return (self._parent is not None) and isinstance(self._parent, Group)

   def _getLocalCornerPosition(self):
      """
      Returns the item's top-left corner, relative to its parent.
      """
      return self._localX, self._localY

   def _setLocalCornerPosition(self, x, y):
      """
      Sets the item's top-left corner, relative to its parent.
      """
      self._localX = x
      self._localY = y
      self._qObject.setPos(x, y)

   def _getGlobalCornerPosition(self):
      """
      Returns the item's top-left corner, relative to its display.
      """
      x, y   = self._getLocalCornerPosition()
      parent = self._parent
      while parent is not None:  # bubble up until we find the Display
         gx, gy = parent._getLocalCornerPosition()
         x = x + gx
         y = y + gy
         parent = parent._parent
      return x, y

   def _setGlobalCornerPosition(self, x, y):
      """
      Sets the item's top-left corner, relative to its display.
      """
      if self._isInGroup():  # calculate local coordinates, relative to parent group
         gx, gy = self._parent._getGlobalCornerPosition()
         x = x - gx
         y = y - gy
      self._setLocalCornerPosition(x, y)

   def _getCenterPosition(self):
      """
      Returns the item's center, relative to its display.
      """
      x, y = self._getGlobalCornerPosition()  # find corner
      x = x + (self._width  / 2)              # offset to find center
      y = y + (self._height / 2)
      return int(x), int(y)

   def _setCenterPosition(self, x, y):
      """
      Sets the item's center, relative to its display.
      """
      x = x - (self._width / 2)   # offset to find corner
      y = y - (self._height / 2)
      self._setGlobalCornerPosition(x, y)

   def _getSize(self):
      """
      Returns the item's dimensions.
      """
      return self._width, self._height

   def _setSize(self, width, height):
      """
      Sets the item's dimensions.
      Each Drawable should override this method based on their geometry.
      """
      # Each QGraphicsItem and QWidget has slightly different
      # internal methods and objects they use to resize.
      self._width  = width
      self._height = height

   ##### DRAWABLE METHODS
   # These methods are user-facing, and are overridden for behavior changes.
   # e.g. Circles use their center coordinate for position, not their top-left corner.
   def getPosition(self):
      """
      Returns the item's (x, y) position (in pixels).
      For most shapes, this is their top-left corner.
      """
      x, y = self._getGlobalCornerPosition()
      return int(x), int(y)

   def setPosition(self, x, y):
      """
      Sets the item's position (in pixels).
      For most shapes, this is their top-left corner.
      """
      self._setGlobalCornerPosition(x, y)

   def getSize(self):
      """
      Returns the item's (width, height) dimensions (in pixels).
      """
      width, height = self._getSize()
      return int(width), int(height)

   def setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      if (width < 0) or (height < 0):  # do some basic input validation
         print(f"{type(self).__name__}.setSize(): width and height should be positive integers (they were {width} and {height}).")
      else:
         self._setSize(width, height)

   def getRotation(self):
      """
      Returns the item's current rotation (in degrees).
      """
      return int(self._rotation)

   def setRotation(self, rotation):
      """
      Sets the item's rotation (in degrees).
      Rotation starts at 3 o'clock, increasing counter-clockwise.
      Items rotate around their x, y position.
      """
      oldRotation = self.getRotation()
      rotationDelta = rotation - oldRotation
      if (int(rotationDelta) != 0):  # skip if no change
         self._rotation = rotation
         qtRotation = -rotation % 360  # reverse increasing direction (CCW -> clockwise)
         self._qObject.prepareGeometryChange()  # invalidate Qt hitbox
         self._qObject.setRotation(qtRotation)  # update rotation

   ##### CONVENIENCE METHODS
   # These methods are aliases for the methods above,
   # and shouldn't need to be changed significantly.
   def getX(self):
      """
      Returns the item's x coordinate.
      """
      x, _ = self.getPosition()
      return x

   def setX(self, x):
      """
      Sets the item's x coordinate.
      """
      self.setPosition(x, self.getY())

   def getY(self):
      """
      Returns the item's y coordinate.
      """
      _, y = self.getPosition()
      return y

   def setY(self, y):
      """
      Sets the item's y coordinate.
      """
      self.setPosition(self.getX(), y)

   def getWidth(self):
      """
      Returns the item's width (in pixels).
      """
      width, _ = self.getSize()
      return width

   def setWidth(self, width):
      """
      Sets the item's width, stretching if needed.
      """
      self.setSize(width, self.getHeight())

   def getHeight(self):
      """
      Returns the item's height (in pixels).
      """
      _, height = self.getSize()
      return height

   def setHeight(self, height):
      """
      Sets the item's height, stretching if needed.
      """
      self.setSize(self.getWidth(), height)

   def move(self, dx, dy):
      """
      Moves the item by (dx, dy) pixels.
      """
      x, y = self.getPosition()
      self.setPosition(x + dx, y + dy)

   def rotate(self, angle):
      """
      Rotates the item by the given angle (in degrees).
      """
      self.setRotation(self.getRotation() + angle)

   ##### LOCATION TESTS
   # These methods help with hit testing and location detection.
   def encloses(self, other):
      """
      Returns True if this item fully encloses the other item.
      """
      if not isinstance(other, Drawable):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.encloses(): other should be a Drawable object (it was {type(other).__name__})')
      encloses = None

      qtA = self._qObject
      qtB = other._qObject
      bothGraphics = isinstance(self, (Graphics, Group)) and isinstance(other, (Graphics, Group))
      sameDisplay  = isinstance(self._parent, Display) and (self._parent == other._parent)

      if bothGraphics and sameDisplay:  # use Qt's spatial hit test, if possible
         pathA = qtA.mapToScene(qtA.shape())
         pathB = qtB.mapToScene(qtB.shape())
         encloses = pathA.contains(pathB)

      else:                             # fallback to bounding box calculation
         x1, y1  = self._getGlobalCornerPosition()
         width, height = self.getSize()
         x2      = x1 + width
         y2      = y1 + height

         otherX1, otherY1 = other._getGlobalCornerPosition()
         otherWidth, otherHeight = other.getSize()
         otherX2 = otherX1 + otherWidth
         otherY2 = otherY1 + otherHeight

         xEncloses = (x1 <= otherX1 <= x2 and x1 <= otherX2 <= x2)
         yEncloses = (y1 <= otherY1 <= y2 and y1 <= otherY2 <= y2)
         encloses  = xEncloses and yEncloses

      return encloses

   def intersects(self, other):
      """
      Returns True if this item intersects the other item.
      """
      if not isinstance(other, Drawable):
         raise TypeError(f'{type(self).__name__}.intersects(): other should be a Drawable object (it was {type(other).__name__})')
      intersects = None

      qtA = self._qObject
      qtB = other._qObject
      bothGraphics = isinstance(self, (Graphics, Group)) and isinstance(other, (Graphics, Group))
      sameDisplay  = isinstance(self._parent, Display) and (self._parent == other._parent)

      if bothGraphics and sameDisplay:  # use Qt's spatial hit test, if possible
         pathA = qtA.mapToScene(qtA.shape())
         pathB = qtB.mapToScene(qtB.shape())
         intersects = pathA.intersects(pathB)

      else:                             # fallback to bounding box calculation
         x1, y1  = self._getGlobalCornerPosition()
         width, height = self.getSize()
         x2      = x1 + width
         y2      = y1 + height

         otherX1, otherY1 = other._getGlobalCornerPosition()
         otherWidth, otherHeight = other.getSize()
         otherX2 = otherX1 + otherWidth
         otherY2 = otherY1 + otherHeight

         xIntersects = (x1 <= otherX1 <= x2 or
                        x1 <= otherX2 <= x2 or
                   otherX1 <= x1      <= otherX2)
         yIntersects = (y1 <= otherY1 <= y2 or
                        y1 <= otherY2 <= y2 or
                   otherY1 <= y1      <= otherY2)
         intersects  = xIntersects and yIntersects

      return intersects

   def contains(self, x, y):
      """
      Returns True if the point (x, y) is inside the item.
      """
      contains = None

      if hasattr(self._qObject, "scene"):  # use Qt's spatial hit test, if possible
         targetPoint = _QtCore.QPointF(x, y)
         targetPos   = self._qObject.mapFromScene(targetPoint)
         contains    = self._qObject.contains(targetPos)

      else:                                 # fallback to bounding box calculation
         x1, y1  = self._getGlobalCornerPosition()
         width, height = self.getSize()
         x2      = x1 + width
         y2      = y1 + height

         xContains = (x1 <= x <= x2)
         yContains = (y1 <= y <= y2)
         contains  = xContains and yContains

      return contains

   def setToolTipText(self, text=None):
      """
      Sets a tooltip for this item (None clears it).
      """
      self._toolTipText = text
      self._qObject.setToolTip(text)


#######################################################################################
# Graphics
#######################################################################################
class Graphics(Drawable, Interactable):
   """
   Superclass for primitive shapes and text on a Display.
   """
   def __init__(self):
      Drawable.__init__(self)
      Interactable.__init__(self)
      self._color     = []    # stored as rgba values, not Color objects
      self._fill      = None
      self._thickness = None

   def __str__(self):
      return f'Graphics(color = {self.getColor()}, fill = {self.getFill()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   ##### NEW GRAPHICS METHODS
   def getColor(self):
      """
      Returns the item's outline and background color.
      """
      r, g, b, a = self._color
      return Color(r, g, b, a)

   def setColor(self, color=None):
      """
      Sets the item's outline and background color.
      If no color is provided, a color selection box will appear.
      """
      if isinstance(color, Color):
         r, g, b, a = color.getRGBA()

      elif color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         a = 255

      else:
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._color = [r, g, b, a]
      qColor      = _QtGui.QColor(r, g, b, a)

      qPen = self._qObject.pen()
      qPen.setColor(qColor)
      self._qObject.setPen(qPen)         # set outline color

      if self.getFill():
         qBrush = self._qObject.brush()
         qBrush.setColor(qColor)
         self._qObject.setBrush(qBrush)  # set fill color, if needed

   def getFill(self):
      """
      Returns whether the item is filled or not.
      """
      return self._fill

   def setFill(self, value):
      """
      Sets whether the item is filled or not.
      """
      self._fill = bool(value)

      if self._fill:  # use outline color
         qColor = self._qObject.pen().color()
      else:           # use transparency
         qColor = _QtGui.QColor(0, 0, 0, 0)

      qBrush = _QtGui.QBrush(qColor)
      self._qObject.setBrush(qBrush)

   def getThickness(self):
      """
      Returns the item outline thickness (in pixels).
      """
      return self._thickness

   def setThickness(self, thickness):
      """
      Sets the item's outline thickness.
      """
      self._thickness = int(thickness)
      qPen = self._qObject.pen()
      qPen.setWidth(thickness)
      self._qObject.setPen(qPen)   # set shape's outline thickness


#######################################################################################
# Group
#######################################################################################
class Group(Drawable, Interactable):
   """
   Container that groups multiple drawables to move/scale/order them together.
   """
   def __init__(self, items=[]):
      Drawable.__init__(self)
      Interactable.__init__(self)

      self._qObject = _QtWidgets.QGraphicsItemGroup()
      # self._qWidget = _QtWidgets.QWidget()
      self._eventDispatcher = EventDispatcher(self)  # event dispatcher for children
      self._itemList = []                            # list of child items

      for item in reversed(items):  # add each item, back to front
         self.add(item)

      # Our parent's EventDispatcher can see our callbacks, but not our children.
      # To ensure children receive events, we initialize each callback to None
      # to register with EventDispatcher without altering delivery behavior.
      self.onMouseClick(None)
      self.onMouseDown(None)
      self.onMouseUp(None)
      self.onMouseMove(None)
      self.onMouseDrag(None)
      self.onMouseEnter(None)
      self.onMouseExit(None)
      self.onKeyType(None)
      self.onKeyDown(None)
      self.onKeyUp(None)

   def __str__(self):
      return f'Group(items = {self._itemList})'

   def _setGlobalCornerPosition(self, x, y):
      """
      Sets the item's top-left corner, relative to its display.
      """
      oldX, oldY = self._getGlobalCornerPosition()
      dx = x - oldX
      dy = y - oldY
      self._setLocalCornerPosition(self._localX + dx, self._localY + dy)

      for child in self._itemList:  # rebase child items
         cx, cy = child._getLocalCornerPosition()
         child._setLocalCornerPosition(cx, cy)

   def _getSize(self):
      """
      Returns the item's (width, height) dimensions (in pixels).
      """
      self._calculateSize()
      return self._width, self._height

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      # TODO
      # find scaling ratios based on current size, avoiding dividing by zero
      oldWidth, oldHeight = self.getSize()
      scaleX = 0 if (oldWidth  == 0) else (width  / oldWidth)
      scaleY = 0 if (oldHeight == 0) else (height / oldHeight)

      if oldWidth != 0:  # don't divide by zero
         ratioX = width / oldWidth
      else:
         ratioX = 1

      if oldWidth != 0:  # don't divide by zero
         ratioY = height / oldHeight
      else:
         ratioY = 1

      if (ratioX != 1) or (ratioY != 1):  # skip if no significant change
         for child in self._itemList:
            w, h = child.getSize()
            newW = w * ratioX
            newH = h * ratioY

            x, y = child._getLocalCornerPosition()
            newX = x * ratioX
            newY = y * ratioY

            child.setSize(newW, newH)
            child._setLocalCornerPosition(newX, newY)
         self._updateHitbox()

   ##### NEW GROUP METHODS
   def _calculateSize(self):
      """
      Recomputes the group’s bounding box from its children.
      """
      if len(self._itemList) == 0:
         self._width  = 0
         self._height = 0
      else:
         x1s = []
         y1s = []
         x2s = []
         y2s = []

         for child in self._itemList:
            lx, ly = child._getLocalCornerPosition()
            w,  h  = child._getSize()
            x1s.append(lx)
            y1s.append(ly)
            x2s.append(lx + w)
            y2s.append(ly + h)

         minX = min(x1s)
         minY = min(y1s)
         maxX = max(x2s)
         maxY = max(y2s)

         self._width  = maxX - minX
         self._height = maxY - minY

   def _updateHitbox(self):
      """
      Updates group's Qt hitbox after geometry changes.
      """
      children = self._qObject.childItems()
      if children is not None and len(children) > 0:
         rect = children[0].boundingRect().translated(children[0].pos())
         for child in children[1:]:
            rect = rect.united(child.boundingRect().translated(child.pos()))
         self._qObject.prepareGeometryChange()
         dummy = children[0]
         self._qObject.removeFromGroup(dummy)
         self._qObject.addToGroup(dummy)

   def add(self, item):
      """
      Adds an item to the group.
      Removes the item from other Groups or Displays first.
      """
      self.addOrder(item, 0)

   def addOrder(self, item, order=0):
      """
      Adds an item to the group at the specified order.
      Removes the item from other Groups or Displays first.
      """
      if not isinstance(item, Drawable):  # do some basic type checking
         raise TypeError(f'{type(self).__name__}.addOrder(): item should be a Drawable object (it was {type(item).__name__}).')

      if isinstance(item._parent, (Group, Display)):
         item._parent.remove(item)  # remove object from any Group or display
      item._parent = self           # tell object it's in this Group now

      # add item in CreativePython
      order = max(0, min(len(self._itemList), order))  # clamp order to possible indices
      self._itemList.insert(order, item)               # insert to items list
      self._eventDispatcher.add(item)                  # register with event dispatcher

      gx, gy = item._getGlobalCornerPosition()         # calculate position in Group
      px, py = self._getGlobalCornerPosition()         # ...
      item._setLocalCornerPosition(gx - px, gy - py)   # ...
      self._calculateSize()                            # update Group dimensions
      self._updateHitbox()

      # calculate Qt zValue
      if order == 0:                             # adding to top...
         qtZValue = 1.0
         if(len(self._itemList) > 1):
            neighbor = self._itemList[1]            # find previous topmost object
            qtZValue = neighbor._qZValue + 1.0      # get zValue above it

      elif order >= len(self._itemList) - 1:     # adding to bottom...
         qtZValue = 0.0
         if len(self._itemList) > 1:
            neighbor = self._itemList[-2]           # find previous bottommost object
            qtZValue = neighbor._qZValue - 1.0      # get zValue underneath it

      else:                                      # inserting somewhere in middle...
         frontNeighbor = self._itemList[order - 1]  # find front neighbor
         backNeighbor  = self._itemList[order + 1]  # find back neighbor
         zFront        = frontNeighbor._qZValue     # find their zValues
         zBack         = backNeighbor._qZValue
         qtZValue      = (zFront + zBack) / 2.0     # find average of neighbor zValues

      # add item in Qt
      if isinstance(item, (Graphics, Group)):  # add QGraphicsItem
         item._qZValue = qtZValue                 # assign zValue
         item._qObject.setZValue(qtZValue)        # set qObject zValue
         self._qObject.addToGroup(item._qObject)  # add to QGraphicsItemGroup
         cacheMode = _QtWidgets.QGraphicsItem.CacheMode.DeviceCoordinateCache
         item._qObject.setCacheMode(cacheMode)    # set graphics caching strategy

      elif isinstance(item, Control):        # add QWidget
         print(f"{type(self).__name__}.add(): Control objects cannot be added to Groups.")
         # item._qZValue = qtZValue               # assign zValue
         # item._qObject.setParent(self._window)  # attach to window
         # item._qObject.show()                   # ensure item is visible

   def remove(self, item):
      """
      Removes an item from the group.
      """
      if item in self._itemList:  # skip if item not in Group
         # remove item in CreativePython
         item._parent = None                 # tell item it's not in this Group
         self._itemList.remove(item)         # remove item from items list
         self._eventDispatcher.remove(item)  # de-register event callbacks

         self._calculateSize()               # update Group dimensions
         self._updateHitbox()

         # remove item in Qt
         if isinstance(item, (Graphics, Group)):       # remove QGraphicsItem
            self._qObject.removeFromGroup(item._qObject)  # remove from scene
         elif isinstance(item, Control):               # remove QWidget
            item._qObject.setParent(None)                 # detach from group
            item._qObject.hide()                          # ensure item is hidden

         # add item to this Group's parent
         if self._parent is not None:
            self._parent.add(item)

   def getOrder(self, object):
      """
      Returns the drawing order (z-index) for an item in the group.
      """
      order = None

      if object in self._itemList:  # skip if item not in Group
         order = self._itemList.index(object)

      return order

   def setOrder(self, object, order):
      """
      Sets the drawing order (z-index) for an item in the group.
      """
      if (object in self._itemList): # skip if item not in Group
         self.addOrder(object, order)  # remove and re-add item at desired order


#######################################################################################
# Music Control
#######################################################################################
class MusicControl(Group):
   """
   Superclass for on-screen music controls (sliders, knobs, pads).
   """
   def __init__(self, updateFunction=None):
      """
      Initializes music control state (value, callback function, component shapes).
      """
      Group.__init__(self)
      self._value           = None
      self._function        = updateFunction
      # Since MusicControls are Groups, users can manipulate them by adding and
      # removing items.  As a result, we need a way to identify the MusicControl's
      # original components without referencing their index in itemList.
      # Also, since Groups' true dimensions change on their items, we use these
      # components' dimensions to resolve value changes from events.
      self._foregroundShape = None
      self._backgroundShape = None
      self._outlineShape    = None

   def __str__(self):
      return f'Control(startValue = {self._value}, updateFunction = {self._function})'

   def _receiveEvent(self, event):
      """
      Injects control-specific events behavior to the event receiver.
      Each MusicControl should override this method based on their function.
      """
      Group._receiveEvent(self, event)

   ##### NEW MUSICCONTROL METHODS
   def _updateAppearance(self):
      """
      Redraws the control based on its current value.
      Each MusicControl should override this method based on their appearance.
      """
      pass

   def getValue(self):
      """
      Returns the control's current value.
      """
      return int(self._value)

   def setValue(self, value):
      """
      Sets the control's current value, and updates its appearance.
      """
      if value != self._value:
         self._value = value
         self._updateAppearance()
         if (self._function is not None) and callable(self._function):
            self._function(self._value)  # call user function


#######################################################################################
# Control
#######################################################################################
class Control(Drawable, Interactable):
   """
   Superclass for widgets that sit above the Display.
   """
   # Controls have the same properties and methods as Drawables, but we have to
   # implement their position and dimension properties differently in Qt, since
   # QGraphicsItems and QWidgets only share some syntax.
   def __init__(self):
      Drawable.__init__(self)
      Interactable.__init__(self)

   def __str__(self):
      return f'Control()'

   def _setLocalCornerPosition(self, x, y):
      """
      Sets the item's top-left corner, relative to its parent.
      """
      self._localX = x
      self._localY = y
      self._qObject.move(x, y)  # .move() instead of .setPos()

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      self._qObject.setFixedSize(width, height)  # update dimensions
      self._width  = width
      self._height = height

   def setRotation(self, rotation):
      """
      Controls cannot be rotated.
      """
      print(f"{type(self).__name__}.setRotation(): Controls cannot be rotated.")


#######################################################################################
# Graphics Objects (Geometric shapes, text, and images)
#######################################################################################
class Rectangle(Graphics):
   """
   Drawable rectangle defined by its bounding box.
   """
   def __init__(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates an rectangle with corners at (x1, y1) to (x2, y2).
      """
      Graphics.__init__(self)

      # calculate bounding box dimensions
      cornerX = min(x1, x2)
      cornerY = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)

      # initialize internal shape
      self._qObject = _QtWidgets.QGraphicsRectItem(0, 0, width, height)

      # set starting values
      Rectangle.setPosition(self, cornerX, cornerY)
      self._width          = width
      self._height         = height
      self._originalWidth  = width
      self._originalHeight = height
      Rectangle.setRotation(self, rotation)
      Rectangle.setColor(self, color)
      Rectangle.setFill(self, fill)
      Rectangle.setThickness(self, thickness)

   def __str__(self):
      x2 = self.getX() + self.getWidth()
      y2 = self.getY() + self.getHeight()
      return f'Rectangle(x1 = {self.getX()}, y1 = {self.getY()}, x2 = {x2}, y2 = {y2}, color = {self.getColor()}, fill = {self.getFill()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      # scaling rectangle is simpler than most shapes
      rectangle = _QtCore.QRectF(0, 0, width, height)

      self._qObject.prepareGeometryChange()  # invalidate hitbox
      self._qObject.setRect(rectangle)       # update internal shape
      self._width  = width
      self._height = height


class Oval(Graphics):
   """
   Drawable oval defined by its bounding box.
   """
   def __init__(self, x1, y1, x2, y2, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates an oval inside the box with corners at (x1, y1) to (x2, y2).
      """
      Graphics.__init__(self)

      # calculate bounding box dimensions
      cornerX = min(x1, x2)
      cornerY = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)

      # initialize internal shape
      self._qObject = _QtWidgets.QGraphicsEllipseItem(0, 0, width, height)

      # set starting values
      Oval.setPosition(self, cornerX, cornerY)
      self._width          = width
      self._height         = height
      self._originalWidth  = width
      self._originalHeight = height
      Oval.setRotation(self, rotation)
      Oval.setColor(self, color)
      Oval.setFill(self, fill)
      Oval.setThickness(self, thickness)

   def __str__(self):
      x2 = self.getX() + self.getWidth()
      y2 = self.getY() + self.getHeight()
      return f'Oval(x1 = {self.getX()}, y1 = {self.getY()}, x2 = {x2}, y2 = {y2}, color = {self.getColor()}, fill = {self.getFill()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      # scaling oval is simpler than most shapes
      rectangle = _QtCore.QRectF(0, 0, width, height)

      self._qObject.prepareGeometryChange()  # invalidate hitbox
      self._qObject.setRect(rectangle)       # update internal shape
      self._width  = width
      self._height = height


class Circle(Oval):
   """
   Drawable circle defined by its center and radius.
   """
   def __init__(self, x, y, radius, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates a circle at (x, y) with the given radius.
      """
      x1 = x - radius  # calculate Oval dimensions
      y1 = y - radius
      x2 = x + radius
      y2 = y + radius
      Oval.__init__(self, x1, y1, x2, y2, color, fill, thickness, rotation)

   def __str__(self):
      return f'Circle(x = {self.getX()}, y = {self.getY()}, radius = {self.getRadius()}, color = {self.getColor()}, fill = {self.getFill()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def getPosition(self):
      """
      Returns the item's (x, y) position (in pixels).
      For Circles, this is their center.
      """
      x, y = self._getCenterPosition()
      return int(x), int(y)

   def setPosition(self, x, y):
      """
      Sets the item's (x, y) position (in pixels).
      For Circles, this is their center.
      """
      self._setCenterPosition(x, y)

   def setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      if int(width) != int(height):
         print(f"{type(self).__name__}.setSize(): width and height should be equal (they were {width} and {height}).")
      else:
         Oval.setSize(self, width, height)

   ##### NEW CIRCLE METHODS
   def getRadius(self):
      """
      Returns the item's radius (in pixels).
      """
      return int(self.getWidth() / 2)

   def setRadius(self, radius):
      """
      Sets the item's radius (in pixels).
      """
      self.setWidth(radius*2)  # actually, set its diameter


class Point(Circle):
   """
   Drawable single point defined by its position.
   """
   def __init__(self, x, y, color=Color.BLACK):
      """
      Creates a point at (x, y).
      """
      Circle.__init__(self, x, y, 1, color, True, 1, 0)

   def __str__(self):
      return f'Point(x = {self.getX()}, y = {self.getY()}, color = {self.getColor()})'

   def setSize(self, width, height):
      """
      Single points can't be resized.
      """
      if not self._isInGroup():
         # Groups resize en masse, so don't print if we're in a Group
         print(f"{type(self).__name__}.setSize(): Can't set the width or height of a {type(self).__name__}.")

   def setRadius(self, radius):
      """
      Single points can't be resized
      """
      print(f"{type(self).__name__}.setRadius(): Can't set the radius of a {type(self).__name__}.")

   def setFill(self, value):
      """
      Single points can't be filled.
      """
      print(f"{type(self).__name__}.setFill(): Can't set the fill of a {type(self).__name__}.")

   def setThickness(self, thickness):
      """
      Single points don't have thickness.
      """
      print(f"{type(self).__name__}.setThickness(): Can't set the thickness of a {type(self).__name__}.")


class Arc(Graphics):
   """
   Drawable arc of an ellipse defined by its bounding box and angles.
   """
   def __init__(self, x1, y1, x2, y2, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates an arc segment inside the box with corners at (x1, y1) to (x2, y2).
      """
      Graphics.__init__(self)

      # calculate dimensions
      cornerX = min(x1, x2)
      cornerY = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)
      arcWidth = -(endAngle - startAngle)  # Qt angles are opposite ours, so negate

      # initialize internal shape
      path = _QtGui.QPainterPath()
      path.arcMoveTo(0, 0, width, height, startAngle)        # move to start angle
      path.arcTo(0, 0, width, height, startAngle, arcWidth)  # draw arc

      if style == PIE:
         centerX = width  / 2
         centerY = height / 2
         path.lineTo(centerX, centerY)  # connect arc to center
         path.closeSubpath()            # return to start point
      elif style == CHORD:
         path.closeSubpath()            # return to start point
      elif style == OPEN:
         pass                           # leave open

      self._qObject    = _QtWidgets.QGraphicsPathItem(path)
      self._startAngle = startAngle
      self._endAngle   = endAngle
      self._arcWidth   = arcWidth
      self._style      = style

      # set starting values
      Arc.setPosition(self, cornerX, cornerY)
      self._width          = width
      self._height         = height
      self._originalWidth  = width
      self._originalHeight = height
      Arc.setRotation(self, rotation)
      Arc.setColor(self, color)
      Arc.setFill(self, fill)
      Arc.setThickness(self, thickness)

   def __str__(self):
      x2 = self.getX() + self.getWidth()
      y2 = self.getY() + self.getHeight()
      return f'Arc(x1 = {self.getX()}, y1 = {self.getY()}, x2 = {x2}, y2 = {y2}, startAngle = {self._startAngle}, endAngle = {self._endAngle}, style = {self._style}, color = {self.getColor()}, fill = {self.getFill()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      oldWidth, oldHeight = self._getSize()

      if (oldWidth != 0) and (oldHeight != 0):
         # If current dimensions are usable, we prefer scaling with QTransform,
         # since it's significantly faster than rebuilding the shape.
         scaleX = width  / oldWidth
         scaleY = height / oldHeight

         oldPath   = self._qObject.path()
         oldRect   = oldPath.boundingRect()
         transform = _QtGui.QTransform()
         transform.translate(-oldRect.x(), -oldRect.y())  # move origin to (0, 0)
         transform.scale(scaleX, scaleY)                  # scale to new size
         transform.translate(oldRect.x(), oldRect.y())    # return to original position
         path = transform.map(oldPath)                    # apply transformation

      else:
         # If either dimension is currently 0, we need to rebuild,
         # since scaling a flattened shape won't restore the original geometry.
         path = _QtGui.QPainterPath()
         path.arcMoveTo(0, 0, width, height, self._startAngle)
         path.arcTo(0, 0, width, height, self._startAngle, self._arcWidth)

         if self._style == PIE:
            centerX = width  / 2
            centerY = height / 2
            path.lineTo(centerX, centerY)  # connect arc to center
            path.closeSubpath()            # return to start point
         elif self._style == CHORD:
            path.closeSubpath()            # return to start point
         elif self._style == OPEN:
            pass                           # leave open

      # either way, update with resized dimensions
      self._qObject.prepareGeometryChange()   # invalidate hitbox
      self._qObject.setPath(path)             # update path
      Drawable._setSize(self, width, height)  # update dimensions


class ArcCircle(Arc):
   """
   Drawable arc of a circle defined by its center, radius, and angles.
   """
   def __init__(self, x, y, radius, startAngle=PI, endAngle=TWO_PI, style=OPEN, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates an arc segment inside the circle at (x, y) with given radius.
      """
      x1 = x - radius  # calculate Arc dimensions
      y1 = y - radius
      x2 = x + radius
      y2 = y + radius
      Arc.__init__(self, x1, y1, x2, y2, startAngle, endAngle, style, color, fill, thickness, rotation)

   def __str__(self):
      return f'ArcCircle(x = {self.getX()}, y = {self.getY()}, radius = {self.getRadius()}, startAngle = {self._startAngle}, endAngle = {self._endAngle}, style = {self._style}, color = {self.getColor()}, fill = {self.getFill()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def getPosition(self):
      """
      Returns the item's (x, y) position (in pixels).
      For ArcCircles, this is their center.
      """
      return self._getCenterPosition()

   def setPosition(self, x, y):
      """
      Sets the item's (x, y) position (in pixels).
      For ArcCircles, this is their center.
      """
      self._setCenterPosition(x, y)

   def setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      if width != height:
         print(f"{type(self).__name__}.setSize(): width and height should be equal (they were {width} and {height}).")
      else:
         Arc.setSize(self, width, height)

   ##### NEW ARCCIRCLE METHODS
   def getRadius(self):
      """
      Returns the item's radius (in pixels).
      """
      return int(self.getWidth() / 2)

   def setRadius(self, radius):
      """
      Sets the item's radius (in pixels).
      """
      self.setWidth(radius*2)  # actually, set its diameter


class PolyLine(Graphics):
   """
   Drawable lines between a series of points.
   """
   def __init__(self, xPoints, yPoints, color=Color.BLACK, thickness=1, rotation=0):
      """
      Creates lines between a series of points.
      """
      if len(xPoints) != len(yPoints):
         raise ValueError(f'{type(self).__name__}(): xPoints and yPoints must have the same number of points (they had {len(xPoints)} and {len(yPoints)} points).')

      Graphics.__init__(self)

      # calculate dimensions
      cornerX = min(xPoints)
      cornerY = min(yPoints)
      width   = max(xPoints) - cornerX
      height  = max(yPoints) - cornerY
      self._xPoints = []   # store original xPoints and yPoints as local coordinates
      self._yPoints = []   # when we need them, we'll recalculate global coordinates

      # initialize internal shape
      path = _QtGui.QPainterPath()
      x = xPoints[0] - cornerX       # get first local point
      y = yPoints[0] - cornerY       # ...
      self._xPoints.append(x)        # remember local position
      self._yPoints.append(y)        # ...
      path.moveTo(x, y)              # move to first point
      for i in range(1, len(xPoints)):  # for every other point...
         x = xPoints[i] - cornerX       # get next local point
         y = yPoints[i] - cornerY       # ...
         self._xPoints.append(x)        # remember local position
         self._yPoints.append(y)        # ...
         path.lineTo(x, y)              # draw to next local point

      self._qObject = _QtWidgets.QGraphicsPathItem(path)

      # set starting values
      PolyLine.setPosition(self, cornerX, cornerY)
      self._width          = width
      self._height         = height
      self._originalWidth  = width
      self._originalHeight = height
      PolyLine.setRotation(self, rotation)
      PolyLine.setColor(self, color)
      PolyLine.setThickness(self, thickness)

   def __str__(self):
      xPoints, yPoints = self._getPoints()
      return f'PolyLine(xPoints = {xPoints}, yPoints = {yPoints}, color = {self.getColor()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      oldWidth, oldHeight = self._getSize()

      if (oldWidth != 0) and (oldHeight != 0):
         # If current dimensions are usable, we prefer scaling with QTransform,
         # since it's significantly faster than rebuilding the shape.
         scaleX = width  / oldWidth
         scaleY = height / oldHeight

         oldPath   = self._qObject.path()
         oldRect   = oldPath.boundingRect()
         transform = _QtGui.QTransform()
         transform.translate(-oldRect.x(), -oldRect.y())  # move origin to (0, 0)
         transform.scale(scaleX, scaleY)                  # scale to new size
         transform.translate(oldRect.x(), oldRect.y())    # return to original position
         path = transform.map(oldPath)                    # apply transformation

      else:
         # If either dimension is currently 0, we need to rebuild,
         # since scaling a flattened shape won't restore the original geometry.

         # find scaling ratios based on original size, avoiding dividing by zero
         scaleX = 0 if (self._originalWidth  == 0) else (width  / self._originalWidth)
         scaleY = 0 if (self._originalHeight == 0) else (height / self._originalHeight)

         # rebuild shape, scaled appropriately
         path = _QtGui.QPainterPath()
         x    = self._xPoints[0] * scaleX     # get first local, scaled point
         y    = self._yPoints[0] * scaleY     # ...
         path.moveTo(x, y)                    # move to first point
         for i in range(1, len(self._xPoints)):  # for every other local point...
            x = self._xPoints[i] * scaleX        # get next scaled point
            y = self._yPoints[i] * scaleY        # ...
            path.lineTo(x, y)                    # draw to scaled point

      # either way, update with resized dimensions
      self._qObject.prepareGeometryChange()   # invalidate hitbox
      self._qObject.setPath(path)             # update path
      Drawable._setSize(self, width, height)  # update dimensions

   ##### NEW POLYLINE METHODS
   def _getPoints(self):
      """
      Rebuilds xPoints and yPoints, accounting for changes in global coordinates.
      """
      # find current scaling ratios, avoiding dividing by zero
      width, height = self._getSize()
      scaleX  = 0 if (self._originalWidth  == 0) else (width  / self._originalWidth)
      scaleY  = 0 if (self._originalHeight == 0) else (height / self._originalHeight)
      xPoints = []
      yPoints = []
      cornerX, cornerY = self.getPosition()

      for i in range(len(self._xPoints)):  # unpack points to global coordinates
         x = int(cornerX + (self._xPoints[i] * scaleX))
         y = int(cornerY + (self._yPoints[i] * scaleY))
         xPoints.append(x)
         yPoints.append(y)

      return xPoints, yPoints


class Line(PolyLine):
   """
   Drawable line between two endpoints.
   """
   def __init__(self, x1, y1, x2, y2, color=Color.BLACK, thickness=1, rotation=0):
      """
      Creates a line from (x1, y1) to (x2, y2).
      """
      xPoints = [x1, x2]
      yPoints = [y1, y2]
      PolyLine.__init__(self, xPoints, yPoints, color, thickness, rotation)

   def __str__(self):
      xPoints, yPoints = self._getPoints()
      x1, x2 = xPoints
      y1, y2 = yPoints
      return f'Line(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, color = {self.getColor()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def getFill(self):
      """
      Returns whether the item is filled or not.
      """
      return False

   def setFill(self, value):
      """
      Lines can't be filled.
      """
      print(f"{type(self).__name__}.setFill(): Can't set the fill of a Line.")

   ##### NEW LINE METHODS
   def getLength(self):
      """
      Returns the distance between the line's endpoints (in pixels).
      """
      width, height = self._getSize()
      length = float(np.sqrt(width**2 + height**2))  # euclidean distance
      return length

   def setLength(self, length):
      """
      Sets the distance between the line's endpoints (in pixels).
      The line's second endpoint (x2, y2) moves to match.
      """
      xPoints, yPoints = self._getPoints()
      x1, x2 = xPoints  # get global endpoints
      y1, y2 = yPoints
      
      dx = x2 - x1  # find distance, preserving direction
      dy = y2 - y1
      distance = np.hypot(dx, dy)

      cornerX, cornerY = self.getPosition()  # find local position

      if distance == 0:
         # line doesn't have direction, since its endpoints are the same
         # default to extending to the right
         newX2 = cornerX + length
         newY2 = cornerY

      else:
         # distance is usable, so find new endpoint
         ux = dx / distance  # find scaling ratio
         uy = dy / distance
         
         newX2 = x1 + (length * ux)  # scale to new endpoint
         newY2 = y1 + (length * uy)

      # recalculate line dimensions
      newCornerX = min(x1, newX2)
      newCornerY = min(y1, newY2)
      newWidth   = max(x1, newX2) - newCornerX
      newHeight  = max(y1, newY2) - newCornerY

      localX1 = x1 - newCornerX
      localY1 = y1 - newCornerY
      localX2 = newX2 - newCornerX
      localY2 = newY2 - newCornerY

      # rebuild internal path object
      path = _QtGui.QPainterPath()
      path.moveTo(localX1, localY1)
      path.lineTo(localX2, localY2)
      self._qObject.prepareGeometryChange()
      self._qObject.setPath(path)

      # reset internal dimensions
      self._xPoints = [localX1, localX2]
      self._yPoints = [localY1, localY2]
      Line.setPosition(self, newCornerX, newCornerY)
      self._width          = newWidth
      self._height         = newHeight
      self._originalWidth  = newWidth
      self._originalHeight = newHeight


class Polygon(Graphics):
   """
   Drawable shape defined by a series of points.
   """
   def __init__(self, xPoints, yPoints, color=Color.BLACK, fill=False, thickness=1, rotation=0):
      """
      Creates a polygon from a series of points.
      """
      if len(xPoints) != len(yPoints):
         raise ValueError(f'{type(self).__name__}(): xPoints and yPoints must have the same number of points (they had {len(xPoints)} and {len(yPoints)} points).')

      Graphics.__init__(self)

      # calculate dimensions
      cornerX = min(xPoints)
      cornerY = min(yPoints)
      width   = max(xPoints) - cornerX
      height  = max(yPoints) - cornerY
      self._xPoints = []   # store original xPoints and yPoints as local coordinates
      self._yPoints = []   # when we need them, we'll recalculate global coordinates

      # initialize internal shape
      polygon = _QtGui.QPolygonF()
      for i in range(len(xPoints)):             # for every global point...
         x = xPoints[i] - cornerX               # get local point
         y = yPoints[i] - cornerY               # ...
         self._xPoints.append(x)                # remember local point
         self._yPoints.append(y)                # ...
         polygon.append(_QtCore.QPointF(x, y))  # add local point to polygon

      self._qObject = _QtWidgets.QGraphicsPolygonItem(polygon)

      # set starting values
      Polygon.setPosition(self, cornerX, cornerY)
      self._width          = width
      self._height         = height
      self._originalWidth  = width
      self._originalHeight = height
      Polygon.setRotation(self, rotation)
      Polygon.setColor(self, color)
      Polygon.setFill(self, fill)
      Polygon.setThickness(self, thickness)

   def __str__(self):
      xPoints, yPoints = self._getPoints()
      return f'Polygon(xPoints = {xPoints}, yPoints = {yPoints}, color = {self.getColor()}, thickness = {self.getThickness()}, rotation = {self.getRotation()})'

   def _setSize(self, width, height):
      """
      Sets the item's dimensions, stretching if needed.
      """
      oldWidth, oldHeight = self._getSize()

      if (oldWidth != 0) and (oldHeight != 0):
         # If current dimensions are usable, we prefer scaling with QTransform,
         # since it's significantly faster than rebuilding the shape.
         scaleX = width  / oldWidth
         scaleY = height / oldHeight

         oldPolygon = self._qObject.polygon()
         oldRect    = oldPolygon.boundingRect()
         transform  = _QtGui.QTransform()
         transform.translate(-oldRect.x(), -oldRect.y())  # move origin to (0, 0)
         transform.scale(scaleX, scaleY)                  # scale to new size
         transform.translate(oldRect.x(), oldRect.y())    # return to original position
         polygon = transform.map(oldPolygon)              # apply transformation

      else:
         # If either dimension is currently 0, we need to rebuild,
         # since scaling a flattened shape won't restore the original geometry.

         # find scaling ratios based on original size, avoiding dividing by zero
         scaleX = 0 if (self._originalWidth  == 0) else (width  / self._originalWidth)
         scaleY = 0 if (self._originalHeight == 0) else (height / self._originalHeight)

         # rebuild shape, scaled appropriately
         polygon = _QtGui.QPolygonF()
         for i in range(len(self._xPoints)):       # for every local point...
            x = self._xPoints[i] * scaleX          # get scaled point
            y = self._yPoints[i] * scaleY          # ...
            polygon.append(_QtCore.QPointF(x, y))  # add scaled point to polygon

      # either way, update with resized dimensions
      self._qObject.prepareGeometryChange()   # invalidate hitbox
      self._qObject.setPolygon(polygon)       # update polygon
      Drawable._setSize(self, width, height)  # update dimensions

   ##### NEW POLYGON METHODS
   def _getPoints(self):
      """
      Rebuilds xPoints and yPoints, accounting for changes in global coordinates.
      """
      # find current scaling ratios, avoiding dividing by zero
      width, height = self.getSize()
      scaleX  = 0 if (self._originalWidth  == 0) else (width  / self._originalWidth)
      scaleY  = 0 if (self._originalHeight == 0) else (height / self._originalHeight)
      xPoints = []
      yPoints = []
      cornerX, cornerY = self.getPosition()

      for i in range(len(self._xPoints)):  # unpack points to global coordinates
         x = int(cornerX + (self._xPoints[i] * scaleX))
         y = int(cornerY + (self._yPoints[i] * scaleY))
         xPoints.append(x)
         yPoints.append(y)

      return xPoints, yPoints


class Icon(Graphics):
   """
   Icons are sprites made from individual pixels.
   """
   def __init__(self, filename, width=None, height=None, rotation=0):
      """
      Creates an icon from a given file, or creates a new, blank icon.
      Supports JPG, JPEG, PNG, GIF, SVG, SVGZ, ICO, BMP, CUR, JFIF, PBM, PGM, PPM, XBM, and XPM formats.
      Read more: https://doc.qt.io/qt-6/qpixmap.html#reading-and-writing-image-files
      """
      Graphics.__init__(self)

      # initialize internal shape
      try:
#          if filename.lower().endswith(".svg"):  # rasterize SVG file
#             # render with QWebEngine... (fails to launch web event loop)
#             view = _QtWebW.QWebEngineView()
#             with open(filename, "r", encoding="utf-8") as f:
#                svg = f.read()

#             html = f"""
# <!DOCTYPE html>
# <html>
#    <body style="margin:0; padding:0; overflow:hidden;">
#       {svg}
#    </body>
# </html>
# """
#             view.setHtml(html, _QtCore.QUrl.fromLocalFile(filename))
#             view.show()
#             size = _QtCore.QSize(600, 400)
#             pixmap = _QtGui.QPixmap(size)
#             pixmap.fill(_QtGui.QColorConstants.Transparent)

         #    # render with SVG Renderer... (only supports Tiny 1.2)
         #    renderer = _QtSvg.QSvgRenderer(filename)
         #    size = renderer.defaultSize()
         #    pixmap = _QtGui.QPixmap(size)
         #    pixmap.fill(_QtGui.QColorConstants.Transparent)
         #    painter = _QtGui.QPainter(pixmap)
         #    renderer.render(painter)
         #    painter.end()

         # else:
         #    pixmap = _QtGui.QPixmap(filename)  # create pixmap from file

         pixmap = _QtGui.QPixmap(filename)  # create pixmap from file

         if width is None and height is None:  # no scaling needed
            width  = pixmap.width()
            height = pixmap.height()
         elif width is None:                   # scale width to height
            width = int(pixmap.width() * (height / pixmap.height()))
         elif height is None:                  # scale height to width
            height = int(pixmap.height() * (width / pixmap.width()))

         scaledPixmap = pixmap.scaled(width, height)  # scale new pixmap

      except:  # ... create blank pixmap if import fails (used intentionally in Image)
         if width is None:
            width = 600
         if height is None:
            height = 400
         pixmap = _QtGui.QPixmap(width, height)       # save original pixmap
         scaledPixmap = pixmap.scaled(width, height)  # alias a scaled pixmap

      self._qObject  = _QtWidgets.QGraphicsPixmapItem(scaledPixmap)
      self._filename = filename
      self._pixmap   = pixmap

      # set starting values
      Icon.setPosition(self, 0, 0)
      self._width          = width
      self._height         = height
      self._originalWidth  = width
      self._originalHeight = height
      Icon.setRotation(self, rotation)
      self._color = [0, 0, 0, 0]

   def __str__(self):
      return f'Icon(filename = "{self._filename}", width = {self.getWidth()}, height = {self.getHeight()}, rotation = {self.getRotation()})'

   @staticmethod
   def _fromPNGBytes(data):
      """
      Returns a new Icon object built from raw PNG data.
      """
      pixmap = _QtGui.QPixmap()
      pixmap.loadFromData(data)  # build pixmap from data

      width  = pixmap.width()    # get pixmap dimensions
      height = pixmap.height()

      icon = Icon("", width, height)   # create blank icon
      icon._pixmap = pixmap            # update icon pixmap
      icon._qObject.setPixmap(pixmap)  # update internal pixmap

      return icon

   def setSize(self, width, height=None):
      """
      Sets the item's dimensions, stretching if needed.
      """
      if height is None:  # scale height to width
         height = int(self._pixmap.height() * (width / self._pixmap.width()))

      pixmap = self._pixmap.scaled(width, height)  # scale new pixmap
      self._qObject.prepareGeometryChange()        # invalidate old hitbox
      self._qObject.setPixmap(pixmap)              # set scaled pixmap to object
      Drawable._setSize(int(width), int(height))   # store dimensions

   def setFill(self, value):
      """
      Icons can't be filled.
      """
      print(f"{type(self).__name__}.setFill(): Can't set the fill of an Icon.")

   def setThickness(self, thickness):
      """
      Icons don't have outline thickness.
      """
      print(f"{type(self).__name__}.setThickness(): Can't set the thickness of an Icon.")

   ##### NEW ICON METHODS
   def crop(self, x, y, width, height):
      """
      Crop the icon to the specified rectangle, relative to the icon's position.
      """
      self._pixmap = self._pixmap.copy(x, y, width, height)  # crop internal pixmap
      pixmap = self._pixmap.scaled(width, height)  # create scaled copy of pixmap
      self._qObject.setPixmap(pixmap)              # set scaled pixmap to object
      self._qObject.moveBy((width/2), (height/2))  # keep icon centered in place
      Drawable._setSize(int(width), int(height))   # store new dimensions

   def getPixel(self, col, row):
      """
      Returns the [r, g, b] color of a given pixel in the icon.
      """
      image = self._pixmap.toImage()      # convert pixmap to image
      color = image.pixelColor(col, row)  # get pixel color
      r = color.red()                     # extract RGB values
      g = color.green()
      b = color.blue()
      a = color.alpha()
      return [r, g, b]

   def setPixel(self, col, row, color):
      """
      Sets the [r, g, b] color of a given pixel in the icon.
      """
      r, g, b = color  # extract RGB values
      a = 255          # set alpha to 255 (fully opaque)
      qtColor = _QtGui.QColor(r, g, b, a)     # create color object

      image = self._pixmap.toImage()          # convert pixmap to image
      image.setPixelColor(col, row, qtColor)  # set pixel color

      self._pixmap = _QtGui.QPixmap(image)    # create new pixmap from image

      scaledPixmap = self._pixmap.scaled(self.getWidth(), self.getHeight())  # create scaled copy of pixmap
      self._qObject.setPixmap(scaledPixmap)   # set scaled pixmap to object

   def getPixels(self):
      """
      Returns the [r, g, b] color of all pixels in the icon as a 2-dimensional array.
      """
      # we could iterate through pixels and extract each color,
      # but we can get better performance by converting the icon to a numpy array
      # and extracting pixels from there.
      image  = self._pixmap.toImage()                                # convert pixmap to image data
      image  = image.convertToFormat(_QtGui.QImage.Format_RGBA8888)  # convert to RGBA format
      ptr    = image.bits()                                          # get pointer bits to image data
      buffer = ptr.tobytes()                                         # safely convert to bytes
      arr    = np.frombuffer(buffer, dtype=np.uint8)                 # generate numpy array from image
      arr    = arr.reshape((image.height(), image.width(), 4))       # reshape to image dimensions
      rgb    = arr[:, :, :3]                                         # slice array to only RGB values
      return rgb.tolist()                                            # return as list

   def setPixels(self, pixels):
      """
      Sets the [r, g, b] color of all pixels in the icon from a 2-dimensional array.
      """
      # reversing the process in getPixels()...
      arr = np.array(pixels, dtype=np.uint8)  # generate numpy array from pixel list
      height, width, channels = arr.shape     # extract image dimensions

      if channels == 3:                       # add alpha channel, if not present
         alpha = np.full((height, width, 1), 255, dtype=np.uint8)
         arr   = np.concatenate((arr, alpha), axis=2)

      arr   = np.ascontiguousarray(arr)       # ensure contiguous array
      image = _QtGui.QImage(arr.data, width, height, width * 4, _QtGui.QImage.Format_RGBA8888)  # generate image
      image = image.copy()                    # detach image from numpy array (important!!)

      self._pixmap = _QtGui.QPixmap(image)                           # store image as pixmap
      scaledPixmap = self._pixmap.scaled(self._width, self._height)  # scale to expected dimensions
      self._qObject.setPixmap(scaledPixmap)                          # set scaled pixmap


class Label(Graphics):
   """
   Drawable single-line text.
   """
   def __init__(self, text, alignment=LEFT, foregroundColor=Color.BLACK, backgroundColor=Color.CLEAR, rotation=0):
      """
      Create a new text label.
      """
      Graphics.__init__(self)

      # initialize internal shapes
      # NOTE: QGraphicsTextItems don't have backgrounds, but Labels do.
      # So, Label's QObject is actually a QGraphicsItemGroup that contains
      # a QGraphicsTextItem and QGraphicsRectItem for a background.
      # However, Label doesn't have full Group functionality because we
      # still want to treat Labels as primitive Graphics.
      textObject = _QtWidgets.QGraphicsTextItem(str(text))  # create foreground text
      r, g, b, a = foregroundColor.getRGBA()                # get color values
      qtForegroundColor = _QtGui.QColor(r, g, b, a)         # create Qt color
      textObject.setDefaultTextColor(qtForegroundColor)     # set foreground color

      background = _QtWidgets.QGraphicsRectItem(textObject.boundingRect())  # create background rectangle
      r, g, b, a = backgroundColor.getRGBA()        # get color values
      backgroundColor = _QtGui.QColor(r, g, b, a)   # create Qt color
      background.setBrush(backgroundColor)          # set background color
      background.setPen(_QtCore.Qt.PenStyle.NoPen)  # remove border

      self._qObject  = _QtWidgets.QGraphicsItemGroup()
      self._qObject.addToGroup(background)  # add background to group
      self._qObject.addToGroup(textObject)  # add foreground to group
      self._qTextObject       = textObject
      self._qBackgroundObject = background

      # start starting values
      Label.setAlignment(self, alignment)
      Label.setRotation(self, rotation)

   def __str__(self):
      return f'Label(text = "{self.getText()}", alignment = {self.getAlignment()}, foregroundColor = {self.getForegroundColor()}, backgroundColor = {self.getBackgroundColor()}, rotation = {self.getRotation()})'

   def setColor(self, color=None):
      """
      Sets the item's font color.
      If no color is provided, a color selection box will appear.
      """
      if isinstance(color, Color):
         r, g, b, a = color.getRGBA()

      elif color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         a = 255

      else:
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._color = [r, g, b, a]
      qColor      = _QtGui.QColor(r, g, b, a)
      self._qTextObject.setDefaultTextColor(qColor)

   def setFill(self, value):
      """
      Sets whether the item's background is filled or not.
      """
      self._fill = bool(value)

      if self._fill:  # use outline color
         qColor = self._qBackgroundObject.pen().color()
      else:           # use transparency
         qColor = _QtGui.QColor(0, 0, 0, 0)

      qBrush = _QtGui.QBrush(qColor)
      self._qBackgroundObject.setBrush(qBrush)

   def setThickness(self, thickness):
      """
      Sets the item's outline thickness.
      """
      self._thickness = int(thickness)
      qPen = self._qBackgroundObject.pen()
      qPen.setWidth(thickness)
      self._qBackgroundObject.setPen(qPen)   # set shape's outline thickness

   ##### NEW LABEL METHODS
   def getText(self):
      """
      Returns the label's text.
      """
      return self._qTextObject.toPlainText()

   def setText(self, text):
      """
      Sets the label's text.
      """
      self._qTextObject.setPlainText(str(text))

   def getForegroundColor(self):
      """
      Returns the label's font color.
      """
      return self.getColor()

   def setForegroundColor(self, color):
      """
      Sets the label's font color.
      If no color is provided, a color selection box will appear.
      """
      self.setColor(color)

   def getBackgroundColor(self):
      """
      Returns the label's background color.
      """
      r, g, b, a = self._backgroundColor
      return Color(r, g, b, a)

   def setBackgroundColor(self, color):
      """
      Sets the label's background color.
      If no color is provided, a color selection box will appear.
      """
      if color is None:  # choose a color
         pass  # TODO: add color selection box

      r, g, b, a = color.getRGBA()
      self._backgroundColor = [r, g, b, a]
      qColor = _QtGui.QColor(r, g, b, a)
      self._qBackgroundObject.setBrush(qColor)

   def getAlignment(self):
      """
      Returns the label's horizontal alignment.
      """
      return self._alignment

   def setAlignment(self, alignment):
      """
      Sets the label's horizontal alignment.
      """
      self._alignment = alignment
      document        = self._qTextObject.document()  # extract internal document
      textOption      = document.defaultTextOption()  # extract text formatting
      textOption.setAlignment(alignment)              # adjust alignment
      document.setDefaultTextOption(textOption)       # apply formatting changes

   def getFont(self):
      """
      Returns the label's font.
      """
      name, style, size = self._font
      return Font(name, style, size)

   def setFont(self, font):
      """
      Sets the label's font.
      """
      if not isinstance(font, Font):  # do some basic error checking
         print(f'{type(self).__name__}.setFont(): font should be a Font object (it was {type(font).__name__})')
      else:
         name  = font.getName()
         style = font.getStyle()
         size  = font.getFontSize()
         self._font = [name, style, size]

         qFont = font._getQFont()
         self._qTextObject.setFont(qFont)


#######################################################################################
# Music Controls
#######################################################################################
class HFader(MusicControl):
   """
   Horizontal fader (slider) control.
   """
   def __init__(self, x1, y1, x2, y2, minValue=0, maxValue=999, startValue=None,
                updateFunction=None, foreground=Color.RED, background=Color.BLACK,
                outline=Color.BLACK, thickness=3, rotation=0):
      """
      Creates a horizontal fader with corners at (x1, y1) to (x2, y2).
      """
      MusicControl.__init__(self, updateFunction)

      # calculate dimensions
      cornerX = min(x1, x2)
      cornerY = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)

      # initialize internal shapes
      self._backgroundShape = Rectangle(
         0, 0, width, height,
         color=background,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._foregroundShape = Rectangle(
         0, 0, width, height,
         color=foreground,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._outlineShape = Rectangle(
         0, 0, width, height,
         color=outline,
         fill=False,
         thickness=thickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting values
      self.setPosition(cornerX, cornerY)
      self.setRotation(rotation)

      if startValue is None:
         startValue = (minValue + maxValue) / 2

      self._minValue = minValue
      self._maxValue = maxValue
      self.setValue(startValue)

   def __str__(self):
      x1, y1          = self._backgroundShape._getGlobalCornerPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'HFader(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, updateFunction = {self._function}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation})'

   # OVERRIDDEN METHODS
   def _receiveEvent(self, event):
      """
      Receives a dispatched Event, triggers any registered callbacks, and updates the control.
      """
      # first, look for user event handlers
      MusicControl._receiveEvent(self, event)

      # then, regardless of whether the event was handled, add fader behavior
      if event.type in ["mouseDown", "mouseDrag"]:
         # update fader value based on mouse position (args = [x, y])
         ex = event.args[0]                 # global event position
         fx = self._backgroundShape.getX()  # fader position
         x  = ex - fx                       # local event position

         valueRatio = x / self._backgroundShape.getWidth()   # (0.0 - 1.0)
         valueRatio = max(0.0, min(1.0, valueRatio))         # clamp ratio
         valueRange = self._maxValue - self._minValue        # possible values
         value = self._minValue + (valueRatio * valueRange)  # scale to range
         self.setValue(value)                                # set value
         event.handled = True                                # report event handled

   def _updateAppearance(self):
      """
      Redraws the control based on its current value.
      """
      valueRatio = (self._value - self._minValue) / (self._maxValue - self._minValue)  # (0.0 - 1.0)
      width, height = self._backgroundShape.getSize()
      x,     y      = self._backgroundShape._getGlobalCornerPosition()
      padding       = self._outlineShape.getThickness() / 2

      fWidth  = (width  - (2 * padding))  # find maximum fader bar dimensions
      fHeight = (height - (2 * padding))  # ...
      fx      = x + padding               # ...
      fy      = y + padding               # ...
      fWidth  = fWidth * valueRatio       # scale to value

      self._foregroundShape.setPosition(fx, fy)
      self._foregroundShape.setSize(fWidth, fHeight)

   def setValue(self, value):
      """
      Sets the control's current value, and updates its appearance.
      """
      value = max(self._minValue, min(self._maxValue, value))  # clamp value
      MusicControl.setValue(self, value)  # update value and call user function


class VFader(HFader):
   """
   Vertical fader (slider) control.
   """
   def __init__(self, x1, y1, x2, y2, minValue=0, maxValue=999, startValue=None,
               updateFunction=None, foreground=Color.RED, background=Color.BLACK,
               outline=Color.BLACK, thickness=3, rotation=0):
      """
      Creates a vertical fader with corners at (x1, y1) to (x2, y2).
      """
      HFader.__init__(self, x1, y1, x2, y2, minValue, maxValue, startValue,
                      updateFunction, foreground, background,
                      outline, thickness, rotation)

   def __str__(self):
      x1, y1          = self._backgroundShape._getGlobalCornerPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'VFader(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, updateFunction = {self._function}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation})'

   # OVERRIDDEN METHODS
   def _receiveEvent(self, event):
      """
      Receives a dispatched Event, triggers any registered callbacks, and updates the control.
      """
      # first, look for user event handlers
      MusicControl._receiveEvent(self, event)

      # then, regardless of whether the event was handled, add fader behavior
      if event.type in ["mouseDown", "mouseDrag"]:
         # update fader value based on mouse position (args = [x, y])
         ey = event.args[1]                 # global event position
         fy = self._backgroundShape.getY()  # fader position
         y  = ey - fy                       # local event position

         valueRatio = 1 - (y / self._backgroundShape.getHeight())  # (0.0 - 1.0)
         valueRatio = max(0.0, min(1.0, valueRatio))               # clamp ratio
         valueRange = self._maxValue - self._minValue              # possible values
         value = self._minValue + (valueRatio * valueRange)        # scale to range
         self.setValue(value)                                      # set value
         event.handled = True                                   # report event handled

   def _updateAppearance(self):
      """
      Redraws the control based on its current value.
      """
      valueRatio = (self._value - self._minValue) / (self._maxValue - self._minValue)  # (0.0 - 1.0)
      width, height = self._backgroundShape.getSize()
      x,     y      = self._backgroundShape._getGlobalCornerPosition()
      padding       = self._outlineShape.getThickness() / 2

      fWidth  = (width  - (2 * padding))  # find maximum fader bar dimensions
      fHeight = (height - (2 * padding))  # ...
      fx      = x + padding               # ...
      fy      = y + padding               # ...
      # As the ratio decreases, the fader bar's height decreases,
      # while its y position increases downward, giving the illusion
      # of shrinking.  We do a little algebra to offset y appropriately.
      fy      = fy + (fHeight * (1 - valueRatio))
      fHeight = fHeight * valueRatio

      self._foregroundShape.setPosition(fx, fy)
      self._foregroundShape.setSize(fWidth, fHeight)

   def setValue(self, value):
      """
      Sets the control's current value, and updates its appearance.
      """
      value = max(self._minValue, min(self._maxValue, value))  # clamp value
      MusicControl.setValue(self, value)  # update value and call user function


class Rotary(MusicControl):
   """
   Rotary knob control.
   """
   def __init__(self, x1, y1, x2, y2, minValue=0, maxValue=999, startValue=None,
               updateFunction=None, foreground=Color.RED, background=Color.BLACK,
               outline=Color.BLUE, thickness=3, arcWidth=300, rotation=0):
      """
      Creates a rotary knob with corners at (x1, y1) to (x2, y2).
      """
      MusicControl.__init__(self, updateFunction)

      # calculate dimensions
      cornerX    = min(x1, x2)
      cornerY    = min(y1, y2)
      width      = abs(x1 - x2)
      height     = abs(y1 - y2)
      startAngle = 90 + arcWidth//2
      endAngle   = startAngle + arcWidth

      # initialize internal shapes
      self._backgroundShape = Arc(
         0, 0, width, height,
         startAngle, endAngle,
         style=PIE,
         color=background,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._foregroundShape = Arc(
         0, 0, width, height,
         startAngle, endAngle,
         style=PIE,
         color=foreground,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._outlineShape = Arc(
         0, 0, width, height,
         startAngle, endAngle,
         style=PIE,
         color=outline,
         fill=False,
         thickness=thickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting values
      self.setPosition(cornerX, cornerY)
      self.setRotation(rotation)

      if startValue is None:
         startValue = (minValue + maxValue) / 2

      self._minValue = minValue
      self._maxValue = maxValue
      self._arcWidth = arcWidth
      self.setValue(startValue)

   def __str__(self):
      x1, y1          = self._backgroundShape._getGlobalCornerPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'Rotary(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, minValue = {self._minValue}, maxValue = {self._maxValue}, startValue = {self.getValue()}, updateFunction = {self._function}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, arcWidth = {self._arcWidth}, rotation = {rotation})'

   # OVERRIDDEN METHODS
   def _receiveEvent(self, event):
      """
      Receives a dispatched Event, triggers any registered callbacks, and updates the control.
      """
      # first, look for user event handlers
      MusicControl._receiveEvent(self, event)

      # then, regardless of whether the event was handled, add rotary behavior
      if event.type in ["mouseDown", "mouseDrag"]:
         # update rotary value based on mouse position (args = [x, y])
         ex, ey = event.args                                  # global event position
         rx, ry = self._backgroundShape.getPosition()         # global rotary position
         x = ex - rx                                          # local event position
         y = ey - ry                                          # ...

         width, height = self._backgroundShape.getSize()
         cx = width / 2                                       # local rotary center
         cy = height / 2                                      # ...
         dx = x - cx                                          # vector to event pos
         dy = cy - y                                          # ...
         mouseAngle = np.degrees(np.arctan2(dy, dx)) % 360    # angle (in degrees)
         startAngle = 90 + self._arcWidth/2                   # rotary start
         eventWidth = (startAngle - mouseAngle) % 360         # from start to mouse

         if 0 <= eventWidth <= self._arcWidth:  # skip if width outside of arc
            valueRatio = eventWidth / self._arcWidth          # (0.0 - 1.0)
            valueRatio = max(0.0, min(1.0, valueRatio))       # clamp ratio
            valueRange = self._maxValue - self._minValue      # possible values
            value = self._minValue + (valueRatio * valueRange)  # scale to range
            self.setValue(value)                              # set value
            event.handled = True                              # report event handled

   def _updateAppearance(self):
      """
      Redraws the control based on its current value.
      """
      # Since Arc can't change its angle, we need to rebuild the Arc.
      # We could create a new Arc object, but we want to be a little more
      # memory efficient... so we update QObject directly.
      valueRatio    = (self._value - self._minValue) / (self._maxValue - self._minValue)  # 0.0 to 1.0
      width, height = self._backgroundShape.getSize()
      startAngle    = self._backgroundShape._startAngle
      arcWidth      = self._arcWidth * valueRatio             # scale to value

      path = _QtGui.QPainterPath()                            # create new path
      path.arcMoveTo(0, 0, width, height, startAngle)         # first point
      path.arcTo(0, 0, width, height, startAngle, -arcWidth)  # arc to end point
      path.lineTo(width/2, height/2)                          # line to center
      path.closeSubpath()                                     # back to start
      self._foregroundShape._qObject.setPath(path)            # set new arc path

   def setValue(self, value):
      """
      Sets the control's current value, and updates its appearance.
      """
      value = max(self._minValue, min(self._maxValue, value))  # clamp value
      MusicControl.setValue(self, value)  # update value and call user function


class Push(MusicControl):
   """
   Push button that resets when released.
   """
   def __init__(self, x1, y1, x2, y2, updateFunction=None, foreground=Color.RED, background=Color.BLACK, outline=Color.CLEAR, thickness=3, rotation=0):
      """
      Creates a push button with corners at (x1, y1) to (x2, y2).
      """
      MusicControl.__init__(self, updateFunction)

      # calculate dimensions
      cornerX = min(x1, x2)
      cornerY = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)
      padding = thickness//2 + 1

      # initialize internal shapes
      self._backgroundShape = Rectangle(
         0, 0, width, height,
         color=background,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._foregroundShape = Rectangle(
         padding, padding, (width - padding), (height - padding),
         color=foreground,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._outlineShape = Rectangle(
         0, 0, width, height,
         color=outline,
         fill=False,
         thickness=thickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting values
      self.setPosition(cornerX, cornerY)
      self.setRotation(rotation)
      self.setValue(False)

   def __str__(self):
      x1, y1          = self._backgroundShape._getGlobalCornerPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'Push(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, updateFunction = {self._function}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation})'

   # OVERRIDDEN METHODS
   def _receiveEvent(self, event):
      """
      Receives a dispatched Event, triggers any registered callbacks, and updates the control.
      """
      # first, look for user event handlers
      MusicControl._receiveEvent(self, event)

      # then, regardless of whether the event was handled, add push button behavior
      if event.type in ["mouseDown"]:
         self.setValue(True)
         event.handled = True

      elif event.type in ["mouseUp", "mouseExit"]:
         self.setValue(False)
         event.handled = True

   def _updateAppearance(self):
      """
      Redraws the control based on its current value.
      """
      if self._value:
         self._foregroundShape._qObject.show()
      else:
         self._foregroundShape._qObject.hide()


class Toggle(Push):
   """
   Rectangular on/off button.
   """
   def __init__(self, x1, y1, x2, y2, updateFunction=None, foreground=Color.RED, background=Color.BLACK, outline=Color.CLEAR, thickness=3, rotation=0):
      """
      Creates a toggle button with corners at (x1, y1) to (x2, y2).
      """
      Push.__init__(self, x1, y1, x2, y2, updateFunction, foreground, background, outline, thickness, rotation)

   def __str__(self):
      x1, y1          = self._backgroundShape._getGlobalCornerPosition()
      width, height   = self._backgroundShape.getSize()
      x2              = x1 + width
      y2              = y1 + height
      foregroundColor = self._foregroundShape.getColor()
      backgroundColor = self._backgroundShape.getColor()
      outlineColor    = self._outlineShape.getColor()
      thickness       = self._outlineShape.getThickness()
      rotation        = self.getRotation()
      return f'Toggle(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, updateFunction = {self._function}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, thickness = {thickness}, rotation = {rotation})'

   # OVERRIDDEN METHODS
   def _receiveEvent(self, event):
      """
      Receives a dispatched Event, triggers any registered callbacks, and updates the control.
      """
      # first, look for user event handlers
      MusicControl._receiveEvent(self, event)

      # then, regardless of whether the event was handled, add toggle button behavior
      if event.type in ["mouseDown"]:
         self.setValue(not self._value)
         event.handled = True


class XYPad(MusicControl):
   """
   2-Dimensional control that reports (x, y) values.
   """
   def __init__(self, x1, y1, x2, y2, updateFunction=None, foreground=Color.RED, background=Color.BLACK, outline=Color.CLEAR, outlineThickness=2, trackerRadius=10, crosshairsThickness=None, rotation=0):
      """
      Creates an XYPad with corners at (x1, y1) to (x2, y2).
      """
      MusicControl.__init__(self, updateFunction)

      # calculate dimensions
      cornerX = min(x1, x2)
      cornerY = min(y1, y2)
      width   = abs(x1 - x2)
      height  = abs(y1 - y2)

      if crosshairsThickness is None:
         crosshairsThickness = outlineThickness

      # initialize internal shapes
      self._backgroundShape = Rectangle(
         0, 0, width, height,
         color=background,
         fill=True,
         thickness=0,
         rotation=0
      )
      self._trackerXLine = Line(
         0, 0, 0, height,  # vertical line
         color=foreground,
         thickness=crosshairsThickness,
         rotation=0
      )
      self._trackerYLine = Line(
         0, 0, width, 0,  # horizontal line
         color=foreground,
         thickness=crosshairsThickness,
         rotation=0
      )
      self._foregroundShape = Circle(
         width/2, height/2,
         trackerRadius,
         color=foreground,
         fill=False,
         thickness=crosshairsThickness,
         rotation=0
      )
      self._outlineShape = Rectangle(
         0, 0, width, height,
         color=outline,
         fill=False,
         thickness=outlineThickness,
         rotation=0
      )

      self.add(self._backgroundShape)
      self.add(self._trackerXLine)
      self.add(self._trackerYLine)
      self.add(self._foregroundShape)
      self.add(self._outlineShape)

      # set starting values
      self.setPosition(cornerX, cornerY)
      self.setRotation(rotation)
      self.setValue(width/2, height/2)

   def __str__(self):
      x1, y1              = self._backgroundShape._getGlobalCornerPosition()
      width, height       = self._backgroundShape.getSize()
      x2                  = x1 + width
      y2                  = y1 + height
      foregroundColor     = self._foregroundShape.getColor()
      backgroundColor     = self._backgroundShape.getColor()
      outlineColor        = self._outlineShape.getColor()
      outlineThickness    = self._outlineShape.getThickness()
      trackerRadius       = self._foregroundShape.getRadius()
      crosshairsThickness = self._foregroundShape.getThickness()
      rotation            = self.getRotation()

      return f'XYPad(x1 = {x1}, y1 = {y1}, x2 = {x2}, y2 = {y2}, updateFunction = {self._function}, foreground = {foregroundColor}, background = {backgroundColor}, outline = {outlineColor}, outlineThickness = {outlineThickness}, trackerRadius = {trackerRadius}, crosshairsThickness = {crosshairsThickness}, rotation = {rotation})'

   # OVERRIDDEN METHODS
   def _receiveEvent(self, event):
      """
      Inject XYPad-specific events to the event handler.
      """
      # first, look for user event handlers
      MusicControl._receiveEvent(self, event)

      # then, regardless of whether the event was handled, add XYPad behavior
      if event.type in ["mouseDown", "mouseDrag"]:
         ex, ey = event.args                           # global event location
         mx, my = self._backgroundShape.getPosition()  # global XYPad position
         x = ex - mx                                   # local event position
         y = ey - my                                   # ...

         self.setValue(x, y)                           # set value
         event.handled = True                          # report event handled

   def _updateAppearance(self):
      """
      Redraws the control based on its current value.
      """
      vx, vy = self._value                          # local value position
      mx, my = self._backgroundShape.getPosition()  # global XYPad position
      x = mx + vx                                   # global value position
      y = my + vy                                   # ...

      self._trackerXLine.setX(x)
      self._trackerYLine.setY(y)
      self._foregroundShape.setPosition(x, y)

   def setValue(self, x, y):
      """
      Sets the control's current value, and updates its appearance.
      """
      width, height = self._backgroundShape.getSize()
      x = max(0, min(x, width))            # clamp values
      y = max(0, min(y, height))           # ...
      MusicControl.setValue(self, [x, y])  # update value and call user function


#######################################################################################
# Controls (Event behavior defined by Qt)
#######################################################################################
class Button(Control):
   """
   Clickable push button.
   """
   def __init__(self, text="", function=None):
      """
      Creates an interactive push button with optional text label.
      """
      Control.__init__(self)

      # initialize internal shape
      self._qObject = _QtWidgets.QPushButton()
      self._qObject.clicked.connect(function)
      self._function = function

      self.setText(text)
      self.setColor(Color.LIGHT_GRAY)

   def __str__(self):
      return f'Button(text = "{self.getText()}", function = {self._function})'

   def setColor(self, color=None):
      """
      Sets the button's color.
      """
      if color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         color = Color(r, g, b)

      elif not isinstance(color, Color):
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._qObject.setStyleSheet(
         f"""
         QPushButton {{
            background-color: {color.getHex()};
            color: black;
         }}
         QPushButton::pressed {{
            background-color: {color.darker().getHex()};
         }}
         """)

   def getText(self):
      """
      Returns the button's text.
      """
      return self._qObject.text()

   def setText(self, text):
      """
      Sets the button's text.
      """
      self._qObject.setText(text)
      self._qObject.adjustSize()   # resize to text - if setSize was set, this is ignored
      self._width  = self._qObject.width()
      self._height = self._qObject.height()


class CheckBox(Control):
   """
   Checkbox with checked/unchecked state.
   """
   def __init__(self, text="", function=None):
      """
      Creates an interactive checkbox with optional text label.
      """
      Control.__init__(self)

      self._qObject = _QtWidgets.QCheckBox(text)
      self._qObject.stateChanged.connect(function)
      self._function = function
      self.setText(text)
      self.setColor(Color.CLEAR)

   def __str__(self):
      return f'CheckBox(text = "{self.getText()}", function = {self._function})'

   def setColor(self, color=None):
      """
      Sets the checkbox's background color.
      """
      if color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         color = Color(r, g, b)

      elif not isinstance(color, Color):
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._qObject.setStyleSheet(
         f"""
         QCheckBox {{
            background-color: {color.getHex()};
            color: black;
         }}
         """)

   def getText(self):
      """
      Returns the checkbox label's text.
      """
      return self._qObject.text()

   def setText(self, text):
      """
      Sets the checkbox label's text.
      """
      self._qObject.setText(text)
      self._qObject.adjustSize()   # resize to text - if setSize was set, this is ignored
      self._width  = self._qObject.width()
      self._height = self._qObject.height()

   def isChecked(self):
      """
      Returns True if checked.
      """
      return self._qObject.isChecked()

   def check(self):
      """
      Sets the checkbox to checked.
      """
      self._qObject.setChecked(True)

   def uncheck(self):
      """
      Sets the checkbox to unchecked.
      """
      self._qObject.setChecked(False)


class Slider(Control):
   """
   Slider control for numeric values.
   """
   def __init__(self, orientation=HORIZONTAL, lower=0, upper=100, start=None, function=None):
      """
      Creates an interactive slider.
      """
      Control.__init__(self)

      if start is None:
         start = int((lower + upper) / 2)

      # initialize internal shape
      self._qObject = _QtWidgets.QSlider(orientation)
      self._qObject.valueChanged.connect(function)
      self._qObject.setRange(lower, upper)
      self._qObject.setValue(start)
      self._qObject.adjustSize()
      self._function    = function
      self._orientation = orientation
      self._lower       = lower
      self._upper       = upper
      # self.setColor(Color.BLACK)

   def __str__(self):
      return f'Slider(orientation = {self._orientation}, lower = {self._lower}, upper = {self._upper}, start = {self.getValue()}, function = {self._function})'

   def setColor(self, color=None):
      """
      Sets the slider's color.
      """
      if color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         color = Color(r, g, b)

      elif not isinstance(color, Color):
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      ## TODO: set color of slider - which part??
      print(f"{type(self).__name__}.setColor(): setColor not yet implemented.")

   def getValue(self):
      """
      Returns the slider's current value.
      """
      return self._qObject.value()

   def setValue(self, value):
      """
      Sets the slider's current value.
      """
      self._qObject.setValue(value)


class DropDownList(Control):
   """
   Drop-down selection list.
   """
   def __init__(self, items=[], function=None):
      """
      Creates an interactive drop-down list with given items.
      """
      Control.__init__(self)

      self._qObject = _QtWidgets.QComboBox()
      self._qObject.addItems(items)
      self._qObject.activated.connect(self._callback)

      self._qObject.adjustSize()  # adjust size to fit text
      self._width    = self._qObject.width()
      self._height   = self._qObject.height()
      self._items    = items
      self._function = function
      self.setColor(Color.LIGHT_GRAY)  # set default color

   def __str__(self):
      return f'DropDownList(items = {self._items}, function = {self._function})'

   def _callback(self, index):
      """
      Calls user function using item at given index.
      """
      if self._function is not None and callable(self._function):
         self._function(self._items[index])  # call function with selected item

   def setColor(self, color=None):
      """
      Set the dropdown's background color.
      """
      if color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         color = Color(r, g, b)

      elif not isinstance(color, Color):
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._qObject.setStyleSheet(
         f"""
         QComboBox {{
            background-color: {color.getHex()};
            color: black;
         }}
         QComboBox QAbstractItemView {{
            background-color: {color.getHex()};
            color: black;
         }}
         """)


class TextField(Control):
   """
   Single-line editable text field.
   """
   def __init__(self, text="", columns=8, function=None):
      """
      Creates a single-line text field with optional starting text.
      """
      Control.__init__(self)

      self._qObject = _QtWidgets.QLineEdit(str(text))
      self._qObject.returnPressed.connect(self._callback)
      self._columns  = columns
      self._function = function

      # calculate width and height, based on default font and
      # system-specific margins and framing
      fontMetrics = self._qObject.fontMetrics()
      charWidth   = fontMetrics.horizontalAdvance('M')
      charHeight  = fontMetrics.lineSpacing()
      margins     = self._qObject.textMargins()

      frameOption = _QtWidgets.QStyleOptionFrame()  # grab and set system text box frame
      self._qObject.initStyleOption(frameOption)
      frame       = self._qObject.style().pixelMetric(
         _QtWidgets.QStyle.PixelMetric.PM_DefaultFrameWidth, frameOption, self._qObject
      )

      horizontalMargins = margins.left() + margins.right()
      verticalMargins   = margins.top() + margins.bottom()

      width  = (charWidth * columns) + horizontalMargins + (2 * frame)
      height = (charHeight) + verticalMargins + (2 * frame)

      self.setSize(width, height)
      self.setColor(Color.WHITE)

   def __str__(self):
      return f'TextField(text = "{self.getText()}", columns = {self._columns}, function = {self._function})'

   def _callback(self):
      """
      Calls user function using current text.
      """
      if self._function is not None and callable(self._function):
         self._function(self._qObject.text())  # call function with text in field

   def setColor(self, color=None):
      """
      Sets the text field's background color.
      """
      if color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         color = Color(r, g, b)

      elif not isinstance(color, Color):
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._qObject.setStyleSheet(
         f"""
         QLineEdit {{
            background-color: {color.getHex()};
            color: black;
         }}
         """)

   def getText(self):
      """
      Returns the current text.
      """
      return self._qObject.text()

   def setText(self, text):
      """
      Sets the current text.
      """
      self._qObject.setText(text)

   def setFont(self, font, resize=True):
      """
      Sets the text field's font and automatically resizes to match.
      Set 'resize' to False to keep current dimensions.
      """
      if not isinstance(font, Font):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.setFont(): font should be a Font object (it was {type(font).__name__})')

      qFont = font._getQFont()
      self._qObject.setFont(qFont)

      if resize:
         fontMetrics = _QtGui.QFontMetrics(qFont)  # get font information
         charWidth   = fontMetrics.horizontalAdvance('M')
         charHeight  = fontMetrics.lineSpacing()
         margins     = self._qObject.textMargins()

         frameOption = _QtWidgets.QStyleOptionFrame()  # grab and set system text box frame
         self._qObject.initStyleOption(frameOption)
         frame = self._qObject.style().pixelMetric(
            _QtWidgets.QStyle.PixelMetric.PM_DefaultFrameWidth, frameOption, self._qObject
         )

         horizontalMargins = margins.left() + margins.right()
         verticalMargins   = margins.top()  + margins.bottom()

         width  = (charWidth)  + horizontalMargins + (2 * frame)
         height = (charHeight) + verticalMargins   + (2 * frame)
         self.setSize(width, height)


class TextArea(Control):
   """
   Multi-line editable text field.
   """
   def __init__(self, text="", columns=8, rows=5):
      """
      Creates a multi-line text field with optional starting text.
      """
      Control.__init__(self)

      self._qObject = _QtWidgets.QTextEdit(str(text))
      self._columns = columns
      self._rows    = rows
      self.setColor(Color.WHITE)  # set default color

   def __str__(self):
      return f'TextArea(text = "{self.getText()}", columns = {self._columns}, rows = {self._rows})'

   def setColor(self, color=None):
      """
      Sets the text area's background color.
      """
      if color is None:
         # open color selector if no value provided
         r, g, b = _selectColor()
         color = Color(r, g, b)

      elif not isinstance(color, Color):
         # throw error if wrong data type entered
         raise TypeError(f'{type(self).__name__}.setColor(): color should be a Color object (it was {type(color).__name__})')

      self._qObject.setStyleSheet(
         f"""
         QTextEdit {{
            background-color: {color.getHex()};
            color: black;
         }}
         """)

   def getText(self):
      """
      Returns the current text.
      """
      return self._qObject.toPlainText()

   def setText(self, text):
      """
      Sets the current text.
      """
      self._qObject.setText(text)

   def setFont(self, font, resize=True):
      """
      Sets the text field's font and automatically resizes to match.
      Set 'resize' to False to keep current dimensions.
      """
      if not isinstance(font, Font):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.setFont(): font should be a Font object (it was {type(font).__name__})')

      qFont = font._getQFont()
      self._qObject.setFont(qFont)

      if resize:
         fontMetrics = _QtGui.QFontMetrics(qFont)  # get font information
         charWidth   = fontMetrics.horizontalAdvance('M')
         charHeight  = fontMetrics.lineSpacing()
         margins     = self._qObject.textMargins()

         frameOption = _QtWidgets.QStyleOptionFrame()  # grab and set system text box frame
         self._qObject.initStyleOption(frameOption)
         frame = self._qObject.style().pixelMetric(
            _QtWidgets.QStyle.PixelMetric.PM_DefaultFrameWidth, frameOption, self._qObject
         )

         horizontalMargins = margins.left() + margins.right()
         verticalMargins   = margins.top()  + margins.bottom()

         width  = (charWidth)  + horizontalMargins + (2 * frame)
         height = (charHeight) + verticalMargins   + (2 * frame)
         self.setSize(width, height)


class Menu():
   """
   Pop-up or context menu containing selectable actions.
   """
   def __init__(self, menuName):
      """
      Creates a menu with given title.
      """
      self._qObject = _QtWidgets.QMenu(menuName)
      self._name = menuName

   def __str__(self):
      return f'Menu(menuName = "{self._name}")'

   def __repr__(self):
      return str(self)

   def addItem(self, item="", functionName=None):
      """
      Adds a selectable item to the menu with optional callback.
      """
      qAction = _QtGui.QAction(item, self._qObject)  # create new action
      if callable(functionName):
         qAction.triggered.connect(functionName)     # attach callback, if any
      self._qObject.addAction(qAction)               # add action to menu

   def addItemList(self, itemList=[""], functionNameList=[None]):
      """
      Adds a list of items to the menu with optional corresponding callbacks.
      """
      for i in range(len(itemList)):
         # get item and function (if available, None otherwise)
         item         = itemList[i]
         functionName = functionNameList[i] if i < len(functionNameList) else None
         self.addItem(item, functionName)

   def addSeparator(self):
      """
      Adds a separator to the menu.
      """
      separator = _QtGui.QAction(self._qObject)  # create new action
      separator.setSeparator(True)               # set action as separator
      self._qObject.addAction(separator)         # add separator to menu

   def addSubmenu(self, menu):
      """
      Adds a submenu to the menu.
      """
      if not isinstance(menu, Menu):  # do some basic error checking
         raise TypeError(f'{type(self).__name__}.addSubmenu(): menu should be a Menu object (it was {type(menu).__name__})')

      self._qObject.addMenu(menu._qObject)

   def enable(self):
      """
      Enables menu interaction.
      """
      self._qObject.setEnabled(True)

   def disable(self):
      """
      Disable menu interaction.
      """
      self._qObject.setEnabled(False)


#######################################################################################
# Animation Engine
#######################################################################################
# animate() - this is a function to register functions that should be called repeatedly.  
# Registered functions should expect zero parameters.  Also provided is setAnimationRate().  
# The idea is to provide a simple way to animate things (be it visual, or other).  
# This is basic functionality, inspired by MIT Processing's draw() function.  
# Anything more involved can be easily created using a Timer.

from timer import Timer

animationRate      = 60                     # 60 times per second
animationInterval  = 1000 / animationRate   # convert to milliseconds

if "_ANIMATIONFUNCTIONS_" not in globals():
   _ANIMATIONFUNCTIONS_ = []  # claim global variable for animation functions

def callAnimationFunctions():
   """When timer goes off, we call this function, which calls all functions added to the animation list."""
   global _ANIMATIONFUNCTIONS_

   # call every function in animationFunctions list
   for function in _ANIMATIONFUNCTIONS_:
      function()   

# animation engine is just a timer
animationEngine = Timer(
   timeInterval=animationInterval,
   function=callAnimationFunctions,
   parameters=[],
   repeat=True
)

animationEngine.start()  # start it


def animate(function):
   """Adds a function to be called repeatedly by the animation engine."""
   global animationEngine

   if callable(function):
      _ANIMATIONFUNCTIONS_.append(function)  # add function to list of functions to call
   else:
      print(f"animate(): function '{function}' is not callable.")


def setAnimationRate(frameRate=60):
   """Set animation frame rate (frames per second)."""
   global animationEngine

   animationInterval  = 1000 / frameRate         # convert to milliseconds
   animationEngine.setDelay(animationInterval)   # and set it


def getAnimationRate():
   """Returns animation frame rate (frames per second)."""
   global animationEngine

   animationInterval = animationEngine.getDelay()   # get delay in milliseconds
   animationRate     = 1000 / animationInterval     # convert to times per second (rate)
   return animationRate


def __stopAnimationEngine__():
   """Function to stop and clean-up animation engine."""
   global animationEngine

   animationEngine.stop()  # first, stop it
   del animationEngine     # then, delete it 

# # now, register function with JEM (if possible)
# try:
#     # if we are inside JEM, registerStopFunction() will be available
#     registerStopFunction(__stopAnimationEngine__)   # tell JEM which function to call when the Stop button is pressed

# except:  # otherwise (if we get an error), we are NOT inside JEM 
#     pass    # so, do nothing.



#######################################################################################
# Test
#######################################################################################

if __name__ == "__main__":
   pass
