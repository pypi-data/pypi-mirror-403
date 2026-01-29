# Use image for running Python 3.13 applications
FROM python:3.13-slim

# Setting working directory inside the container
WORKDIR /gonzo_card_games

# Do a local install of gonzo_card_games package
COPY pyproject.toml .
COPY LICENSE . 
COPY README.md . 
COPY src/ .
RUN python -m pip install . 

# Copy card games runner script to be ran in container
COPY DockerCardGamesRunner.py . 

# Launch Card Games Runner
CMD ["python", "DockerCardGamesRunner.py"]