{
  nixpkgs,
  builders,
  scripts,
  src,
}:
{
  inherit src;
  root_path = "observes/common/connection-manager";
  module_name = "fluidattacks_connection_manager";
  pypi_token_var = "CONNECTION_MANAGER_TOKEN";
  override = b: b;
}
