# Cell-DRL: AI agent reconstructs Intermediate paths from single-cell genomics data

<div style="text-align:center;">
  <img src="Cell-DRL_Architecture.png" alt="Cell-DRL Model Architecture" width="850"/>
</div>

**Cell-DRL**  is a deep reinforcement learning agent capable of reconstructing intermediate cellular states in health, disease, and regenerative processes. Cell-DRL's cellular state reconstruction is based on defining initial and target cellular states of interest from single-cell RNA-seq data.


## Installation

To set up Cell-DRL on your machine, follow these steps:

### System Dependencies

Before installing the Python package, install the required system libraries:

```bash
sudo apt-get update
sudo apt-get install libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev cmake
```

**On macOS:**
```bash
brew install sdl2 sdl2_image sdl2_mixer sdl2_ttf cmake
```

### Python Installation

1. **Download the package files:**

    - **Option 1: Using Git**
        ```bash
        git clone https://gitlab.com/ama.bioinfo/cell-drl.git
        ```

    - **Option 2: Downloading a ZIP file**
        If you prefer not to use Git, you can download a ZIP file of the repository. 


2. **Open your Terminal:**
    - On Windows, you can use Command Prompt or PowerShell.
    - On macOS or Linux, you can use the Terminal.


3. **Navigate to the project directory:**
    ```bash
    cd /path/to/your_project/celldrl_Dir/
    ```

4. **Install New Conda Environment:**
    ```bash
    conda create -n CellDRL_Env python=3.9
    conda activate CellDRL_Env 
    ```

5. **Install the required dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
   This command will automatically install all the necessary packages listed in the `requirements.txt` file. The `cmake` dependency is now included in the build system, so it will be installed automatically.

6. **Open your jupyterlab book:**
    ```bash
    jupyter lab
    ```

## Tutorial

Please open the [tutorial](./tutorial) folder to start running Cell-DRL agent [jupyter notebook](./tutorial/Cell-DRL_Tutorial_EMT_Ver_1.003.ipynb).
