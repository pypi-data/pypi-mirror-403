from setuptools import setup, find_packages

setup(
    name="rpi_lcd_i2c",                     
    version="2.0.0",                  
    description="HD44780 I2C LCD driver for Raspberry Pi (Bookworm)",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Samarth Joneja",
    author_email="Samarth.Joneja@gmail.com",
    url="https://github.com/Sam67-coder/rpi-lcd-i2c",
    license="MIT",
    packages=find_packages(),
    install_requires=["smbus2"],
    python_requires=">=3.9",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: POSIX :: Linux",
        "Topic :: System :: Hardware",
    ],
)
