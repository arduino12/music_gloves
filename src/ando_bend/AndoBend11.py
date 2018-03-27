import SocketServer
# not used:
# import OSC
import rtmidi
import socket
import time
import sys
import threading
import argparse
import time
import Tkinter
from time import sleep
import Tkinter as tk
import ttk
from array import *
from multiprocessing import Process, Queue

column_prnt=1

# global dilul_prnt_cntr

# global dilul_saf # = 100  # how many midi msgs to not print.
dbg_print=0
# 1 allows prints on every message - show info and slow response.


# dilul_prnt_cntr = 0
# dilul_saf  = 100
pitch_server = None
modulation_server = None
## servers = [pitch_server, modulation_server ]
## 13-4-14  12:50 ^


# MIDI device name
MIDI_LOOP_OUT = 'LoopBe Internal MIDI'

# Background path
BACKGROUND_PATH = 'C:\proj_b\AndoBend\wave.jpg'

# Gui global variable
gui = None

# Listening ports
PITCH_LISTENING_PORT = 12002
MODULATION_LISTENING_PORT = 12003 #  12002 no need disable firewall.  was =  5556 needed disable fire wall in eset setup network.
# in fire Wall eset,  f5 advanced setup, network, rules and zones, andosc rule. allow udp ports 12002 12003.

#############
## GUI ######
#############
# Pitch
glob_pitch_sent_pitch = 0             # for gui
glob_pitch_elevation_value = 0        # for gui
# the reset value of OrientationPitch of FreqPitch
glob_pitch_value_bias = 0                   # for gui
# the threshold (saf) which the OrientationPitch starts to change the FreqPitch at
glob_pitch_threshold_value = 10       # constant   to cause a pitch massage - pass the threshold filter
# the maximum FreqPitch value which the OrientationPitch can set
glob_pitch_saturation_value = 20      # constant
# complicated
glob_pitch_bias_buffer_size = 700     # constant
pitch_bias_buffer = [0] * glob_pitch_bias_buffer_size
pitch_bias_buffer_pointer = 0
# initial OrientationPitch balance value
glob_pitch_first = 1

# Modulation
glob_modulation_sent_pitch = 0             # for gui
glob_modulation_elevation_value = 0        # for gui
glob_modulation_bias = 0                   # for gui
glob_modulation_threshold_value = 10       # constant   to cause a modulation massage - pass the threshold filter
glob_modulation_saturation_value = 20      # constant
# complicated
glob_modulation_bias_buffer_size = 700     # constant
modulation_bias_buffer = [0] * glob_modulation_bias_buffer_size
modulation_bias_buffer_pointer = 0
glob_modulation_first = 1

class Gui(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        ## GUI
        ## Setting Title
## ORIG 1 SENSOR         self.geometry('300x320+0+0')
        self.geometry('300x640+0+0')   ## ROOM FOR 2  SENSORS. wanted side by side. got top bottom of form = window.
        self.title("AndoBend10")   # update here when growing number of version of program.
        background_image=tk.PhotoImage(BACKGROUND_PATH)
        background_label = tk.Label(image=background_image)
        background_label.place(x=10, y=10, relwidth=200, relheight=200)
        background_label.image = background_image
        background_label.pack()
#___ 13-4-15-17;27  start copy   from pitch  to  modulation
        self.pitch_start_button= ttk.Button(text="start_Pitch", command=self.start_Pitch)
        self.pitch_start_button.pack()
        self.pitch_stop_button = ttk.Button(text="stop_Pitch", command=self.stop_Pitch)
        self.pitch_stop_button.pack()
        self.pitch_rebalance_button = ttk.Button(text="re-balance_Pitch", command=self.rebalance_pitch)
        self.pitch_rebalance_button.pack()
# 13-4-15  17:32  to here make mod instead of pitch :

        self.modulation_start_button = ttk.Button(text="start_modulation", command=self.start_modulation)
        self.modulation_start_button.pack()
        self.modulation_stop_button = ttk.Button(text="stop_modulation", command=self.stop_modulation)
        self.modulation_stop_button.pack()
        self.modulation_rebalance_button = ttk.Button(text="re-balance_modulation", command=self.rebalance_modulation)
        self.modulation_rebalance_button.pack()

        self.scale_pitch_elevation = tk.Scale(self, from_=-90, to=90, orient="horizontal")
        self.scale_pitch_elevation.pack()
        self.label_pitch_elevation= ttk.Label(self, text="Elevation")
        self.label_pitch_elevation.pack()
        self.scale_pitch_value = tk.Scale(self, from_=0, to=16384, orient="horizontal")
        self.scale_pitch_value.pack()
        self.label_pitch_value= ttk.Label(self, text="Pitch")
        self.label_pitch_value.pack()
        self.scale_pitch_bias = tk.Scale(self, from_=-90, to=+90, orient="horizontal")
        self.scale_pitch_bias.pack()
        self.label_pitch_bias= ttk.Label(self, text="Bias")
        self.label_pitch_bias.pack()
        """
        self.scale_pitch_elevation = tk.Scale(self, from_=-90, to=90, orient="horizontal")
        self.scale_pitch_elevation.pack()
        self.label_pitch_elevation= ttk.Label(self, text="Elevation")
        self.label_pitch_elevation.pack()
        self.scale_pitch_value = tk.Scale(self, from_=0, to=16384, orient="horizontal")
        self.scale_pitch_value.pack()
        self.label_pitch_value= ttk.Label(self, text="Pitch")
        self.label_pitch_value.pack()
        self.scale_pitch_bias = tk.Scale(self, from_=-90, to=+90, orient="horizontal")
        self.scale_pitch_bias.pack()
        self.label_pitch_bias= ttk.Label(self, text="Bias")
        self.label_pitch_bias.pack()
        """
        self.scale_modulation_elevation = tk.Scale(self, from_=-90, to=90, orient="horizontal")
        self.scale_modulation_elevation.pack()
        self.label_modulation_elevation= ttk.Label(self, text="Elevation")
        self.label_modulation_elevation.pack()
        self.scale_modulation_value = tk.Scale(self, from_=0, to=16384, orient="horizontal")
        self.scale_modulation_value.pack()
        self.label_modulation_value= ttk.Label(self, text="Modulation")
        self.label_modulation_value.pack()
        self.scale_modulation_bias = tk.Scale(self, from_=-90, to=+90, orient="horizontal")
        self.scale_modulation_bias.pack()
        self.label_modulation_bias= ttk.Label(self, text="Bias")
        self.label_modulation_bias.pack()

        ## Definitions
        self.pitch = 0
        self.max = 16384
        self.value = 0

    def start_Pitch(self):
        self.scale_pitch_value.set(16384 / 2)
      #  self.scale_pitch_value.set(16384)
        self.scale_pitch_elevation.set(0)
        #self.scale_pitch_elevation["maximum"] = 180
        self.scale_pitch_bias.set(0)
     #   self.scale_pitch_bias["maximum"] = 180

        if pitch_server:
            print 'started pitch server'
        else:
            print 'no pitch server'


        if pitch_server:
            self.pitch_start_button.config(text='working')
            orient_thread = threading.Thread(target=pitch_server.serve_forever)
            orient_thread.start()
            print 'pitch-server thread started'
        else:
            print 'pitch server not found'


    def stop_Pitch(self):
        self.pitch_start_button.config(text='start')
        if pitch_server:

            print 'shutting  down pitch server'

            pitch_server.shutdown()
    ## Within the program we need to use this IF to change the value of the bar

        else:
             print 'no pitch  server to stop'




    def rebalance_pitch(self):
        global glob_pitch_first
        glob_pitch_first = 1

    """
    def update_pitchfreq_progressbar(self, value,elevation,bias):
        self.scale_pitch_value.set(value)
        self.scale_pitch_elevation.set(elevation)
        self.scale_pitch_bias.set(bias)
#### second time :?
        self.scale_pitch_elevation = tk.Scale(self, from_=-90, to=90, orient="horizontal")
        self.scale_pitch_elevation.pack()
        self.label_pitch_elevation= ttk.Label(self, text="Elevation")
        self.label_pitch_elevation.pack()


##        self.scale_modulation = tk.Scale(self, from_=0, to=16384, orient="horizontal")
## 13-4-15  18:51 change pitch to modulation ?
        self.scale_pitch_value = tk.Scale(self, from_=0, to=16384, orient="horizontal")

        # comment 15/5/15
        #self.scale_pitch_value.pack()
        #self.label_pitch= ttk.Label(self, text="Pitch")
        #self.label_pitch.pack()
        #self.scale_bias = tk.Scale(self, from_=-90, to=+90, orient="horizontal")
        #self.scale_bias.pack()
        #self.label_bias= ttk.Label(self, text="Bias")
        #self.label_bias.pack()
        ## Definitions
        # NOT IN USE AT ALL
        #self.modulation_valuepitch = 0
        #self.max = 16384
        #self.value = 0        self.pitch = 0
        #self.max = 16384
        #self.value = 0
    """

    def start_modulation(self):

        self.scale_modulation_value.set(16384 / 2)
      #  self.scale_modulation_value.set(16384)
        self.scale_modulation_elevation.set(0)
        #self.scale_modulation_elevation["maximum"] = 180
        self.scale_modulation_bias.set(0)
     #   self.scale_modulation_bias["maximum"] = 180

        if modulation_server:
            self.modulation_start_button.config(text='working')
            orient_thread = threading.Thread(target=modulation_server.serve_forever)
            orient_thread.start()
            print 'started modulation server'
        else:
            print 'no modulation server'


##        servers = [pitch_server, modulation_server ]
## 13-4-14  12:48 ^

# 13-4-15 do replace with pitch server only ! :

    def stop_modulation(self):

        self.modulation_start_button.config(text='start')
        #global modulation_server
        if modulation_server:
            print 'shutdowning modulation server'
            modulation_server.shutdown()
        else:
             print 'no modulation server to stop'


    ## Within the program we need to use this IF to change the value of the bar

    def rebalance_modulation(self):
        global glob_modulation_first
        glob_modulation_first = 1



# end copy and make mod instead of pitch


    def update_pitchfreq_progressbar(self, pitch,elevation,bias):
        self.scale_pitch_value.set(pitch)
        self.scale_pitch_elevation.set(elevation)
        self.scale_pitch_bias.set(bias)

    def update_modulationfreq_progressbar(self, pitch,elevation,bias):
            self.scale_modulation_value.set(pitch)
            self.scale_modulation_elevation.set(elevation)
            self.scale_modulation_bias.set(bias)



def put_between(val, lower, upper):
    val = min(val, upper)
    val = max(val, lower)
    return val

def initiate_pitch_bias_buffer(value):
    global glob_pitch_bias_buffer_size
    global pitch_bias_buffer
    for i in range(1,glob_pitch_bias_buffer_size):
        pitch_bias_buffer[i]= value

def initiate_modulation_bias_buffer(value):
    global glob_modulation_bias_buffer_size
    global modulation_bias_buffer
    for i in range(1,glob_modulation_bias_buffer_size):
        modulation_bias_buffer[i]= value

# define a class for the axis
# the pitch value deliminator
class OrientationAxis(object):
    def __init__(self, min, max):
        self.min = min
        self.mid = (max - min) / 2
        self.max = max
        self.range = max - min

    def set_axis(self, value): # value - the bias axis value to be set to mid, min,max,range will be set according to "value"
        global glob_pitch_threshold_value
        global glob_pitch_saturation_value
        self.mid = value
        self.min = value - glob_pitch_saturation_value  # angle between bias position and max position
        self.max = value + glob_pitch_saturation_value  # angle between bias position and max position
        self.upper_margin = self.mid + glob_pitch_threshold_value
        self.lower_margin = self.mid - glob_pitch_threshold_value
        self.range = self.max - self.min - (self.upper_margin - self.lower_margin)


class MidiMessageMaker(object):
    def make_message(self, value, channel=0):
        raise NotImplementedError()

    def __str__(self):
        raise NotImplementedError()


class MidiController(MidiMessageMaker):
    midi_opcode = 0xb0
    max = 127
    controller_names = {0x01: 'Modulation Wheel',
                        0x02: 'Breath Controller',
                        0x03: 'Undefined',

                        11: 'Expression (CC11)',
                        74: 'Frequency Cutoff (CC74)'}

    def __init__(self, controller_code):
        self.controller_code = controller_code

    def make_message(self, value, channel=0):
        return [self.midi_opcode + channel, self.controller_code, value]

    def __str__(self):
        return self.controller_names[self.controller_code]


class ModulationWheel(MidiController):
    def __init__(self):
        super(ModulationWheel, self).__init__(0x01)
        self.dilul_prnt_cntr_mod=0

    def make_message(self, value, channel=0):

# global dilul_saf # = 100  # how many midi msgs to not print.


        if column_prnt:
            self.dilul_prnt_cntr_mod += 1
#             print '   self.dilul_prnt_cntr_mod = ' ,  self.dilul_prnt_cntr_mod  . debug line of debug option
            if (self.dilul_prnt_cntr_mod > 100 ):  # i want : 100):
                print value-35 # print same val as sent to midi in next big code   line
                self.dilul_prnt_cntr_mod = 0

        return [self.midi_opcode + channel, self.controller_code, value-35]  # 16-4-15 was -30 less hear mod lfo so chng to 10.
        #over ride for adding -30 only on modulation, not pitch bend

class PitchWheel(MidiController):
    def __init__(self):
        self.dilul_prnt_cntr_pitch=0

    midi_opcode = 0xE0
    max = 16383 # 1<<14 - 1, or 2**14 - 1

    def make_message(self, value, channel=0):
#        self.global dilul_prnt_cntr_pitch
        if column_prnt:

            self.dilul_prnt_cntr_pitch+=1
            if (self.dilul_prnt_cntr_pitch > 100 ):  # 100):
                self.dilul_prnt_cntr_pitch = 0
                print '    '   , value  # pitch bend 14 bits.

        return [self.midi_opcode + channel, value & 0x7f, value >> 7]

    def __str__(self):
        return "Pitch Wheel"


# sensor IDs from Sensorstream app code
BLH_SENSOR_ID = 1 # currently unsupported by the app
ACCELEROMETER_SENSOR_ID = 3
GYROSCOPE_SENSOR_ID = 4
MAG_SENSOR_ID = 5
XYZ_WGS84_SENSOR_ID = 6 # currently unsupported by the app
VELOCITY_WGS84_SENSOR_ID = 7 # currently unsupported by the app
GPS_UTC_TIME_SENSOR_ID = 8 # currently unsupported by the app
ORIENTATION_SENSOR_ID = 81
LIN_ACC_SENSOR_ID = 82
GRAVITY_SENSOR_ID = 83
ROT_VEC_SENSOR_ID = 84
PRESSURE_SENSOR_ID = 85
BAT_TEMP_SENSOR_ID = 86
num_sensor_values = {
    PRESSURE_SENSOR_ID: 1, BAT_TEMP_SENSOR_ID: 1, ACCELEROMETER_SENSOR_ID: 3,
    GYROSCOPE_SENSOR_ID: 3, MAG_SENSOR_ID: 3, ORIENTATION_SENSOR_ID: 3,
    LIN_ACC_SENSOR_ID: 3, GRAVITY_SENSOR_ID: 3, ROT_VEC_SENSOR_ID: 3
}

class SensorHandler(SocketServer.DatagramRequestHandler):
    """Handles IMU+GPS-Stream's messages.
    Every coma-separated message starts with a timestamp, followed by sensor values.
    Sensor values are either triple or single float values, formatted as 7.3f,
    except for the battery temperature sensor, whose only value is passed with %d.
    Assuming only the three mandatory sensors and the orientation sensor are chosen, messages should look like:
    "%(timestamp).5f, %(accel_id)d,  %(sensor_values)7.3f7.3f7.3f, %(gyro_id)d,  %(gyro_values)7.3f7.3f7.3f, %(mag_id=5)d, %(mag_values)7.3f7.3f7.3f, %(orientation_id=81)d,  %(orient_values)7.3f7.3f7.3f"
    The extra spaces between the sensor id and the values originate from the Sensorstream app.
    An instance of this class is created for each request from the server."""

    def handle(self):
        if dbg_print:
            print 'handling client %s' % (self.request, )
        'This func is called for every message received'

        packet, from_ip_port = self.request
        # timestamp, *sensor_vals = eval(packet) # Only works in Python3
        packet = eval(packet)
        timestamp, sensor_data = packet[0], packet[1:]
        while sensor_data:
            sensor_id, sensor_data = sensor_data[0], sensor_data[1:]
            vals_to_get = num_sensor_values[sensor_id]
            sensor_vals, sensor_data = sensor_data[:vals_to_get], sensor_data[vals_to_get:]
            if sensor_id == ORIENTATION_SENSOR_ID:
                self.server.handle_orientation(sensor_vals)



class SensorHandlingServer(SocketServer.UDPServer):

    def __init__(self, socket_pair, yaw_to, pitch_to, roll_to, midiout):
        SocketServer.UDPServer.__init__(self, socket_pair, SensorHandler)
        self.last_time = time.time()
        self.last_print_time = time.time()
        self.last_vals = [0, 0, 0]
        self.min_interval = 0.05     # minimum time interval to send midi massage- TO CAHNGE
        self.axis_num_to_contrlr = [yaw_to, pitch_to, roll_to] # in same order as axes
        # define an instance for yaw, pitch, roll
        self.yaw_axis = OrientationAxis(-180, 179) # 0 - North, 90 - East, -180 - South, -90 - east
        #  OLD : pitch_axis = OrientationAxis(-90, 90) # assuming screen is up
        self.pitch_axis = OrientationAxis(-110, 110) # assuming screen is up
        # 0 - horizontal, -90 - negative vertical, 90 - positive vertical
        self.roll_axis = OrientationAxis(-90, 90)  # assuming screen is up
        # -90 - screen to the left, +90 - screen to the right.
        self.axes = [self.yaw_axis, self.pitch_axis, self.roll_axis]

        self.midiout = midiout
        self.Cmax_0_5 = self.axis_num_to_contrlr[
                            1].max / 2 # keep the value of controller.max/2 to save real-time calculations
        ##global glob_pitch_first
        ##glob_pitch_first = 1
    def handle_orientation(self, yaw_pitch_roll):
        raise NotImplementedError()


class PitchFreqServer(SensorHandlingServer):
    def __init__(self, bind_address, midiout):
        print 'pitchfreqserver\tenter'
        pitch_undefined_controller = MidiController(0x03)
        pitch_wheel = PitchWheel()

        print 'pitchfreqserver\tcreating sensorhandlingserver...'
        SensorHandlingServer.__init__(
            self,
            bind_address,
            yaw_to=pitch_undefined_controller,
            pitch_to=pitch_wheel,
            roll_to=pitch_undefined_controller,
            midiout=midiout
        )
        print 'pitchfreqserver\tcreated sensorhandlingserver.'
        global glob_pitch_first
        glob_pitch_first = 1


    def handle_orientation(self, yaw_pitch_roll):
        print 'pitchfreqserver\thandle_orientation\tenter.'
        global glob_pitch_elevation_value
        global glob_pitch_threshold_value
        global glob_pitch_first
        global glob_pitch_bias
        global glob_pitch_bias_buffer_size
        global pitch_bias_buffer_pointer
        global pitch_bias_buffer
        'Translate orientation values to pitch control'
        # if its the first time the function runs, set the parameters axis.min axis.max:
        if dbg_print:
            print "yaw_pitch_roll ",yaw_pitch_roll
        ## 13-4-15 21:49  see any wi fi data in.

        yaw_pitch_roll2 = list(yaw_pitch_roll)
        if dbg_print:
            print 'mila ' , yaw_pitch_roll
        ## 13-4-15 21:49  see any wi fi data in.

        pitch = yaw_pitch_roll2[1]
        glob_pitch_elevation_value = pitch
        # DEBUGGER
        #import pdb ; pdb.set_trace()
        if (glob_pitch_first == 1):
            self.pitch_axis.set_axis(int(pitch))

            glob_pitch_bias = pitch
            initiate_pitch_bias_buffer(glob_pitch_bias)
            # version 8.3 : consider changing or deleting the next line:
            midi_msg = self.axis_num_to_contrlr[1].make_message(
                int(self.Cmax_0_5 + float(self.axis_num_to_contrlr[1].max) / self.pitch_axis.range * (pitch - self.pitch_axis.mid)))
            self.midiout.send_message(midi_msg)


            # if its the first time the function runs, then Print the parameters rcvd ,  in any case ,  to see tkinut.
            print "yaw_pitch_roll ",yaw_pitch_roll
            ## 13-4-15 21:49  see any wi fi data in.

            glob_pitch_first = 0
            print "pitch recieved:   ", pitch  # 11.11.2013 canceled prints
        ## 13-4-15 21:49  see any wi fi data in.

        # Fixing axis_val to ergonomic limits
        pitch = put_between(pitch, self.pitch_axis.min, self.pitch_axis.max)
        if dbg_print:
            print "pitch after fix:  ", pitch  # 11.11.2013 canceled prints
        ## 13-4-15 21:49  see any wi fi data in.

        # 20/10/2013 adding filter: send massage only if movement passed the threshold(far enough from mid point that was set in the start)
        relative_pitch = pitch - self.pitch_axis.mid
        is_beyond_threshold = [abs(relative_pitch) > glob_pitch_threshold_value]

        deltas = [abs(last_val - val) for last_val, val in zip(self.last_vals, yaw_pitch_roll)]
        is_delta_big = [delta > 0 for delta, axis in zip(deltas, self.axes)]
        controller = self.axis_num_to_contrlr[1]  # controller gets the "class pitchWheel"
        # controller.max = 16383 (2^14 - 1)

        global glob_pitch_sent_pitch  # for gui
        if (time.time() - self.last_time > self.min_interval) and any(is_delta_big):
            if (is_beyond_threshold == [True]):
                if (relative_pitch > 0):   #  relative_pitch > threshold
                    # 0.49 & 0.4 are to normalize it to half tone. remove those to get one tone pitch
                    glob_pitch_sent_pitch = int(
                        self.Cmax_0_5 + float(controller.max)*0.49 / self.pitch_axis.range * (pitch - self.pitch_axis.upper_margin))
                    midi_msg = controller.make_message(glob_pitch_sent_pitch)
                else: # relative_pitch < -threshold
                    glob_pitch_sent_pitch = int(
                        self.Cmax_0_5 + float(controller.max)*0.409 / self.pitch_axis.range * (pitch - self.pitch_axis.lower_margin))
                    midi_msg = controller.make_message(glob_pitch_sent_pitch)
                self.midiout.send_message(midi_msg)
                self.last_time = time.time()
                self.last_vals = yaw_pitch_roll
            else:   # player wants the bias pitch
                glob_pitch_sent_pitch = int(self.Cmax_0_5)
                midi_msg = self.axis_num_to_contrlr[1].make_message(glob_pitch_sent_pitch)
                self.midiout.send_message(midi_msg)

                if dbg_print:
                    print midi_msg # if debug. was ovrflow

                # set adaptive bias - moving average
                pitch_bias_buffer_pointer += 1
                pitch_bias_buffer[pitch_bias_buffer_pointer % glob_pitch_bias_buffer_size] = pitch;

                glob_pitch_bias += (pitch_bias_buffer[(pitch_bias_buffer_pointer) % glob_pitch_bias_buffer_size] - pitch_bias_buffer[(pitch_bias_buffer_pointer+1) % glob_pitch_bias_buffer_size]) / glob_pitch_bias_buffer_size
                self.pitch_axis.set_axis(glob_pitch_bias)

        if dbg_print:

            print "pitch: glob_pitch_sent_pitch \n"
            print glob_pitch_sent_pitch

            print "pitch: glob_pitch_bias \n"
            print glob_pitch_bias
        # prints were in remark in production version ^
#        print 'pitch: before update_progressbar part'
        global gui
        try:
            gui.update_pitchfreq_progressbar(glob_pitch_sent_pitch, glob_pitch_elevation_value, glob_pitch_bias)
            if dbg_print:
                print 'pitch: after gui.update_progressbar'
        except Exception, e:
            print 'pitch: error: %s' % e
#        print 'pitch: after update_progressbar part'


class ModulationFreqServer(SensorHandlingServer):
    def __init__(self, bind_address, midiout):
        modulation_undefined_controller = MidiController(0x03)
        modulation_wheel = ModulationWheel()

        SensorHandlingServer.__init__(
            self,
            bind_address,
            yaw_to=modulation_undefined_controller,
            pitch_to=modulation_wheel,
            roll_to=modulation_undefined_controller,
            midiout=midiout
        )
        global glob_modulation_first
        glob_modulation_first = 1


    def handle_orientation(self, yaw_pitch_roll):
        global glob_modulation_elevation_value
        global glob_modulation_threshold_value
        global glob_modulation_first
        global glob_modulation_bias
        global glob_modulation_bias_buffer_size
        global modulation_bias_buffer_pointer
        global modulation_bias_buffer
        'Translate orientation values to modulation control'
        # if its the first time the function runs, set the parameters axis.min axis.max:
        if dbg_print:
            print "yaw_pitch_roll ",yaw_pitch_roll
        ## 13-4-15 21:49  see any wi fi data in.

        yaw_pitch_roll2 = list(yaw_pitch_roll)
        if dbg_print:
            print 'mila ' , yaw_pitch_roll
        ## 13-4-15 21:49  see any wi fi data in.

        pitch = yaw_pitch_roll2[1]
        glob_modulation_elevation_value = pitch
        # DEBUGGER
        #import pdb ; pdb.set_trace()
        if (glob_modulation_first == 1):
            self.pitch_axis.set_axis(int(pitch))

            glob_modulation_bias = pitch
            initiate_modulation_bias_buffer(glob_modulation_bias)
            # version 8.3 : consider changing or deleting the next line:
            midi_msg = self.axis_num_to_contrlr[1].make_message(
                int(self.Cmax_0_5 + float(self.axis_num_to_contrlr[1].max) / self.pitch_axis.range * (pitch - self.pitch_axis.mid)))
            self.midiout.send_message(midi_msg)


            # if its the first time the function runs, then Print the parameters rcvd ,  in any case ,  to see tkinut.
            print "yaw_pitch_roll ",yaw_pitch_roll
            ## 13-4-15 21:49  see any wi fi data in.

            glob_modulation_first = 0
            print "pitch recieved:   ", pitch  # 11.11.2013 canceled prints
        ## 13-4-15 21:49  see any wi fi data in.

        # Fixing axis_val to ergonomic limits
        pitch = put_between(pitch, self.pitch_axis.min, self.pitch_axis.max)
        if dbg_print:
            print "pitch after fix:  ", pitch  # 11.11.2013 canceled prints
        ## 13-4-15 21:49  see any wi fi data in.

        # 20/10/2013 adding filter: send massage only if movement passed the threshold(far enough from mid point that was set in the start)
        relative_pitch = pitch - self.pitch_axis.mid
        is_beyond_threshold = [abs(relative_pitch) > glob_modulation_threshold_value]

        deltas = [abs(last_val - val) for last_val, val in zip(self.last_vals, yaw_pitch_roll)]
        is_delta_big = [delta > 0 for delta, axis in zip(deltas, self.axes)]
        controller = self.axis_num_to_contrlr[1]  # controller gets the "class pitchWheel"
        # controller.max = 16383 (2^14 - 1)

        global glob_modulation_sent_pitch  # for gui
        if (time.time() - self.last_time > self.min_interval) and any(is_delta_big):
            if (is_beyond_threshold == [True]):
                if (relative_pitch > 0):   #  relative_pitch > threshold
                    # 0.49 & 0.4 are to normalize it to half tone. remove those to get one tone pitch
                    glob_modulation_sent_pitch = int(
                        self.Cmax_0_5 + float(controller.max)*0.49 / self.pitch_axis.range * (pitch - self.pitch_axis.upper_margin))
                    midi_msg = controller.make_message(glob_modulation_sent_pitch)
                else: # relative_pitch < -threshold
                    glob_modulation_sent_pitch = int(
                        self.Cmax_0_5 + float(controller.max)*0.409 / self.pitch_axis.range * (pitch - self.pitch_axis.lower_margin))
                    midi_msg = controller.make_message(glob_modulation_sent_pitch)
                self.midiout.send_message(midi_msg)
                self.last_time = time.time()
                self.last_vals = yaw_pitch_roll
            else:   # player wants the bias pitch
                glob_modulation_sent_pitch = int(self.Cmax_0_5)
                midi_msg = self.axis_num_to_contrlr[1].make_message(glob_modulation_sent_pitch)
                self.midiout.send_message(midi_msg)

                if dbg_print:
                    print midi_msg # if debug. was ovrflow

                # set adaptive bias - moving average
                modulation_bias_buffer_pointer += 1
                modulation_bias_buffer[modulation_bias_buffer_pointer % glob_modulation_bias_buffer_size] = pitch;

                glob_modulation_bias += (modulation_bias_buffer[(modulation_bias_buffer_pointer) % glob_modulation_bias_buffer_size] - modulation_bias_buffer[(modulation_bias_buffer_pointer+1) % glob_modulation_bias_buffer_size]) / glob_modulation_bias_buffer_size
                self.pitch_axis.set_axis(glob_modulation_bias)

        if dbg_print:

            print "modulation: glob_pitch_sent_pitch \n"
            print glob_modulation_sent_pitch

            print "modulation: glob_pitch_bias \n"
            print glob_modulation_bias
        # prints were in remark in production version ^
#        print 'modulation: before update_progressbar part'
        global gui
        try:
            gui.update_modulationfreq_progressbar(glob_modulation_sent_pitch, glob_modulation_elevation_value, glob_modulation_bias)
# 21.5.2015 - mod bar display affects pitch frq average. putting mod bar in remark

            if dbg_print:
                print 'modulation: after gui.update_progressbar'
        except Exception, e:
            print 'modulation: error: %s' % e
#        print 'modulation: after update_progressbar part'


class MidiInputCallback(object):
    def __init__(self, midiout, do_prints=False):
        self.midiout = midiout

    def __call__(self, message_and_delta, data):
        message, time_delta = message_and_delta
        # 14/12/2014 trying to not send the lower part of the keyboard
        if (message[1] > 55):
            self.midiout.send_message(message)

#################
### MAIN #####3##
#################
# Get bind addresses
#-----------------------------
# 1. Modulation bind addresses
##    modulation_bind_address = [BIND_IP, MODULATION_LISTENING_PORT]
modulation_bind_addresses = socket.getaddrinfo(socket.gethostname(), MODULATION_LISTENING_PORT, socket.AF_INET,
                     socket.SOCK_DGRAM)
modulation_bind_address = [t[-1] for t in modulation_bind_addresses][0]
print "listening for modulation on %s" % (modulation_bind_address, )

# 2. Pitch bind address
#pitch_bind_address = (BIND_IP, PITCH_LISTENING_PORT)
pitch_bind_addresses = socket.getaddrinfo(socket.gethostname(), PITCH_LISTENING_PORT, socket.AF_INET,
                     socket.SOCK_DGRAM)
# sock_addrs gets the IP , Port of the computer
#  t gets 4 elements as a list. the last element is the IP, Port
pitch_bind_address = [t[-1] for t in pitch_bind_addresses][0]
print "listening for pitch on %s" % (pitch_bind_address, )

# Get midi interfaces
#-----------------------------
midiout = rtmidi.MidiOut()
midiin = rtmidi.MidiIn()

#set midi out port
out_ports = midiout.get_ports()
out_port = out_ports.index(MIDI_LOOP_OUT)
midiout.open_port(out_port)
print "MIDI sent to %s" % (MIDI_LOOP_OUT, )

#set midi - in port
in_ports = midiin.get_ports() # checks automaticaly for midi ports.
print "searching for midi input ports \n"
for in_port, in_port_name in enumerate(in_ports):    # should find the komplete audio 6 sound card..
    if "Loop" not in in_port_name:
        midiin.open_port(in_port)
        print "MIDI received from %s" % (in_port_name, )
        midiin.set_callback(MidiInputCallback(midiout, )) # setting the handler for data(notes)

# Create servers
#-----------------------------


# Modulation server
try:
    #global modulation_server
    modulation_server = ModulationFreqServer(
        modulation_bind_address,
        midiout=midiout
    )


    print 'Modulation server is ready.'
except Exception, e:
    print 'Modulation server failed: %s' % (e, )


# Pitch server
try:
    pitch_server = PitchFreqServer(
        pitch_bind_address,
        midiout=midiout
    )

    print 'Pitch server is ready.'
except Exception, e:
    print 'Pitch server failed: %s' % (e, )


##    servers=[pitch_server, modulation_server ]
##13-4-15  12:54


print 'Working...'

# Start GUI

## 13-4-15
##    servers = [pitch_server, modulation_server ]


gui = Gui()
###    servers = [pitch_server, modulation_server ]
##13-4-15 try ^

gui.mainloop()
raw_input("Press Enter to exit\n")



# remarks :
# 11-4-2015  added  sensor :  modulation wheel. now 2 sensors : modulation on pitch bend.
# 13-4-15 - changing gui to include  2  sensor streams. COPY BUTONS FOR 2 TYPES - MOD, PITCH.
# 13-4-15 - adding slides for mod, separating vars of mod in sliders from pitch.



 