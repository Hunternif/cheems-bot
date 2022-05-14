import yaml

discord_token = ''

with open('config.yaml', 'r') as f:
    try:
        config = yaml.safe_load(f)
        discord_token = config['discord_token']
    except Exception as e:
        print(f"Couldn't read config.yaml. Caught {e}")