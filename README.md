# Web_app
```python
# Project Title

Brief description of what the project does and who it's for.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- **Python**: You must have Python 3.10.11 installed on your machine. If you have multiple versions of Python installed, make sure Python 3.10.11 is set as the primary version in your system's environment path.

## Installation

Follow these steps to get your development environment set up:

1. **Clone the repository**

   ```bash
   git clone <repository link>
   ```

2. **Navigate to the repository directory**

   ```bash
   cd <repository directory>
   ```

3. **Create a Python virtual environment**

   ```bash
   python -m venv .venv
   ```

4. **Activate the virtual environment**

   - On Windows:

     ```bash
     .venv\Scripts\activate
     ```

   - On Unix or MacOS:

     ```bash
     source .venv/bin/activate
     ```

5. **Install the required dependencies**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To use the webapp, follow these steps:

1. **Start the application**

   ```bash
   python -m app
   ```

2. **Capture Image**

   - Press the `Capture` button within the webapp to take an image of the current frame.
   - The application will run YOLO inference on the captured image.
   - Results will be saved in the `outputs` folder.

## Contributing

Contributions are welcome! For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## To download image thru URL
   - Paste this URL /download_image/<int:image_id> after the http://127.0.0.1:5000.
   - Change the <int:image_id> with the appropriate ID number in the database using SQL Viewer.
   - Results will be saved in the ~/Downloads of your computer.

## To reset database
   - Paste this URL /reset_database after the http://127.0.0.1:5000.
   - Hit enter.
```
