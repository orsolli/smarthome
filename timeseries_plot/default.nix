{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.smarthome;
in
{
  options = {
    services.smarthome.timeseries_plot = {
      enable = mkOption {
        type = types.bool;
        default = cfg.enable;
        description = "Enable the smarthome service.";
      };

      database = mkOption {
        type = types.str;
        default = cfg.database;
        description = "Path to the SQLite database.";
      };

      bind = mkOption {
        type = types.str;
        default = "127.0.0.1:8000";
        description = "Bind address for the web server.";
      };
    };
  };

  config = mkIf cfg.enable {
    systemd.services.airwave-web = {
      description = "Airwave Plus Web Service";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./timeseries_plot.nix {}}/bin/start-server -w 1 -b ${cfg.timeseries_plot.bind} app:app";
        User = "smarthome";
        Group = "smarthome";
      };
      environment = { DATABASE_PATH = cfg.database; };
    };
  };
}