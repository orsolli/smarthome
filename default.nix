{ config, lib, ... }:

with lib;

let
  cfg = config.services.smarthome;
in
{
  imports = [
    ./read_waveplus
    ./timeseries_plot
    ./read_han
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
    };
  };

  config = mkIf cfg.enable {
    systemd.tmpfiles.rules = [
      "d /var/lib/smarthome 0775 smarthome smarthome"
      "f ${cfg.database} 0664 smarthome smarthome"
    ];
    users.groups.smarthome = {};
    users.users.smarthome = {
      isSystemUser = true;
      home = "/var/lib/smarthome";
      group = "smarthome";
    };
  };
}