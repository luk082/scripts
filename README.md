
# MicroMelon Rover Scripts
## Usage
Follow these steps carefully to set up and use the scripts in this repository.  
> **Note:** Currently supported on **Windows only**. Mac support is planned for the future.
### 1. Download the repository
1. Click the green **Code** button on this page.  
2. Choose **Download ZIP** from the dropdown.  
3. Extract the files using Windows' built-in utility, 7-Zip, or WinRAR.
### 2. Install Python
1. Open **Windows PowerShell** (search for it in the Start menu).  
2. Type:
   ```powershell
   python
   ```
* If Python is not installed, this may open the Microsoft Store.
* You can also download Python directly from the official website: [python.org](https://www.python.org/downloads/).
3. Install the latest version and wait for the setup to finish.
   > If you already have Python installed, you can skip this step, but we recommend updating to the latest version.
### 3. Install Pip
Pip is Python’s package manager, needed for installing extra libraries.
1. In File Explorer, navigate to the folder containing the file `get-pip.py` (included in this repository).
2. Right-click inside the folder and choose **Open in Terminal**.
3. Run:
   ```powershell
   python get-pip.py
   ```
4. Wait for the installation to complete.
### 4. Install Dependencies
The scripts require [`micromelon`](https://pypi.org/project/micromelon/) and [`keyboard`](https://pypi.org/project/keyboard/).
Install them by running:
```powershell
python -m pip install micromelon keyboard
```
### 5. Run a Script
1. Navigate to the folder containing the script you want to run (e.g., `drive.py` or `sim.py`).
2. Right-click in the folder and choose **Open in Terminal**.
3. Run the script with:
   ```powershell
   python drive.py
   ```
   Replace `drive.py` with any other script name (e.g., `sim.py`).
## Congratulations 🎉
If everything is installed correctly, your MicroMelon rover should now be ready to connect and run with these scripts.
