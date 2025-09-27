package games

import (
	"adb-auto-player/internal/app"
	"adb-auto-player/internal/event_names"
	"adb-auto-player/internal/ipc"
	"adb-auto-player/internal/logger"
	"adb-auto-player/internal/process"
	"adb-auto-player/internal/settings"
	"archive/zip"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	stdruntime "runtime"
	"sync"
)

type GamesService struct {
	mu                     sync.Mutex
	gameGUI                *ipc.GameGUI
	lastOpenGameConfigPath string
}

func (g *GamesService) GetGameGUI() (*ipc.GameGUI, error) {
	if err := g.resolvePythonBinaryPathIfNeeded(); err != nil {
		return nil, err
	}

	logMessages, err := process.GetService().POSTCommand([]string{"DisplayGUI"})
	if err != nil {
		return nil, err
	}

	var gameGUI ipc.GameGUI

	if len(logMessages) == 0 {
		return nil, errors.New("empty Response from Python")
	}

	last := logMessages[len(logMessages)-1]
	if last.Level == "ERROR" {
		return nil, errors.New(last.Message)
	}

	err = json.Unmarshal([]byte(last.Message), &gameGUI)
	if err != nil {
		println(last.Message)
		println(err.Error())
		return nil, err
	}

	g.mu.Lock()
	g.gameGUI = &gameGUI
	result := g.gameGUI
	g.mu.Unlock()

	return result, nil
}

func (g *GamesService) Debug() error {
	if err := g.resolvePythonBinaryPathIfNeeded(); err != nil {
		return err
	}
	if err := process.GetService().StartTask([]string{"Debug"}, false, 2); err != nil {
		logger.Get().Errorf("Failed starting process: %v", err)
		return err
	}
	return nil
}

func (g *GamesService) SaveDebugZip() {
	const debugDir = "debug"

	var zipPath string
	if stdruntime.GOOS == "darwin" {
		cwd, err := os.Getwd()
		if err != nil {
			log.Fatalf("failed to get current directory: %v", err)
		}

		parentDir := filepath.Clean(filepath.Join(cwd, "..", "..", ".."))
		zipPath = filepath.Join(parentDir, "debug.zip")
	} else {
		zipPath = "debug.zip"

	}

	if _, err := os.Stat(debugDir); os.IsNotExist(err) {
		logger.Get().Errorf("debug directory does not exist")
		return
	}

	zipFile, err := os.Create(zipPath)
	if err != nil {
		logger.Get().Errorf("%s", fmt.Errorf("failed to create zip file: %w", err))
		return
	}
	defer func(zipFile *os.File) {
		err = zipFile.Close()
		if err != nil {
			logger.Get().Errorf("%s", fmt.Errorf("%w", err))
		}
	}(zipFile)

	zipWriter := zip.NewWriter(zipFile)
	defer func(zipWriter *zip.Writer) {
		err = zipWriter.Close()
		if err != nil {
			logger.Get().Errorf("%s", fmt.Errorf("%w", err))
		}
	}(zipWriter)

	err = filepath.Walk(debugDir, func(filePath string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if info.IsDir() {
			return nil
		}

		relPath, err := filepath.Rel(debugDir, filePath)
		if err != nil {
			return err
		}

		zipEntry, err := zipWriter.Create(relPath)
		if err != nil {
			return err
		}

		file, err := os.Open(filePath)
		if err != nil {
			return err
		}
		defer func(file *os.File) {
			err = file.Close()
			if err != nil {
				logger.Get().Errorf("%s", fmt.Errorf("%w", err))
			}
		}(file)

		_, err = io.Copy(zipEntry, file)
		return err
	})

	if err != nil {
		logger.Get().Errorf("%s", fmt.Errorf("failed to create zip archive: %w", err))
		return
	}

	logger.Get().Infof("debug.zip saved")
}

func (g *GamesService) StartGameProcess(args []string) error {
	if err := process.GetService().StartTask(args, true); err != nil {
		logger.Get().Errorf("Failed starting process: %v", err)
		return err
	}
	return nil
}

func (g *GamesService) KillGameProcess() {
	process.GetService().StopTask()
}

func (g *GamesService) resolvePythonBinaryPathIfNeeded() error {
	if process.GetService().GetPythonBinaryPath() == "" {
		err := g.setPythonBinaryPath()
		if err != nil {
			logger.Get().Errorf("Error resolving python binary path: %v", err)
			return err
		}
	}

	return nil
}

func (g *GamesService) setPythonBinaryPath() error {
	workingDir, err := os.Getwd()
	if err != nil {
		return err
	}


	if override := os.Getenv("ADB_AUTOPLAYER_PYTHON_DIR"); override != "" {
		if stat, statErr := os.Stat(override); statErr == nil && stat.IsDir() {
			process.GetService().SetPythonBinaryPath(override)
			return nil
		}
	}

	if process.GetService().IsDev {
		pythonPath := filepath.Join(workingDir, "python")
		process.GetService().SetPythonBinaryPath(pythonPath)
		return nil
	}

	executable := "adb_auto_player.exe"
	if stdruntime.GOOS != "windows" {
		executable = "adb_auto_player"
	}

	if stdruntime.GOOS == "darwin" {
		process.GetService().SetPythonBinaryPath(filepath.Join(workingDir, "../Resources/binaries", executable))
	} else {
		process.GetService().SetPythonBinaryPath(filepath.Join(workingDir, "binaries", executable))
	}
	return nil
}

func resolveGameConfigPathForLogging(rawPath string) string {
	if rawPath == "" {
		return ""
	}

	normalized := filepath.FromSlash(rawPath)
	if filepath.IsAbs(normalized) {
		logger.Get().Debugf("Game config path already absolute: %s", normalized)
		return filepath.Clean(normalized)
	}

	gamesDir := settings.GamesDir()
	candidates := []string{filepath.Join(gamesDir, normalized)}

	if absPath, err := filepath.Abs(normalized); err == nil {
		candidates = append(candidates, absPath)
	}

	candidates = append(candidates, normalized)

	for _, candidate := range candidates {
		if _, err := os.Stat(candidate); err == nil {
			logger.Get().Debugf("Resolved game config path for %s -> %s", rawPath, candidate)
			return filepath.Clean(candidate)
		}
	}

	cleaned := filepath.Clean(candidates[0])
	logger.Get().Debugf("Using default game config path for %s -> %s", rawPath, cleaned)
	return cleaned
}

func (g *GamesService) GetGameSettingsForm(game ipc.GameGUI) (map[string]interface{}, error) {
	var gameConfig interface{}
	var err error

	gamesDir := settings.GamesDir()
	configPath := filepath.Join(gamesDir, game.ConfigPath)
	logger.Get().Debugf("Resolved config path for game %s -> %s", game.GameTitle, configPath)

	if err := os.MkdirAll(filepath.Dir(configPath), 0755); err != nil {
		logger.Get().Errorf("Failed to create game config directory: %v", err)
		return nil, err
	}

	g.mu.Lock()
	g.lastOpenGameConfigPath = configPath
	g.mu.Unlock()

	if _, statErr := os.Stat(configPath); errors.Is(statErr, os.ErrNotExist) {
		response := map[string]interface{}{
			"settings":    map[string]interface{}{},
			"constraints": game.Constraints,
		}
		logger.Get().Debugf("Game config file does not exist; returning empty settings for %s", configPath)
		return response, nil
	} else if statErr != nil {
		logger.Get().Errorf("Failed to access game config: %v", statErr)
		return nil, statErr
	}

	gameConfig, err = settings.LoadTOML[map[string]interface{}](configPath)
	if err != nil {
		logger.Get().Errorf("Failed to load game config %s: %v", configPath, err)
		return nil, err
	}

	logger.Get().Debugf("Loaded game config %s successfully", configPath)

	response := map[string]interface{}{
		"settings":    gameConfig,
		"constraints": game.Constraints,
	}
	return response, nil
}

func (g *GamesService) SaveGameSettings(gameSettings map[string]interface{}) (*ipc.GameGUI, error) {
	g.mu.Lock()
	defer app.Emit(event_names.GameSettingsUpdated)
	defer g.mu.Unlock()

	if g.lastOpenGameConfigPath == "" || nil == g.gameGUI {
		return nil, errors.New("cannot save game settings: no game settings found")
	}

	if err := settings.SaveTOML[map[string]interface{}](g.lastOpenGameConfigPath, &gameSettings); err != nil {
		return nil, err
	}
	logger.Get().Infof("Saving Game Settings")

	g.lastOpenGameConfigPath = ""

	displayNames := make(map[string]string)
	for key, value := range gameSettings {
		if nestedMap, ok := value.(map[string]interface{}); ok {
			if displayName, okDN := nestedMap["Display Name"].(string); okDN {
				displayNames[key] = displayName
			}
		}
	}

	for i, option := range g.gameGUI.MenuOptions {
		if displayName, exists := displayNames[option.Label]; exists {
			g.gameGUI.MenuOptions[i].CustomLabel = displayName
		}
	}

	return g.gameGUI, nil
}
