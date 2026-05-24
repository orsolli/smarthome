{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.smarthome;
in
{
  options = {
    services.smarthome.storage = {
      enable = mkOption {
        type = types.bool;
        default = false;
        description = "Enable the storage scanner service.";
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

  config = mkIf cfg.storage.enable {
    systemd.services.storage-web = {
      description = "Storage Scanner Web API";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./storage.nix {}}/bin/storage-web";
        User = "smarthome";
        Group = "smarthome";
      };

      environment = {
        DATABASE_PATH = "${cfg.storage.database}";
        BIND_ADDRESS = "${cfg.storage.bind}";
      };
    };

    systemd.services.storage-scan = {
      description = "Storage Scanner Service";
      after = [ "systemd-tmpfiles-setup.service" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./storage.nix {}}/bin/storage-scanner";
        User = "smarthome";
        Group = "smarthome";
      };

      environment = {
        DATABASE_PATH = "${cfg.storage.database}";
      };
    };

    systemd.timers.storage-scan = {
      description = "Storage Scanner Timer";
      wantedBy = [ "timers.target" ];

      timerConfig = {
        Unit = "storage-scan.service";
        OnBootSec = "5min"; # Start 5 minutes after boot
        OnUnitActiveSec = "1h"; # Run every hour after the last execution finishes
      };
    };
  };
}
