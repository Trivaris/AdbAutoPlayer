package settings

import (
	"adb-auto-player/internal/app"
	"adb-auto-player/internal/event_names"
	"adb-auto-player/internal/ipc"
	"adb-auto-player/internal/logger"
	"github.com/wailsapp/wails/v3/pkg/application"
	"os"
	"path/filepath"
	"runtime"
	"sync"
)

var (
	instance *SettingsService
	once     sync.Once
)

type SettingsService struct {
	generalSettings     GeneralSettings
	generalSettingsPath *string
	mu                  sync.RWMutex
}

// GetService returns the singleton instance of SettingsService
func GetService() *SettingsService {
	generalSettingsPath := resolveGeneralSettingsPath()
	once.Do(func() {
		instance = &SettingsService{
			generalSettingsPath: &generalSettingsPath,
			generalSettings:     loadGeneralSettingsOrDefault(&generalSettingsPath),
		}
	})
	return instance
}

// LoadGeneralSettings reloads the general settings
func (s *SettingsService) LoadGeneralSettings() GeneralSettings {
	s.mu.Lock()
	generalSettings := loadGeneralSettingsOrDefault(s.generalSettingsPath)
	s.generalSettings = generalSettings
	s.mu.Unlock()
	updateLogLevel(generalSettings.Logging.Level)
	return generalSettings
}

// GetGeneralSettings returns the current general settings
func (s *SettingsService) GetGeneralSettings() GeneralSettings {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return s.generalSettings
}

func (s *SettingsService) GetGeneralSettingsForm() map[string]interface{} {
	generalSettings := s.LoadGeneralSettings()

	response := map[string]interface{}{
		"settings":    generalSettings,
		"constraints": ipc.GetMainConfigConstraints(),
	}
	return response
}

func (s *SettingsService) SaveGeneralSettings(settings GeneralSettings) error {
	s.mu.Lock()
	if err := SaveTOML[GeneralSettings](*s.generalSettingsPath, &settings); err != nil {
		s.mu.Unlock()
		app.Error(err.Error())
		return err
	}

	old := s.generalSettings.Advanced
	if old.AutoPlayerHost != settings.Advanced.AutoPlayerHost || old.AutoPlayerPort != settings.Advanced.AutoPlayerPort {
		app.Emit(event_names.ServerAddressChanged)
	}

	s.generalSettings = settings
	updateLogLevel(s.generalSettings.Logging.Level)
	s.mu.Unlock()

	if settings.UI.NotificationsEnabled && runtime.GOOS != "windows" {
		logger.Get().Warningf("Setting: 'Enable Notifications' only works on Windows")
	}
	if settings.UI.CloseShouldMinimize && runtime.GOOS != "windows" {
		logger.Get().Warningf("Setting: 'Close button should minimize the window' only works on Windows")
	}

	app.EmitEvent(&application.CustomEvent{Name: event_names.GeneralSettingsUpdated, Data: settings})
	logger.Get().Infof("Saved General Settings")
	return nil
}

func updateLogLevel(logLevel string) {
	logger.Get().SetLogLevelFromString(logLevel)
}

func loadGeneralSettingsOrDefault(tomlPath *string) GeneralSettings {
	generalSettings := NewGeneralSettings()

	if tomlPath != nil {
		loadedSettings, err := LoadGeneralSettings(*tomlPath)
		if err != nil {
			app.Error(err.Error())
		} else {
			generalSettings = *loadedSettings
			updateLogLevel(generalSettings.Logging.Level)
		}
	}

	return generalSettings
}

func resolveGeneralSettingsPath() string {
	path := filepath.Join(ConfigDir(), "config.toml")
	logger.Get().Debugf("Resolved general settings path: %s", path)
	return path
}

func resolveConfigDir() string {
	return configDirForOS(runtime.GOOS, getUserHomeDir(), os.Getenv("APPDATA"))
}

// ConfigDir returns the absolute directory for shared configuration files.
func ConfigDir() string {
	dir := resolveConfigDir()
	logger.Get().Debugf("Resolved config directory: %s", dir)
	if err := os.MkdirAll(dir, 0755); err != nil {
		logger.Get().Debugf("Unable to ensure config directory exists: %v", err)
	}
	return dir
}

// GamesDir returns the absolute directory that should contain game configs.
func GamesDir() string {
	gamesDir := filepath.Join(ConfigDir(), "games")
	logger.Get().Debugf("Resolved games directory: %s", gamesDir)
	if err := os.MkdirAll(gamesDir, 0755); err != nil {
		logger.Get().Debugf("Unable to ensure games directory exists: %v", err)
	}
	return gamesDir
}

func getUserHomeDir() string {
	home, err := os.UserHomeDir()
	if err != nil || home == "" {
		return os.TempDir()
	}
	return home
}

func configDirForOS(goos string, home string, appdata string) string {
	switch goos {
	case "linux":
		return filepath.Join(home, ".config", "adbautoplayer")
	case "windows":
		base := appdata
		if base == "" {
			base = filepath.Join(home, "AppData", "Roaming")
		}
		return filepath.Join(base, "AdbAutoPlayer")
	case "darwin":
		return filepath.Join(home, "Library", "Application Support", "AdbAutoPlayer")
	default:
		return filepath.Join(home, ".adbautoplayer")
	}
}
