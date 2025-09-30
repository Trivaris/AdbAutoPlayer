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
    recursiveUpdate
    ;

  cfg = config.programs.adbAutoPlayer;
  tomlFormat = pkgs.formats.toml { };
  parseToml = path: builtins.fromTOML (builtins.readFile path);
in
{
  options.programs.adbAutoPlayer = {
    enable = mkEnableOption "Wether to enable the AdbAutoPlayer Macro Program";
    settings = mkOption {
      inherit (tomlFormat) type;
      default = { };
    };

    games = {
      afkJourney = mkOption {
        inherit (tomlFormat) type;
        default = { };
      };

      guitarGirl = mkOption {
        inherit (tomlFormat) type;
        default = { };
      };
    };
  };

  config = mkIf cfg.enable {
    home = {
      packages = [ self.packages.${pkgs.system}.default ];
      file = {
        ".config/adb_auto_player/config.toml".text = tomlFormat.generate "config.toml" (
          recursiveUpdate (parseToml ./config/config.toml) cfg.settings
        );

        ".config/adb_auto_player/games/afk_journey/AfkJourney.toml".text =
          tomlFormat.generate "AfkJourney.toml" (
            recursiveUpdate (parseToml ./python/adb_auto_player/games/afk_journey/AfkJourney.toml) cfg.games.afkJourney
          );

        ".config/adb_auto_player/games/guitar_girl/GuitarGirl.toml".text =
          tomlFormat.generate "GuitarGirl.toml" (
            recursiveUpdate (parseToml ./python/adb_auto_player/games/afk_journey/AfkJourney.toml) cfg.games.guitarGirl
          );
      };
    };
  };
}
