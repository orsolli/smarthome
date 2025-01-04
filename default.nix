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
        default = 300;
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
        ExecStart = "${pkgs.callPackage ./read_waveplus {}}/bin/read_waveplus ${cfg.device} ${toString cfg.samplerate} ${cfg.database}";
        User = "airwave";
        Group = "airwave";
      };
    };

    systemd.services.airwave-web = {
      description = "Airwave Plus Web Service";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./web {}}/bin/start-server -w 1 -b 127.0.0.1:8000 app:app";
        User = "airwave";
        Group = "airwave";
      };
      environment = { DATABASE_PATH = cfg.database; };
    };

    users.groups.airwave = {};
    users.users.airwave = {
      isSystemUser = true;
      home = "/var/lib/airwave";
      group = "airwave";
    };

    #systemd.tmpfiles.rules = ["d /var/lib/airwave 1755 airwave airwave"];
  };
}