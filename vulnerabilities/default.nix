{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.smarthome;
  scanner = pkgs.callPackage ./vulnerabilities.nix { };
in
{
  options = {
    services.smarthome.vulnerabilities = {
      enable = mkOption {
        type = types.bool;
        default = false;
        description = "Enable the vulnerability scanner service.";
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

  config = mkIf cfg.vulnerabilities.enable {
    systemd.services.vulnerability-web = {
      description = "Vulnerability Scanner Web API";
      after = [ "network.target" ];
      wantedBy = [ "multi-user.target" ];

      serviceConfig = {
        ExecStart = "${scanner}/bin/vuln-web";
        User = "smarthome";
        Group = "smarthome";
      };

      environment = {
        DATABASE_PATH = cfg.vulnerabilities.databasePath;
        BIND_ADDRESS = cfg.vulnerabilities.bindAddress;
      };
    };

    # The scan is a service: a timer only schedules it, it has no
    # serviceConfig of its own.
    systemd.services.vulnerability-scan = {
      description = "Vulnerability Scanner";
      after = [ "network.target" "systemd-tmpfiles-setup.service" ];

      serviceConfig = {
        ExecStart = "${scanner}/bin/vuln-scanner";
        User = "smarthome";
        Group = "smarthome";
      };

      environment = {
        DATABASE_PATH = cfg.vulnerabilities.databasePath;
        VULNIX_PATH = "${pkgs.vulnix}/bin/vulnix";
      };
    };

    systemd.timers.vulnerability-scan = {
      description = "Vulnerability Scanner Timer";
      wantedBy = [ "timers.target" ];

      timerConfig = {
        Unit = "vulnerability-scan.service";
        OnBootSec = "5min";
        OnUnitActiveSec = "1h";
      };
    };
  };
}
