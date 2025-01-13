# AdbAutoPlayer

## [Click Here to Access the Full Documentation and Usage Details](https://yulesxoxo.github.io/AdbAutoPlayer/)
![gui.png](docs/src/images/app/app.png)

## Supported Games
- AFK Journey

```shell
pyinstaller --onefile adb_auto_player/main.py
```

## Windows Native Setup
1. Install [Python](https://www.python.org/downloads/)
2. Install [Poetry](https://python-poetry.org/docs/#installing-with-the-official-installer)
3. Create virtualenv and install
   ```shell
   poetry shell
   poetry install
   poetry run pre-commit install
   ```

## MacOS Setup
1. Install [Python](https://formulae.brew.sh/formula/python@3.12)
2. Install [Poetry](https://python-poetry.org/docs/#installing-with-pipx)
3. Install [Adb](https://formulae.brew.sh/cask/android-platform-tools)
4. Create virtualenv and install
   ```shell
   poetry shell
   poetry install
   poetry run pre-commit install
   ```

## Build
```shell
poetry run nuitka --standalone --onefile --output-filename=adb_auto_player.exe --assume-yes-for-downloads --windows-console-mode=disable adb_auto_player/main.py 
```

## Contact
[Discord](https://discord.com/users/518169167048998913)
