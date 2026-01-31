from setuptools import setup, find_packages

# Nom du package PyPI ('pip install NAME')
NAME = "aait"

# Version du package PyPI
VERSION = "2.3.15.996"  # la version doit être supérieure à la précédente sinon la publication sera refusée

# Facultatif / Adaptable à souhait
AUTHOR = "Orange community"
AUTHOR_EMAIL = ""
URL = ""
DESCRIPTION = "Advanced Artificial Intelligence Tools is a package meant to develop and enable advanced AI functionalities in Orange"
LICENSE = ""

# 'orange3 add-on' permet de rendre l'addon téléchargeable via l'interface addons d'Orange
KEYWORDS = ["orange3 add-on",]

# Tous les packages python existants dans le projet (avec un __ini__.py)
PACKAGES = find_packages()
PACKAGES = [pack for pack in PACKAGES if "AAIT" in pack]
PACKAGES.append("orangecontrib")
print(PACKAGES)



# Fichiers additionnels aux fichiers .py (comme les icons ou des .ows)
PACKAGE_DATA = {
    "orangecontrib.AAIT.widgets": ["icons/*", "designer/*"],
    "orangecontrib.AAIT.llm": ["resources/*"],
    "orangecontrib.AAIT.utils.tools": ["owcorpus_ok.txt"],
    "orangecontrib.AAIT.audit_widget": ["dataTests/*"],
}
# /!\ les noms de fichier 'orangecontrib.hkh_bot.widgets' doivent correspondre à l'arborescence

# Dépendances

INSTALL_REQUIRES = [
    "torch",
    "sentence-transformers",
    "gpt4all[all]",
    "sacremoses",
    "transformers",
    "sentencepiece",
    "optuna",
    "spacy",
    "markdown",
    "python-multipart",
    "PyMuPDF",
    "chonkie",
    "GPUtil",
    "unidecode",
    "python-docx",
    "psutil",
    "thefuzz",
    "beautifulsoup4",
    "rank_bm25",
    "CATEGORIT"]


# Spécifie le dossier contenant les widgets et le nom de section qu'aura l'addon sur Orange
ENTRY_POINTS = {
    "orange.widgets": (
        "Advanced Artificial Intelligence Tools = orangecontrib.AAIT.widgets",
        "AAIT - API = orangecontrib.API.widgets",
        "AAIT - MODELS = orangecontrib.LLM_MODELS.widgets",
        "AAIT - LLM INTEGRATION = orangecontrib.LLM_INTEGRATION.widgets",
        "AAIT - TOOLBOX = orangecontrib.TOOLBOX.widgets",
        "AAIT - ALGORITHM = orangecontrib.ALGORITHM.widgets",
    )
}
# /!\ les noms de fichier 'orangecontrib.hkh_bot.widgets' doivent correspondre à l'arborescence

NAMESPACE_PACKAGES = ["orangecontrib"]

setup(name=NAME,
      version=VERSION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      url=URL,
      description=DESCRIPTION,
      license=LICENSE,
      keywords=KEYWORDS,
      packages=PACKAGES,
      package_data=PACKAGE_DATA,
      install_requires=INSTALL_REQUIRES,
      entry_points=ENTRY_POINTS,
      namespace_packages=NAMESPACE_PACKAGES,
      )
