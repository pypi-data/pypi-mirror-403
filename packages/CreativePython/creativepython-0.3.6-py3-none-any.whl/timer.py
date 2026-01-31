###############################################################################
# timer.py       Version 1.0     20-Aug-2025
# Trevor Ritchie, Taj Ballinger, Drew Smuniewski, and Bill Manaris
#
###############################################################################
#
# [LICENSING GOES HERE]
#
###############################################################################
#
# Timer class for scheduling tasks to run or repeat at fixed time intervals.
#
# REVISIONS:
#
#
# TODO:
#  -
#
###############################################################################

# Timer (uses Qt's timer, intended for endusers to avoid gui conflicts)
from PySide6.QtWidgets import QApplication
from PySide6.QtCore    import QTimer
from PySide6 import QtCore as _QtCore

# Timer2 (a custom implementation, used internally)
import threading
import time
import atexit

##############################################################################
# ensure a QApplication exists (needed for QTimer in Timer class)
if "_QTAPP_" not in globals():
   _QTAPP_ = None  # claim global variable for QApplication

def _ensureApp():
   """Guarantee that a QApplication is running."""
   # this function is called whenever we create a new display,
   # or queue a function that modifies the display (or the display's items)
   global _QTAPP_
   if _QTAPP_ is None:
      # try to find an existing QApplication instance
      _QTAPP_ = QApplication.instance()
      if _QTAPP_ is None:
         # if no existing QApplication, create a new instance
         _QTAPP_ = QApplication([])
         _QTAPP_.setApplicationName("CreativePython")
         _QTAPP_.setStyleSheet(  # force ToolTip font color to black
            """
            QToolTip {
               color: black;
            }
            """)

_ensureApp()


###############################################################################
# Timer
#
# Class for creating a timer (for use to schedule tasks to be executed after
# a given time interval, repeatedly or once).
# Extends Java's Swing Timer.
#
# Methods:
#
# Timer( timeInterval, function, parameters, repeat)
#  Creates a new Timer to call 'function' with 'parameters', after 'timeInterval'
#  If 'repeat' is True this will go on indefinitely (default); False means once.
#
# start()
#   Starts the timer.
#
# stop()
#   Stops the timer.
#
# isRunning()
#   Returns True if timer is running; False otherwise.
#
# stop()
#   Stops the timer.
#
# setRepeats( flag )
#   Sets the repeat attribute of the timer (True means repeat; False means once).
###############################################################################

class Timer():
   """Timer used to schedule tasks to be run at fixed time intervals."""

   def __init__ (self, timeInterval, function, parameters=[], repeat=True):
      """Specify time interval (in milliseconds), which function to call when the time interval has passed
         and the parameters to pass this function, and whether to repeat (True) or do it only once."""
      # create an internal QTimer
      self._timer = QTimer()                                        # default QTimer() is a CoarseTimer
      self._timer.setTimerType(_QtCore.Qt.TimerType.PreciseTimer)   # use PreciseTimer for smoother animations

      self.parameters = parameters

      self.setDelay(timeInterval)               # how often should the timer trigger?
      self.setRepeat(repeat)                    # should we do this once or forever?
      self.setFunction(function, parameters)    # register callback function

      self._timer.timeout.connect(self._run)    # connect QTimer timeout signal to our internal run method

      # _timers.append(self)   # add this timer instance to the global timers list

   def __str__(self):
      """Return a string representation of the timer."""
      return f"Timer(timeInterval = {self.getDelay()}, function = {self._function}, parameters = {self.parameters}, repeat = {self.getRepeat()})"

   def __repr__(self):
      """Return the string representation for repr."""
      return str(self)

   def _run(self):
      """Call the user-supplied function with parameters."""
      self._function(*self._parameters)   # call the user-supplied function with parameters

   def start(self):
      """Start the Timer."""
      self._timer.start()   # start the QTimer

   def stop(self):
      """Stop the Timer."""
      self._timer.stop()   # stop the QTimer

   def getDelay(self):
      """Return the timer interval in milliseconds."""
      return self._timer.interval()   # return the timer interval in milliseconds

   def setDelay(self, timeInterval):
      """Set the timer interval."""
      self._timer.setInterval(int(timeInterval))   # set timer interval

      if self.isRunning():
         self._timer.start()   # restart timer if it is already running

   def isRunning(self):
      """Check if the timer is currently active."""
      return self._timer.isActive()   # check if timer is currently active

   def setFunction(self, function, parameters=[]):
      """Set the callback function and its parameters."""
      self._function   = function     # set callback function
      self._parameters = parameters   # set parameters for the callback

   def getRepeat(self):
      """Return true if timer is set to repeat."""
      repeat = not self._timer.isSingleShot()
      return repeat

   def setRepeat(self, repeat):
      """Set the timer to repeat (True) or run once (False)."""
      # set timer to single shot if repeat is false
      singleShot = not repeat
      self._timer.setSingleShot(singleShot)


############### Timer2 ########################################################
# To work around the limitation that we can't easily schedule callbacks
# at specific times, we create a ticker thread that wakes up at
# short intervals to check if any timers need to be triggered.
#
# ACCURACY ADVANTAGES:
# 1. Running in a separate thread means timing isn't affected by operations
#    in the main thread.
# 2. Measuring actual elapsed time (dt) compensates for any processing delays
# 3. Accumulating precise time values prevents long-term drift
#
# Timers are added to _activeTimers when they start, and removed when they stop
# or, if they are oneshots, when they call their callback function.
###############################################################################

class Timer2:
   """Custom timer used to schedule tasks to be run at fixed time intervals."""

   def __init__(self, timeInterval, function, parameters=[], repeat=True):
      """Specify time interval (in milliseconds), which function to call when the time interval has passed
         and the parameters to pass this function, and whether to repeat (True) or do it only once."""
      self._interval = timeInterval / 1000.0   # convert ms to seconds to work with Python's Time module
      self._function = function                # callback function to execute
      self._parameters = parameters            # parameters to pass to the callback function
      self._repeat = repeat                    # whether to repeat the timer or run once
      self._scheduled = False                  # flag indicating if timer is scheduled
      self._accumulatedTime = 0                # tracks elapsed time since last execution
      self._running = False                    # flag indicating if timer is currently running

   def __str__(self):
      return f"Timer(timeInterval = {self.getDelay()}, function = {self._function}, parameters = {self._parameters}, repeat = {self.getRepeat()})"

   def __repr__(self):
      return str(self)

   def _tick(self, dt):
      """Internal method called by the ticker thread to update timer state."""
      if not self._running:
         return

      # accumulate the actual elapsed time with high precision
      self._accumulatedTime += dt

      # check if it's time to run the callback
      if self._accumulatedTime >= self._interval:
         # call the function
         self._function(*self._parameters)

         # reset accumulated time, accounting for overshooting
         if self._repeat:
            # DRIFT PREVENTION: subtract exactly one interval, preserving any excess time
            # this is critical for preventing long-term drift in repeated timers
            self._accumulatedTime -= self._interval
         else:
            # for one-shot timers, remove from active timers
            self.stop()

   def start(self):
      """Creates a timer task to perform the desired task as specified (in terms of timeInterval and repeat)."""
      # check if timer is not already running
      if not self._running:
         self._running = True         # set running flag to true
         self._accumulatedTime = 0    # reset accumulated time
         _activeTimers.append(self)   # add this timer to the active timers list

   def stop(self):
      """Stops scheduled task from executing."""
      # check if timer is currently running
      if self._running:
         self._running = False         # set running flag to false

         # remove this timer from the active timers list if it exists
         if self in _activeTimers:
            _activeTimers.remove(self)

   def getDelay(self):
      """Returns the delay time interval (in milliseconds)."""
      return self._interval * 1000   # convert back to ms for API consistency

   def setDelay(self, timeInterval):
      """
      Sets a new delay time interval for timer t (in milliseconds).
         This allows to change the speed of the animation, after some event occurs..
      """
      self._interval = timeInterval / 1000.0

      # if running, restart with new interval
      if self.isRunning():
         self.stop()
         self.start()

   def isRunning(self):
      """Returns True if timer is still running, False otherwise."""
      return self._running

   def setFunction(self, function, parameters=[]):
      """
      Sets the function to execute. The optional parameter, parameters,
      is a list of parameters to pass to the function (when called).
      """
      self._function = function
      self._parameters = parameters

   def getRepeat(self):
      """Returns True if timer is set to repeat, False otherwise."""
      return self._repeat

   def setRepeat(self, repeat):
      """Timer is set to repeat if flag is True, and not to repeat if flag is False."""
      self._repeat = repeat


# global ticker thread that calls timer callbacks
def _tickerThread():
   """
   Internal function that periodically updates all active timers.

   This function runs in a separate thread and wakes up at regular intervals
   to call the _tick method of all active timers. It measures the actual time
   elapsed between calls to ensure timing accuracy.
   """

   lastTime = time.time()
   while _tickerRunning:
      currentTime = time.time()
      dt = currentTime - lastTime  # measure actual elapsed time between ticks
      lastTime = currentTime

      # call tick for all active timers with the precise time difference
      for timer in list(_activeTimers):
         timer._tick(dt)

      # sleep for a short time (adjust as needed for precision)
      time.sleep(0.01)  # 10ms resolution - balances CPU usage with timing precision


# register cleanup on exit
def _cleanup():
   """Cleans up all active timers when the program exits.

   This function is registered with atexit to ensure proper cleanup
   even if the program terminates unexpectedly.
   """
   global _tickerRunning
   _tickerRunning = False

   # stop all active timers
   for timer in list(_activeTimers):
      timer.stop()


# if this is the first time loading this module
_initialized = False
if not _initialized:
   _initialized = True
   _activeTimers = []
   _tickerRunning = True

   # allow Python to exit even if thread is running
   _ticker = threading.Thread(target=_tickerThread, daemon=True)

   # start ticker thread
   _ticker.start()

   # NOTE: We don't need a blocking thread when using python -i,
   # since the interpreter stays open already

   atexit.register(_cleanup)   # cleanup active timers at exit


#######################################################################################
# LinearRamp
#
# Creates a linear ramp that calls a function at regular intervals with interpolated values.
# - delayMs: total duration of the ramp in milliseconds
# - startValue: value at the start of the ramp
# - endValue: value at the end of the ramp
# - function: callback function to call with the current interpolated value
# - stepMs: interval between function calls in milliseconds (default: 10)
#
# The ramp will smoothly transition from startValue to endValue over delayMs milliseconds,
# calling the provided function at regular intervals with the current interpolated value.
# The function should accept a single argument representing the current ramp value.
#######################################################################################

class LinearRamp:
   """Creates a linear ramp that calls a function at regular intervals with interpolated values."""

   def __init__(self, delayMs, startValue, endValue, function, stepMs=10):
      """
      Initializes a linear ramp with the given parameters. The ramp will smoothly transition
      from startValue to endValue over delayMs milliseconds, calling the provided function at regular intervals
      (approximately stepMs milliseconds apart) with the current interpolated value.
      The function should accept a single argument representing the current ramp value.
      """
      # remember callback function and step interval
      self._function = function
      self._stepMs = self._sanitizeStep(stepMs)
      self._timer = None

      # initialize value tracking
      self._currentValue = startValue
      self._sourceValue = startValue
      self._targetValue = endValue

      # initialize timing variables
      self._delayMs = 0.0
      self._durationSeconds = 0.0
      self._ratePerSecond = 0.0

      # initialize ramp state
      self._phase = 0.0
      self._isRunning = False
      self._lastTickTime = None

      # set the ramp duration
      self._setDuration(delayMs)

      # make sure function is callable
      if not callable(function):
         print("LinearRamp: Error - function must be callable.")

   def __str__(self):
      return (f"LinearRamp(delayMs={self._delayMs}, currentValue={self._currentValue}, "
              f"targetValue={self._targetValue}, stepMs={self._stepMs})")

   def __repr__(self):
      return str(self)

   def start(self):
      """Start moving toward the current target value."""
      # make sure function is callable
      if not callable(self._function):
         print("LinearRamp: Error - callback function must be callable to start.")
         return

      # stop if already running
      if self._isRunning:
         self.stop()

      # initialize ramp from current value
      self._sourceValue = self._currentValue
      self._phase = 0.0
      self._lastTickTime = time.perf_counter()

      # notify with initial value
      self._notify()

      # handle immediate execution for zero or negative delay
      if self._delayMs <= 0:
         self._completeImmediately()
         return

      # create and start the timer
      self._ensureTimer()
      self._isRunning = True
      self._timer.start()

   def stop(self):
      """Stop the ramp and release timer resources."""
      if self._timer:   # stop the timer if it exists
         self._timer.stop()
      self._isRunning = False   # clear running flag
      self._lastTickTime = None   # reset tick time

   def setTarget(self, targetValue, delayMs=None):
      """Retarget the ramp to a new value, optionally specifying a new duration."""
      # update target value
      self._targetValue = targetValue

      # update duration if provided
      if delayMs is not None:
         self._setDuration(delayMs)

      # reset ramp to start from current value
      self._sourceValue = self._currentValue
      self._phase = 0.0
      self._lastTickTime = time.perf_counter()

      # notify with current value
      self._notify()

      # handle immediate execution for zero or negative delay
      if self._delayMs <= 0:
         self._completeImmediately()
         return

      # start the timer if not already running
      if not self._isRunning:
         self._ensureTimer()
         self._isRunning = True
         self._timer.start()

   def setDuration(self, delayMs):
      """Adjust the ramp duration without resetting current progress."""
      # update duration
      self._setDuration(delayMs)

      # handle immediate execution for zero or negative delay
      if self._delayMs <= 0:
         self._completeImmediately()
         return

      # reset tick time if running
      if self._isRunning:
         self._lastTickTime = time.perf_counter()

   def isRunning(self):
      """Return True when the ramp is actively progressing toward its target."""
      return self._isRunning

   def getCurrentValue(self):
      """Return the most recent value emitted by the ramp."""
      return self._currentValue

   def _ensureTimer(self):
      """Internal method to create or reconfigure the timer."""
      if self._timer is None:   # create new timer
         self._timer = Timer2(timeInterval=self._stepMs,
                              function=self._tick,
                              parameters=[],
                              repeat=True)
      else:   # reconfigure existing timer
         self._timer.setDelay(self._stepMs)
         self._timer.setFunction(self._tick, [])
         self._timer.setRepeat(True)

   def _tick(self):
      """Internal method called by the timer to update ramp progress."""
      if not self._isRunning:   # exit if not running
         return

      # measure elapsed time since last tick
      now = time.perf_counter()
      if self._lastTickTime is None:   # first tick, just initialize
         self._lastTickTime = now
         return

      dt = now - self._lastTickTime   # calculate time delta
      self._lastTickTime = now

      # update phase based on elapsed time
      if self._durationSeconds <= 0:
         self._phase = 1.0   # instant completion
      else:
         self._phase += dt * self._ratePerSecond   # advance phase proportionally

      # check if ramp is complete
      if self._phase >= 1.0:
         self._phase = 1.0   # clamp to 1.0
         self._currentValue = self._targetValue   # ensure exact target value
         self._notify()   # notify with final value
         self.stop()   # stop the ramp
      else:   # ramp in progress
         # calculate interpolated value
         self._currentValue = self._sourceValue + (self._phase * (self._targetValue - self._sourceValue))
         self._notify()   # notify with current value

   def _completeImmediately(self):
      """Internal method to immediately complete the ramp."""
      self._phase = 1.0   # set phase to complete
      self._currentValue = self._targetValue   # jump to target value
      self._notify()   # notify with final value
      self.stop()   # stop the ramp

   def _notify(self):
      """Internal method to call the callback function with the current value."""
      if not callable(self._function):   # skip if function is not callable
         return

      # call the callback function with error handling
      try:
         self._function(self._currentValue)
      except Exception as error:
         print(f"LinearRamp: Warning - callback raised {error}.")

   def _setDuration(self, delayMs):
      """Internal method to set the ramp duration and calculate rate."""
      # validate and convert delay to float
      try:
         delay = float(delayMs)
      except (TypeError, ValueError):
         delay = 0.0

      # ensure non-negative delay
      if delay < 0:
         delay = 0.0

      # store duration in milliseconds and seconds
      self._delayMs = delay
      self._durationSeconds = delay / 1000.0

      # calculate rate per second for phase advancement
      if self._durationSeconds <= 0:
         self._ratePerSecond = 0.0   # instant completion
      else:
         self._ratePerSecond = 1.0 / self._durationSeconds   # phase units per second

   def _sanitizeStep(self, stepMs):
      """Internal method to validate and sanitize the step interval."""
      # validate and convert step to float
      try:
         step = float(stepMs)
      except (TypeError, ValueError):
         step = 10.0   # default to 10ms if invalid

      # ensure positive step value
      if step <= 0:
         step = 10.0   # default to 10ms if non-positive

      return step


# tests
if __name__ == '__main__':
   import time
   seconds = 0
   startTime = time.time()

   def echoTime():
      global seconds
      current = seconds
      seconds += 1
      print(f"Timed Seconds: {current+1}, Actual Seconds: {time.time()-startTime:.3f}")

   # define timer to count and output elapsed time (in seconds)
   t = Timer(1000, echoTime, [], True)
   t.start()

   # test LinearRamp
   print("\n--- LinearRamp Test (0 to 10 over 2 seconds) ---")
   rampStartTime = time.time()
   def printRampValue(value):
      """Test callback to print ramp values."""
      print(f"Ramp Value: {value:.2f} at {time.time() - rampStartTime:.3f}s")

   # ramp from 0 to 10 over 2 seconds, with steps approx every 200ms
   ramp = LinearRamp(delayMs=2000, startValue=0, endValue=10, function=printRampValue, stepMs=200)
   ramp.start()
