package settings

import (
	"github.com/stretchr/testify/assert"
	"os"
	"path/filepath"
	"testing"
)

func TestLoadConfig(t *testing.T) {
	tempDir := t.TempDir()
	configPath := filepath.Join(tempDir, "config.toml")
	configContent := []byte(`[device]
ID = "127.0.0.1:7555"
`)

	if err := os.WriteFile(configPath, configContent, 0644); err != nil {
		t.Fatalf("failed to write temp config: %v", err)
	}

	mainConfig, err := LoadTOML[GeneralSettings](configPath)
	if err != nil {
		t.Errorf("[Error LoadTOML()] %v", err)
		return
	}
	assert.Equal(t, "127.0.0.1:7555", mainConfig.Device.ID)
}

func TestSaveConfig(t *testing.T) {
	testFilePath := filepath.Join(t.TempDir(), "test_config.toml")

	mainConfig := NewGeneralSettings()

	if err := SaveTOML[GeneralSettings](testFilePath, &mainConfig); err != nil {
		t.Errorf("[Error SaveTOML()] %v", err)
		return
	}

	if _, err := os.Stat(testFilePath); os.IsNotExist(err) {
		t.Errorf("[Error] File does not exist after SaveTOML")
		return
	}
}
