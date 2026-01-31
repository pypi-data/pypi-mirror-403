from setuptools import setup, find_packages

setup(
    name="iflow-mcp-nikoko107-mcp-datagouv-ign",
    version="0.1.1",
    description="Serveur MCP complet pour data.gouv.fr + 4 APIs nationales françaises",
    py_modules=["french_opendata_complete_mcp", "ign_geo_services"],
    install_requires=[
        "mcp>=1.0.0",
        "httpx>=0.27.0",
    ],
    entry_points={
        "console_scripts": [
            "french-opendata-complete-mcp=french_opendata_complete_mcp:main",
        ],
    },
    python_requires=">=3.8",
)