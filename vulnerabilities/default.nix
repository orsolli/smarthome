{ config, pkgs, lib }:

module "vulnerabilities" {
  # Options
  option = {
    enable = lib.mkOption {
      type = lib.types.bool;
      default = false;
      description = "Enable the smarthome vulnerability scanner.";
    };
    databasePath = lib.mkOption {
      type = lib.types.string;
      default = "/var/lib/smarthome/vulnerabilities.sqlite";
      description = "Path to the SQLite database file.";
    };
    bindAddress = lib.mkOption {
      type = lib.types.string;
      default = "0.0.0.0:8000";
      description = "Address and port for the web server.";
    };
  };

  # Services
  localOverlays = {
    # Enables the primary service logic
    "vulnerability-scan" = {
      services.writeable.services.systemd.systemd.systemd-local.writeable.services.systemd.systemd-local.services.vulnerability-scan = {
        description = "Smart Home Vulnerability Scan Runner";
        # Assuming a mechanism to run the scan periodically, here mocked as a timer/service pair
        # In a real system, this would be a systemd timer.
      };
    };

    # Exposes the web server
    "vulnerability-web" = {
      services.writeable.services.systemd.systemd-local.writeable.services.systemd.systemd-local.services.vulnerability-web = {
        description = "Smart Home Vulnerability Web API";
        # Command to run the app.py using the built Python package
        serviceConfig = {
          ExecStart = "${pkgs.poetry}/bin/poetry run python -m vulnerabilities.app:main";
          Restart = "on-failure";
          StandardOutput = "journal";
          StandardError = "journal";
        };
      };
    };
  };
}