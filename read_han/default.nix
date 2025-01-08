{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.smarthome;
in
{
  options = {
    services.smarthome.han = {
      enable = mkOption {
        type = types.bool;
        default = cfg.enable;
        description = "Enable the HAN data collection service.";
      };

      database = mkOption {
        type = types.str;
        default = cfg.database;
        description = "Path to the SQLite database.";
      };
    };
  };

  config = mkIf cfg.han.enable {
    systemd.services.read_han = {
      description = "HAN Data Collection Service";
      after = [ "local-fs.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./read_han.nix {}}/bin/read_han ${cfg.han.database}";
        User = "smarthome-han";
        Group = "smarthome";
      };
    };

    users.users.smarthome-han = {
      isSystemUser = true;
      group = "smarthome";
      extraGroups = [ "dialout" ];
    };
    services.udev.extraRules = ''
      KERNEL=="ttyUSB0", \
        ENV{MANAGER_USER_WANTS}+="read_han.service", \
        ENV{SYSTEMD_USER_WANTS}+="read_han.service", \
        ENV{SYSTEMD_WANTS}+="read_han.service"
    '';
  };
}