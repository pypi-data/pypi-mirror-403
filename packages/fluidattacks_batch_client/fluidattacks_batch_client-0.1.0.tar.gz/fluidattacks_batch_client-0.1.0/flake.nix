{
  description = "Utils for sending aws batch jobs";

  inputs = {
    observes_flake_builder = {
      url = "git+ssh://git@gitlab.com/fluidattacks/universe?shallow=1&rev=3fa54e41d48bd54a59a76f3b0495998663758538&dir=observes/common/std_flake_2";
    };
  };

  outputs =
    { self, ... }@inputs:
    let
      build_args =
        {
          system,
          python_version,
          nixpkgs,
          builders,
          scripts,
        }:
        import ./build {
          inherit nixpkgs builders scripts;
          src = import ./build/filter.nix nixpkgs.nix-filter self;
        };
    in
    {
      packages = inputs.observes_flake_builder.outputs.build build_args;
    };
}
