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
        default = cfg.enable;
        description = "Enable the storage scanner service.";
      };

      databasePath = mkOption {
        type = types.str;
        default = cfg.database;
        description = "Path to the SQLite database.";
      };

      bindAddress = mkOption {
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
        Environment = {
          DATABASE_PATH = cfg.storage.databasePath;
          BIND_ADDRESS = cfg.storage.bindAddress;
        };
      };
    };

    systemd.timers.storage-scan = {
      description = "Storage Scanner Timer";
      wantedBy = [ "timers.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./storage.nix {}}/bin/storage-scanner";
        User = "smarthome";
        Group = "smarthome";
        Environment = {
          DATABASE_PATH = cfg.storage.databasePath;
          DF_PATH = "${pkgs.coreutils}/bin/df";
        };
      };

      timerConfig = {
        OnBootSec = "5min"; # Start 5 minutes after boot
        OnUnitActiveSec = "1h"; # Run every hour after the last execution finishes
      };
    };
  };
}
