## Usage
In order to use the scripts listed here, follow these directions carefully.
**This project is only supported for Windows users only right now, more features will be comming to Mac.**
### Download repository
To download all necessary files and dependencies, click the green 'Code' button and choose 'Download ZIP' in the dropdown. Open the download location then extract all of the files using Windows' built-in utility or utilities such as 7-Zip or WinRAR.
### Get python 
Open Windows PowerShell. Simply launch the application by searching for it in the search bar.
In the window, type `python` (without the quotation marks). This should launch Microsoft Store. (If you do not wish to use the Microsoft Store, you may also download and install python from its official website, python.org.) In this window, you will have to press 'Get' in order to download python. This step is crucial as python is essential for running scripts. Wait for the installer to finish, then proceed. You may close this window. **If you already have python for other reasons, you can skip this step, but your version might be outdated so best redownload it.**
### Get Pip
Pip is the package manager for python. This is crucial for installing and managing the modules 'keyboard' and 'micromelon' in order to control the robot. Install python by navigating to the extracted repository folder, either by going into File Explorer, navigating to the folder that contains the file 'get-pip.py', or using CLI commands. If you are using File Explorer, right click on any empty space inside the folder, then select 'Open in Terminal'. In this PowerShell window, type in `python get-pip.py`. Wait for the command to finish running. This will install pip, the package manager for python. 
### Install dependencies
For drive.py and sim.py, you will need `micromelon` and `keyboard`. Install these by typing in the terminal (Windows PowerShell) `python -m pip install micromelon keyboard`. This will install the dependencies required to run these scripts.
### Run script
If you do these steps correctly, you should be able to navigate to the folder containing your desired script, such as drive.py, then in the right click menu, choose Open in Terminal. Then run the script by typing `python [script].py` and replace [script] with your script name, such as `python drive.py`. Congratulations, and enjoy!
