import nidaqmx
from nidaqmx.constants import AcquisitionType
import numpy as np
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
import time
import datetime
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


class ContinuousDAQ:
    def __init__(self, sampling_rate, chunk_size, output_file):
        """
        Initialize the DAQ parameters.

        Args:
            sampling_rate (int): The sampling rate in Hz.
            chunk_size (int): The number of samples to read in each chunk.
            output_file (str): Base name of the output file for saving data.
        """
        self.channels = ["Dev1/ai0", "Dev1/ai1", "Dev1/ai2"]
        self.sampling_rate = sampling_rate
        self.chunk_size = chunk_size
        self.output_file = output_file
        self.all_data = [[] for _ in self.channels]
        self.timestamps_start = []
        self.timestamps_current = []
        self.acquisition_running = False
        self.save_counter = 0  # saving  sample number

    def start_measurement(self):
        """
        Start the data acquisition process.
        """
        self.acquisition_running = True
        try:
            with nidaqmx.Task() as task:
                # Add channels to the task
                for channel in self.channels:
                    task.ai_channels.add_ai_voltage_chan(channel)
                
                # Configure task timing
                task.timing.cfg_samp_clk_timing(
                    self.sampling_rate, sample_mode=AcquisitionType.CONTINUOUS
                )

                start_time = time.time()
                self.timestamps_start.append(start_time)
                logging.info("Acquisition started.")

                while self.acquisition_running:
                    # Read samples
                    samples = task.read(number_of_samples_per_channel=self.chunk_size)
                    current_time = time.time()
                    self.timestamps_current.append(current_time)

                    # Store channel data
                    if len(self.channels) > 1:
                        for i, channel_data in enumerate(samples):
                            self.all_data[i].extend(channel_data)
                    else:
                        self.all_data[0].extend(samples)

                    self._save_data()
                    logging.debug(
                        f"Current time: {datetime.datetime.now().strftime('%m/%d/%Y, %H:%M:%S')}"
                    )
        except nidaqmx.DaqError as e:
            logging.error(f"DAQ Error: {e}")
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
        finally:
            self.acquisition_running = False
            logging.info("Measurement loop exited.")

    def stop_measurement(self):
        """
        Stop the data acquisition process and save remaining data.
        """
        self.acquisition_running = False
        self._save_data()
        logging.info("Acquisition stopped and data saved.")

    def _save_data(self):
        """
        Save the acquired data and timestamps to a unique file using a counter.
        """
        try:
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
            logging.info(f"Data saved to {unique_output_file}")
        except Exception as e:
            logging.error(f"Error saving data: {e}")


