{
  nixpkgs,
  builders,
  scripts,
  src,
}:
{
  inherit src;
  root_path = "observes/common/batch-client";
  module_name = "fluidattacks_batch_client";
  pypi_token_var = "BATCH_CLIENT_TOKEN";
  override = b: b;
}
