{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable-small";
    pythonOverlays.url = "github:Trivaris/TrivnixOverlays";
  };

  outputs =
    {
      self,
      nixpkgs,
      pythonOverlays,
    }:
    let
      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "x86_64-darwin"
        "aarch64-darwin"
      ];

      overlays = [
        pythonOverlays.overlays.python
      ];

      forAllSystems =
        func:
        nixpkgs.lib.genAttrs systems (system: func system (import nixpkgs { inherit system overlays; }));
    in
    {
      homeModules.default = import ./modules.nix self;
      packages = forAllSystems (system: pkgs: import ./packages.nix { inherit self pkgs system; });

      devShells = forAllSystems (system: pkgs:
        {
          default = pkgs.mkShell {
            packages = builtins.attrValues {
              inherit (pkgs.python313Packages)
                python
                hatchling
                ruff
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
                nuitka
                pytest
                pytest-cov
              ;

              inherit (pkgs)
                uv
                go
                nodejs
                pre-commit
                android-tools
                tesseract
                ffmpeg
                commitizen
                pkg-config
                makeWrapper
                gtk3
                webkitgtk_4_1
                glib
                gsettings-desktop-schemas
                libappindicator-gtk3
                libnotify
                ;
            };
          };
        });
    };
}
