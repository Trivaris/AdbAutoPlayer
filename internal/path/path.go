package path

import (
	"fmt"
	"os"
	"path/filepath"
	stdruntime "runtime"
	"strings"
)

func GetFirstPathThatExists(paths []string) string {
	for _, path := range paths {
		if stat, _ := os.Stat(path); stat != nil {
			return path
		}
	}

	return ""
}

// ChangeWorkingDirForProd changes the working directory for production builds
func ChangeWorkingDirForProd() {
	execPath, err := os.Executable()
	if err != nil {
		panic(fmt.Sprintf("Unable to get executable path: %v", err))
	}

	execDir := filepath.Dir(execPath)
	if stdruntime.GOOS != "windows" && strings.Contains(execDir, "internal.app") {
		execDir = filepath.Dir(filepath.Dir(filepath.Dir(filepath.Dir(execPath)))) // Go outside the .app bundle
	}
	if err = os.Chdir(execDir); err != nil {
		panic(fmt.Sprintf("Failed to change working directory to %s: %v", execDir, err))
	}

	_, err = os.Getwd()
	if err != nil {
		panic(err)
	}
}

// expandUser replaces a leading "~" with the current user's home dir.
// If the path does not start with "~", it is returned unchanged.
func ExpandUser(path string) (string, error) {
	if path == "" || path[0] != '~' {
		return path, nil
	}

	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}

	if path == "~" {
		return home, nil
	}
	if strings.HasPrefix(path, "~/") {
		return filepath.Join(home, path[2:]), nil
	}

	// "~something" (like ~user) not handled here
	return path, nil
}
