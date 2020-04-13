# -*- coding: utf-8 -*-

import warnings
with warnings.catch_warnings():
    warnings.simplefilter("ignore"); 
    import matplotlib.pyplot as plt

import sys
import threading
import collections
import struct
import logging
import time

from matplotlib import colors
from matplotlib.colors import LogNorm
import matplotlib.image as mpimg

import numpy as np


class Plotter(threading.Thread):
    def __init__(self, event = None):
        threading.Thread.__init__(self)

        self.event = event

        self.delta_time = 0.1
        self.total_time = 0.0
        self.samples = 5000
        
        self.current_temp = collections.deque(maxlen=self.samples)
        self.target_temp  = collections.deque(maxlen=self.samples)
        self.error_temp   = collections.deque(maxlen=self.samples)
        self.current_pwm  = collections.deque(maxlen=self.samples)
        self.current_time = collections.deque(maxlen=self.samples)
        
        self.is_finished = False

    def exit(self):
        logging.info("exit")
        self.is_finished = True

    def run(self):
        logging.info("run")

        # Create figure
        fig = plt.figure(figsize=(12, 9))

        plt.ion()
        fig.show(False)

        # Two subplots, one for temperature and one for PWM
        ax1 = fig.add_subplot(2,2,1)
        ax2 = fig.add_subplot(2,2,2)
        ax3 = fig.add_subplot(2,2,3)

        fig.show()
        fig.canvas.draw()

        while not self.is_finished:
            # Wait for image to be received or timeout
            if (self.event.wait(self.delta_time)):

                # Append current time
                self.current_time.append(self.total_time)

                # Clear the asynchronous event
                self.event.clear()

                # Clear plots
                ax1.clear()
                ax2.clear()
                ax3.clear()

                # Plot target temperature
                temp1 = np.asarray(self.target_temp, dtype=np.float)
                temp2 = np.asarray(self.current_temp, dtype=np.float)

                # Plot target and current temperature
                ax1.plot(temp1, label="Temperatura objetivo")
                ax1.plot(temp2, label="Temperature actual")
                               
                ax1.set_title("Temperatura")
                ax1.set_ylabel("Temperatura ($^\circ$C)")
                ax1.set_xlabel("Tiempo (segundos)")
                ax1.set_ylim((0,120))
                ax1.set_xticks(np.arange(0, self.samples + 1, step=self.samples/10))
                ax1.set_xticklabels(np.arange(0, self.samples/10 + 1, step=self.samples/100))
                ax1.legend()
                ax1.grid(True)

                # Plot temperature error
                length = min(len(temp2), len(temp1))
                error = temp1[:length] - temp2[:length]
                ax2.plot(error, label="Error temperatura")
                ax2.set_title("Error temperatura")
                ax2.set_ylabel("Temperatura ($^\circ$C)")
                ax2.set_xlabel("Tiempo (segundos)")
                ax2.set_ylim((-20,20))
                ax2.set_xticks(np.arange(0, self.samples + 1, step=self.samples/10))
                ax2.set_xticklabels(np.arange(0, self.samples/10 + 1, step=self.samples/100))
                ax2.legend()
                ax2.grid(True)

                # Plot PWM value                                
                temp3 = np.asarray(self.current_pwm, dtype=np.float)
                ax3.plot(temp3, label="PWM actual")

                ax3.set_title("PWM")
                ax3.set_ylabel("PWM (%)")
                ax3.set_xlabel("Tiempo (segundos)")
                ax3.set_ylim((0,100))
                ax3.legend()
                ax3.set_xticks(np.arange(0, self.samples + 1, step=self.samples/10))
                ax3.set_xticklabels(np.arange(0, self.samples/10 + 1, step=self.samples/100))
                ax3.grid(True)

                # Draw the new figure
                fig.canvas.draw()

                # Flush events
                fig.canvas.flush_events()

            self.total_time += self.delta_time

        plt.ioff()
        plt.close()

        logging.info("exit")
            
    
    def set_current_temp(self, data):
        self.current_temp.append(data)

    def set_target_temp(self, data):
        self.target_temp.append(data)

    def set_current_pwm(self, data):
        self.current_pwm.append(data)