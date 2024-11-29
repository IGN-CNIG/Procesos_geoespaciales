import subprocess
import sys
import os

def install_wheel(wheel_file):
    '''
    Installs a given .whl (wheel) file using pip.
    
    Args:
        wheel_file (str): The path to the wheel file (.whl) to be installed.
    
    Raises:
        subprocess.CalledProcessError: If the wheel installation fails.
    '''
    if os.path.exists(wheel_file):
        try:
            print(f'Installing wheel from {wheel_file}...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', wheel_file])
            print('Wheel installation complete.')
        except subprocess.CalledProcessError as e:
            print(f'Failed to install wheel from {wheel_file}. Error: {e}')
            raise
    else:
        print(f'Wheel file {wheel_file} does not exist.')
        raise FileNotFoundError(f'{wheel_file} not found.')

def install_requirements(requirements_file='requirements.txt'):
    '''
    Installs all packages listed in the given requirements file using pip.
    
    Args:
        requirements_file (str): The path to the requirements.txt file.
                                 Defaults to 'requirements.txt'.
    
    Raises:
        subprocess.CalledProcessError: If the installation fails.
    '''
    if os.path.exists(requirements_file):
        try:
            print(f'Installing packages from {requirements_file}...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', requirements_file])
            print('Installation complete.')
        except subprocess.CalledProcessError as e:
            print(f'Failed to install requirements from {requirements_file}. Error: {e}')
            raise
    else:
        print(f'Requirements file {requirements_file} does not exist.')
        raise FileNotFoundError(f'{requirements_file} not found.')

# Example usage:
if __name__ == '__main__':
    wheel_file = 'GDAL-3.4.3-cp311-cp311-win_amd64.whl'  # Replace with your .whl file
    requirements_file = 'requirements.txt'  # Replace with the path to your requirements.txt
    
    try:
        # Install the wheel file first
        install_wheel(wheel_file)
        
        # Install requirements after the wheel installation
        install_requirements(requirements_file)
        
    except Exception as e:
        print(f'An error occurred: {e}')
