{ config, lib, pkgs, ... }:

with lib;

let
  cfg = config.services.smarthome;
in
{
  options = {
    services.smarthome.vulnerabilities = {
      enable = mkOption {
        type = types.bool;
        default = cfg.enable;
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
        ExecStart = "${pkgs.callPackage ./vulnerabilities.nix {}}/bin/vuln-web";
        User = "smarthome";
        Group = "smarthome";
        Environment = "DATABASE_PATH=${cfg.vulnerabilities.databasePath}";
        Environment = "BIND_ADDRESS=${cfg.vulnerabilities.bindAddress}";
      };
    };

    systemd.timers.vulnerability-scan = {
      description = "Vulnerability Scanner Timer";
      wantedBy = [ "timers.target" ];

      serviceConfig = {
        ExecStart = "${pkgs.callPackage ./vulnerabilities.nix {}}/bin/vuln-scanner";
        User = "smarthome";
        Group = "smarthome";
        Environment = "DATABASE_PATH=${cfg.vulnerabilities.databasePath}";
        Environment = "VULNIX_PATH=${pkgs.vulnix}";
      };

      timerConfig = {
        OnBootSec = "5min";
        OnUnitActiveSec = "1h";
      };
    };
  };
}
