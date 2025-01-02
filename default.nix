{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.airwave;
in
{
  options = {
    services.airwave = {
      enable = mkOption {
        type = types.bool;
        default = false;
        description = "Enable the Airwave Plus data collection service.";
      };

      device = mkOption {
        type = types.str;
        description = "The serial number or MAC address of the Airwave Plus device.";
      };

      samplerate = mkOption {
        type = types.int;
        default = 60;
        description = "The sample rate in seconds.";
      };

      database = mkOption {
        type = types.str;
        default = "/var/lib/airwave/airwave.db";
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
        User = "airwave";
        Group = "airwave";
      };
    };

    users.groups.airwave = {};
    users.users.airwave = {
      isSystemUser = true;
      home = "/var/lib/airwave";
      createHome = true;
      group = "airwave";
    };
  };
}