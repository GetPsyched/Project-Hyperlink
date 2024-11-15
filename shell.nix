{
  pkgs ? import <nixpkgs> { },
}:

pkgs.mkShellNoCC {
  nativeBuildInputs = with pkgs; [
    railway
    (python3.withPackages (
      py-pkgs: with py-pkgs; [
        asyncpg
        discordpy
        fluent-runtime
        fluent-pygments
        google-api-python-client
        google-auth-httplib2
        google-auth-oauthlib
        python-dotenv
        pytz
        tabulate
      ]
    ))
  ];
}
