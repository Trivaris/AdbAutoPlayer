{
  description = "AdbAutoPlayer GUI build";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05-small";

  outputs =
    { self, nixpkgs }:
    let
      system = "x86_64-linux";
      pkgs = import nixpkgs { inherit system; };
      lib = pkgs.lib;
    in
    {
      overlays.default = final: prev: { adbAutoPlayer = self.packages.${system}.adbAutoPlayer; };
      
      apps.${system}.default = {
        inherit (self.packages.${system}.adbAutoPlayer) meta;
        type = "app";
        program = "${self.packages.${system}.adbAutoPlayer}/bin/adb-auto-player";
      };

      packages.${system} = {
        default = self.packages.${system}.adbAutoPlayer;

        adbAutoPlayer = pkgs.buildGoModule {
          pname = "adb-auto-player";
          version = "10.0.9-dev";
          src = ./.;
          subPackages = [ "." ];
          vendorHash = "sha256-L0ufF3QoMpuEijo7zcuG53r5/6gsdEEIlZDbZXBLWaE=";
          env.CGO_ENABLED = "1";

          nativeBuildInputs = [
            pkgs.pkg-config
            pkgs.wrapGAppsHook3
            pkgs.makeWrapper
          ];

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
            cp -R ${self.packages.${system}.frontend}/dist frontend/dist
          '';

          postInstall = ''
            mkdir -p $out/share
            cp -r --no-preserve=mode ${./python} $out/share/python
            rm -rf $out/share/python/.venv

            wrapProgram $out/bin/adb-auto-player \
              --prefix PATH : ${pkgs.uv}/bin \
              --set WEBKIT_DISABLE_DMABUF_RENDERER 1 \
              --set ADB_AUTOPLAYER_FORCE_DEV 1 \
              --set LD_LIBRARY_PATH "${pkgs.stdenv.cc.cc.lib}/lib:${pkgs.libGL}/lib:${pkgs.glib.out}/lib:\$LD_LIBRARY_PATH"
          '';

          ldflags = [
            "-s"
            "-w"
            "-X main.Version=${self.shortRev or "dev"}"
          ];

          buildFlagsArray = [
            "-trimpath"
            "-buildvcs=false"
          ];

          meta = {
            description = "AdbAutoPlayer desktop application";
            homepage = "https://github.com/AdbAutoPlayer/AdbAutoPlayer";
            license = lib.licenses.mit;
            maintainers = [ lib.maintainers.trivaris ];
            mainProgram = "adb-auto-player";
          };
        };

        frontend = pkgs.buildNpmPackage {
          pname = "adbautoplayer-frontend";
          version = "10.0.9-dev";
          src = ./frontend;
          npmDepsHash = "sha256-pGjIbco+VPdmNC7Cj0NU3r9ITQJD7mPqlG80iZU3vjc=";
          npmBuildScript = "build";
          installPhase = ''
            mkdir -p $out
            cp -R dist $out/dist
          '';
        };
      };
    };
}
