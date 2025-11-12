import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'drone_hardware'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*launch.[pxy][yma]*'))),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Vladyslav Havriutkin',
    maintainer_email='havriutkin@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': ['pytest'],
    },
    entry_points={
        'console_scripts': [
            'gimbal_bridge_sim = drone_hardware.gimbal_bridge_sim:main',
            'gimbal_bridge_real = drone_hardware.gimbal_bridge_real:main',
        ],
    },
)