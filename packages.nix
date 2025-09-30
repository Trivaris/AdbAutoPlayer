{ pkgs, ... }:
let
  version = "10.0.9";
  py = pkgs.python313Packages;

  frontend = pkgs.buildNpmPackage {
    inherit version;
    pname = "adb-auto-player-frontend";
    src = ./frontend;
    npmDepsHash = "sha256-pGjIbco+VPdmNC7Cj0NU3r9ITQJD7mPqlG80iZU3vjc=";
    npmBuildScript = "build";

    installPhase = ''
      runHook preInstall
      mkdir -p $out/dist
      cp -R dist/. $out/dist
      runHook postInstall
    '';
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

    postInstall = ''
      wrapProgram $out/bin/adb-auto-player \
        --prefix PATH : "${pkgs.android-tools}/bin:${pkgs.tesseract}/bin:${pkgs.ffmpeg}/bin"
    '';
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

      mkdir -p $out/bin/games/{afk_journey,guitar_girl}/templates
      cp -R ${./python/adb_auto_player/games/afk_journey/templates}/. $out/bin/games/afk_journey/templates
      cp -R ${./python/adb_auto_player/games/guitar_girl/templates}/. $out/bin/games/guitar_girl/templates
    '';

    postInstall = ''
      mkdir -p $out/bin/binaries
      install -Dm755 ${pythonBackend}/bin/adb-auto-player $out/bin/binaries/adb_auto_player

      wrapProgram $out/bin/adb-auto-player \
        --prefix PATH : "${pkgs.uv}/bin" \
        --suffix PATH : "${pkgs.android-tools}/bin:${pkgs.tesseract}/bin:${pkgs.ffmpeg}/bin" \
        --set WEBKIT_DISABLE_DMABUF_RENDERER 1 \
        --suffix LD_LIBRARY_PATH : "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.libGL}/lib:${pkgs.glib.out}/lib"
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
