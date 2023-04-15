import io
import os
import shutil
def get_platform():
    """Gets platform name and checks if it is a raspberry pi

    Returns
    -------
    str, bool
        name of the platform on which the code is running, boolean that is true if the platform is a raspberry pi"""

    platform = 'unknown'
    on_pi = False
    try:
        with io.open('/sys/firmware/devicetree/base/model', 'r') as f:
            platform = f.read().lower()
        if 'raspberry pi' in platform:
            on_pi = True
    except FileNotFoundError:
        pass
    return platform, on_pi

def change_config(config_file, verbose=True):
    cwd = os.getcwd()
    try:
        shutil.copyfile(f'{cwd}/OhmPi/config.py', f'{cwd}/OhmPi/config_tmp.py')
        shutil.copyfile(f'{cwd}/OhmPi/{config_file}', f'{cwd}/OhmPi/config.py')
        if verbose:
            print(f'Changed to {cwd}/OhmPi/{config_file}:\n')
            with open(f'{cwd}/OhmPi/config.py', mode='r') as f:
                print(f.read())

    except Exception as error:
        print(f'Could not change config file to {cwd}/OhmPi/{config_file}:\n{error}')