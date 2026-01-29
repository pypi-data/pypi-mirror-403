"""Setup configuration for agent-flight-recorder package."""

from setuptools import find_packages, setup


with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="agent-flight-recorder",
    version="0.2.0",
    author="0xdivin3",
    author_email="chukwuebukawilliams6@gmail.com",
    description="Debug AI Agents without burning money",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/0xdivin3/agent-flight-recorder",
    packages=find_packages(include=["agent_flight_recorder", "agent_flight_recorder.*"]),
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
    ],
    entry_points={
        "console_scripts": [
            "afr=agent_flight_recorder.cli:main",
        ],
    },
)