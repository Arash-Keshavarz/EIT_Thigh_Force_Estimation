import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import threading
import time
import datetime


class ContinuousDAQ:
    def __init__(self, sampling_rate, chunk_size, output_file):
        """
        Initialize the DAQ parameters.
        """
        self.channels = ["Dev1/ai0", "Dev1/ai1", "Dev1/ai2"]
        self.sampling_rate = sampling_rate
        self.chunk_size = chunk_size
        self.output_file = output_file
        self.all_data = [[] for _ in self.channels]
        self.timestamps_start = []
        self.timestamps_current = []
        self.acquisition_running = False
        self.save_counter = 0 # initialize a counter

    def start_measurement(self):
        """
        Start the data acquisition process.
        """
        self.acquisition_running = True
        with nidaqmx.Task() as task:
            for channel in self.channels:
                task.ai_channels.add_ai_voltage_chan(channel)

            task.timing.cfg_samp_clk_timing(
                self.sampling_rate, sample_mode=AcquisitionType.CONTINUOUS
            )

            start_time = time.time()
            self.timestamps_start.append(start_time)
            print("Acquisition started.")

            while self.acquisition_running:
                samples = task.read(number_of_samples_per_channel=self.chunk_size)
                current_time = time.time()
                self.timestamps_current.append(current_time)

                # Extend channel data
                if len(self.channels) > 1:
                    for i, channel_data in enumerate(samples):
                        self.all_data[i].extend(channel_data)
                else:
                    self.all_data[0].extend(samples)
                self._save_data()
                # Debugging: Print current time
                print(
                    "Current Time:",
                    datetime.datetime.now().strftime("%m/%d/%Y, %H:%M:%S"),
                )
                time.sleep(0.1)

    def stop_measurement(self):
        """
        Stop the data acquisition process.
        """
        self.acquisition_running = False
        self._save_data()
        
        print("Acquisition stopped and data saved.")

    def _save_data(self):
        """
             Save the acquired data and timestamps to a unique file using a counter.
        """
        unique_output_file = f"{self.output_file}_{self.save_counter}.npz"
        self.save_counter += 1
        data_array = np.array([np.array(channel_data) for channel_data in self.all_data])
        np.savez(
            unique_output_file,
            data=data_array,
            timestamps_start=self.timestamps_start,
            timestamps_current=self.timestamps_current,
            sampling_rate=self.sampling_rate,
        )
        print(f"Data saved to {self.output_file}")


