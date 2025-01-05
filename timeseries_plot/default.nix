{ config, lib, pkgs, ... }:

with lib;

let
  default_cfg = config.services.smarthome;
  cfg = config.services.timeseries_plot;
in
{
  options = {
    services.timeseries_plot = {
      enable = mkOption {
        type = types.bool;
        default = default_cfg.enable;
        description = "Enable the smarthome service.";
      };

      database = mkOption {
        type = types.str;
        default = default_cfg.database;
        description = "Path to the SQLite database.";
      };

      bind = mkOption {
        type = types.str;
        default = default_cfg.bind;
        description = "Bind address for the web server.";
      };
    };
  };

  config = mkIf cfg.enable {
    services.airwave.enable = true;

    systemd.services.airwave-web = {
      description = "Airwave Plus Web Service";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./timeseries_plot.nix {}}/bin/start-server -w 1 -b ${cfg.bind} app:app";
        User = "smarthome";
        Group = "smarthome";
      };
      environment = { DATABASE_PATH = cfg.database; };
    };
  };
}