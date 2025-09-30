{ pkgs, ... }:
let
  version = "10.0.9";
  py = pkgs.python313Packages;

  frontend = pkgs.buildNpmPackage {
    inherit version;
    pname = "adb-auto-player-frontend";
    src = ./frontend;
    npmDepsHash = "sha256-7Y3UOQ4uT2rcNXS2opoE3ZvH20k7vL3+sawZhBT75r4=";
    npmBuildScript = "build";

    installPhase = ''
      runHook preInstall
      mkdir -p $out/dist
      cp -R dist/. $out/dist
      runHook postInstall
    '';

    meta = {
      description = "AdbAutoPlayer svelte frontend";
      homepage = "https://github.com/AdbAutoPlayer/AdbAutoPlayer";
      license = pkgs.lib.licenses.mit;
      maintainers = [ pkgs.lib.maintainers.trivaris ];
    };
  };

  pythonBackend = py.buildPythonApplication {
    inherit version;
    pname = "adb-auto-player-backend";
    src = ./python;
    pyproject = true;
    doCheck = false;
    pythonImportsCheck = [ "adb_auto_player" ];

    propagatedBuildInputs = builtins.attrValues {
      inherit (py)
        anyio
        av
        adbutils
        colorama
        fastapi
        numpy
        opencv4
        pillow
        psutil
        pydantic
        pytesseract
        python-dotenv
        pyyaml
        requests
        starlette
        typing-extensions
        uvicorn
        uvloop
        websockets
        watchfiles
        httptools
        ;
    };

    nativeBuildInputs = [
      py.hatchling
      pkgs.makeWrapper
    ];

    pythonRemoveDeps = [
      "opencv-python"
      "uvicorn[standard]"
    ];

    makeWrapperArgs = [
      "--prefix" "PATH" ":" "${pkgs.android-tools}/bin:${pkgs.tesseract}/bin:${pkgs.ffmpeg}/bin"
    ];

    meta = {
      description = "AdbAutoPlayer python backend";
      homepage = "https://github.com/AdbAutoPlayer/AdbAutoPlayer";
      license = pkgs.lib.licenses.mit;
      maintainers = [ pkgs.lib.maintainers.trivaris ];
      mainProgram = "adb-auto-player";
    };
  };

  gui = pkgs.buildGo124Module {
    inherit version;
    pname = "adb-auto-player";
    src = ./.;
    subPackages = [ "." ];
    vendorHash = "sha256-fdhYlsUUg+LBhdvHKb1z1fdYago1biMh6VD/6OrPbxc=";
    env.CGO_ENABLED = "1";

    nativeBuildInputs = builtins.attrValues {
      inherit (pkgs) pkg-config makeWrapper;
    };

    buildInputs = builtins.attrValues {
      inherit (pkgs)
        gtk3
        webkitgtk_4_1
        glib
        gsettings-desktop-schemas
        libappindicator-gtk3
        libnotify
        ;
    };

    preBuild = ''
      rm -rf frontend/dist
      mkdir -p frontend
      cp -R ${frontend}/dist frontend/dist

      mkdir -p $out/share/adb_auto_player/templates/{afk_journey,guitar_girl}
      cp -R ${./python/adb_auto_player/games/afk_journey/templates}/. $out/share/adb_auto_player/templates/afk_journey/
      cp -R ${./python/adb_auto_player/games/guitar_girl/templates}/. $out/share/adb_auto_player/templates/guitar_girl/
    '';

    postInstall = ''
      mkdir -p $out/bin/binaries
      install -Dm755 ${pythonBackend}/bin/adb-auto-player $out/bin/binaries/adb_auto_player

      wrapProgram $out/bin/adb-auto-player \
        --prefix PATH : "${pkgs.uv}/bin" \
        --suffix PATH : "${pkgs.android-tools}/bin:${pkgs.tesseract}/bin:${pkgs.ffmpeg}/bin" \
        --suffix LD_LIBRARY_PATH : "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.libGL}/lib:${pkgs.glib.out}/lib" \
        --set ADB_AUTO_PLAYER_CONFIG_DIR "~/.config/adb_auto_player" \
        --set ADB_AUTO_PLAYER_TEMPLATE_DIR "$out/share/adb_auto_player/templates" \
        --set ADB_AUTO_PLAYER_DEBUG_DIR "~/.local/state/adb_auto_player/debug"
    '';

    postConfigure = ''
      chmod 777 vendor
      cp -a vendor/vendor/* vendor
    '';

    ldflags = [
      "-s"
      "-w"
      "-X 'main.Version=${version}'"
    ];

    buildFlagsArray = [
      "-trimpath"
      "-buildvcs=false"
    ];

    meta = {
      description = "AdbAutoPlayer desktop application";
      homepage = "https://github.com/AdbAutoPlayer/AdbAutoPlayer";
      license = pkgs.lib.licenses.mit;
      maintainers = [ pkgs.lib.maintainers.trivaris ];
      mainProgram = "adb-auto-player";
    };
  };

in
{
  inherit frontend;
  default = gui;
  desktop = gui;
  backend = pythonBackend;
}
