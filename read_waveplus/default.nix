{ config, lib, pkgs, ... }:

with lib;

let
  default_cfg = config.services.smarthome;
  cfg = config.services.airwave;
in
{
  options = {
    services.airwave = {
      enable = mkOption {
        type = types.bool;
        default = default_cfg.enable;
        description = "Enable the Airwave Plus data collection service.";
      };

      device = mkOption {
        type = types.str;
        description = "The serial number or MAC address of the Airwave Plus device.";
      };

      samplerate = mkOption {
        type = types.int;
        default = 300;
        description = "The sample rate in seconds.";
      };

      database = mkOption {
        type = types.str;
        default = default_cfg.database;
        description = "Path to the SQLite database.";
      };
    };
  };

  config = mkIf cfg.enable {
    systemd.services.airwave = {
      description = "Airwave Plus Data Collection Service";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./read_waveplus.nix {}}/bin/read_waveplus ${cfg.device} ${toString cfg.samplerate} ${cfg.database}";
        User = "smarthome";
        Group = "smarthome";
      };
    };
  };
}