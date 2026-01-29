#!/usr/bin/env python3
import os
from pathlib import Path

from springboot_generator.generator import (
    prompt_project_config,
    collect_all_modules,
    create_directory_structure,
    generate_main_application,
    generate_application_yml,
    generate_pom_xml,
    generate_gitignore,
    generate_readme,
    generate_swagger_config,
    generate_redoc_html,
    generate_dockerfile,
    generate_dockerignore,
    generate_docker_compose,
    generate_entity,
    generate_dto,
    generate_repository,
    generate_mapper,
    generate_service,
    generate_service_impl,
    generate_controller,
)


def main():
    print("\n🚀 Spring Boot Generator (PyPI Edition)")
    print("=" * 60)

    base_path = Path.cwd()

    config = prompt_project_config()
    modules = collect_all_modules()
    config["modules"] = modules

    print("\n📦 Génération du projet...")
    
    # Structure & core
    generate_main_application(base_path, config)
    generate_application_yml(base_path, config)
    generate_pom_xml(base_path, config)
    generate_gitignore(base_path)
    generate_readme(base_path, config)

    # Swagger
    generate_swagger_config(base_path, config)
    generate_redoc_html(base_path, config)

    # Docker
    generate_dockerfile(base_path, config)
    generate_dockerignore(base_path, config)
    generate_docker_compose(base_path, config)

    # Modules
    for module in modules:
        print(f"\n🔧 Module: {module['name']}")
        create_directory_structure(base_path, config["basePackage"], module)
        generate_entity(base_path, config["basePackage"], module)
        generate_dto(base_path, config["basePackage"], module, config)
        generate_repository(base_path, config["basePackage"], module)
        generate_mapper(base_path, config["basePackage"], module)
        generate_service(base_path, config["basePackage"], module)
        generate_service_impl(base_path, config["basePackage"], module)
        generate_controller(base_path, config["basePackage"], module, config)

    print("\n✅ Projet Spring Boot généré avec succès 🎉")
    print("📂 Dossier :", base_path)


if __name__ == "__main__":
    main()
