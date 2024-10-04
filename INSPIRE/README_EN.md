# Project Documentation


## Table of Contents
- [Inspire Module Documentation](documentation/INSPIRE_EN)
- [Capabilities Module Documentation](documentation/CAPABILITIES_EN)
- [Database Module Documentation](documentation/DATABASE_EN)
- [Logging Module Documentation](documentation/LOGGING_EN)
- [Reports Module Documentation](documentation/REPORTS_EN)

## Requirements

-   Python 3.11
-   `pip` must be installed and available in the Python environment.

## Installation Instructions

To set up this project, you need to clone it and install the necessary dependencies. Follow the steps below:

### 1. Clone the Repository

First, clone the repository to your local machine:

```bash
git clone https://github.com/username/your_project.git
cd your_project
```

### 2. Create a Virtual Environment (Optional but Recommended)
-   **Using `venv`**:
    
    -   Create an isolated Python virtual environment.
    -   Activate it based on your operating system.
    -   Use the provided script to install GDAL and other dependencies.
-   **Using Conda**:
    
    -   Create and activate a Conda environment.
    -   Install dependencies directly from the `environment.yaml` file for easy environment setup.

This ensures your project remains modular and replicable across systems, making it easier to manage dependencies and avoid conflicts.

---
#### **2.1. Python Virtual Environment**

**Step 1: Create a Virtual Environment**

To create a virtual environment named `venv`, run the following command:

```bash
python -m venv venv
```

**Step 2: Activate the Virtual Environment**
  - On Windows:
```bash
.\venv\Scripts\activate.bat
```
  - On macOS/Linux:
```bash
source venv/bin/activate.bat
```

**Step 3: Install GDAL and Other Packages**

This script installs the GDAL package through a Python wheel file (`.whl`) followed by the packages listed in the `requirements.txt` file using `pip`. It automates the process of installing a wheel file first and then running the `pip install -r requirements.txt` command directly from a Python script.

```bash
python install_requirements.py
```

*How the Script Works*:

- The script uses the `subprocess` module to invoke the `pip` installation process for both the wheel file and the packages listed in the `requirements.txt`.
- If the wheel file is not found, the script will stop with an error.
- After the wheel file is successfully installed, the script installs the packages from the `requirements.txt`.

*Features*:

- **Wheel File Installation**: The script can install a specified wheel file before installing other packages.
- **Error Handling**: If the wheel or package installation fails, the script catches the error and displays a relevant message.
- **Custom File Paths**: By default, the script looks for `GDAL-3.4.3-cp311-cp311-win_amd64.whl` and `requirements.txt` in the same directory. You can modify this behavior by passing custom file paths.

---
#### **2.2. Conda Environment**

An alternative to using `venv` is to create a Conda environment. Conda manages both dependencies and the Python interpreter itself, making it a convenient tool for project environments.

**Step 1: Create a Conda Environment**

To create a new Conda environment with Python 3.11, run:

```bash
conda create --name <env_name> python=3.11
```

Replace `<env_name>` with the desired name for your environment.

**Step 2: Activate the Conda Environment**

Once the environment is created, activate it by running:

```bash
conda activate <env_name>
```

When the environment is activated, its name will appear in your terminal prompt, and you can install packages and dependencies within this isolated environment.

 **Step 3: Installing Dependencies from `environment.yaml`**

To share or replicate the environment setup on another machine, you can use the `environment.yaml` file to install all necessary dependencies with a single command. This ensures consistency across different environments.

To install the environment from the `environment.yaml` file:

```bash
conda env create -f environment.yaml
```

This will create the environment with the specified dependencies.

**Step 4: Activate the Recreated Environment**

After the environment is created, activate it as follows:

```bash
conda activate <env_name>
```

In most cases, the name of the environment is included in the `environment.yaml` file (e.g., `Inspire_ENV`).



## Running Examples
To run the examples provided in this project, use the following command structure:

```bash
python -m examples.<example_name>
```

#### Example
To run a specific example, for instance, `WCS_IGN.py`, execute:

```bash
python -m examples.WCS_IGN
```

### Debugging Examples
If you want to debug the examples instead of running them normally, consider using a debugger in your IDE or inserting `pdb.set_trace()` in the script where you want to pause execution.

### Important Notes
Ensure that the virtual environment is activated before running the examples to avoid any dependency issues.
Make sure to replace `<example_name>` with the actual name of the example script you wish to run.