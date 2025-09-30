self:
{
  config,
  pkgs,
  lib,
  ...
}:
let
  inherit (lib)
    mkEnableOption
    mkIf
    mkOption
    ;

  cfg = config.programs.adbautoplayer;
  tomlFormat = pkgs.formats.toml { };
  parseToml = path: builtins.fromTOML (builtins.readFile path);
  mkTomlOptionWithDefault =
    path:
    mkOption {
      inherit (tomlFormat) type;
      default = parseToml path;
    };
in
{
  options.programs.adbAutoPlayer = {
    enable = mkEnableOption "Wether to enable the AdbAutoPlayer Macro Program";
    settings = mkOption {
      inherit (tomlFormat) type;
      default = parseToml ./config/config.toml;
    };

    games = {
      afkJourney = mkTomlOptionWithDefault ./python/adb_auto_player/games/afk_journey/AfkJourney.toml;
      guitarGirl = mkTomlOptionWithDefault ./python/adb_auto_player/games/guitar_girl/GuitarGirl.toml;
    };

    config = mkIf cfg.enable {
      home = {
        packages = [ self.packages.${pkgs.system}.default ];
        file = {
          ".config/adb_auto_player/config.toml".text = tomlFormat.generate "config.toml" cfg.settings;

          ".config/adb_auto_player/games/afk_journey/AfkJourney.toml".text =
            tomlFormat.generate "AfkJourney.toml" cfg.games.afkJourney;

          ".config/adb_auto_player/games/guitar_girl/GuitarGirl.toml".text =
            tomlFormat.generate "GuitarGirl.toml" cfg.games.guitarGirl;
        };
      };
    };
  };
}
