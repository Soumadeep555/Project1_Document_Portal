import yaml

def load_config(config_path: str = "C:\\Users\\Support\\Documents\\Soumadeep_Local\\LLMOPs\\Project1_Document_Portal\\config\\config.yaml") -> dict:
    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)
    return config

