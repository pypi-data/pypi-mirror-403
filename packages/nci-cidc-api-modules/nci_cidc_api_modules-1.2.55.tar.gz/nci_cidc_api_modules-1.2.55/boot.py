from os import mkdir, path
import shutil
from flask_migrate import upgrade

TEMPLATES_DIR = path.join("/tmp", "templates")


def apply_migrations():
    from cidc_api.app import app

    with app.app_context():
        upgrade(app.config["MIGRATIONS_PATH"])


# set up the directories for holding generated templates
def set_up_templates_directories():
    if path.exists(TEMPLATES_DIR):
        shutil.rmtree(TEMPLATES_DIR)
    mkdir(TEMPLATES_DIR)
    for family in ["assays", "manifests", "analyses"]:
        family_dir = path.join(TEMPLATES_DIR, family)
        mkdir(family_dir)
