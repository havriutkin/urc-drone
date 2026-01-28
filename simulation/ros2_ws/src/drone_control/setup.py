import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'drone_control'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
        (os.path.join('share', package_name, 'config'), glob(os.path.join('config', '*.yaml'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vladyslav Havriutkin',
    maintainer_email='havriutkin@gmail.com',
    description='High-level control nodes for the drone.',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'mission_manager_node = drone_control.mission_manager:main',
            'geolocation_node = drone_control.geolocation_node:main',
            'auto_collector_node = drone_control.auto_collector:main',
            'inference_node = drone_control.inference_node:main',
        ],
    },
)