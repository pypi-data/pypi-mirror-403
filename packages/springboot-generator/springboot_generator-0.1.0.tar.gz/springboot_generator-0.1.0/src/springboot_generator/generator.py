#!/usr/bin/env python3
"""
Générateur Spring Boot Interactif
Permet de créer des projets Spring Boot avec modules personnalisés
"""

from logging import config
import os
import json
from pathlib import Path
from typing import Dict, List, Optional


# ============================================================================
# NOUVELLES MÉTHODES - CONFIGURATION INTERACTIVE
# ============================================================================

def prompt_project_config() -> Dict:
    """
    Collecte interactivement la configuration du projet Spring Boot.
    Appelée une seule fois au démarrage.
    """
    print("\n" + "="*60)
    print("CONFIGURATION DU PROJET SPRING BOOT")
    print("="*60)
    
    # Package de base
    base_package = input("\n📦 Package de base (ex: com.example.demo): ").strip()
    while not base_package or not is_valid_package(base_package):
        print("❌ Package invalide. Utilisez le format: com.example.demo")
        base_package = input("📦 Package de base: ").strip()
    
    # Version Java
    print("\n☕ Version Java:")
    print("  1. Java 17")
    print("  2. Java 21")
    java_choice = input("Votre choix (1-2): ").strip()
    java_version = "17" if java_choice == "1" else "21"
    
    # Base de données
    print("\n🗄️  Base de données:")
    print("  1. PostgreSQL")
    print("  2. MySQL")
    print("  3. MariaDB")
    print("  4. H2 (mémoire)")
    db_choice = input("Votre choix (1-4): ").strip()
    db_map = {"1": "postgresql", "2": "mysql", "3": "mariadb", "4": "h2"}
    database = db_map.get(db_choice, "postgresql")
    
    # Docker
    docker = input("\n🐳 Activer Docker ? (y/n): ").strip().lower() == 'y'
    
    # Swagger/Redoc Documentation
    swagger = input("\n📚 Activer Swagger/Redoc Documentation ? (y/n): ").strip().lower() == 'y'
    
    config = {
        "basePackage": base_package,
        "javaVersion": java_version,
        "database": database,
        "docker": docker,
        "swagger": swagger,
        "modules": []
    }
    config['projet_name'] = config['basePackage']
    
    print("\n✅ Configuration enregistrée:")
    print(f"   Package: {base_package}")
    print(f"   Java: {java_version}")
    print(f"   Database: {database}")
    print(f"   Docker: {'Oui' if docker else 'Non'}")
    print(f"   Swagger/Redoc: {'Oui' if swagger else 'Non'}")
    
    return config


def prompt_module_creation() -> Optional[Dict]:
    """
    Demande interactivement la création d'un module.
    Retourne None si l'utilisateur ne veut plus créer de module.
    """
    print("\n" + "-"*60)
    create = input("Créer un nouveau module ? (y/n): ").strip().lower()
    
    if create != 'y':
        return None
    
    module_name = input("📝 Nom du module (ex: user): ").strip().lower()
    while not module_name or not module_name.isidentifier():
        print("❌ Nom invalide. Utilisez uniquement lettres, chiffres et underscore")
        module_name = input("📝 Nom du module: ").strip().lower()
    
    # Sélection des packages
    print(f"\n📂 Packages à générer pour le module '{module_name}':")
    available_packages = [
        "controller",
        "service",
        "serviceImpl",
        "repository",
        "dto",
        "entity",
        "mapper"
    ]
    
    selected_packages = []
    for pkg in available_packages:
        choice = input(f"  ➤ {pkg} ? (y/n): ").strip().lower()
        if choice == 'y':
            selected_packages.append(pkg)
    
    if not selected_packages:
        print("⚠️  Aucun package sélectionné, module ignoré")
        return None
    
    print(f"\n✅ Module '{module_name}' configuré avec: {', '.join(selected_packages)}")
    
    return {
        "name": module_name,
        "packages": selected_packages
    }


def is_valid_package(package: str) -> bool:
    """Valide le format d'un package Java."""
    parts = package.split('.')
    return len(parts) >= 2 and all(p.isidentifier() for p in parts)


def collect_all_modules() -> List[Dict]:
    """
    Boucle de collecte de tous les modules via interaction CLI.
    """
    modules = []
    
    while True:
        module = prompt_module_creation()
        if module is None:
            break
        modules.append(module)
    
    return modules


# ============================================================================
# MÉTHODES EXISTANTES - GÉNÉRATION DE FICHIERS
# ============================================================================

def create_directory_structure(base_path: str, package: str, module: Dict):
    """
    Crée la structure de répertoires pour un module donné.
    Méthode existante adaptée pour supporter les packages conditionnels.
    """
    package_path = package.replace('.', '/')
    selected_packages = module.get('packages', [])
    
    # Mapping des packages vers leurs chemins
    package_dirs = {
        'controller': f'{module["name"]}/controller',
        'service': f'{module["name"]}/service',
        'serviceImpl': f'{module["name"]}/service/impl',
        'repository': f'{module["name"]}/repository',
        'dto': f'{module["name"]}/dto',
        'entity': f'{module["name"]}/entity',
        'mapper': f'{module["name"]}/mapper'
    }
    
    # Créer uniquement les packages sélectionnés
    for pkg_name, pkg_path in package_dirs.items():
        if pkg_name in selected_packages:
            full_path = os.path.join(base_path, 'src/main/java', package_path, pkg_path)
            os.makedirs(full_path, exist_ok=True)
            print(f"  📁 {pkg_path}")


def generate_entity(base_path: str, package: str, module: Dict):
    """Génere la classe Entity JPA."""
    if 'entity' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    entity_content = f"""package {package}.{module_name}.entity;

import jakarta.persistence.*;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.time.LocalDateTime;

@Entity
@Table(name = "{module_name}s")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class {class_name} {{

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false)
    private String name;

    @Column(name = "created_at", updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at")
    private LocalDateTime updatedAt;

    @PrePersist
    protected void onCreate() {{
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }}

    @PreUpdate
    protected void onUpdate() {{
        updatedAt = LocalDateTime.now();
    }}
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path, 
                             module_name, 'entity', f'{class_name}.java')
    with open(file_path, 'w') as f:
        f.write(entity_content)


def generate_dto(base_path: str, package: str, module: Dict, config: Dict):
    """Génere les classes DTO."""
    if 'dto' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    # Annotations Swagger si activé
    swagger_imports = ""
    schema_annotation = ""
    if config.get('swagger', False):
        swagger_imports = """import io.swagger.v3.oas.annotations.media.Schema;
"""
        schema_annotation = f"""
    @Schema(description = "Identifiant unique")
    private Long id;

    @Schema(description = "Nom du {module_name}")
    private String name;

    @Schema(description = "Date et heure de création")
    private LocalDateTime createdAt;

    @Schema(description = "Date et heure de derniere modification")"""
    
    dto_content = f"""package {package}.{module_name}.dto;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import lombok.Builder;
{swagger_imports}
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
@Schema(description = "{class_name} Data Transfer Object")
public class {class_name}DTO {{
{schema_annotation if config.get('swagger', False) else "    private Long id;\n    private String name;\n    private LocalDateTime createdAt;"}
    private LocalDateTime updatedAt;
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path,
                             module_name, 'dto', f'{class_name}DTO.java')
    with open(file_path, 'w') as f:
        f.write(dto_content)


def generate_repository(base_path: str, package: str, module: Dict):
    """Génere l'interface Repository Spring Data JPA."""
    if 'repository' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    repo_content = f"""package {package}.{module_name}.repository;

import {package}.{module_name}.entity.{class_name};
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;

@Repository
public interface {class_name}Repository extends JpaRepository<{class_name}, Long> {{

    Optional<{class_name}> findByName(String name);
    
    boolean existsByName(String name);
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path,
                             module_name, 'repository', f'{class_name}Repository.java')
    with open(file_path, 'w') as f:
        f.write(repo_content)


def generate_mapper(base_path: str, package: str, module: Dict):
    """Génere le Mapper Entity <-> DTO."""
    if 'mapper' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    mapper_content = f"""package {package}.{module_name}.mapper;

import {package}.{module_name}.entity.{class_name};
import {package}.{module_name}.dto.{class_name}DTO;
import org.springframework.stereotype.Component;

@Component
public class {class_name}Mapper {{

    public {class_name}DTO toDTO({class_name} entity) {{
        if (entity == null) return null;
        
        return {class_name}DTO.builder()
                .id(entity.getId())
                .name(entity.getName())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .build();
    }}

    public {class_name} toEntity({class_name}DTO dto) {{
        if (dto == null) return null;
        
        {class_name} entity = new {class_name}();
        entity.setId(dto.getId());
        entity.setName(dto.getName());
        return entity;
    }}
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path,
                             module_name, 'mapper', f'{class_name}Mapper.java')
    with open(file_path, 'w') as f:
        f.write(mapper_content)


def generate_service(base_path: str, package: str, module: Dict):
    """Génere l'interface Service."""
    if 'service' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    service_content = f"""package {package}.{module_name}.service;

import {package}.{module_name}.dto.{class_name}DTO;

import java.util.List;
import java.util.Optional;

public interface {class_name}Service {{

    {class_name}DTO create({class_name}DTO dto);
    
    Optional<{class_name}DTO> findById(Long id);
    
    List<{class_name}DTO> findAll();
    
    {class_name}DTO update(Long id, {class_name}DTO dto);
    
    void deleteById(Long id);
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path,
                             module_name, 'service', f'{class_name}Service.java')
    with open(file_path, 'w') as f:
        f.write(service_content)


def generate_service_impl(base_path: str, package: str, module: Dict):
    """Génere l'implémentation du Service."""
    if 'serviceImpl' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    impl_content = f"""package {package}.{module_name}.service.impl;

import {package}.{module_name}.dto.{class_name}DTO;
import {package}.{module_name}.entity.{class_name};
import {package}.{module_name}.mapper.{class_name}Mapper;
import {package}.{module_name}.repository.{class_name}Repository;
import {package}.{module_name}.service.{class_name}Service;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Optional;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional
public class {class_name}ServiceImpl implements {class_name}Service {{

    private final {class_name}Repository repository;
    private final {class_name}Mapper mapper;

    @Override
    public {class_name}DTO create({class_name}DTO dto) {{
        {class_name} entity = mapper.toEntity(dto);
        {class_name} saved = repository.save(entity);
        return mapper.toDTO(saved);
    }}

    @Override
    @Transactional(readOnly = true)
    public Optional<{class_name}DTO> findById(Long id) {{
        return repository.findById(id)
                .map(mapper::toDTO);
    }}

    @Override
    @Transactional(readOnly = true)
    public List<{class_name}DTO> findAll() {{
        return repository.findAll().stream()
                .map(mapper::toDTO)
                .collect(Collectors.toList());
    }}

    @Override
    public {class_name}DTO update(Long id, {class_name}DTO dto) {{
        {class_name} entity = repository.findById(id)
                .orElseThrow(() -> new RuntimeException("{class_name} not found"));
        
        entity.setName(dto.getName());
        {class_name} updated = repository.save(entity);
        return mapper.toDTO(updated);
    }}

    @Override
    public void deleteById(Long id) {{
        repository.deleteById(id);
    }}
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path,
                             module_name, 'service/impl', f'{class_name}ServiceImpl.java')
    with open(file_path, 'w') as f:
        f.write(impl_content)


def generate_controller(base_path: str, package: str, module: Dict, config: Dict):
    """Génere le Controller REST."""
    if 'controller' not in module.get('packages', []):
        return
    
    module_name = module['name']
    class_name = module_name.capitalize()
    package_path = package.replace('.', '/')
    
    # Imports supplémentaires si Swagger est activé
    swagger_imports = ""
    swagger_annotations = ""
    if config.get('swagger', False):
        swagger_imports = """import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.media.Content;
import io.swagger.v3.oas.annotations.media.Schema;
"""
        swagger_annotations = f"""
@Tag(name = "{class_name}", description = "API pour la gestion des {module_name}s")"""
    
    controller_content = f"""package {package}.{module_name}.controller;

import {package}.{module_name}.dto.{class_name}DTO;
import {package}.{module_name}.service.{class_name}Service;

import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
{swagger_imports}
import java.util.List;

@RestController
@RequestMapping("/api/{module_name}s")
@RequiredArgsConstructor{swagger_annotations}
public class {class_name}Controller {{

    private final {class_name}Service service;

    @PostMapping
    @Operation(
        summary = "Créer un nouveau {module_name}",
        description = "Crée un nouvel enregistrement {module_name} et retourne l'objet créé"
    )
    @ApiResponse(responseCode = "201", description = "{class_name} créé avec succes")
    @ApiResponse(responseCode = "400", description = "Données invalides")
    public ResponseEntity<{class_name}DTO> create(@RequestBody {class_name}DTO dto) {{
        {class_name}DTO created = service.create(dto);
        return ResponseEntity.status(HttpStatus.CREATED).body(created);
    }}

    @GetMapping("/{{id}}")
    @Operation(
        summary = "Obtenir un {module_name} par ID",
        description = "Récupere un {module_name} spécifique par son identifiant"
    )
    @ApiResponse(responseCode = "200", description = "{class_name} trouvé")
    @ApiResponse(responseCode = "404", description = "{class_name} non trouvé")
    public ResponseEntity<{class_name}DTO> findById(
            @Parameter(description = "ID du {module_name}")
            @PathVariable Long id) {{
        return service.findById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }}

    @GetMapping
    @Operation(
        summary = "Lister tous les {module_name}s",
        description = "Récupere la liste complete de tous les {module_name}s"
    )
    @ApiResponse(responseCode = "200", description = "Liste des {module_name}s")
    public ResponseEntity<List<{class_name}DTO>> findAll() {{
        List<{class_name}DTO> list = service.findAll();
        return ResponseEntity.ok(list);
    }}

    @PutMapping("/{{id}}")
    @Operation(
        summary = "Mettre à jour un {module_name}",
        description = "Met à jour un {module_name} existant"
    )
    @ApiResponse(responseCode = "200", description = "{class_name} mis à jour avec succes")
    @ApiResponse(responseCode = "404", description = "{class_name} non trouvé")
    public ResponseEntity<{class_name}DTO> update(
            @Parameter(description = "ID du {module_name}")
            @PathVariable Long id, 
            @RequestBody {class_name}DTO dto) {{
        {class_name}DTO updated = service.update(id, dto);
        return ResponseEntity.ok(updated);
    }}

    @DeleteMapping("/{{id}}")
    @Operation(
        summary = "Supprimer un {module_name}",
        description = "Supprime un {module_name} par son identifiant"
    )
    @ApiResponse(responseCode = "204", description = "{class_name} supprimé avec succes")
    @ApiResponse(responseCode = "404", description = "{class_name} non trouvé")
    public ResponseEntity<Void> delete(
            @Parameter(description = "ID du {module_name}")
            @PathVariable Long id) {{
        service.deleteById(id);
        return ResponseEntity.noContent().build();
    }}
}}
"""
    
    file_path = os.path.join(base_path, 'src/main/java', package_path,
                             module_name, 'controller', f'{class_name}Controller.java')
    with open(file_path, 'w') as f:
        f.write(controller_content)


# ============================================================================
# NOUVELLES MÉTHODES - GÉNÉRATION FICHIERS TECHNIQUES
# ============================================================================

def generate_application_yml(base_path: str, config: Dict):
    """
    Génère le fichier application.yml avec configuration datasource.
    MODIFIÉ: Configuration Springdoc simplifiée sans redoc.*
    """
    database = config['database']
    
    # Configuration selon la base de données
    db_configs = {
        'postgresql': {
            'driver': 'org.postgresql.Driver',
            'url': 'jdbc:postgresql://postgres:5432/dbname',
            'dialect': 'org.hibernate.dialect.PostgreSQLDialect'
        },
        'mysql': {
            'driver': 'com.mysql.cj.jdbc.Driver',
            'url': 'jdbc:mysql://mysql:3306/dbname',
            'dialect': 'org.hibernate.dialect.MySQLDialect'
        },
        'mariadb': {
            'driver': 'org.mariadb.jdbc.Driver',
            'url': 'jdbc:mariadb://mariadb:3306/dbname',
            'dialect': 'org.hibernate.dialect.MariaDBDialect'
        },
        'h2': {
            'driver': 'org.h2.Driver',
            'url': 'jdbc:h2:mem:testdb',
            'dialect': 'org.hibernate.dialect.H2Dialect'
        }
    }
    
    db_config = db_configs[database]
    
    swagger_config = ""
    if config.get('swagger', False):
        swagger_config = """
  # Springdoc OpenAPI Configuration
  springdoc:
    swagger-ui:
      enabled: true
      path: /swagger-ui.html
    api-docs:
      path: /v3/api-docs
    show-actuator: false
"""
    
    yml_content = f"""spring:
  application:
    name: spring-boot-app
  
  datasource:
    driver-class-name: {db_config['driver']}
    url: {db_config['url']}
    username: user
    password: password
  
  jpa:
    hibernate:
      ddl-auto: update
    show-sql: true
    properties:
      hibernate:
        dialect: {db_config['dialect']}
        format_sql: true{swagger_config}

server:
  port: 8080

logging:
  level:
    root: INFO
    org.hibernate.SQL: DEBUG
"""
    
    resources_path = os.path.join(base_path, 'src/main/resources')
    os.makedirs(resources_path, exist_ok=True)
    
    with open(os.path.join(resources_path, 'application.yml'), 'w', encoding='utf-8') as f:
        f.write(yml_content)
    
    print("  📄 application.yml généré")


def generate_swagger_dependencies(config: Dict) -> str:
    """
    Génère les dépendances Swagger/Redoc si activé.
    MODIFIÉ: Une seule dépendance Maven nécessaire.
    """
    if not config.get('swagger', False):
        return ""
    
    return """<!-- Springdoc OpenAPI (Swagger + Redoc) -->
        <dependency>
            <groupId>org.springdoc</groupId>
            <artifactId>springdoc-openapi-starter-webmvc-ui</artifactId>
            <version>2.3.0</version>
        </dependency>
        
"""


def generate_pom_xml(base_path: str, config: Dict):
    """
    Génère le pom.xml enrichi avec dépendances avancées et plugins optimisés.
    
    Inclut :
    - Gestion des versions centralisée
    - Dépendances de sécurité, monitoring, caching
    - Plugins de qualité de code et couverture
    - Support Docker et profils Maven
    """
    java_version = config['javaVersion']
    database = config['database']
    
    # ========================================================================
    # VERSIONS CENTRALISÉES
    # ========================================================================
    versions = {
        'spring.boot': '3.2.0',
        'mapstruct': '1.5.5.Final',
        'lombok.mapstruct.binding': '0.2.0',
        'testcontainers': '1.19.3',
        'modelmapper': '3.2.0',
        'jackson': '2.15.3',
        'commons.lang3': '3.14.0',
        'guava': '32.1.3-jre',
        'caffeine': '3.1.8',
        'resilience4j': '2.1.0'
    }
    
    # ========================================================================
    # DÉPENDANCES BASE DE DONNÉES
    # ========================================================================
    db_dependencies = {
        'postgresql': '''<!-- PostgreSQL Driver -->
        <dependency>
            <groupId>org.postgresql</groupId>
            <artifactId>postgresql</artifactId>
            <scope>runtime</scope>
        </dependency>''',
        
        'mysql': '''<!-- MySQL Driver -->
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>''',
        
        'mariadb': '''<!-- MariaDB Driver -->
        <dependency>
            <groupId>org.mariadb.jdbc</groupId>
            <artifactId>mariadb-java-client</artifactId>
            <scope>runtime</scope>
        </dependency>''',
        
        'h2': '''<!-- H2 Database (Embedded) -->
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>runtime</scope>
        </dependency>'''
    }
    
    # ========================================================================
    # DÉPENDANCES CONDITIONNELLES
    # ========================================================================
    swagger_deps = generate_swagger_dependencies(config)
    
    # Dépendances optionnelles avancées
    optional_deps = ""
    
    # Support MapStruct (mapping avancé)
    if config.get('use_mapstruct', True):
        optional_deps += f"""
        <!-- MapStruct (Mapping avancé) -->
        <dependency>
            <groupId>org.mapstruct</groupId>
            <artifactId>mapstruct</artifactId>
            <version>${{mapstruct.version}}</version>
        </dependency>
        <dependency>
            <groupId>org.mapstruct</groupId>
            <artifactId>mapstruct-processor</artifactId>
            <version>${{mapstruct.version}}</version>
            <scope>provided</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok-mapstruct-binding</artifactId>
            <version>${{lombok.mapstruct.binding.version}}</version>
            <scope>provided</scope>
        </dependency>
"""
    
    # Support Caching
    if config.get('enable_cache', True):
        optional_deps += """
        <!-- Caching avec Caffeine -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-cache</artifactId>
        </dependency>
        <dependency>
            <groupId>com.github.ben-manes.caffeine</groupId>
            <artifactId>caffeine</artifactId>
            <version>${caffeine.version}</version>
        </dependency>
"""
    
    # Support Resilience (Circuit Breaker, Retry, etc.)
    if config.get('enable_resilience', False):
        optional_deps += """
        <!-- Resilience4j (Circuit Breaker, Retry, Rate Limiter) -->
        <dependency>
            <groupId>io.github.resilience4j</groupId>
            <artifactId>resilience4j-spring-boot3</artifactId>
            <version>${resilience4j.version}</version>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-aop</artifactId>
        </dependency>
"""
    
    # Support Monitoring (Actuator + Micrometer)
    if config.get('enable_monitoring', True):
        optional_deps += """
        <!-- Monitoring et Métriques -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-actuator</artifactId>
        </dependency>
        <dependency>
            <groupId>io.micrometer</groupId>
            <artifactId>micrometer-registry-prometheus</artifactId>
        </dependency>
"""
    
    # Support Security
    if config.get('enable_security', False):
        optional_deps += """
        <!-- Spring Security -->
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>0.12.3</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>0.12.3</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>0.12.3</version>
            <scope>runtime</scope>
        </dependency>
"""
    
    # ========================================================================
    # GÉNÉRATION DU POM.XML
    # ========================================================================
    pom_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 
         https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>
    
    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>{versions['spring.boot']}</version>
        <relativePath/>
    </parent>
    
    <groupId>{config['basePackage']}</groupId>
    <artifactId>spring-boot-app</artifactId>
    <version>1.0.0-SNAPSHOT</version>
    <packaging>jar</packaging>
    
    <name>Spring Boot Application</name>
    <description>Application Spring Boot générée automatiquement</description>
    
    <properties>
        <!-- Java Version -->
        <java.version>{java_version}</java.version>
        <maven.compiler.source>{java_version}</maven.compiler.source>
        <maven.compiler.target>{java_version}</maven.compiler.target>
        <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
        <project.reporting.outputEncoding>UTF-8</project.reporting.outputEncoding>
        
        <!-- Dependency Versions -->
        <mapstruct.version>{versions['mapstruct']}</mapstruct.version>
        <lombok.mapstruct.binding.version>{versions['lombok.mapstruct.binding']}</lombok.mapstruct.binding.version>
        <testcontainers.version>{versions['testcontainers']}</testcontainers.version>
        <modelmapper.version>{versions['modelmapper']}</modelmapper.version>
        <jackson.version>{versions['jackson']}</jackson.version>
        <commons.lang3.version>{versions['commons.lang3']}</commons.lang3.version>
        <guava.version>{versions['guava']}</guava.version>
        <caffeine.version>{versions['caffeine']}</caffeine.version>
        <resilience4j.version>{versions['resilience4j']}</resilience4j.version>
        
        <!-- Plugin Versions -->
        <jacoco.version>0.8.11</jacoco.version>
        <sonar.version>3.10.0.2594</sonar.version>
        <maven.surefire.version>3.2.2</maven.surefire.version>
    </properties>
    
    <dependencies>
        <!-- ============================================================ -->
        <!-- SPRING BOOT STARTERS                                         -->
        <!-- ============================================================ -->
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-jpa</artifactId>
        </dependency>
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        
        <!-- ============================================================ -->
        <!-- DATABASE                                                     -->
        <!-- ============================================================ -->
        
        {db_dependencies[database]}
        
        <!-- Flyway Migration (optionnel) -->
        <dependency>
            <groupId>org.flywaydb</groupId>
            <artifactId>flyway-core</artifactId>
        </dependency>
        
        <!-- ============================================================ -->
        <!-- DOCUMENTATION API                                            -->
        <!-- ============================================================ -->
        
        {swagger_deps}
        
        <!-- ============================================================ -->
        <!-- UTILITIES                                                    -->
        <!-- ============================================================ -->
        
        <!-- Lombok -->
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        
        <!-- Apache Commons Lang3 -->
        <dependency>
            <groupId>org.apache.commons</groupId>
            <artifactId>commons-lang3</artifactId>
            <version>${{commons.lang3.version}}</version>
        </dependency>
        
        <!-- Google Guava -->
        <dependency>
            <groupId>com.google.guava</groupId>
            <artifactId>guava</artifactId>
            <version>${{guava.version}}</version>
        </dependency>
        
        <!-- ModelMapper (alternative à MapStruct) -->
        <dependency>
            <groupId>org.modelmapper</groupId>
            <artifactId>modelmapper</artifactId>
            <version>${{modelmapper.version}}</version>
        </dependency>
        
        <!-- Jackson Datatype JSR310 (Java 8 Date/Time) -->
        <dependency>
            <groupId>com.fasterxml.jackson.datatype</groupId>
            <artifactId>jackson-datatype-jsr310</artifactId>
        </dependency>
        
        <!-- ============================================================ -->
        <!-- OPTIONAL DEPENDENCIES                                        -->
        <!-- ============================================================ -->
        {optional_deps}
        
        <!-- ============================================================ -->
        <!-- TESTING                                                      -->
        <!-- ============================================================ -->
        
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
        </dependency>
        
        <!-- REST Assured (Tests API REST) -->
        <dependency>
            <groupId>io.rest-assured</groupId>
            <artifactId>rest-assured</artifactId>
            <scope>test</scope>
        </dependency>
        
        <!-- Testcontainers -->
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>testcontainers</artifactId>
            <version>${{testcontainers.version}}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>junit-jupiter</artifactId>
            <version>${{testcontainers.version}}</version>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.testcontainers</groupId>
            <artifactId>{get_testcontainer_module(database)}</artifactId>
            <version>${{testcontainers.version}}</version>
            <scope>test</scope>
        </dependency>
        
        <!-- H2 pour tests (si DB principale n'est pas H2) -->
        {'' if database == 'h2' else '''<dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>'''}
    </dependencies>
    
    <build>
        <finalName>${{project.artifactId}}-${{project.version}}</finalName>
        
        <plugins>
            <!-- ======================================================== -->
            <!-- SPRING BOOT PLUGIN                                       -->
            <!-- ======================================================== -->
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
                <configuration>
                    <excludes>
                        <exclude>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                        </exclude>
                    </excludes>
                    <image>
                        <name>${{project.groupId}}/${{project.artifactId}}:${{project.version}}</name>
                    </image>
                </configuration>
            </plugin>
            
            <!-- ======================================================== -->
            <!-- MAVEN COMPILER PLUGIN                                    -->
            <!-- ======================================================== -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-compiler-plugin</artifactId>
                <version>3.11.0</version>
                <configuration>
                    <source>${{java.version}}</source>
                    <target>${{java.version}}</target>
                    <annotationProcessorPaths>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok</artifactId>
                            <version>${{lombok.version}}</version>
                        </path>
                        {'''<path>
                            <groupId>org.mapstruct</groupId>
                            <artifactId>mapstruct-processor</artifactId>
                            <version>${mapstruct.version}</version>
                        </path>
                        <path>
                            <groupId>org.projectlombok</groupId>
                            <artifactId>lombok-mapstruct-binding</artifactId>
                            <version>${lombok.mapstruct.binding.version}</version>
                        </path>''' if config.get('use_mapstruct', True) else ''}
                    </annotationProcessorPaths>
                </configuration>
            </plugin>
            
            <!-- ======================================================== -->
            <!-- SUREFIRE (Tests Unitaires)                              -->
            <!-- ======================================================== -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-surefire-plugin</artifactId>
                <version>${{maven.surefire.version}}</version>
                <configuration>
                    <includes>
                        <include>**/*Test.java</include>
                        <include>**/*Tests.java</include>
                    </includes>
                </configuration>
            </plugin>
            
            <!-- ======================================================== -->
            <!-- JACOCO (Couverture de code)                             -->
            <!-- ======================================================== -->
            <plugin>
                <groupId>org.jacoco</groupId>
                <artifactId>jacoco-maven-plugin</artifactId>
                <version>${{jacoco.version}}</version>
                <executions>
                    <execution>
                        <id>prepare-agent</id>
                        <goals>
                            <goal>prepare-agent</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>report</id>
                        <phase>test</phase>
                        <goals>
                            <goal>report</goal>
                        </goals>
                    </execution>
                    <execution>
                        <id>jacoco-check</id>
                        <goals>
                            <goal>check</goal>
                        </goals>
                        <configuration>
                            <rules>
                                <rule>
                                    <element>PACKAGE</element>
                                    <limits>
                                        <limit>
                                            <counter>LINE</counter>
                                            <value>COVEREDRATIO</value>
                                            <minimum>0.50</minimum>
                                        </limit>
                                    </limits>
                                </rule>
                            </rules>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
            
            <!-- ======================================================== -->
            <!-- SONARQUBE                                                -->
            <!-- ======================================================== -->
            <plugin>
                <groupId>org.sonarsource.scanner.maven</groupId>
                <artifactId>sonar-maven-plugin</artifactId>
                <version>${{sonar.version}}</version>
            </plugin>
            
            <!-- ======================================================== -->
            <!-- MAVEN ENFORCER (Vérifications)                          -->
            <!-- ======================================================== -->
            <plugin>
                <groupId>org.apache.maven.plugins</groupId>
                <artifactId>maven-enforcer-plugin</artifactId>
                <version>3.4.1</version>
                <executions>
                    <execution>
                        <id>enforce-versions</id>
                        <goals>
                            <goal>enforce</goal>
                        </goals>
                        <configuration>
                            <rules>
                                <requireMavenVersion>
                                    <version>[3.6.3,)</version>
                                </requireMavenVersion>
                                <requireJavaVersion>
                                    <version>[{java_version},)</version>
                                </requireJavaVersion>
                            </rules>
                        </configuration>
                    </execution>
                </executions>
            </plugin>
        </plugins>
    </build>
    
    <!-- ================================================================ -->
    <!-- PROFILS MAVEN                                                    -->
    <!-- ================================================================ -->
    <profiles>
        <!-- Profil Développement -->
        <profile>
            <id>dev</id>
            <activation>
                <activeByDefault>true</activeByDefault>
            </activation>
            <properties>
                <spring.profiles.active>dev</spring.profiles.active>
            </properties>
        </profile>
        
        <!-- Profil Production -->
        <profile>
            <id>prod</id>
            <properties>
                <spring.profiles.active>prod</spring.profiles.active>
            </properties>
            <build>
                <plugins>
                    <plugin>
                        <groupId>org.springframework.boot</groupId>
                        <artifactId>spring-boot-maven-plugin</artifactId>
                        <configuration>
                            <executable>true</executable>
                        </configuration>
                    </plugin>
                </plugins>
            </build>
        </profile>
        
        <!-- Profil Docker -->
        <profile>
            <id>docker</id>
            <build>
                <plugins>
                    <plugin>
                        <groupId>org.springframework.boot</groupId>
                        <artifactId>spring-boot-maven-plugin</artifactId>
                        <executions>
                            <execution>
                                <goals>
                                    <goal>build-image</goal>
                                </goals>
                            </execution>
                        </executions>
                    </plugin>
                </plugins>
            </build>
        </profile>
    </profiles>
</project>
"""
    
    with open(os.path.join(base_path, 'pom.xml'), 'w', encoding='utf-8') as f:
        f.write(pom_content)
    
    print("  📄 pom.xml enrichi généré")
    print(f"     • Java {java_version}")
    print(f"     • Database: {database}")
    print(f"     • Swagger: {'✓' if config.get('swagger') else '✗'}")
    print(f"     • MapStruct: {'✓' if config.get('use_mapstruct', True) else '✗'}")
    print(f"     • Caching: {'✓' if config.get('enable_cache', True) else '✗'}")
    print(f"     • Monitoring: {'✓' if config.get('enable_monitoring', True) else '✗'}")
    print(f"     • Security: {'✓' if config.get('enable_security', False) else '✗'}")


def get_testcontainer_module(database: str) -> str:
    """Retourne le module Testcontainers approprié selon la base de données."""
    mapping = {
        'postgresql': 'postgresql',
        'mysql': 'mysql',
        'mariadb': 'mariadb',
        'h2': 'postgresql'  # Fallback
    }
    return mapping.get(database, 'postgresql')

def generate_swagger_config(base_path: str, config: Dict):
    """
    Génère la classe de configuration Swagger/OpenAPI.
    MODIFIÉ: Configuration simplifiée compatible Spring Boot 3
    """
    if not config.get('swagger', False):
        return
    
    package = config['basePackage']
    package_path = package.replace('.', '/')
    
    swagger_config_content = f"""package {package};

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.License;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class SpringdocOpenApiConfig {{

    @Bean
    public OpenAPI customOpenAPI() {{
        return new OpenAPI()
                .info(new Info()
                        .title("Spring Boot API")
                        .description("Documentation API générée avec Springdoc OpenAPI")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("API Support")
                                .email("support@example.com"))
                        .license(new License()
                                .name("Apache 2.0")
                                .url("https://www.apache.org/licenses/LICENSE-2.0.html")));
    }}
}}
"""
    
    config_path = os.path.join(base_path, 'src/main/java', package_path)
    os.makedirs(config_path, exist_ok=True)
    
    with open(os.path.join(config_path, 'SpringdocOpenApiConfig.java'), 'w', encoding='utf-8') as f:
        f.write(swagger_config_content)
    
    print("  📚 SpringdocOpenApiConfig.java généré")

def generate_redoc_html(base_path: str, config: Dict):
    """
    Génère le fichier ReDoc HTML statique dans src/main/resources/static/.
    NOUVEAU: ReDoc accessible via /redoc.html
    """
    if not config.get('swagger', False):
        return
    
    redoc_html = """<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>API Documentation - ReDoc</title>
    <style>
        body {
            margin: 0;
            padding: 0;
        }
    </style>
</head>
<body>
    <redoc spec-url="/v3/api-docs"></redoc>
    <script src="https://cdn.redoc.ly/redoc/latest/bundles/redoc.standalone.js"></script>
</body>
</html>
"""
    
    static_path = os.path.join(base_path, 'src/main/resources/static')
    os.makedirs(static_path, exist_ok=True)
    
    with open(os.path.join(static_path, 'redoc.html'), 'w', encoding='utf-8') as f:
        f.write(redoc_html)
    
    print("  📄 redoc.html généré")

def generate_main_application(base_path: str, config: Dict):
    """
    Génere la classe principale Spring Boot Application.
    """
    package = config['basePackage']
    package_path = package.replace('.', '/')
    
    app_content = f"""package {package};

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class Application {{

    public static void main(String[] args) {{
        SpringApplication.run(Application.class, args);
    }}
}}
"""
    
    main_path = os.path.join(base_path, 'src/main/java', package_path)
    os.makedirs(main_path, exist_ok=True)
    
    with open(os.path.join(main_path, 'Application.java'), 'w') as f:
        f.write(app_content)
    
    print("  📄 Application.java généré")


def generate_dockerfile(base_path: str, config: Dict):
    """
    Génere le Dockerfile multi-stage pour Spring Boot.
    """
    if not config.get('docker', False):
        return
    
    java_version = config['javaVersion']
    
    dockerfile_content = f"""# Stage 1: Build
FROM maven:3.9-eclipse-temurin-{java_version} AS build
WORKDIR /app

COPY pom.xml .
RUN mvn dependency:go-offline

COPY src ./src
RUN mvn clean package -DskipTests

# Stage 2: Runtime
FROM eclipse-temurin:{java_version}-jre-alpine
WORKDIR /app

COPY --from=build /app/target/*.jar app.jar

EXPOSE 8080

ENTRYPOINT ["java", "-jar", "app.jar"]
"""
    
    with open(os.path.join(base_path, 'Dockerfile'), 'w') as f:
        f.write(dockerfile_content)
    
    print("  🐳 Dockerfile généré")


def generate_dockerignore(base_path: str, config: Dict):
    """
    Génere le fichier .dockerignore.
    """
    if not config.get('docker', False):
        return
    
    dockerignore_content = """target/
.mvn/
.git/
.gitignore
*.md
.idea/
*.iml
.vscode/
"""
    
    with open(os.path.join(base_path, '.dockerignore'), 'w') as f:
        f.write(dockerignore_content)
    
    print("  🐳 .dockerignore généré")


def generate_docker_compose(base_path: str, config: Dict):
    """
    Génere le docker-compose.yml avec la base de données.
    """
    if not config.get('docker', False):
        return
    
    database = config['database']
    
    # Configuration selon la base de données
    db_services = {
        'postgresql': """  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: dbname
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - app-network

volumes:
  postgres_data:""",
        
        'mysql': """  mysql:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: dbname
      MYSQL_USER: user
      MYSQL_PASSWORD: password
      MYSQL_ROOT_PASSWORD: rootpassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
    networks:
      - app-network

volumes:
  mysql_data:""",
        
        'mariadb': """  mariadb:
    image: mariadb:11
    environment:
      MARIADB_DATABASE: dbname
      MARIADB_USER: user
      MARIADB_PASSWORD: password
      MARIADB_ROOT_PASSWORD: rootpassword
    ports:
      - "3306:3306"
    volumes:
      - mariadb_data:/var/lib/mysql
    networks:
      - app-network

volumes:
  mariadb_data:"""
    }
    
    if database == 'h2':
        print("  ℹ️  docker-compose.yml non généré (H2 est embarqué)")
        return
    
    compose_content = f"""

services:
  app:
    build: .
    ports:
      - "8080:8080"
    depends_on:
        - {database}
    networks:
      - app-network

{db_services[database]}

networks:
  app-network:
    driver: bridge
"""
    
    with open(os.path.join(base_path, 'docker-compose.yml'), 'w') as f:
        f.write(compose_content)
    
    print("  🐳 docker-compose.yml généré")


def generate_gitignore(base_path: str):
    """
    Génere le fichier .gitignore standard pour Spring Boot.
    """
    gitignore_content = """# Maven
target/
pom.xml.tag
pom.xml.releaseBackup
pom.xml.versionsBackup
pom.xml.next
release.properties
dependency-reduced-pom.xml
buildNumber.properties
.mvn/timing.properties
.mvn/wrapper/maven-wrapper.jar

# IntelliJ IDEA
.idea/
*.iws
*.iml
*.ipr

# Eclipse
.settings/
.project
.classpath

# VS Code
.vscode/

# macOS
.DS_Store

# Logs
*.log

# Application
application-local.yml
application-local.properties
"""
    
    with open(os.path.join(base_path, '.gitignore'), 'w') as f:
        f.write(gitignore_content)
    
    print("  📄 .gitignore généré")


def generate_readme(base_path: str, config: Dict):
    """
    Génère un fichier README.md avec les instructions.
    MODIFIÉ: Ajout section documentation API
    """
    project_name = config['basePackage'].split('.')[-1]
    readme_content = f"""# {project_name.capitalize()} Spring Boot Application

## Description
Projet Spring Boot généré automatiquement avec architecture modulaire.

## Technologies
- **Java**: {config['javaVersion']}
- **Spring Boot**: 3.2.0
- **Database**: {config['database']}
- **Build Tool**: Maven
"""

    if config.get('swagger', False):
        readme_content += """- **Documentation API**: Springdoc OpenAPI 2.3.0
"""

    readme_content += """
## Démarrage

### Prérequis
- Java {config['javaVersion']}+
- Maven 3.6+
"""
    
    if config.get('docker', False):
        readme_content += """
### Avec Docker
```bash
# Build et lancement
docker-compose up --build

# Arrêt
docker-compose down
```
"""
    
    readme_content += """
### Sans Docker
```bash
# Compilation
mvn clean install

# Lancement
mvn spring-boot:run
```
"""

    if config.get('swagger', False):
        readme_content += """
## Documentation API

Une fois l'application démarrée, accédez à :

- **Swagger UI**: [http://localhost:8080/swagger-ui.html](http://localhost:8080/swagger-ui.html)
- **ReDoc**: [http://localhost:8080/redoc.html](http://localhost:8080/redoc.html)
- **OpenAPI JSON**: [http://localhost:8080/v3/api-docs](http://localhost:8080/v3/api-docs)
"""

    readme_content += """
## API Endpoints
"""
    
    for module in config.get('modules', []):
        module_name = module['name']
        readme_content += f"""
### {module_name.capitalize()}
- `POST   /api/{module_name}s` - Créer
- `GET    /api/{module_name}s` - Lister tous
- `GET    /api/{module_name}s/{{id}}` - Obtenir par ID
- `PUT    /api/{module_name}s/{{id}}` - Modifier
- `DELETE /api/{module_name}s/{{id}}` - Supprimer
"""
    
    readme_content += """
## Structure du projet
```
src/
├── main/
│   ├── java/
│   │   └── [package]/
│   │       ├── Application.java
│   │       ├── SpringdocOpenApiConfig.java
│   │       └── [modules]/
│   └── resources/
│       ├── application.yml
│       └── static/
│           └── redoc.html
└── test/
```

## Configuration
Modifier `src/main/resources/application.yml` selon vos besoins.

## License
MIT
"""
    
    with open(os.path.join(base_path, 'README.md'), 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print("  📄 README.md généré")

def generate_project(config: Dict):
    """
    Génère le projet Spring Boot complet à partir de la configuration.
    MODIFIÉ: Ajout génération redoc.html
    """
    print("\n" + "="*60)
    print("GÉNÉRATION DU PROJET SPRING BOOT")
    print("="*60)
    output_dir = config['basePackage']
    base_path = os.path.abspath(output_dir)
    
    # Création du répertoire racine
    if os.path.exists(base_path):
        print(f"\n⚠️  Le répertoire '{output_dir}' existe déjà")
        overwrite = input("Écraser ? (y/n): ").strip().lower()
        if overwrite != 'y':
            print("❌ Génération annulée")
            return
        import shutil
        shutil.rmtree(base_path)
    
    os.makedirs(base_path)
    print(f"\n📁 Répertoire créé: {base_path}")
    
    # Génération des fichiers techniques de base
    print("\n🔧 Génération des fichiers techniques...")
    generate_pom_xml(base_path, config)
    generate_application_yml(base_path, config)
    generate_main_application(base_path, config)
    generate_gitignore(base_path)
    
    if config.get('docker', False):
        generate_dockerfile(base_path, config)
        generate_dockerignore(base_path, config)
        generate_docker_compose(base_path, config)
    
    # Génération des modules
    print(f"\n📦 Génération de {len(config['modules'])} module(s)...")
    
    for module in config['modules']:
        module_name = module['name']
        print(f"\n  ➤ Module: {module_name}")
        
        create_directory_structure(base_path, config['basePackage'], module)
        
        generate_entity(base_path, config['basePackage'], module)
        generate_dto(base_path, config['basePackage'], module, config)
        generate_repository(base_path, config['basePackage'], module)
        generate_mapper(base_path, config['basePackage'], module)
        generate_service(base_path, config['basePackage'], module)
        generate_service_impl(base_path, config['basePackage'], module)
        generate_controller(base_path, config['basePackage'], module, config)
    
    # Génération de la configuration Swagger
    if config.get('swagger', False):
        print("\n📚 Génération de la documentation API...")
        generate_swagger_config(base_path, config)
        generate_redoc_html(base_path, config)  # ✅ AJOUT ICI
    
    # Génération du README
    print("\n📄 Génération de la documentation...")
    generate_readme(base_path, config)
    
    print("\n" + "="*60)
    print("✅ PROJET GÉNÉRÉ AVEC SUCCÈS")
    print("="*60)
    print(f"\n📂 Emplacement: {base_path}")
    print("\n🚀 Prochaines étapes:")
    print("   1. cd " + output_dir)
    
    if config.get('docker', False):
        print("   2. docker-compose up --build")
    else:
        print("   2. mvn clean install")
        print("   3. mvn spring-boot:run")
    
    if config.get('swagger', False):
        print("\n📚 Documentation API:")
        print("   • Swagger UI: http://localhost:8080/swagger-ui.html")
        print("   • ReDoc:      http://localhost:8080/redoc.html")
        print("   • OpenAPI:    http://localhost:8080/v3/api-docs")
    
    print(f"\n📖 Consultez {output_dir}/README.md pour plus d'informations\n")


def save_config(config: Dict, filename: str = "project-config.json"):
    """
    Sauvegarde la configuration dans un fichier JSON.
    Utile pour régénérer le projet plus tard.
    """
    with open(filename, 'w') as f:
        json.dump(config, f, indent=2)
    print(f"\n💾 Configuration sauvegardée dans: {filename}")


def main():
    """
    Point d'entrée principal du générateur interactif.
    """
    print("""
╔══════════════════════════════════════════════════════════╗
║                                                          ║
║    GÉNÉRATEUR SPRING BOOT INTERACTIF                    ║
║    Version 2.0 - Mode CLI Avancé                        ║
║                                                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # Étape 1: Configuration du projet
    config = prompt_project_config()
    
    # Étape 2: Création des modules
    print("\n" + "="*60)
    print("CRÉATION DES MODULES")
    print("="*60)
    
    modules = collect_all_modules()
    
    if not modules:
        print("\n⚠️  Aucun module créé. Génération du projet de base uniquement.")
    
    config['modules'] = modules
    
    # Étape 3: Confirmation finale
    print("\n" + "="*60)
    print("RÉSUMÉ DE LA CONFIGURATION")
    print("="*60)
    print(f"\n📦 Package de base: {config['basePackage']}")
    print(f"☕ Java: {config['javaVersion']}")
    print(f"🗄️  Database: {config['database']}")
    print(f"🐳 Docker: {'Activé' if config['docker'] else 'Désactivé'}")
    print(f"\n📋 Modules ({len(modules)}):")
    
    for module in modules:
        print(f"   • {module['name']}: {', '.join(module['packages'])}")
    
    print("\n" + "-"*60)
    confirm = input("Générer le projet avec cette configuration ? (y/n): ").strip().lower()
    
    if confirm != 'y':
        print("\n❌ Génération annulée par l'utilisateur")
        return
    
    # Étape 4: Génération du projet
    generate_project(config)
    
    # Étape 5: Sauvegarde de la configuration
    save = input("\nSauvegarder la configuration ? (y/n): ").strip().lower()
    if save == 'y':
        save_config(config)


# ============================================================================
# EXÉCUTION
# ============================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Génération interrompue par l'utilisateur")
    except Exception as e:
        print(f"\n\n💥 Erreur: {e}")
        import traceback
        traceback.print_exc()