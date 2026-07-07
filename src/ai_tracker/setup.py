from setuptools import find_packages, setup

package_name = 'ai_tracker'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='puttidet_a',
    maintainer_email='puttidet_a@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'speed_detector = ai_tracker.speed_detect_node:main',
            'speed_subscriber = ai_tracker.speed_subscriber_node:main', # 🌟 เพิ่มบรรทัดนี้เข้าไป
        ],
    }
)
