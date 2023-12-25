import os

from decouple import Config, RepositoryEnv

app_profile = os.getenv('APP_PROFILE')
allowed_profiles = ['dev', 'stage', 'prod', 'test']
if app_profile not in allowed_profiles:
    raise RuntimeError("APP_PROFILE must have one of the following values: ", allowed_profiles)
print(f"Starting application using profile {app_profile}")
config = Config(RepositoryEnv(f".env.{app_profile}"))
