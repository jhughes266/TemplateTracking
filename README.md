# Object Tracker with Timer

## Table of Contents
- [Overview](#overview)
- [Key Features](#key-features)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Setup Instructions](#setup-instructions)
- [Example Output](#example-output)
- [My Role / What I Learned](#my-role--what-i-learned)
- [License](#license)

## Overview

This tool demonstrates a basic implementation of real-time object tracking using a webcam feed, built with OpenCV. It uses template tracking to locate and track a template on the screen. It also provides serial communication options to send results from tracking serially.

## Key Features

- Utilizes OpenCV object tracking
- Configurable tracking from a simple config file
- Re-calibration if template position is lost
- Serial communication of tracking positions

## Project Structure

| Folder/File              | Description                                                                               |
|--------------------------|-------------------------------------------------------------------------------------------|
| `main.py`                | Entry point. Sets up the tracker.                                                         |
| `ObjectTrackingClass.py` | Contains `ObjectTracking` class for managing tracker initialization, updates, and drawing |
| `timerClass.py`          | Utility class to measure time intervals of different parts of program execution           |
| `config.txt`             | Plain text configuration file for selecting tracker type                                  |
| `Output.txt`             | Output log for program                                                                    |
| templates                | Stores the reference template used by the tracking program                                |
| trackingLocations        | Stores .txt files that record the tracking locations                                      |
## Technologies Used

| Tool       | Purpose                    |
|------------|----------------------------|
| Python     | Programming language       |
| OpenCV     | Computer vision and object tracking |
| Time module | Timing logic and duration tracking |

## Setup Instructions

Make sure you have Python 3.7 or higher installed.

```bash
# 1. Clone the repository or copy the project files into a local folder

# 2. Install dependencies
pip install opencv-python

# 3. Check or update the tracker type in config.txt

# 4. Run the tracker
python main.py
```

## Example Output

Once the program is running:

1) A window will open showing your webcam feed. (You can exit the program by pressing 'q' and **exiting the graphs that appear**)
2) Move a template that replicates the one in the template file into the screen (This template can be hand drawn or printed)
3) If it is not registered move your template toward and away from the screen.
4) If this does not work you will need to record two things whilst the program is running.
   1) Move the template back and forward when inside the screen. Take note of the lowest value of the **Max Difference Threshold** during this process.
   2) Move the template **OUT** of screen and note the value of the **Max Difference Threshold**.
   3) Go into the "config.txt" file and under the "Program Settings" change this value to halfway between the two recorded values.
   4) Restart the program.
   5) It should now work.
5) If this still does not work ensure that your background is not to cluttered this program works best against a monotone clear background.

## My Role / What I Learned

- Gained understanding of real-time video processing with Python
- Basic object tracking
- Use of Serial communication inside python
- File reading and writing


## License

MIT License

© 2025 Jotham Hughes

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
