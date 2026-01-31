{
  nixpkgs,
  builders,
  scripts,
  src,
}:
{
  inherit src;
  root_path = "observes/common/etl-utils";
  module_name = "fluidattacks_etl_utils";
  pypi_token_var = "ETL_UTILS_TOKEN";
  override = b: b;
}
