{
  description = "Sweetiebot XMPP chat bot";

  inputs.nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

  outputs =
    { self, nixpkgs }:
    let
      forAllSystems = nixpkgs.lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
      ];

      overlay = final: prev: {
        pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
          (pyFinal: pyPrev: {
            # used by modules/Experiments.py and modules/SweetieSeen.py; not in nixpkgs
            laboratory = pyFinal.buildPythonPackage rec {
              pname = "laboratory";
              version = "1.0.2";
              format = "wheel";
              src = final.fetchurl {
                url = "https://files.pythonhosted.org/packages/be/c4/915d8f1d7dcf6c055c70976e1b44d12fa4691cd2493b1474aca689d459d1/laboratory-1.0.2-py2.py3-none-any.whl";
                hash = "sha256-lQGvqFpCUuImmuftCK7e2NgO0N5WkbBil8qrHzC0Enc=";
              };
              dist = "py2.py3-none-any";
              python = "py2.py3";
            };

            # modules/SweetieMoon.py uses the `Astral` class dropped in astral>=2;
            # pinned to the version in Pipfile.lock instead of nixpkgs' current astral (3.x)
            astral = pyFinal.buildPythonPackage rec {
              pname = "astral";
              version = "1.6";
              format = "wheel";
              src = final.fetchurl {
                url = "https://files.pythonhosted.org/packages/5c/13/6f099c94ef58b154845a44830abe5eb213ce1ffba0e49c451f5620ba241a/astral-1.6-py2.py3-none-any.whl";
                hash = "sha256-zaVYFI1V0xAY571K0bZ5ArdkJvxP0aJh4kdcU/vqRSI=";
              };
              dist = "py2.py3-none-any";
              python = "py2.py3";
              propagatedBuildInputs = [ pyFinal.pytz ];
            };
          })
        ];
      };
    in
    {
      overlays.default = overlay;

      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system}.extend overlay;

          pythonEnv = pkgs.python3.withPackages (
            ps: with ps; [
              astral
              beautifulsoup4
              requests
              pytz
              redis
              psycopg2
              slixmpp
              laboratory
              # opencensus-ext-azure is currently broken in nixpkgs; Azure App
              # Insights logging (config.app_insights_key) is a soft
              # dependency guarded by a try/except in sweetiebot.py, so it's
              # left out here rather than pinned to a broken package.
            ]
          );

          sweetiebot = pkgs.stdenvNoCC.mkDerivation {
            pname = "sweetiebot";
            version = "9.1";
            src = ./.;

            dontBuild = true;
            dontConfigure = true;

            installPhase = ''
              mkdir -p $out/share/sweetiebot
              cp -r config.py modules utils sweetiebot.py sql $out/share/sweetiebot/

              mkdir -p $out/bin
              cat > $out/bin/sweetiebot <<EOF
              #!${pkgs.runtimeShell}
              exec ${pythonEnv}/bin/python $out/share/sweetiebot/sweetiebot.py "\$@"
              EOF
              chmod +x $out/bin/sweetiebot
            '';

            passthru = { inherit pythonEnv; };
          };
        in
        {
          inherit sweetiebot;
          default = sweetiebot;
        }
      );

      nixosModules.default =
        { config, lib, pkgs, ... }:
        let
          cfg = config.services.sweetiebot;
        in
        {
          options.services.sweetiebot = {
            enable = lib.mkEnableOption "Sweetiebot XMPP chat bot";

            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.stdenv.hostPlatform.system}.sweetiebot;
              description = "The sweetiebot package to run.";
            };

            environmentFile = lib.mkOption {
              type = lib.types.nullOr lib.types.path;
              default = null;
              description = ''
                Path to an EnvironmentFile containing the secrets sweetiebot needs
                (at minimum SB_JID, SB_PASSWORD, SB_PG_DB). This file is not managed
                by nix and should be kept out of the nix store, e.g. via sops-nix or
                agenix.
              '';
            };

            settings = lib.mkOption {
              type = lib.types.attrsOf lib.types.str;
              default = { };
              description = ''
                Non-secret environment variables (SB_CHATROOM, SB_NICKNAME,
                SB_HOSTNAME, SB_PORT, SB_DEBUG, ...) to pass to sweetiebot.
              '';
              example = {
                SB_CHATROOM = "some_room@conference.jabberserver";
                SB_NICKNAME = "Sweetiebot";
              };
            };
          };

          config = lib.mkIf cfg.enable {
            systemd.services.sweetiebot = {
              description = "Sweetiebot XMPP chat bot";
              after = [ "network-online.target" ];
              wants = [ "network-online.target" ];
              wantedBy = [ "multi-user.target" ];

              environment = cfg.settings;

              serviceConfig = {
                ExecStart = "${cfg.package}/bin/sweetiebot";
                EnvironmentFile = lib.mkIf (cfg.environmentFile != null) cfg.environmentFile;

                Restart = "on-failure";
                RestartSec = "5s";

                # sandboxing equivalent to running in an isolated container
                DynamicUser = true;
                PrivateTmp = true;
                PrivateDevices = true;
                PrivateNetwork = false; # needs to reach the jabber server and postgres
                ProtectSystem = "strict";
                ProtectHome = true;
                ProtectKernelTunables = true;
                ProtectKernelModules = true;
                ProtectKernelLogs = true;
                ProtectControlGroups = true;
                ProtectClock = true;
                ProtectHostname = true;
                ProtectProc = "invisible";
                ProcSubset = "pid";
                RestrictNamespaces = true;
                RestrictRealtime = true;
                RestrictSUIDSGID = true;
                LockPersonality = true;
                MemoryDenyWriteExecute = true;
                NoNewPrivileges = true;
                RemoveIPC = true;
                CapabilityBoundingSet = "";
                AmbientCapabilities = "";
                SystemCallFilter = [ "@system-service" ];
                SystemCallErrorNumber = "EPERM";
                RestrictAddressFamilies = [
                  "AF_UNIX"
                  "AF_INET"
                  "AF_INET6"
                ];
              };
            };
          };
        };
    };
}
