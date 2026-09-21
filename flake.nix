{
  description = "Sweetiebot XMPP chat bot";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs =
    { self, nixpkgs, pyproject-nix, uv2nix, pyproject-build-systems, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs [
        "x86_64-linux"
        "aarch64-linux"
      ];

      # dependencies only: our own code isn't a uv-managed package, see
      # `tool.uv.package = false` in pyproject.toml
      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
      overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };

      pythonSets = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python311;
        in
        (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]
        )
      );
    in
    {
      packages = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system};
          venv = pythonSet.mkVirtualEnv "sweetiebot-env" workspace.deps.default;

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
              exec ${venv}/bin/python $out/share/sweetiebot/sweetiebot.py "\$@"
              EOF
              chmod +x $out/bin/sweetiebot
            '';

            passthru = { inherit venv; };
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
                SB_HOSTNAME, SB_PORT, SB_DEBUG, SB_APPINSIGHTS_KEY, ...) to pass
                to sweetiebot.
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
