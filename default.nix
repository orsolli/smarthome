{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.smarthome;
in
{
  imports = [
    ./read_waveplus
    ./timeseries_plot
  ];

  options = {
    services.smarthome = {
      enable = mkOption {
        type = types.bool;
        default = false;
        description = "Enable the smarthome service.";
      };

      database = mkOption {
        type = types.str;
        default = "/var/lib/smarthome/smarthome.db";
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
    systemd.tmpfiles.rules = [
      "d /var/lib/smarthome 0775 smarthome smarthome"
    ];
    users.groups.smarthome = {};
    users.users.smarthome = {
      isSystemUser = true;
      home = "/var/lib/smarthome";
      group = "smarthome";
    };
  };
}